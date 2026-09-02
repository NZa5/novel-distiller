#!/usr/bin/env python3
"""Render complete human-readable analysis artifacts from validated profile data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import validate_profile


ARTIFACT_SCHEMA_VERSION = "1.0"


def artifact_header(kind: str, profile: dict, evidence: Sequence[dict]) -> str:
    metadata = {
        "kind": kind,
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "profile_id": profile.get("profile_id"),
        "profile_sha256": validate_profile.canonical_json_sha256(profile),
        "evidence_sha256": validate_profile.canonical_json_sha256(list(evidence)),
    }
    return f"<!-- novel-distiller-artifact {json.dumps(metadata, ensure_ascii=False, sort_keys=True)} -->"


def joined(values: object) -> str:
    if not isinstance(values, list) or not values:
        return "—"
    return "、".join(str(value) for value in values)


def render_analysis(profile: dict, evidence: Sequence[dict]) -> str:
    lines = [
        artifact_header("author-analysis", profile, evidence),
        "# Author Analysis",
        "",
        f"- profile_id: {profile.get('profile_id')}",
        f"- profile_scope: {profile.get('profile_scope')}",
        f"- master_voice: {profile.get('master_voice')}",
        "",
        "## Coverage",
        "",
    ]
    for item in profile.get("coverage", []):
        if not isinstance(item, dict):
            continue
        lines.extend([
            f"### {item.get('dimension')}", "",
            f"- status: {item.get('status')}",
            f"- reviewed_sample_ids: {joined(item.get('reviewed_sample_ids'))}",
            f"- evidence_count: {item.get('evidence_count')}",
            f"- finding_summary: {item.get('finding_summary')}",
            f"- uncovered: {joined(item.get('uncovered'))}", "",
        ])

    lines.extend(["", "## Rules", ""])
    evidence_by_rule: dict[str, list[str]] = {}
    for item in evidence:
        if isinstance(item, dict) and isinstance(item.get("rule_id"), str):
            evidence_by_rule.setdefault(item["rule_id"], []).append(str(item.get("evidence_id")))
    for rule in profile.get("rules", []):
        if not isinstance(rule, dict):
            continue
        rule_id = str(rule.get("rule_id"))
        lines.extend([
            f"### {rule_id}",
            "",
            f"- dimension: {rule.get('dimension')}",
            f"- level: {rule.get('level')}",
            f"- classification: {rule.get('classification')}",
            f"- category: {rule.get('category')}",
            f"- trigger: {rule.get('trigger')}",
            f"- observable: {rule.get('observable')}",
            f"- mechanism: {rule.get('mechanism')}",
            f"- effect: {rule.get('effect')}",
            f"- action: {rule.get('action')}",
            f"- limits: {rule.get('limits')}",
            f"- evidence_ids: {joined(evidence_by_rule.get(rule_id, []))}",
            f"- metric_refs: {joined(rule.get('metric_refs'))}",
            f"- metric_claims: {json.dumps(rule.get('metric_claims'), ensure_ascii=False)}",
            f"- support_sample_count: {rule.get('support_sample_count')}",
            f"- support_work_count: {rule.get('support_work_count')}",
            f"- support_scene_type_count: {rule.get('support_scene_type_count')}",
            f"- counterexample_count: {rule.get('counterexample_count')}",
            f"- counterexample_search: {json.dumps(rule.get('counterexample_search'), ensure_ascii=False, sort_keys=True)}",
            f"- holdout_status: {rule.get('holdout_status')}",
            f"- holdout_evaluation: {json.dumps(rule.get('holdout_evaluation'), ensure_ascii=False, sort_keys=True)}",
            f"- distinctiveness_status: {rule.get('distinctiveness_status')}",
            f"- confidence: {rule.get('confidence')}",
            f"- confidence_basis: {rule.get('confidence_basis')}",
            "",
        ])

    lines.extend([
        "## Scene Modes",
        "",
        "```json",
        json.dumps(profile.get("scene_modes"), ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Character Voices",
        "",
        "```json",
        json.dumps(profile.get("character_voices"), ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Rule Precedence",
        "",
        joined(profile.get("rule_precedence")),
        "",
        "## Analysis Saturation",
        "",
        "```json",
        json.dumps(profile.get("analysis_saturation"), ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in profile.get("limitations", [])],
        "",
    ])
    lines.extend(["## Evidence", ""])
    for item in evidence:
        lines.extend([f"### {item.get('evidence_id')}", "",
            f"- rule_id / role: {item.get('rule_id')} / {item.get('evidence_role')}",
            f"- source: {item.get('source_path')}",
            f"- source_sha256: {item.get('source_sha256')}",
            f"- sample / chunk: {item.get('sample_id')} / {item.get('chunk_id')}",
            f"- paragraphs: {item.get('paragraph_start')}–{item.get('paragraph_end')}",
            f"- observation: {item.get('observation')}",
            f"- eligibility / outcome: {item.get('eligibility')} / {item.get('evaluation_outcome')}",
            "", *[f"> {line}" for line in str(item.get('excerpt', '')).splitlines()], ""])
    return "\n".join(lines)


def render_packet(profile: dict, evidence: Sequence[dict]) -> str:
    writing_packet = profile.get("writing_packet", {})
    rules = {rule['rule_id']: rule for rule in profile.get('rules', []) if isinstance(rule, dict) and 'rule_id' in rule}
    evidence_by_id = {item.get('evidence_id'): item for item in evidence}
    lines = [
        artifact_header("writing-packet", profile, evidence),
        "# Writing Packet",
        "",
        f"- profile_id: {profile.get('profile_id')}",
        f"- master_voice: {writing_packet.get('master_voice')}",
        f"- selector_order: {joined(writing_packet.get('selector_order'))}",
        f"- shared_rule_ids: {joined(writing_packet.get('shared_rule_ids'))}",
        "",
    ]
    for packet in writing_packet.get("packets", []):
        if not isinstance(packet, dict):
            continue
        lines.extend([
            f"## {packet.get('packet_id')} — {packet.get('name')}",
            "",
            f"- triggers: {joined(packet.get('triggers'))}",
            f"- active_dimension_ids: {joined(packet.get('active_dimension_ids'))}",
            f"- active_rule_ids: {joined(packet.get('active_rule_ids'))}",
            f"- scene_mode_ids: {joined(packet.get('scene_mode_ids'))}",
            f"- character_voice_ids: {joined(packet.get('character_voice_ids'))}",
            f"- rule_precedence: {joined(packet.get('rule_precedence'))}",
            f"- evidence_ids: {joined(packet.get('evidence_ids'))}",
            f"- surface_range_refs: {joined(packet.get('surface_range_refs'))}",
            f"- drift_corrections: {joined(packet.get('drift_corrections'))}",
            "",
        ])
        selected = set(writing_packet.get('shared_rule_ids', [])) | set(packet.get('active_rule_ids', []))
        for rule_id in packet.get('rule_precedence', []):
            if rule_id not in selected or rule_id not in rules:
                continue
            rule = rules[rule_id]
            lines.extend([f"### {rule_id}", "",
                f"- trigger: {rule.get('trigger')}", f"- action: {rule.get('action')}",
                f"- mechanism / effect: {rule.get('mechanism')} / {rule.get('effect')}",
                f"- limits: {rule.get('limits')}",
                f"- confidence: {rule.get('confidence')} — {rule.get('confidence_basis')}",
                f"- metric_claims: {json.dumps(rule.get('metric_claims'), ensure_ascii=False)}", ""])
        for evidence_id in packet.get('evidence_ids', []):
            item = evidence_by_id.get(evidence_id, {})
            lines.extend([f"- {evidence_id} / {item.get('sample_id')}: {item.get('observation')}",
                          f"  - excerpt: {item.get('excerpt')}"])
        lines.append("")
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从画像与证据生成绑定哈希的完整 Markdown 交付文件")
    parser.add_argument("profile", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--narrative", type=Path, help="附加的深度语义分析 Markdown；保留标准正文以供门禁核对")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        inputs = {path.resolve() for path in (args.profile, args.evidence, args.narrative) if path}
        if args.analysis.resolve() == args.packet.resolve() or {args.analysis.resolve(), args.packet.resolve()} & inputs:
            raise ValueError('输出路径不能互相覆盖或覆盖输入文件')
        profile = json.loads(args.profile.read_text(encoding="utf-8-sig"))
        evidence = validate_profile.read_jsonl(args.evidence, "证据文件")
        narrative = args.narrative.read_text(encoding='utf-8-sig') if args.narrative else ''
        args.analysis.parent.mkdir(parents=True, exist_ok=True)
        args.packet.parent.mkdir(parents=True, exist_ok=True)
        args.analysis.write_text(render_analysis(profile, evidence) + ('\n\n' + narrative if narrative else ''), encoding="utf-8")
        args.packet.write_text(render_packet(profile, evidence), encoding="utf-8")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"已生成分析报告：{args.analysis}")
    print(f"已生成写作参数包：{args.packet}")
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
