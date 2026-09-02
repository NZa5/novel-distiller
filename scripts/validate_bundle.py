#!/usr/bin/env python3
"""Validate a complete, reusable Novel Distiller analysis bundle."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence

import corpus_index
import analyze_style
import validate_profile
import render_profile


METRICS_SCHEMA_VERSION = "1.1"
ARTIFACT_SCHEMA_VERSION = "1.0"
ARTIFACT_HEADER_RE = re.compile(r"<!--\s*novel-distiller-artifact\s+(\{.*?\})\s*-->")
METRICS_HEADER_RE = re.compile(r"<!--\s*novel-distiller-metrics\s+(\{.*?\})\s*-->")
ALLOWED_METRIC_REF_RE = re.compile(r"^/(?:aggregate|source_ranges)(?:/|$)")


def json_pointer(value: object, pointer: str) -> object:
    if not pointer.startswith("/"):
        raise ValueError(f"指标引用必须是 JSON Pointer：{pointer}")
    current = value
    for raw_part in pointer.split("/")[1:]:
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            raise ValueError(f"指标引用不存在：{pointer}")
    return current


def parse_header(text: str, pattern: re.Pattern[str], label: str, errors: list[str]) -> dict:
    match = pattern.search(text[:4096])
    if not match:
        errors.append(f"{label} 缺少绑定元数据头")
        return {}
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        errors.append(f"{label} 绑定元数据不是有效 JSON：{exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} 绑定元数据必须是对象")
        return {}
    return value


def identifier_present(text: str, identifier: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(identifier)}(?![\w-])", text) is not None


def validate_bundle(
    profile: dict,
    evidence: Sequence[dict],
    index_records: Sequence[dict],
    manifest_path: Path,
    ledger_path: Path,
    metrics_path: Path,
    metrics_markdown_path: Path,
    analysis_path: Path,
    packet_path: Path,
    index_path: Path,
    comparison_index_records: Sequence[dict] | None = None,
    holdout_index_records: Sequence[dict] | None = None,
    holdout_index_path: Path | None = None,
    holdout_commitment_path: Path | None = None,
    holdout_reveal_path: Path | None = None,
    provisional_profile_path: Path | None = None,
) -> list[str]:
    errors = validate_profile.validate_profile(
        profile,
        evidence,
        index_records,
        comparison_index_records,
        holdout_index_records,
    )

    manifest_hash = validate_profile.file_sha256(manifest_path)
    if profile.get("corpus", {}).get("manifest_sha256") != manifest_hash:
        errors.append("corpus.manifest_sha256 与当前语料清单不一致")
    try:
        corpus_index.load_manifest(manifest_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"语料清单无效：{exc}")
    for record in list(index_records) + list(holdout_index_records or []):
        if isinstance(record, dict) and record.get("preprocessing", {}).get("manifest_sha256") != manifest_hash:
            errors.append(f"索引块未绑定当前语料清单：{record.get('chunk_id')}")
    # Hash declarations alone cannot prove that indexed text is still source text.
    try:
        supplied_records = list(index_records) + list(holdout_index_records or [])
        configurations: dict[tuple[str, int, bool, bool], list[dict]] = {}
        for record in supplied_records:
            preprocessing = record.get('preprocessing', {})
            config = (record['source_path'], preprocessing.get('chunk_chars', 1800),
                      preprocessing.get('reflow_hard_wrap', False), preprocessing.get('strip_annotations', False))
            configurations.setdefault(config, []).append(record)
        for (source_path, chunk_chars, reflow, strip), supplied in configurations.items():
            rebuilt = corpus_index.build_index([Path(source_path)], chunk_chars, reflow, strip, manifest_path)
            expected = {record['chunk_id']: record for record in rebuilt}
            if set(expected) != {record['chunk_id'] for record in supplied}:
                errors.append(f'索引未完整对应来源重建结果：{source_path}')
            for record in supplied:
                original = expected.get(record['chunk_id'], {})
                for field in ('text', 'work_id', 'sample_ids', 'scene_ids', 'chapter_ids', 'scene_types',
                              'paragraph_start', 'paragraph_end', 'content_char_start', 'content_char_end',
                              'preprocessing_fingerprint'):
                    if record.get(field) != original.get(field):
                        errors.append(f"索引块 {record['chunk_id']} 的 {field} 与来源重建结果不一致")
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        errors.append(f'来源重建核验失败：{exc}')

    try:
        ledger = corpus_index.read_ledger(ledger_path)
        corpus_index.verify_ledger_index(ledger, index_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"取样账本无效：{exc}")
        ledger = {"items": []}

    ledger_by_chunk = {
        item.get("chunk_id"): item
        for item in ledger.get("items", [])
        if isinstance(item, dict) and isinstance(item.get("chunk_id"), str)
    }
    indexed_by_chunk = {record.get('chunk_id'): record for record in list(index_records) + list(holdout_index_records or [])}
    for chunk_id, item in ledger_by_chunk.items():
        record = indexed_by_chunk.get(chunk_id)
        if record is None:
            errors.append(f'账本文本块不存在于分析或留出索引：{chunk_id}')
            continue
        for field in ('work_id', 'sample_ids', 'chapter_ids', 'scene_ids', 'scene_types', 'paragraph_start', 'paragraph_end'):
            if item.get(field) != record.get(field):
                errors.append(f'账本 {chunk_id} 的 {field} 与索引不一致')
    holdout_chunks = {item['chunk_id'] for item in ledger_by_chunk.values() if item.get('role') == 'holdout'}
    if holdout_chunks or profile.get('corpus', {}).get('holdout_sample_ids'):
        if ledger.get('holdout_separation') != 'separate':
            errors.append("留出验证必须使用 prepare 生成的分离索引")
        if not all((holdout_index_path, holdout_commitment_path, holdout_reveal_path, provisional_profile_path)):
            errors.append("留出验证缺少 holdout-index/commitment/reveal/provisional-profile")
        else:
            try:
                commitment = json.loads(holdout_commitment_path.read_text(encoding='utf-8-sig'))
                reveal = json.loads(holdout_reveal_path.read_text(encoding='utf-8-sig'))
                provisional = json.loads(provisional_profile_path.read_text(encoding='utf-8-sig'))
                if not all(isinstance(value, dict) for value in (commitment, reveal, provisional)):
                    raise ValueError('留出记录和初稿必须是 JSON 对象')
                holdout_hash = validate_profile.file_sha256(holdout_index_path)
                commitment_hash = validate_profile.file_sha256(holdout_commitment_path)
                provisional_hash = validate_profile.file_sha256(provisional_profile_path)
                if commitment.get('schema_version') != corpus_index.HOLDOUT_COMMITMENT_SCHEMA_VERSION or reveal.get('schema_version') != corpus_index.HOLDOUT_REVEAL_SCHEMA_VERSION:
                    errors.append('留出承诺或解封记录版本不受支持')
                if any(value != holdout_hash for value in (ledger.get('holdout_index_sha256'), commitment.get('holdout_index_sha256'), reveal.get('holdout_index_sha256'))):
                    errors.append('留出索引哈希与承诺、账本或解封记录不一致')
                if any(value != commitment_hash for value in (ledger.get('holdout_commitment_sha256'), reveal.get('commitment_sha256'))):
                    errors.append('留出承诺哈希不一致')
                if commitment.get('manifest_sha256') != manifest_hash:
                    errors.append('留出承诺未绑定当前清单')
                if set(commitment.get('chunk_ids', [])) != holdout_chunks or holdout_chunks != {record.get('chunk_id') for record in holdout_index_records or []}:
                    errors.append('留出块与账本、承诺不一致')
                if reveal.get('provisional_profile_sha256') != provisional_hash or profile.get('corpus', {}).get('provisional_profile_sha256') != provisional_hash:
                    errors.append('初稿已变化或未绑定解封记录')
                if not reveal.get('revealed_at_utc') or provisional.get('profile_id') != profile.get('profile_id'):
                    errors.append('解封时间或初稿 profile_id 无效')
                frozen_rules = {rule.get('rule_id'): rule for rule in provisional.get('rules', []) if isinstance(rule, dict)}
                for rule in profile.get('rules', []):
                    if not isinstance(rule, dict) or rule.get('holdout_status') != 'passed':
                        continue
                    frozen = frozen_rules.get(rule.get('rule_id'), {})
                    if any(rule.get(field) != frozen.get(field) for field in ('dimension', 'trigger', 'observable', 'mechanism', 'action', 'limits')):
                        errors.append(f"规则 {rule.get('rule_id')} 在解封后改变，不能沿用 passed")
            except (OSError, UnicodeError, ValueError, TypeError) as exc:
                errors.append(f'留出记录无效：{exc}')
    pending = [item for item in ledger_by_chunk.values() if item.get("status") == "pending"]
    followup = [item for item in ledger_by_chunk.values() if item.get("status") == "needs_followup"]
    if pending:
        errors.append(f"取样账本仍有 {len(pending)} 个 pending 文本块")
    if followup:
        errors.append(f"取样账本仍有 {len(followup)} 个 needs_followup 文本块")
    skipped = [item for item in ledger_by_chunk.values() if item.get("status") == "skipped"]
    for item in ledger_by_chunk.values():
        if item.get("status") == "skipped" and not item.get("notes"):
            errors.append(f"跳过的文本块必须说明理由：{item.get('chunk_id')}")
    if skipped and profile.get("profile_scope") in {"period", "author"}:
        errors.append("阶段/作者级完整画像不能跳过计划精读文本块")
    if profile.get("profile_scope") in {"period", "author"}:
        if ledger.get("scene_grouping_status") != "complete":
            errors.append("阶段/作者画像要求完整 scene_id 标注")
        if ledger.get("scene_granularity_status") != "acceptable":
            errors.append("阶段/作者画像存在过粗场景组；请把章节细分为真实场景")

    for item in evidence:
        if not isinstance(item, dict) or item.get("corpus_role") == "control":
            continue
        ledger_item = ledger_by_chunk.get(item.get("chunk_id"))
        if ledger_item is None:
            errors.append(f"目标证据不在取样账本中：{item.get('evidence_id')}")
            continue
        if item.get("evidence_role") == "holdout":
            if ledger_item.get("role") != "holdout":
                errors.append(f"留出证据未来自账本留出组：{item.get('evidence_id')}")
        elif ledger_item.get("role") != "analysis" or ledger_item.get("status") != "analyzed":
            errors.append(f"建模证据必须来自已精读文本块：{item.get('evidence_id')}")

    analyzed_sample_ids = {
        sample_id
        for item in ledger_by_chunk.values()
        if item.get("role") == "analysis" and item.get("status") == "analyzed"
        for sample_id in item.get("sample_ids", [])
        if isinstance(sample_id, str)
    }
    for rule in profile.get("rules", []):
        if not isinstance(rule, dict):
            continue
        reviewed_ids = rule.get("counterexample_search", {}).get("reviewed_sample_ids", [])
        missing_reviewed = sorted(
            sample_id for sample_id in reviewed_ids
            if isinstance(sample_id, str) and sample_id not in analyzed_sample_ids
        )
        if missing_reviewed:
            errors.append(
                f"规则 {rule.get('rule_id')} 的反例搜索样本未进入已精读账本：{', '.join(missing_reviewed)}"
            )
    for entry in profile.get('coverage', []):
        if isinstance(entry, dict) and not set(entry.get('reviewed_sample_ids', [])).issubset(analyzed_sample_ids):
            errors.append(f"维度 {entry.get('dimension')} 的检查样本未进入已精读账本")

    saturation = profile.get("analysis_saturation", {})
    ledger_hash = validate_profile.file_sha256(ledger_path)
    if saturation.get("ledger_sha256") != ledger_hash:
        errors.append("analysis_saturation.ledger_sha256 与当前取样账本不一致")
    updates_by_sequence = {
        update.get("sequence"): update
        for update in ledger.get("updates", [])
        if isinstance(update, dict) and isinstance(update.get("sequence"), int)
    }
    analyzed_chunk_ids = {
        item.get("chunk_id")
        for item in ledger_by_chunk.values()
        if item.get("role") == "analysis" and item.get("status") == "analyzed"
    }
    for round_value in saturation.get("rounds", []):
        if not isinstance(round_value, dict):
            continue
        sequences = round_value.get("ledger_update_sequences", [])
        round_updates = [updates_by_sequence.get(sequence) for sequence in sequences]
        if any(update is None or update.get("action") != "extend" for update in round_updates):
            errors.append(f"饱和轮次 {round_value.get('round_id')} 必须绑定有效 extend 更新")
            continue
        update_sample_ids = {
            sample_id
            for update in round_updates
            for sample_id in update.get("added_sample_ids", [])
            if isinstance(sample_id, str)
        }
        if update_sample_ids != set(round_value.get("added_sample_ids", [])):
            errors.append(f"饱和轮次 {round_value.get('round_id')} 的新增样本与账本 extend 更新不一致")
        update_chunk_ids = {
            chunk_id
            for update in round_updates
            for chunk_id in update.get("added_chunk_ids", [])
            if isinstance(chunk_id, str)
        }
        actual_sample_ids = {sample_id for chunk_id in update_chunk_ids
            for sample_id in indexed_by_chunk.get(chunk_id, {}).get('sample_ids', [])}
        if actual_sample_ids != update_sample_ids:
            errors.append(f"饱和轮次 {round_value.get('round_id')} 的新增样本不匹配实际新增索引块")
        if not update_chunk_ids or not update_chunk_ids.issubset(analyzed_chunk_ids):
            errors.append(f"饱和轮次 {round_value.get('round_id')} 的补读文本块尚未全部精读")
    if saturation.get("status") == "limited" and profile.get("profile_scope") == "author":
        errors.append("受限分析不能交付为 author 级完整画像；请继续取样或降低画像层级")
    if saturation.get("status") == "full_corpus":
        indexed_analysis_ids = {
            record.get("chunk_id")
            for record in index_records
            if isinstance(record, dict) and record.get("holdout") is not True
        }
        ledger_analysis_ids = {
            item.get("chunk_id")
            for item in ledger_by_chunk.values()
            if item.get("role") == "analysis" and item.get("status") == "analyzed"
        }
        if indexed_analysis_ids != ledger_analysis_ids:
            errors.append("full_corpus 要求全部非留出索引块都已精读")

    try:
        metrics = json.loads(metrics_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"表层指标 JSON 无效：{exc}")
        metrics = {}
    if metrics.get("schema_version") != METRICS_SCHEMA_VERSION:
        errors.append(f"表层指标 schema_version 必须是 {METRICS_SCHEMA_VERSION}")
    if metrics.get("report_sha256") != analyze_style.report_sha256(metrics):
        errors.append("表层指标 report_sha256 与 JSON 内容不一致")
    metrics_hash = validate_profile.file_sha256(metrics_path)
    if profile.get("surface_ranges", {}).get("metrics_sha256") != metrics_hash:
        errors.append("surface_ranges.metrics_sha256 与当前指标文件不一致")
    metric_source_hashes = {
        item.get("source_sha256")
        for item in metrics.get("sources", [])
        if isinstance(item, dict) and isinstance(item.get("source_sha256"), str)
    }
    expected_metric_hashes = {record.get('source_sha256') for record in index_records}
    if metric_source_hashes != expected_metric_hashes:
        errors.append("表层指标来源与目标语料来源不一致")
    if holdout_chunks and metrics.get('input_mode') != 'analysis_index':
        errors.append('有留出集时必须从分析索引统计，不能读取完整来源正文')
    if metrics.get('input_mode') == 'analysis_index' and metrics.get('index_sha256') != validate_profile.file_sha256(index_path):
        errors.append('表层指标未绑定当前分析索引')
    if metrics.get('errors'):
        errors.append('表层指标存在未解决的来源读取错误')
    try:
        if metrics.get('input_mode') == 'analysis_index':
            rebuilt_metrics = analyze_style.build_report_from_index(index_path)
        else:
            preprocessing = profile.get('corpus', {}).get('preprocessing', {})
            paths = [Path(source['source_path']) for source in metrics.get('sources', [])]
            rebuilt_metrics = analyze_style.build_report(paths, preprocessing.get('reflow_hard_wrap', False),
                preprocessing.get('strip_annotations', False))
        if metrics.get('report_sha256') != rebuilt_metrics['report_sha256']:
            errors.append('表层指标与重新计算结果不一致')
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        errors.append(f'表层指标重算失败：{exc}')

    metric_refs = {
        reference
        for rule in profile.get("rules", [])
        if isinstance(rule, dict)
        for reference in rule.get("metric_refs", [])
        if isinstance(reference, str)
    }
    metric_refs.update(
        reference
        for packet in profile.get("writing_packet", {}).get("packets", [])
        if isinstance(packet, dict)
        for reference in packet.get("surface_range_refs", [])
        if isinstance(reference, str)
    )
    for reference in sorted(metric_refs):
        if not ALLOWED_METRIC_REF_RE.match(reference):
            errors.append(f"指标引用只能指向 aggregate 或 source_ranges 数值：{reference}")
            continue
        try:
            metric_value = json_pointer(metrics, reference)
            if isinstance(metric_value, bool) or not isinstance(metric_value, (int, float)):
                errors.append(f"指标引用必须指向数值叶节点：{reference}")
        except ValueError as exc:
            errors.append(str(exc))
    rules_by_id = {
        rule.get("rule_id"): rule
        for rule in profile.get("rules", [])
        if isinstance(rule, dict) and isinstance(rule.get("rule_id"), str)
    }
    shared_rule_ids = profile.get("writing_packet", {}).get("shared_rule_ids", [])
    for packet in profile.get("writing_packet", {}).get("packets", []):
        if not isinstance(packet, dict):
            continue
        active_rule_ids = set(shared_rule_ids) | set(packet.get("active_rule_ids", []))
        allowed_packet_refs = {
            reference
            for rule_id in active_rule_ids
            for reference in rules_by_id.get(rule_id, {}).get("metric_refs", [])
            if isinstance(reference, str)
        }
        if any(reference not in allowed_packet_refs for reference in packet.get("surface_range_refs", [])):
            errors.append(f"场景包 {packet.get('packet_id')} 引用了未由激活规则解释的指标")
    quote_warning = any(
        item.get("preprocessing", {}).get("quote_pair_warnings")
        for item in metrics.get("sources", [])
        if isinstance(item, dict)
    )
    hard_wrap_warning = any(
        item.get("preprocessing", {}).get("hard_wrap_detected")
        and not item.get("preprocessing", {}).get("hard_wrap_reflow_applied")
        for item in metrics.get("sources", [])
        if isinstance(item, dict)
    )
    if quote_warning and any("/dialogue" in ref or "引号" in ref for ref in metric_refs):
        errors.append("引号警告未解决，不能引用对白或引号指标")
    if hard_wrap_warning and any("/paragraph" in ref for ref in metric_refs):
        errors.append("硬换行警告未解决，不能引用段落指标")

    try:
        metrics_markdown_text = metrics_markdown_path.read_text(encoding="utf-8-sig")
        analysis_text = analysis_path.read_text(encoding="utf-8-sig")
        packet_text = packet_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        errors.append(f"Markdown 交付文件不可读：{exc}")
        metrics_markdown_text = ""
        analysis_text = ""
        packet_text = ""
    metrics_header = parse_header(
        metrics_markdown_text, METRICS_HEADER_RE, "style-metrics.md", errors
    )
    if metrics_header.get("schema_version") != METRICS_SCHEMA_VERSION:
        errors.append("style-metrics.md 的 schema_version 与指标 JSON 不一致")
    if metrics_header.get("report_sha256") != metrics.get("report_sha256"):
        errors.append("style-metrics.md 与 style-metrics.json 不是同一份统计结果")
    if metrics and metrics.get('aggregate') and analyze_style.render_markdown(metrics).strip() not in metrics_markdown_text:
        errors.append('style-metrics.md 缺少完整统计正文或正文已变化')

    profile_hash = validate_profile.canonical_json_sha256(profile)
    evidence_hash = validate_profile.canonical_json_sha256(list(evidence))
    analysis_header = parse_header(analysis_text, ARTIFACT_HEADER_RE, "author-analysis.md", errors)
    packet_header = parse_header(packet_text, ARTIFACT_HEADER_RE, "writing-packet.md", errors)
    for header, kind, label in (
        (analysis_header, "author-analysis", "author-analysis.md"),
        (packet_header, "writing-packet", "writing-packet.md"),
    ):
        if header.get("kind") != kind or header.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
            errors.append(f"{label} 的交付类型或 schema_version 不正确")
        if header.get("profile_sha256") != profile_hash:
            errors.append(f"{label} 未绑定当前 author-profile.json")
        if header.get("evidence_sha256") != evidence_hash:
            errors.append(f"{label} 未绑定当前 evidence-map.jsonl")
    profile_id = str(profile.get("profile_id", ""))
    if not identifier_present(analysis_text, profile_id) or not identifier_present(packet_text, profile_id):
        errors.append("author-analysis.md 与 writing-packet.md 必须包含当前 profile_id")
    for coverage_item in profile.get("coverage", []):
        if not isinstance(coverage_item, dict):
            continue
        dimension = coverage_item.get("dimension")
        summary = coverage_item.get("finding_summary")
        if isinstance(dimension, str) and not identifier_present(analysis_text, dimension):
            errors.append(f"author-analysis.md 缺少覆盖维度：{dimension}")
        if isinstance(summary, str) and summary not in analysis_text:
            errors.append(f"author-analysis.md 缺少维度结论：{dimension}")
    for rule in profile.get("rules", []):
        rule_id = rule.get("rule_id") if isinstance(rule, dict) else None
        if not isinstance(rule, dict):
            continue
        if isinstance(rule_id, str) and not identifier_present(analysis_text, rule_id):
            errors.append(f"author-analysis.md 缺少规则：{rule_id}")
        for field in (
            "trigger", "observable", "mechanism", "effect", "action", "limits", "confidence_basis"
        ):
            value = rule.get(field)
            if isinstance(value, str) and value not in analysis_text:
                errors.append(f"author-analysis.md 缺少规则 {rule_id} 的 {field}")
    for item in evidence:
        evidence_id = item.get("evidence_id") if isinstance(item, dict) else None
        if isinstance(evidence_id, str) and not identifier_present(analysis_text, evidence_id):
            errors.append(f"author-analysis.md 缺少证据：{evidence_id}")
    for packet in profile.get("writing_packet", {}).get("packets", []):
        packet_id = packet.get("packet_id") if isinstance(packet, dict) else None
        if not isinstance(packet, dict):
            continue
        if isinstance(packet_id, str) and not identifier_present(packet_text, packet_id):
            errors.append(f"writing-packet.md 缺少场景包：{packet_id}")
        for field in ("name", "triggers", "drift_corrections"):
            value = packet.get(field)
            values = value if isinstance(value, list) else [value]
            for current in values:
                if isinstance(current, str) and current not in packet_text:
                    errors.append(f"writing-packet.md 缺少场景包 {packet_id} 的 {field}")
    if render_profile.render_analysis(profile, evidence).strip() not in analysis_text:
        errors.append('author-analysis.md 缺少完整标准分析正文；请运行 render_profile.py')
    if render_profile.render_packet(profile, evidence).strip() not in packet_text:
        errors.append('writing-packet.md 缺少完整标准参数正文；请运行 render_profile.py')
    return errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验完整 Novel Distiller 分析包")
    parser.add_argument("profile", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--comparison-index", type=Path)
    parser.add_argument("--holdout-index", type=Path)
    parser.add_argument("--holdout-commitment", type=Path)
    parser.add_argument("--holdout-reveal", type=Path)
    parser.add_argument("--provisional-profile", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--metrics-markdown", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        profile = json.loads(args.profile.read_text(encoding="utf-8-sig"))
        evidence = validate_profile.read_jsonl(args.evidence, "证据文件")
        index_records = validate_profile.read_jsonl(args.index, "目标索引")
        comparison_records = (
            validate_profile.read_jsonl(args.comparison_index, "对照索引")
            if args.comparison_index
            else None
        )
        errors = validate_bundle(
            profile,
            evidence,
            index_records,
            args.manifest,
            args.ledger,
            args.metrics,
            args.metrics_markdown,
            args.analysis,
            args.packet,
            args.index,
            comparison_records,
            validate_profile.read_jsonl(args.holdout_index, '留出索引') if args.holdout_index else None,
            args.holdout_index,
            args.holdout_commitment,
            args.holdout_reveal,
            args.provisional_profile,
        )
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("完整分析包校验通过。")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
