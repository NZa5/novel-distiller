#!/usr/bin/env python3
"""Validate a complete, reusable Novel Distiller analysis bundle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import corpus_index
import validate_profile


METRICS_SCHEMA_VERSION = "1.0"


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


def validate_bundle(
    profile: dict,
    evidence: Sequence[dict],
    index_records: Sequence[dict],
    manifest_path: Path,
    ledger_path: Path,
    metrics_path: Path,
    analysis_path: Path,
    packet_path: Path,
    index_path: Path,
    comparison_index_records: Sequence[dict] | None = None,
) -> list[str]:
    errors = validate_profile.validate_profile(
        profile,
        evidence,
        index_records,
        comparison_index_records,
    )

    manifest_hash = validate_profile.file_sha256(manifest_path)
    if profile.get("corpus", {}).get("manifest_sha256") != manifest_hash:
        errors.append("corpus.manifest_sha256 与当前语料清单不一致")
    try:
        corpus_index.load_manifest(manifest_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"语料清单无效：{exc}")
    for record in index_records:
        if isinstance(record, dict) and record.get("preprocessing", {}).get("manifest_sha256") != manifest_hash:
            errors.append(f"索引块未绑定当前语料清单：{record.get('chunk_id')}")

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
    pending = [item for item in ledger_by_chunk.values() if item.get("status") == "pending"]
    followup = [item for item in ledger_by_chunk.values() if item.get("status") == "needs_followup"]
    if pending:
        errors.append(f"取样账本仍有 {len(pending)} 个 pending 文本块")
    if followup:
        errors.append(f"取样账本仍有 {len(followup)} 个 needs_followup 文本块")
    for item in ledger_by_chunk.values():
        if item.get("status") == "skipped" and not item.get("notes"):
            errors.append(f"跳过的文本块必须说明理由：{item.get('chunk_id')}")
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

    saturation = profile.get("analysis_saturation", {})
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
    metrics_hash = validate_profile.file_sha256(metrics_path)
    if profile.get("surface_ranges", {}).get("metrics_sha256") != metrics_hash:
        errors.append("surface_ranges.metrics_sha256 与当前指标文件不一致")
    metric_source_hashes = {
        item.get("source_sha256")
        for item in metrics.get("sources", [])
        if isinstance(item, dict) and isinstance(item.get("source_sha256"), str)
    }
    if metric_source_hashes != set(profile.get("corpus", {}).get("source_hashes", [])):
        errors.append("表层指标来源与目标语料来源不一致")

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
        try:
            json_pointer(metrics, reference)
        except ValueError as exc:
            errors.append(str(exc))
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
        analysis_text = analysis_path.read_text(encoding="utf-8-sig")
        packet_text = packet_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        errors.append(f"Markdown 交付文件不可读：{exc}")
        analysis_text = ""
        packet_text = ""
    profile_id = str(profile.get("profile_id", ""))
    if profile_id not in analysis_text or profile_id not in packet_text:
        errors.append("author-analysis.md 与 writing-packet.md 必须包含当前 profile_id")
    for rule in profile.get("rules", []):
        rule_id = rule.get("rule_id") if isinstance(rule, dict) else None
        if isinstance(rule_id, str) and rule_id not in analysis_text:
            errors.append(f"author-analysis.md 缺少规则：{rule_id}")
    for packet in profile.get("writing_packet", {}).get("packets", []):
        packet_id = packet.get("packet_id") if isinstance(packet, dict) else None
        if isinstance(packet_id, str) and packet_id not in packet_text:
            errors.append(f"writing-packet.md 缺少场景包：{packet_id}")
    return errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验完整 Novel Distiller 分析包")
    parser.add_argument("profile", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--comparison-index", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
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
            args.analysis,
            args.packet,
            args.index,
            comparison_records,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
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
