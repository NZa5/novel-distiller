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


SCHEMA_VERSION = "2.0"
INDEX_SCHEMA_VERSION = 4
ANALYSIS_DIMENSIONS = (
    "syntax_rhythm",
    "paragraph_organization",
    "diction_register",
    "function_words_cohesion",
    "rhetoric_imagery_senses",
    "sound_repetition",
    "chinese_specific_features",
    "narrator_evaluative_stance",
    "viewpoint_focalization_interiority",
    "speech_dialogue_organization",
    "narrative_time",
    "information_release",
    "openings_transitions_endings",
    "character_introduction_reference",
    "characterization_channels",
    "desire_agency_character_arc",
    "relationships_social_network",
    "event_selection_density",
    "causality_escalation",
    "conflict_plot_arc",
    "space_environment",
    "world_rules_social_texture",
    "theme_motif_value_structure",
    "genre_tradition_reader_contract",
    "topic_reference_ellipsis",
    "modality_evidentiality_negation",
    "conversation_pragmatics_repair",
    "humor_irony_satire",
    "plot_threads_chapter_rhythm",
    "viewpoint_transition_matrix",
    "relationship_network_evolution",
    "foreshadowing_payoff",
    "motif_imagery_trajectory",
    "period_style_drift",
    "negative_profile_avoidance",
)
ANALYSIS_DIMENSION_SET = set(ANALYSIS_DIMENSIONS)
PROFILE_SCOPES = {"passage", "work", "period", "author"}
RULE_LEVELS = {"sentence", "paragraph", "scene", "chapter", "work", "period", "author"}
CLASSIFICATIONS = {"stable", "conditional", "variable", "uncertain"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
HOLDOUT_STATUSES = {"passed", "partial", "failed", "not_tested", "not_applicable"}
DISTINCTIVENESS_STATUSES = {"supported", "shared", "uncertain", "not_tested"}
COVERAGE_STATUSES = {"analyzed", "no_stable_finding", "insufficient", "not_applicable"}
EVIDENCE_ROLES = {"support", "counterexample", "holdout", "control"}
CORPUS_ROLES = {"target", "control"}
HOLDOUT_OUTCOMES = {"matched", "missed", "contradicted", "not_applicable"}
COUNTEREXAMPLE_SEARCH_STATUSES = {"complete", "partial", "not_tested"}
SATURATION_STATUSES = {"saturated", "full_corpus", "limited"}
CORPUS_FIELDS = (
    "supplied_only", "target_label", "work_ids", "sample_ids", "source_hashes",
    "comparison_supplied", "comparison_work_ids", "comparison_sample_ids",
    "comparison_source_hashes", "holdout_sample_ids", "preprocessing", "manifest_sha256",
)
PROFILE_FIELDS = (
    "schema_version", "profile_id", "profile_scope", "corpus", "coverage",
    "master_voice", "rules", "scene_modes", "character_voices", "rule_precedence",
    "surface_ranges", "analysis_saturation", "writing_packet", "limitations",
)
RULE_FIELDS = (
    "rule_id", "dimension", "level", "classification", "category", "trigger", "observable",
    "mechanism", "effect", "action", "limits", "evidence_ids", "metric_refs",
    "support_sample_count", "support_work_count", "support_scene_type_count",
    "counterexample_count", "holdout_status", "distinctiveness_status",
    "counterexample_search", "holdout_evaluation", "distinctiveness_evidence_ids",
    "confidence", "confidence_basis",
)
EVIDENCE_FIELDS = (
    "schema_version", "profile_id", "evidence_id", "rule_id", "dimension",
    "corpus_role", "sample_id", "work_id", "scene_type", "source_path", "source_sha256",
    "chunk_id", "paragraph_start", "paragraph_end", "content_char_start",
    "content_char_end", "evidence_role", "evaluation_outcome", "excerpt", "observation", "eligibility",
)
SCENE_MODE_FIELDS = ("mode_id", "name", "triggers", "rule_ids", "evidence_ids")
CHARACTER_VOICE_FIELDS = (
    "voice_id", "character_label", "conditions", "rule_ids", "evidence_ids",
)
WRITING_PACKET_FIELDS = ("master_voice", "selector_order", "shared_rule_ids", "packets")
PACKET_FIELDS = (
    "packet_id", "name", "triggers", "active_dimension_ids", "active_rule_ids",
    "scene_mode_ids", "character_voice_ids", "rule_precedence", "evidence_ids",
    "surface_range_refs", "drift_corrections",
)
INDEX_FIELDS = (
    "schema_version", "chunk_id", "source_path", "source_sha256", "work_id",
    "paragraph_start", "paragraph_end", "content_char_start", "content_char_end",
    "sample_ids", "chapter_ids", "scene_ids", "scene_types", "text",
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
    comparison_index_records: Sequence[dict] | None = None,
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
    comparison_work_ids: list[str] = []
    comparison_sample_ids: list[str] = []
    comparison_source_hashes: list[str] = []
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
        comparison_work_ids = validate_unique_string_list(
            corpus.get("comparison_work_ids"), "corpus.comparison_work_ids", errors
        )
        comparison_sample_ids = validate_unique_string_list(
            corpus.get("comparison_sample_ids"), "corpus.comparison_sample_ids", errors
        )
        comparison_source_hashes = validate_unique_string_list(
            corpus.get("comparison_source_hashes"), "corpus.comparison_source_hashes", errors
        )
        holdout_ids = validate_unique_string_list(corpus.get("holdout_sample_ids"), "corpus.holdout_sample_ids", errors)
        if any(item not in sample_ids for item in holdout_ids):
            errors.append("corpus.holdout_sample_ids 必须是 corpus.sample_ids 的子集")
        for source_hash in source_hashes + comparison_source_hashes:
            if not re.fullmatch(r"[0-9a-fA-F]{64}", source_hash):
                errors.append(f"corpus.source_hashes 包含无效 SHA-256：{source_hash}")
        comparison_supplied = corpus.get("comparison_supplied") is True
        if not isinstance(corpus.get("comparison_supplied"), bool):
            errors.append("corpus.comparison_supplied 必须是布尔值")
        if not isinstance(corpus.get("preprocessing"), dict):
            errors.append("corpus.preprocessing 必须是对象")
        manifest_sha256 = corpus.get("manifest_sha256")
        if not isinstance(manifest_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", manifest_sha256):
            errors.append("corpus.manifest_sha256 必须是 64 位十六进制 SHA-256")
        comparison_lists_have_values = bool(
            comparison_work_ids or comparison_sample_ids or comparison_source_hashes
        )
        if comparison_supplied != comparison_lists_have_values:
            errors.append("comparison_supplied 必须与对照作品、样本和来源列表保持一致")
        if comparison_supplied and not (
            comparison_work_ids and comparison_sample_ids and comparison_source_hashes
        ):
            errors.append("提供对照语料时，对照作品、样本和来源列表均不能为空")
    if profile.get("profile_scope") == "author" and len(work_ids) < 2:
        errors.append("author 画像至少需要两部目标作品")

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
                if dimension not in ANALYSIS_DIMENSION_SET:
                    errors.append(f"{label}.dimension 不受支持：{dimension}")
                if dimension in coverage_by_dimension:
                    errors.append(f"coverage.dimension 重复：{dimension}")
                coverage_by_dimension[dimension] = item
            if not isinstance(item.get("status"), str) or item.get("status") not in COVERAGE_STATUSES:
                errors.append(f"{label}.status 不受支持")
            require_nonnegative_int(item.get("evidence_count"), f"{label}.evidence_count", errors)
            uncovered = validate_unique_string_list(item.get("uncovered"), f"{label}.uncovered", errors)
            if item.get("status") == "analyzed" and item.get("evidence_count") == 0:
                errors.append(f"{label} 标为 analyzed 时 evidence_count 必须大于 0")
            if item.get("status") == "insufficient" and not uncovered:
                errors.append(f"{label} 标为 insufficient 时必须说明 uncovered")
            if item.get("status") == "not_applicable" and item.get("evidence_count") != 0:
                errors.append(f"{label} 标为 not_applicable 时 evidence_count 必须为 0")
        missing_dimensions = [
            dimension for dimension in ANALYSIS_DIMENSIONS if dimension not in coverage_by_dimension
        ]
        if missing_dimensions:
            errors.append(f"coverage 缺少固定分析维度：{', '.join(missing_dimensions)}")

    require_nonempty_string(profile["master_voice"], "master_voice", errors)
    limitations = validate_unique_string_list(profile["limitations"], "limitations", errors, False)
    if not isinstance(profile["surface_ranges"], dict):
        errors.append("surface_ranges 必须是对象")
    else:
        metrics_sha256 = profile["surface_ranges"].get("metrics_sha256")
        if not isinstance(metrics_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", metrics_sha256):
            errors.append("surface_ranges.metrics_sha256 必须是 64 位十六进制 SHA-256")

    saturation = profile["analysis_saturation"]
    if not isinstance(saturation, dict):
        errors.append("analysis_saturation 必须是对象")
    else:
        require_fields(
            saturation,
            ("status", "rounds", "unresolved_dimension_ids", "stop_reason"),
            "analysis_saturation",
            errors,
        )
        status = saturation.get("status")
        if status not in SATURATION_STATUSES:
            errors.append("analysis_saturation.status 不受支持")
        unresolved = validate_unique_string_list(
            saturation.get("unresolved_dimension_ids"),
            "analysis_saturation.unresolved_dimension_ids",
            errors,
        )
        for dimension in unresolved:
            if dimension not in ANALYSIS_DIMENSION_SET:
                errors.append(f"analysis_saturation 引用了未知维度：{dimension}")
        require_nonempty_string(saturation.get("stop_reason"), "analysis_saturation.stop_reason", errors)
        rounds = saturation.get("rounds")
        if not isinstance(rounds, list):
            errors.append("analysis_saturation.rounds 必须是数组")
            rounds = []
        normalized_rounds = []
        round_ids: set[str] = set()
        for round_index, round_value in enumerate(rounds, 1):
            label = f"analysis_saturation.rounds[{round_index}]"
            if not isinstance(round_value, dict):
                errors.append(f"{label} 必须是对象")
                continue
            require_fields(
                round_value,
                ("round_id", "added_sample_ids", "new_rule_count", "new_counterexample_count", "unresolved_dimension_ids", "note"),
                label,
                errors,
            )
            round_id = round_value.get("round_id")
            require_nonempty_string(round_id, f"{label}.round_id", errors)
            if isinstance(round_id, str):
                if round_id in round_ids:
                    errors.append(f"analysis_saturation.round_id 重复：{round_id}")
                round_ids.add(round_id)
            added = validate_unique_string_list(round_value.get("added_sample_ids"), f"{label}.added_sample_ids", errors)
            if any(item not in sample_ids for item in added):
                errors.append(f"{label}.added_sample_ids 必须来自 corpus.sample_ids")
            require_nonnegative_int(round_value.get("new_rule_count"), f"{label}.new_rule_count", errors)
            require_nonnegative_int(
                round_value.get("new_counterexample_count"),
                f"{label}.new_counterexample_count",
                errors,
            )
            round_unresolved = validate_unique_string_list(
                round_value.get("unresolved_dimension_ids"),
                f"{label}.unresolved_dimension_ids",
                errors,
            )
            if any(item not in ANALYSIS_DIMENSION_SET for item in round_unresolved):
                errors.append(f"{label}.unresolved_dimension_ids 包含未知维度")
            require_nonempty_string(round_value.get("note"), f"{label}.note", errors)
            normalized_rounds.append(round_value)
        if status == "saturated":
            if len(normalized_rounds) < 2:
                errors.append("saturated 至少需要两轮连续无新增验证")
            for round_value in normalized_rounds[-2:]:
                if (
                    round_value.get("new_rule_count") != 0
                    or round_value.get("new_counterexample_count") != 0
                    or round_value.get("unresolved_dimension_ids")
                ):
                    errors.append("saturated 的最后两轮必须无新规则、无新反例且无未解决维度")
                    break
            if unresolved:
                errors.append("saturated 不能保留未解决维度")
        if status == "full_corpus" and unresolved:
            errors.append("full_corpus 不能保留未解决维度")
        if status == "limited" and not unresolved:
            errors.append("limited 必须列出未解决维度")
        if status == "limited" and not limitations:
            errors.append("limited 必须在 limitations 中说明限制")

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
        dimension = rule.get("dimension")
        if not isinstance(dimension, str) or dimension not in ANALYSIS_DIMENSION_SET:
            errors.append(f"{label}.dimension 不受支持：{dimension}")
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
        validate_unique_string_list(rule.get("metric_refs"), f"{label}.metric_refs", errors)
        validate_unique_string_list(
            rule.get("distinctiveness_evidence_ids"),
            f"{label}.distinctiveness_evidence_ids",
            errors,
        )
        for field in ("dimension", "level", "category", "trigger", "observable", "mechanism", "effect", "action", "limits", "confidence_basis"):
            require_nonempty_string(rule.get(field), f"{label}.{field}", errors)
        counter_search = rule.get("counterexample_search")
        if not isinstance(counter_search, dict):
            errors.append(f"{label}.counterexample_search 必须是对象")
        else:
            require_fields(
                counter_search,
                (
                    "status", "eligible_sample_count", "reviewed_sample_count",
                    "eligible_sample_ids", "reviewed_sample_ids", "notes",
                ),
                f"{label}.counterexample_search",
                errors,
            )
            if counter_search.get("status") not in COUNTEREXAMPLE_SEARCH_STATUSES:
                errors.append(f"{label}.counterexample_search.status 不受支持")
            require_nonnegative_int(
                counter_search.get("eligible_sample_count"),
                f"{label}.counterexample_search.eligible_sample_count",
                errors,
            )
            require_nonnegative_int(
                counter_search.get("reviewed_sample_count"),
                f"{label}.counterexample_search.reviewed_sample_count",
                errors,
            )
            if (
                isinstance(counter_search.get("eligible_sample_count"), int)
                and isinstance(counter_search.get("reviewed_sample_count"), int)
                and counter_search["reviewed_sample_count"] > counter_search["eligible_sample_count"]
            ):
                errors.append(f"{label}.counterexample_search.reviewed_sample_count 不能超过 eligible_sample_count")
            if (
                counter_search.get("status") == "complete"
                and counter_search.get("reviewed_sample_count") != counter_search.get("eligible_sample_count")
            ):
                errors.append(f"{label}.counterexample_search.complete 必须检查全部适用样本")
            eligible_search_ids = validate_unique_string_list(
                counter_search.get("eligible_sample_ids"),
                f"{label}.counterexample_search.eligible_sample_ids",
                errors,
            )
            reviewed_search_ids = validate_unique_string_list(
                counter_search.get("reviewed_sample_ids"),
                f"{label}.counterexample_search.reviewed_sample_ids",
                errors,
            )
            if any(item not in sample_ids or item in holdout_ids for item in eligible_search_ids):
                errors.append(f"{label}.counterexample_search.eligible_sample_ids 必须来自非留出目标样本")
            if any(item not in eligible_search_ids for item in reviewed_search_ids):
                errors.append(f"{label}.counterexample_search.reviewed_sample_ids 必须是适用样本子集")
            if counter_search.get("eligible_sample_count") != len(eligible_search_ids):
                errors.append(f"{label}.counterexample_search.eligible_sample_count 与样本 ID 数量不一致")
            if counter_search.get("reviewed_sample_count") != len(reviewed_search_ids):
                errors.append(f"{label}.counterexample_search.reviewed_sample_count 与样本 ID 数量不一致")
            if counter_search.get("status") == "complete" and set(reviewed_search_ids) != set(eligible_search_ids):
                errors.append(f"{label}.counterexample_search.complete 必须覆盖全部适用样本 ID")
            if counter_search.get("status") == "partial" and not (
                0 <= len(reviewed_search_ids) < len(eligible_search_ids)
            ):
                errors.append(f"{label}.counterexample_search.partial 必须仍有未检查的适用样本")
            if counter_search.get("status") == "not_tested" and reviewed_search_ids:
                errors.append(f"{label}.counterexample_search.not_tested 不能包含已检查样本")
            require_nonempty_string(counter_search.get("notes"), f"{label}.counterexample_search.notes", errors)
            if rule.get("confidence") == "high" and counter_search.get("status") != "complete":
                errors.append(f"{label} 的 high 可信度要求完成反例搜索")
        holdout_evaluation = rule.get("holdout_evaluation")
        if not isinstance(holdout_evaluation, dict):
            errors.append(f"{label}.holdout_evaluation 必须是对象")
        else:
            require_fields(
                holdout_evaluation,
                ("eligible", "matched", "missed", "contradicted", "not_applicable"),
                f"{label}.holdout_evaluation",
                errors,
            )
            for field in ("eligible", "matched", "missed", "contradicted", "not_applicable"):
                require_nonnegative_int(
                    holdout_evaluation.get(field), f"{label}.holdout_evaluation.{field}", errors
                )
            integer_values = all(
                isinstance(holdout_evaluation.get(field), int)
                and not isinstance(holdout_evaluation.get(field), bool)
                for field in ("eligible", "matched", "missed", "contradicted")
            )
            if integer_values and holdout_evaluation["eligible"] != (
                holdout_evaluation["matched"]
                + holdout_evaluation["missed"]
                + holdout_evaluation["contradicted"]
            ):
                errors.append(f"{label}.holdout_evaluation.eligible 与结果计数不一致")
        if rule.get("level") == "author" and rule.get("support_work_count", 0) < 2:
            errors.append(f"{label} 的 author 规则至少需要两部作品支持")

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
    validate_unique_string_list(writing_packet.get("selector_order"), "writing_packet.selector_order", errors, False)
    shared_rule_ids = validate_unique_string_list(
        writing_packet.get("shared_rule_ids"), "writing_packet.shared_rule_ids", errors
    )
    for reference in shared_rule_ids:
        if reference not in rule_ids:
            errors.append(f"writing_packet.shared_rule_ids 引用了未知规则：{reference}")
    packets_value = writing_packet.get("packets")
    packets: dict[str, dict] = {}
    covered_modes: set[str] = set()
    if not isinstance(packets_value, list) or not packets_value:
        errors.append("writing_packet.packets 必须是非空数组")
    else:
        for packet_index, packet in enumerate(packets_value, 1):
            label = f"writing_packet.packets[{packet_index}]"
            if not isinstance(packet, dict):
                errors.append(f"{label} 必须是对象")
                continue
            require_fields(packet, PACKET_FIELDS, label, errors)
            packet_id = packet.get("packet_id")
            require_nonempty_string(packet_id, f"{label}.packet_id", errors)
            if isinstance(packet_id, str):
                if packet_id in packets:
                    errors.append(f"packet_id 重复：{packet_id}")
                packets[packet_id] = packet
            require_nonempty_string(packet.get("name"), f"{label}.name", errors)
            field_targets = (
                ("active_dimension_ids", ANALYSIS_DIMENSION_SET),
                ("active_rule_ids", rule_ids),
                ("scene_mode_ids", set(scene_modes)),
                ("character_voice_ids", set(voices)),
                ("rule_precedence", rule_ids),
            )
            validated_lists: dict[str, list[str]] = {}
            for field, known in field_targets:
                references = validate_unique_string_list(packet.get(field), f"{label}.{field}", errors)
                validated_lists[field] = references
                for reference in references:
                    if reference not in known:
                        errors.append(f"{label}.{field} 引用了未知编号：{reference}")
            for field in ("triggers", "evidence_ids", "drift_corrections"):
                validate_unique_string_list(packet.get(field), f"{label}.{field}", errors, False)
            validate_unique_string_list(
                packet.get("surface_range_refs"), f"{label}.surface_range_refs", errors
            )
            active_rules = set(shared_rule_ids) | set(validated_lists.get("active_rule_ids", []))
            if any(rule_id not in active_rules for rule_id in validated_lists.get("rule_precedence", [])):
                errors.append(f"{label}.rule_precedence 只能引用共享或当前激活规则")
            covered_modes.update(validated_lists.get("scene_mode_ids", []))
    missing_mode_packets = sorted(set(scene_modes) - covered_modes)
    if missing_mode_packets:
        errors.append(f"writing_packet 缺少场景模式包：{', '.join(missing_mode_packets)}")
    if writing_packet.get("master_voice") != profile.get("master_voice"):
        errors.append("writing_packet.master_voice 必须与 master_voice 一致")

    def validate_index(
        records: Sequence[dict] | None,
        index_name: str,
        expected_hashes: Sequence[str],
        expected_works: Sequence[str],
        expected_samples: Sequence[str],
    ) -> dict[str, dict]:
        by_chunk: dict[str, dict] = {}
        if records is None:
            return by_chunk
        valid_records = []
        actual_hashes: dict[str, str | None] = {}
        for position, record in enumerate(records, 1):
            index_label = f"{index_name} line {record.get('_line_number', position)}" if isinstance(record, dict) else f"{index_name} item {position}"
            if not isinstance(record, dict):
                errors.append(f"{index_label} 必须是对象")
                continue
            valid_records.append(record)
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
            for field in ("sample_ids", "chapter_ids", "scene_ids", "scene_types"):
                values = record.get(field)
                if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
                    errors.append(f"{index_label}.{field} 必须是非空字符串数组")
            if isinstance(chunk_id, str):
                if chunk_id in by_chunk:
                    errors.append(f"{index_name} chunk_id 重复：{chunk_id}")
                by_chunk[chunk_id] = record
            source_path = record.get("source_path")
            key = path_key(source_path)
            if key and key not in actual_hashes:
                source = Path(str(source_path))
                actual_hashes[key] = file_sha256(source) if source.is_file() else None
                if actual_hashes[key] is None:
                    errors.append(f"{index_name} 来源文件不存在：{source_path}")
            if key and actual_hashes.get(key) is not None and actual_hashes[key] != record.get("source_sha256"):
                errors.append(f"{index_name} 来源文件哈希已变化：{source_path}")
        observed_hashes = {record.get("source_sha256") for record in valid_records if isinstance(record.get("source_sha256"), str)}
        observed_works = {record.get("work_id") for record in valid_records if isinstance(record.get("work_id"), str)}
        observed_samples = {
            value
            for record in valid_records
            for value in record.get("sample_ids", [])
            if isinstance(value, str)
        }
        if set(expected_hashes) != observed_hashes:
            errors.append(f"{index_name} 来源哈希与画像不一致")
        if set(expected_works) != observed_works:
            errors.append(f"{index_name} 作品编号与画像不一致")
        if set(expected_samples) != observed_samples:
            errors.append(f"{index_name} 样本编号与画像不一致")
        return by_chunk

    index_by_chunk = validate_index(index_records, "目标索引", source_hashes, work_ids, sample_ids)
    comparison_index_by_chunk = validate_index(
        comparison_index_records,
        "对照索引",
        comparison_source_hashes,
        comparison_work_ids,
        comparison_sample_ids,
    )
    if comparison_supplied and comparison_index_records is None:
        errors.append("提供对照语料时必须提供 comparison index")
    if not comparison_supplied and comparison_index_records is not None:
        errors.append("未声明对照语料时不能提供 comparison index")

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
            if dimension not in ANALYSIS_DIMENSION_SET:
                errors.append(f"{label}.dimension 不受支持：{dimension}")
            if item.get("corpus_role") == "target":
                evidence_by_dimension[dimension].add(evidence_id)
            if dimension not in coverage_by_dimension:
                errors.append(f"{label}.dimension 未在 coverage 中声明：{dimension}")
        if not isinstance(item.get("evidence_role"), str) or item.get("evidence_role") not in EVIDENCE_ROLES:
            errors.append(f"{label}.evidence_role 不受支持")
        if item.get("corpus_role") not in CORPUS_ROLES:
            errors.append(f"{label}.corpus_role 不受支持")
        if item.get("evidence_role") == "control" and item.get("corpus_role") != "control":
            errors.append(f"{label} 的 control 证据必须来自对照语料")
        if item.get("evidence_role") != "control" and item.get("corpus_role") != "target":
            errors.append(f"{label} 的目标证据必须来自目标语料")
        if item.get("evaluation_outcome") not in HOLDOUT_OUTCOMES:
            errors.append(f"{label}.evaluation_outcome 不受支持")
        if item.get("evidence_role") != "holdout" and item.get("evaluation_outcome") != "not_applicable":
            errors.append(f"{label} 的非留出证据必须使用 not_applicable 结果")
        for field in ("paragraph_start", "paragraph_end", "content_char_start", "content_char_end"):
            require_positive_int(item.get(field), f"{label}.{field}", errors)
        if isinstance(item.get("paragraph_start"), int) and isinstance(item.get("paragraph_end"), int) and item["paragraph_start"] > item["paragraph_end"]:
            errors.append(f"{label} 的段落起点不能大于终点")
        if isinstance(item.get("content_char_start"), int) and isinstance(item.get("content_char_end"), int) and item["content_char_start"] > item["content_char_end"]:
            errors.append(f"{label} 的内容字符起点不能大于终点")
        for field in ("sample_id", "work_id", "scene_type", "source_path", "source_sha256", "chunk_id", "excerpt", "observation", "eligibility"):
            require_nonempty_string(item.get(field), f"{label}.{field}", errors)
        is_control = item.get("corpus_role") == "control"
        expected_sample_ids = comparison_sample_ids if is_control else sample_ids
        expected_work_ids = comparison_work_ids if is_control else work_ids
        expected_source_hashes = comparison_source_hashes if is_control else source_hashes
        if item.get("sample_id") not in expected_sample_ids:
            errors.append(f"{label}.sample_id 不在对应语料样本中")
        if not is_control and item.get("evidence_role") == "holdout" and item.get("sample_id") not in holdout_ids:
            errors.append(f"{label}.sample_id 未声明在 corpus.holdout_sample_ids 中")
        if not is_control and item.get("evidence_role") != "holdout" and item.get("sample_id") in holdout_ids:
            errors.append(f"{label}.sample_id 已声明为留出样本，不能作为建模证据")
        if item.get("work_id") not in expected_work_ids:
            errors.append(f"{label}.work_id 不在对应语料作品中")
        if item.get("source_sha256") not in expected_source_hashes:
            errors.append(f"{label}.source_sha256 不在对应语料来源中")

        current_index = comparison_index_by_chunk if is_control else index_by_chunk
        current_index_records = comparison_index_records if is_control else index_records
        indexed = current_index.get(item.get("chunk_id"))
        if current_index_records is not None and indexed is None:
            errors.append(f"{label}.chunk_id 不存在于对应索引：{item.get('chunk_id')}")
        elif indexed is not None:
            if path_key(item.get("source_path")) != path_key(indexed.get("source_path")):
                errors.append(f"{label}.source_path 与索引不一致")
            if item.get("source_sha256") != indexed.get("source_sha256"):
                errors.append(f"{label}.source_sha256 与索引不一致")
            if item.get("work_id") != indexed.get("work_id"):
                errors.append(f"{label}.work_id 与索引不一致")
            if item.get("sample_id") not in indexed.get("sample_ids", []):
                errors.append(f"{label}.sample_id 不在索引块的样本标注中")
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
    if isinstance(packets_value, list):
        validate_references(packets_value, "writing_packet.packets", "evidence_ids", known_evidence, errors)

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
            elif item.get("dimension") != rule.get("dimension"):
                errors.append(f"证据 {evidence_id} 的 dimension 与规则 {rule_id} 不一致")

        records = evidence_by_rule.get(rule_id, [])
        support = [item for item in records if item.get("evidence_role") == "support"]
        counterexamples = [item for item in records if item.get("evidence_role") == "counterexample"]
        holdout = [item for item in records if item.get("evidence_role") == "holdout"]
        control = [item for item in records if item.get("evidence_role") == "control"]
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
        outcome_by_sample: dict[str, str] = {}
        for item in holdout:
            sample_id = item.get("sample_id")
            outcome = item.get("evaluation_outcome")
            if isinstance(sample_id, str) and isinstance(outcome, str):
                if sample_id in outcome_by_sample and outcome_by_sample[sample_id] != outcome:
                    errors.append(f"规则 {rule_id} 的同一留出样本出现冲突结果：{sample_id}")
                outcome_by_sample[sample_id] = outcome
        observed_holdout = {
            "matched": sum(outcome == "matched" for outcome in outcome_by_sample.values()),
            "missed": sum(outcome == "missed" for outcome in outcome_by_sample.values()),
            "contradicted": sum(outcome == "contradicted" for outcome in outcome_by_sample.values()),
            "not_applicable": sum(outcome == "not_applicable" for outcome in outcome_by_sample.values()),
        }
        observed_holdout["eligible"] = (
            observed_holdout["matched"] + observed_holdout["missed"] + observed_holdout["contradicted"]
        )
        declared_holdout = rule.get("holdout_evaluation", {})
        if isinstance(declared_holdout, dict):
            for field, observed in observed_holdout.items():
                if declared_holdout.get(field) != observed:
                    errors.append(f"规则 {rule_id} 的 holdout_evaluation.{field} 与证据不一致")
        if holdout_status == "passed" and not (
            observed_holdout["eligible"] > 0
            and observed_holdout["matched"] == observed_holdout["eligible"]
        ):
            errors.append(f"规则 {rule_id} 的 passed 必须全部命中适用留出样本")
        if holdout_status == "not_tested" and holdout:
            errors.append(f"规则 {rule_id} 有 holdout 证据但状态仍是 not_tested")
        if holdout_status in {"partial", "failed"} and observed_holdout["eligible"] == 0:
            errors.append(f"规则 {rule_id} 的 {holdout_status} 缺少适用留出样本")
        if holdout_status == "partial" and not (
            observed_holdout["matched"] > 0
            and (observed_holdout["missed"] > 0 or observed_holdout["contradicted"] > 0)
        ):
            errors.append(f"规则 {rule_id} 的 partial 必须同时包含命中与未命中/冲突")
        if holdout_status == "failed" and not (
            observed_holdout["matched"] == 0
            and (observed_holdout["missed"] > 0 or observed_holdout["contradicted"] > 0)
        ):
            errors.append(f"规则 {rule_id} 的 failed 必须没有命中且存在未命中/冲突")
        if holdout_status == "not_applicable" and observed_holdout["eligible"] != 0:
            errors.append(f"规则 {rule_id} 的 not_applicable 不能包含适用留出结果")
        distinctiveness_ids = rule.get("distinctiveness_evidence_ids", [])
        for evidence_id in distinctiveness_ids if isinstance(distinctiveness_ids, list) else []:
            referenced_ids.add(evidence_id)
            item = evidence_by_id.get(evidence_id)
            if item is None:
                errors.append(f"规则 {rule_id} 引用了不存在的对照证据：{evidence_id}")
            elif item.get("rule_id") != rule_id or item.get("evidence_role") != "control":
                errors.append(f"规则 {rule_id} 的区分度证据必须是本规则的 control 证据")
        distinctiveness_status = rule.get("distinctiveness_status")
        if distinctiveness_status == "not_tested" and distinctiveness_ids:
            errors.append(f"规则 {rule_id} 未测试区分度时不能引用对照证据")
        if distinctiveness_status in {"supported", "shared", "uncertain"} and not distinctiveness_ids:
            errors.append(f"规则 {rule_id} 的区分度结论缺少对照证据")
        if control and not distinctiveness_ids:
            errors.append(f"规则 {rule_id} 存在未引用的 control 证据")

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
    parser.add_argument("--comparison-index", type=Path, help="comparison-index.jsonl；提供对照语料时必需")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.evidence and not args.index:
            raise ValueError("提供 --evidence 时必须同时提供 --index")
        profile = json.loads(args.profile.read_text(encoding="utf-8-sig"))
        evidence = read_jsonl(args.evidence, "证据文件") if args.evidence else None
        index_records = read_jsonl(args.index, "索引文件") if args.index else None
        comparison_index_records = (
            read_jsonl(args.comparison_index, "对照索引文件") if args.comparison_index else None
        )
        errors = validate_profile(profile, evidence, index_records, comparison_index_records)
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
