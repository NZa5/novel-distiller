#!/usr/bin/env python3
"""Validate an author profile against evidence, index records, and source files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence


SCHEMA_VERSION = "1.0"
INDEX_SCHEMA_VERSION = 3
PROFILE_SCOPES = {"passage", "work", "period", "author"}
RULE_LEVELS = {"sentence", "paragraph", "scene", "chapter", "work", "period", "author"}
CLASSIFICATIONS = {"stable", "conditional", "variable", "uncertain"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
HOLDOUT_STATUSES = {"passed", "partial", "failed", "not_tested", "not_applicable"}
DISTINCTIVENESS_STATUSES = {"supported", "shared", "uncertain", "not_tested"}
COVERAGE_STATUSES = {"analyzed", "no_stable_finding", "insufficient", "not_applicable"}
EVIDENCE_ROLES = {"support", "counterexample", "holdout"}
CORPUS_FIELDS = (
    "supplied_only", "target_label", "work_ids", "sample_ids", "source_hashes",
    "comparison_supplied", "holdout_sample_ids", "preprocessing",
)
PROFILE_FIELDS = (
    "schema_version", "profile_id", "profile_scope", "corpus", "coverage",
    "master_voice", "rules", "scene_modes", "character_voices", "rule_precedence",
    "surface_ranges", "writing_packet", "limitations",
)
RULE_FIELDS = (
    "rule_id", "level", "classification", "category", "trigger", "observable",
    "mechanism", "effect", "action", "limits", "evidence_ids",
    "support_sample_count", "support_work_count", "support_scene_type_count",
    "counterexample_count", "holdout_status", "distinctiveness_status",
    "confidence", "confidence_basis",
)
EVIDENCE_FIELDS = (
    "schema_version", "profile_id", "evidence_id", "rule_id", "dimension",
    "sample_id", "work_id", "scene_type", "source_path", "source_sha256",
    "chunk_id", "paragraph_start", "paragraph_end", "content_char_start",
    "content_char_end", "evidence_role", "excerpt", "observation", "eligibility",
)
SCENE_MODE_FIELDS = ("mode_id", "name", "triggers", "rule_ids", "evidence_ids")
CHARACTER_VOICE_FIELDS = (
    "voice_id", "character_label", "conditions", "rule_ids", "evidence_ids",
)
WRITING_PACKET_FIELDS = (
    "master_voice", "active_rule_ids", "scene_mode_ids", "character_voice_ids",
    "rule_precedence", "drift_corrections",
)
INDEX_FIELDS = (
    "schema_version", "chunk_id", "source_path", "source_sha256", "work_id",
    "paragraph_start", "paragraph_end", "content_char_start", "content_char_end",
    "scene_types", "text",
)


def require_fields(value: dict, fields: Iterable[str], label: str, errors: list[str]) -> None:
    for field in fields:
        if field not in value:
            errors.append(f"{label} 缺少字段：{field}")


def require_nonempty_string(value: object, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} 必须是非空字符串")


def require_nonnegative_int(value: object, label: str, errors: list[str]) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        errors.append(f"{label} 必须是非负整数")


def require_positive_int(value: object, label: str, errors: list[str]) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        errors.append(f"{label} 必须是正整数")


def validate_unique_string_list(
    value: object,
    label: str,
    errors: list[str],
    allow_empty: bool = True,
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label} 必须是数组")
        return []
    valid = [item for item in value if isinstance(item, str) and item.strip()]
    if len(valid) != len(value):
        errors.append(f"{label} 必须全部是非空字符串")
    if len(set(valid)) != len(valid):
        errors.append(f"{label} 不能包含重复值")
    if not allow_empty and not valid:
        errors.append(f"{label} 不能为空")
    return valid


def read_jsonl(path: Path, label: str = "JSONL") -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{label} 第 {line_number} 行必须是 JSON 对象")
            value["_line_number"] = line_number
            records.append(value)
    return records


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_excerpt(text: str) -> str:
    return re.sub(r"\s+", "", text)


def path_key(path_value: object) -> str:
    if not isinstance(path_value, str) or not path_value:
        return ""
    return str(Path(path_value).resolve()).casefold()


def validate_structured_group(
    values: object,
    label: str,
    fields: Sequence[str],
    id_field: str,
    list_fields: Sequence[str],
    errors: list[str],
) -> dict[str, dict]:
    if not isinstance(values, list):
        errors.append(f"{label} 必须是数组")
        return {}
    found: dict[str, dict] = {}
    for index, value in enumerate(values, 1):
        item_label = f"{label}[{index}]"
        if not isinstance(value, dict):
            errors.append(f"{item_label} 必须是对象")
            continue
        require_fields(value, fields, item_label, errors)
        identifier = value.get(id_field)
        require_nonempty_string(identifier, f"{item_label}.{id_field}", errors)
        if isinstance(identifier, str) and identifier.strip():
            if identifier in found:
                errors.append(f"{id_field} 重复：{identifier}")
            found[identifier] = value
        for field in fields:
            if field in list_fields:
                validate_unique_string_list(value.get(field), f"{item_label}.{field}", errors, allow_empty=False)
            elif field != id_field:
                require_nonempty_string(value.get(field), f"{item_label}.{field}", errors)
    return found


def validate_references(
    values: Sequence[dict],
    label: str,
    field: str,
    known: set[str],
    errors: list[str],
) -> None:
    for index, value in enumerate(values, 1):
        if not isinstance(value, dict):
            continue
        for reference in value.get(field, []) if isinstance(value.get(field), list) else []:
            if not isinstance(reference, str) or reference not in known:
                errors.append(f"{label}[{index}].{field} 引用了未知编号：{reference}")


def validate_profile(
    profile: object,
    evidence: Sequence[dict] | None = None,
    index_records: Sequence[dict] | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(profile, dict):
        return ["画像根节点必须是 JSON 对象"]
    require_fields(profile, PROFILE_FIELDS, "画像", errors)
    if errors:
        return errors

    if profile["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version 必须是 {SCHEMA_VERSION}")
    require_nonempty_string(profile["profile_id"], "profile_id", errors)
    if not isinstance(profile["profile_scope"], str) or profile["profile_scope"] not in PROFILE_SCOPES:
        errors.append("profile_scope 必须是 passage/work/period/author")

    corpus = profile["corpus"]
    work_ids: list[str] = []
    sample_ids: list[str] = []
    source_hashes: list[str] = []
    holdout_ids: list[str] = []
    comparison_supplied = False
    if not isinstance(corpus, dict):
        errors.append("corpus 必须是对象")
    else:
        require_fields(corpus, CORPUS_FIELDS, "corpus", errors)
        if corpus.get("supplied_only") is not True:
            errors.append("corpus.supplied_only 必须为 true")
        require_nonempty_string(corpus.get("target_label"), "corpus.target_label", errors)
        work_ids = validate_unique_string_list(corpus.get("work_ids"), "corpus.work_ids", errors, False)
        sample_ids = validate_unique_string_list(corpus.get("sample_ids"), "corpus.sample_ids", errors, False)
        source_hashes = validate_unique_string_list(corpus.get("source_hashes"), "corpus.source_hashes", errors, False)
        holdout_ids = validate_unique_string_list(corpus.get("holdout_sample_ids"), "corpus.holdout_sample_ids", errors)
        if any(item not in sample_ids for item in holdout_ids):
            errors.append("corpus.holdout_sample_ids 必须是 corpus.sample_ids 的子集")
        for source_hash in source_hashes:
            if not re.fullmatch(r"[0-9a-fA-F]{64}", source_hash):
                errors.append(f"corpus.source_hashes 包含无效 SHA-256：{source_hash}")
        comparison_supplied = corpus.get("comparison_supplied") is True
        if not isinstance(corpus.get("comparison_supplied"), bool):
            errors.append("corpus.comparison_supplied 必须是布尔值")
        if not isinstance(corpus.get("preprocessing"), dict):
            errors.append("corpus.preprocessing 必须是对象")

    coverage = profile["coverage"]
    coverage_by_dimension: dict[str, dict] = {}
    if not isinstance(coverage, list) or not coverage:
        errors.append("coverage 必须是非空数组")
    else:
        for index, item in enumerate(coverage, 1):
            label = f"coverage[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} 必须是对象")
                continue
            require_fields(item, ("dimension", "status", "evidence_count", "uncovered"), label, errors)
            dimension = item.get("dimension")
            require_nonempty_string(dimension, f"{label}.dimension", errors)
            if isinstance(dimension, str):
                if dimension in coverage_by_dimension:
                    errors.append(f"coverage.dimension 重复：{dimension}")
                coverage_by_dimension[dimension] = item
            if not isinstance(item.get("status"), str) or item.get("status") not in COVERAGE_STATUSES:
                errors.append(f"{label}.status 不受支持")
            require_nonnegative_int(item.get("evidence_count"), f"{label}.evidence_count", errors)
            validate_unique_string_list(item.get("uncovered"), f"{label}.uncovered", errors)

    require_nonempty_string(profile["master_voice"], "master_voice", errors)
    validate_unique_string_list(profile["limitations"], "limitations", errors, False)
    if not isinstance(profile["surface_ranges"], dict):
        errors.append("surface_ranges 必须是对象")

    rules = profile["rules"] if isinstance(profile["rules"], list) else []
    if not isinstance(profile["rules"], list):
        errors.append("rules 必须是数组")
    rules_by_id: dict[str, dict] = {}
    for index, rule in enumerate(rules, 1):
        label = f"rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{label} 必须是对象")
            continue
        require_fields(rule, RULE_FIELDS, label, errors)
        rule_id = rule.get("rule_id")
        require_nonempty_string(rule_id, f"{label}.rule_id", errors)
        if isinstance(rule_id, str):
            if rule_id in rules_by_id:
                errors.append(f"rule_id 重复：{rule_id}")
            rules_by_id[rule_id] = rule
        if not isinstance(rule.get("classification"), str) or rule.get("classification") not in CLASSIFICATIONS:
            errors.append(f"{label}.classification 不受支持")
        if not isinstance(rule.get("level"), str) or rule.get("level") not in RULE_LEVELS:
            errors.append(f"{label}.level 不受支持")
        if not isinstance(rule.get("confidence"), str) or rule.get("confidence") not in CONFIDENCE_LEVELS:
            errors.append(f"{label}.confidence 不受支持")
        if not isinstance(rule.get("holdout_status"), str) or rule.get("holdout_status") not in HOLDOUT_STATUSES:
            errors.append(f"{label}.holdout_status 不受支持")
        if not isinstance(rule.get("distinctiveness_status"), str) or rule.get("distinctiveness_status") not in DISTINCTIVENESS_STATUSES:
            errors.append(f"{label}.distinctiveness_status 不受支持")
        elif not comparison_supplied and rule.get("distinctiveness_status") != "not_tested":
            errors.append(f"{label}.distinctiveness_status 在没有对照语料时必须为 not_tested")
        for field in ("support_sample_count", "support_work_count", "support_scene_type_count", "counterexample_count"):
            require_nonnegative_int(rule.get(field), f"{label}.{field}", errors)
        validate_unique_string_list(rule.get("evidence_ids"), f"{label}.evidence_ids", errors, False)
        for field in ("level", "category", "trigger", "observable", "mechanism", "effect", "action", "limits", "confidence_basis"):
            require_nonempty_string(rule.get(field), f"{label}.{field}", errors)

    rule_ids = set(rules_by_id)
    precedence = validate_unique_string_list(profile["rule_precedence"], "rule_precedence", errors)
    for rule_id in precedence:
        if rule_id not in rule_ids:
            errors.append(f"rule_precedence 引用了未知规则：{rule_id}")

    scene_modes_value = profile["scene_modes"]
    scene_modes = validate_structured_group(
        scene_modes_value, "scene_modes", SCENE_MODE_FIELDS, "mode_id",
        ("triggers", "rule_ids", "evidence_ids"), errors,
    )
    voices_value = profile["character_voices"]
    voices = validate_structured_group(
        voices_value, "character_voices", CHARACTER_VOICE_FIELDS, "voice_id",
        ("conditions", "rule_ids", "evidence_ids"), errors,
    )
    if isinstance(scene_modes_value, list):
        validate_references(scene_modes_value, "scene_modes", "rule_ids", rule_ids, errors)
    if isinstance(voices_value, list):
        validate_references(voices_value, "character_voices", "rule_ids", rule_ids, errors)

    writing_packet = profile["writing_packet"]
    if not isinstance(writing_packet, dict):
        errors.append("writing_packet 必须是对象")
        writing_packet = {}
    require_fields(writing_packet, WRITING_PACKET_FIELDS, "writing_packet", errors)
    require_nonempty_string(writing_packet.get("master_voice"), "writing_packet.master_voice", errors)
    for field, known in (
        ("active_rule_ids", rule_ids),
        ("scene_mode_ids", set(scene_modes)),
        ("character_voice_ids", set(voices)),
        ("rule_precedence", rule_ids),
    ):
        references = validate_unique_string_list(writing_packet.get(field), f"writing_packet.{field}", errors)
        for reference in references:
            if reference not in known:
                errors.append(f"writing_packet.{field} 引用了未知编号：{reference}")
    validate_unique_string_list(writing_packet.get("drift_corrections"), "writing_packet.drift_corrections", errors)
    if writing_packet.get("master_voice") != profile.get("master_voice"):
        errors.append("writing_packet.master_voice 必须与 master_voice 一致")
    if writing_packet.get("rule_precedence") != profile.get("rule_precedence"):
        errors.append("writing_packet.rule_precedence 必须与 rule_precedence 一致")

    index_by_chunk: dict[str, dict] = {}
    if index_records is not None:
        for position, record in enumerate(index_records, 1):
            index_label = f"index line {record.get('_line_number', position)}" if isinstance(record, dict) else f"index item {position}"
            if not isinstance(record, dict):
                errors.append(f"{index_label} 必须是对象")
                continue
            require_fields(record, INDEX_FIELDS, index_label, errors)
            if record.get("schema_version") != INDEX_SCHEMA_VERSION:
                errors.append(f"{index_label}.schema_version 必须是 {INDEX_SCHEMA_VERSION}")
            chunk_id = record.get("chunk_id")
            require_nonempty_string(chunk_id, f"{index_label}.chunk_id", errors)
            require_nonempty_string(record.get("source_path"), f"{index_label}.source_path", errors)
            require_nonempty_string(record.get("work_id"), f"{index_label}.work_id", errors)
            require_nonempty_string(record.get("text"), f"{index_label}.text", errors)
            if not isinstance(record.get("source_sha256"), str) or not re.fullmatch(r"[0-9a-fA-F]{64}", record["source_sha256"]):
                errors.append(f"{index_label}.source_sha256 必须是 64 位十六进制 SHA-256")
            for field in ("paragraph_start", "paragraph_end", "content_char_start", "content_char_end"):
                require_positive_int(record.get(field), f"{index_label}.{field}", errors)
            if isinstance(record.get("paragraph_start"), int) and isinstance(record.get("paragraph_end"), int) and record["paragraph_start"] > record["paragraph_end"]:
                errors.append(f"{index_label} 的段落起点不能大于终点")
            if isinstance(record.get("content_char_start"), int) and isinstance(record.get("content_char_end"), int) and record["content_char_start"] > record["content_char_end"]:
                errors.append(f"{index_label} 的内容字符起点不能大于终点")
            if not isinstance(record.get("scene_types"), list) or any(not isinstance(value, str) for value in record.get("scene_types", [])):
                errors.append(f"{index_label}.scene_types 必须是字符串数组")
            if isinstance(chunk_id, str):
                if chunk_id in index_by_chunk:
                    errors.append(f"索引 chunk_id 重复：{chunk_id}")
                index_by_chunk[chunk_id] = record
        valid_index_records = [record for record in index_records if isinstance(record, dict)]
        observed_hashes = {record.get("source_sha256") for record in valid_index_records if isinstance(record.get("source_sha256"), str)}
        observed_works = {record.get("work_id") for record in valid_index_records if isinstance(record.get("work_id"), str)}
        if set(source_hashes) != observed_hashes:
            errors.append("corpus.source_hashes 与索引中的来源哈希不一致")
        if set(work_ids) != observed_works:
            errors.append("corpus.work_ids 与索引中的作品编号不一致")
        actual_hashes: dict[str, str | None] = {}
        for record in valid_index_records:
            source_path = record.get("source_path")
            key = path_key(source_path)
            if not key:
                errors.append("索引记录缺少有效 source_path")
                continue
            if key not in actual_hashes:
                source = Path(str(source_path))
                if not source.is_file():
                    errors.append(f"索引来源文件不存在：{source_path}")
                    actual_hashes[key] = None
                else:
                    actual_hashes[key] = file_sha256(source)
            if actual_hashes[key] is not None and actual_hashes[key] != record.get("source_sha256"):
                errors.append(f"索引来源文件哈希已变化：{source_path}")

    if evidence is None:
        return errors
    if index_records is None:
        errors.append("提供 evidence-map.jsonl 时必须同时提供 corpus-index.jsonl")

    evidence_by_id: dict[str, dict] = {}
    evidence_by_rule: dict[str, list[dict]] = defaultdict(list)
    evidence_by_dimension: dict[str, set[str]] = defaultdict(set)
    for index, item in enumerate(evidence, 1):
        if not isinstance(item, dict):
            errors.append(f"evidence item {index} 必须是对象")
            continue
        line_number = item.get("_line_number", index)
        label = f"evidence line {line_number}"
        require_fields(item, EVIDENCE_FIELDS, label, errors)
        if item.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{label}.schema_version 必须是 {SCHEMA_VERSION}")
        if item.get("profile_id") != profile.get("profile_id"):
            errors.append(f"{label}.profile_id 与画像不一致")
        evidence_id = item.get("evidence_id")
        require_nonempty_string(evidence_id, f"{label}.evidence_id", errors)
        if isinstance(evidence_id, str):
            if evidence_id in evidence_by_id:
                errors.append(f"evidence_id 重复：{evidence_id}")
            evidence_by_id[evidence_id] = item
        rule_id = item.get("rule_id")
        if not isinstance(rule_id, str) or rule_id not in rules_by_id:
            errors.append(f"{label}.rule_id 引用了未知规则：{rule_id}")
        else:
            evidence_by_rule[rule_id].append(item)
        dimension = item.get("dimension")
        require_nonempty_string(dimension, f"{label}.dimension", errors)
        if isinstance(dimension, str) and isinstance(evidence_id, str):
            evidence_by_dimension[dimension].add(evidence_id)
            if dimension not in coverage_by_dimension:
                errors.append(f"{label}.dimension 未在 coverage 中声明：{dimension}")
        if not isinstance(item.get("evidence_role"), str) or item.get("evidence_role") not in EVIDENCE_ROLES:
            errors.append(f"{label}.evidence_role 不受支持")
        for field in ("paragraph_start", "paragraph_end", "content_char_start", "content_char_end"):
            require_positive_int(item.get(field), f"{label}.{field}", errors)
        if isinstance(item.get("paragraph_start"), int) and isinstance(item.get("paragraph_end"), int) and item["paragraph_start"] > item["paragraph_end"]:
            errors.append(f"{label} 的段落起点不能大于终点")
        if isinstance(item.get("content_char_start"), int) and isinstance(item.get("content_char_end"), int) and item["content_char_start"] > item["content_char_end"]:
            errors.append(f"{label} 的内容字符起点不能大于终点")
        for field in ("sample_id", "work_id", "scene_type", "source_path", "source_sha256", "chunk_id", "excerpt", "observation", "eligibility"):
            require_nonempty_string(item.get(field), f"{label}.{field}", errors)
        if item.get("sample_id") not in sample_ids:
            errors.append(f"{label}.sample_id 不在 corpus.sample_ids 中")
        if item.get("evidence_role") == "holdout" and item.get("sample_id") not in holdout_ids:
            errors.append(f"{label}.sample_id 未声明在 corpus.holdout_sample_ids 中")
        if item.get("evidence_role") != "holdout" and item.get("sample_id") in holdout_ids:
            errors.append(f"{label}.sample_id 已声明为留出样本，不能作为建模证据")
        if item.get("work_id") not in work_ids:
            errors.append(f"{label}.work_id 不在 corpus.work_ids 中")
        if item.get("source_sha256") not in source_hashes:
            errors.append(f"{label}.source_sha256 不在 corpus.source_hashes 中")

        indexed = index_by_chunk.get(item.get("chunk_id"))
        if index_records is not None and indexed is None:
            errors.append(f"{label}.chunk_id 不存在于索引：{item.get('chunk_id')}")
        elif indexed is not None:
            if path_key(item.get("source_path")) != path_key(indexed.get("source_path")):
                errors.append(f"{label}.source_path 与索引不一致")
            if item.get("source_sha256") != indexed.get("source_sha256"):
                errors.append(f"{label}.source_sha256 与索引不一致")
            if item.get("work_id") != indexed.get("work_id"):
                errors.append(f"{label}.work_id 与索引不一致")
            scene_types = indexed.get("scene_types", [])
            if isinstance(scene_types, list) and scene_types and item.get("scene_type") not in scene_types:
                errors.append(f"{label}.scene_type 不在索引块的场景标注中")
            for start_field, end_field in (("paragraph_start", "paragraph_end"), ("content_char_start", "content_char_end")):
                if (
                    isinstance(item.get(start_field), int)
                    and isinstance(item.get(end_field), int)
                    and isinstance(indexed.get(start_field), int)
                    and isinstance(indexed.get(end_field), int)
                    and not (indexed[start_field] <= item[start_field] <= item[end_field] <= indexed[end_field])
                ):
                    errors.append(f"{label}.{start_field}/{end_field} 超出索引块范围")
            excerpt = normalized_excerpt(str(item.get("excerpt", "")))
            indexed_text = normalized_excerpt(str(indexed.get("text", "")))
            if excerpt and excerpt not in indexed_text:
                errors.append(f"{label}.excerpt 不存在于对应索引块原文中")

    known_evidence = set(evidence_by_id)
    if isinstance(scene_modes_value, list):
        validate_references(scene_modes_value, "scene_modes", "evidence_ids", known_evidence, errors)
    if isinstance(voices_value, list):
        validate_references(voices_value, "character_voices", "evidence_ids", known_evidence, errors)

    referenced_ids: set[str] = set()
    for rule_id, rule in rules_by_id.items():
        evidence_ids = rule.get("evidence_ids", [])
        for evidence_id in evidence_ids if isinstance(evidence_ids, list) else []:
            referenced_ids.add(evidence_id)
            item = evidence_by_id.get(evidence_id)
            if item is None:
                errors.append(f"规则 {rule_id} 引用了不存在的证据：{evidence_id}")
            elif item.get("rule_id") != rule_id:
                errors.append(f"证据 {evidence_id} 的 rule_id 与规则 {rule_id} 不一致")

        records = evidence_by_rule.get(rule_id, [])
        support = [item for item in records if item.get("evidence_role") == "support"]
        counterexamples = [item for item in records if item.get("evidence_role") == "counterexample"]
        holdout = [item for item in records if item.get("evidence_role") == "holdout"]
        observed_counts = {
            "support_sample_count": len({item.get("sample_id") for item in support if isinstance(item.get("sample_id"), str)}),
            "support_work_count": len({item.get("work_id") for item in support if isinstance(item.get("work_id"), str)}),
            "support_scene_type_count": len({item.get("scene_type") for item in support if isinstance(item.get("scene_type"), str)}),
            "counterexample_count": len({item.get("sample_id") for item in counterexamples if isinstance(item.get("sample_id"), str)}),
        }
        for field, observed in observed_counts.items():
            if rule.get(field) != observed:
                errors.append(f"规则 {rule_id} 的 {field}={rule.get(field)}，证据实际为 {observed}")
        holdout_status = rule.get("holdout_status")
        if isinstance(holdout_status, str) and holdout_status in {"passed", "partial", "failed"} and not holdout:
            errors.append(f"规则 {rule_id} 声称完成留出验证，但没有 holdout 证据")
        if holdout_status == "not_tested" and holdout:
            errors.append(f"规则 {rule_id} 有 holdout 证据但状态仍是 not_tested")

    for evidence_id in evidence_by_id:
        if evidence_id not in referenced_ids:
            errors.append(f"存在未被规则引用的证据：{evidence_id}")
    for dimension, item in coverage_by_dimension.items():
        observed = len(evidence_by_dimension.get(dimension, set()))
        if item.get("evidence_count") != observed:
            errors.append(f"coverage {dimension} 的 evidence_count={item.get('evidence_count')}，证据实际为 {observed}")
    return errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验作者画像、证据地图、语料索引和原始来源")
    parser.add_argument("profile", type=Path, help="author-profile.json")
    parser.add_argument("--evidence", type=Path, help="evidence-map.jsonl")
    parser.add_argument("--index", type=Path, help="corpus-index.jsonl；提供证据时必需")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.evidence and not args.index:
            raise ValueError("提供 --evidence 时必须同时提供 --index")
        profile = json.loads(args.profile.read_text(encoding="utf-8-sig"))
        evidence = read_jsonl(args.evidence, "证据文件") if args.evidence else None
        index_records = read_jsonl(args.index, "索引文件") if args.index else None
        errors = validate_profile(profile, evidence, index_records)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    evidence_message = "、证据地图及语料索引" if evidence is not None else ""
    print(f"画像{evidence_message}校验通过。")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
