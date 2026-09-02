#!/usr/bin/env python3
"""Build, enrich, search, sample, and resume Chinese-fiction corpus indexes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

from analyze_style import (
    analyze_text,
    content_length,
    prepare_text,
    read_text,
    resolve_inputs,
    unique_labels,
)


SCHEMA_VERSION = 4
MANIFEST_SCHEMA_VERSION = "2.0"
LEDGER_SCHEMA_VERSION = "1.3"
HOLDOUT_COMMITMENT_SCHEMA_VERSION = "1.0"
HOLDOUT_REVEAL_SCHEMA_VERSION = "1.0"
SEMANTIC_FIELDS = {
    "sample_ids": "sample_id",
    "chapter_ids": "chapter_id",
    "scene_ids": "scene_id",
    "scene_types": "scene_type",
    "viewpoints": "viewpoint",
    "characters": "character",
    "relationship_states": "relationship_state",
    "emotions": "emotion",
    "chapter_positions": "chapter_position",
}
LEDGER_STATUSES = {"pending", "analyzed", "skipped", "needs_followup", "holdout"}
SAMPLING_FIELDS = (
    "sample_ids",
    "chapter_ids",
    "scene_ids",
    "scene_types",
    "viewpoints",
    "characters",
    "relationship_states",
    "emotions",
    "chapter_positions",
)


def paragraph_units(text: str, target_chars: int) -> list[tuple[int, str]]:
    """Return paragraph-numbered units, splitting only exceptionally long blocks."""
    paragraphs = [block.strip() for block in re.split(r"\n+", text) if block.strip()]
    units: list[tuple[int, str]] = []
    hard_limit = max(int(target_chars * 1.5), target_chars + 100)
    for paragraph_number, paragraph in enumerate(paragraphs, 1):
        if content_length(paragraph) <= hard_limit:
            units.append((paragraph_number, paragraph))
            continue
        start = 0
        while start < len(paragraph):
            end = min(start + target_chars, len(paragraph))
            if end < len(paragraph):
                punctuation_end = max(
                    paragraph.rfind(mark, start, end)
                    for mark in ("。", "！", "？", "!", "?", "……")
                )
                if punctuation_end > start + target_chars // 2:
                    end = punctuation_end + 1
            units.append((paragraph_number, paragraph[start:end].strip()))
            start = end
    return [(number, unit) for number, unit in units if unit]


def split_chunks(
    text: str,
    target_chars: int = 1800,
    break_after_paragraphs: set[int] | None = None,
) -> list[dict]:
    """Group prepared paragraphs into stable chunks near the requested size."""
    if target_chars < 200:
        raise ValueError("chunk_chars 必须至少为 200")
    units = paragraph_units(text, target_chars)
    chunks: list[dict] = []
    current: list[tuple[int, str]] = []
    current_size = 0
    content_offset = 0

    boundaries = break_after_paragraphs or set()

    def flush(boundary_after: bool = False) -> None:
        nonlocal current, current_size, content_offset
        if not current:
            return
        chunk_text = "\n\n".join(unit for _, unit in current)
        size = content_length(chunk_text)
        chunks.append({
            "paragraph_start": current[0][0],
            "paragraph_end": current[-1][0],
            "content_char_start": content_offset + 1 if size else content_offset,
            "content_char_end": content_offset + size,
            "text": chunk_text,
            "_boundary_after": boundary_after,
        })
        content_offset += size
        current = []
        current_size = 0

    for unit_index, (paragraph_number, unit) in enumerate(units):
        unit_size = content_length(unit)
        if current and current_size + unit_size > target_chars and current_size >= target_chars * 0.55:
            flush()
        current.append((paragraph_number, unit))
        current_size += unit_size
        is_last_unit_for_paragraph = (
            unit_index == len(units) - 1 or units[unit_index + 1][0] != paragraph_number
        )
        if paragraph_number in boundaries and is_last_unit_for_paragraph:
            flush(boundary_after=True)
        elif current_size >= target_chars * 1.25:
            flush()
    flush()

    if (
        len(chunks) > 1
        and content_length(chunks[-1]["text"]) < target_chars * 0.25
        and not chunks[-2].get("_boundary_after")
    ):
        tail = chunks.pop()
        previous = chunks[-1]
        previous["text"] += "\n\n" + tail["text"]
        previous["paragraph_end"] = tail["paragraph_end"]
        previous["content_char_end"] = tail["content_char_end"]
        previous["_boundary_after"] = tail.get("_boundary_after", False)
    for chunk in chunks:
        chunk.pop("_boundary_after", None)
    return chunks


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_string_list(value: object, label: str) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list) and all(isinstance(item, str) for item in value):
        values = value
    else:
        raise ValueError(f"{label} 必须是字符串或字符串数组")
    return list(dict.fromkeys(item.strip() for item in values if item.strip()))


def semantic_values(container: dict, plural_field: str, label: str) -> list[str]:
    singular_field = SEMANTIC_FIELDS[plural_field]
    return normalize_string_list(
        container.get(plural_field, container.get(singular_field)),
        f"{label}.{plural_field}",
    )


def resolve_manifest_source(path_value: str, manifest_path: Path) -> Path:
    source_path = Path(path_value)
    if not source_path.is_absolute():
        source_path = manifest_path.parent / source_path
    return source_path.resolve()


def load_manifest(path: Path) -> tuple[dict[str, dict], str]:
    """Load source/work/scene metadata keyed by resolved source path."""
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or data.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError(f"语料清单 schema_version 必须是 {MANIFEST_SCHEMA_VERSION}")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("语料清单 sources 必须是非空数组")

    result: dict[str, dict] = {}
    for index, source in enumerate(sources, 1):
        label = f"sources[{index}]"
        if not isinstance(source, dict):
            raise ValueError(f"{label} 必须是对象")
        path_value = source.get("path")
        work_id = source.get("work_id")
        if not isinstance(path_value, str) or not path_value.strip():
            raise ValueError(f"{label}.path 必须是非空字符串")
        if not isinstance(work_id, str) or not work_id.strip():
            raise ValueError(f"{label}.work_id 必须是非空字符串")
        resolved = resolve_manifest_source(path_value, path)
        key = str(resolved).casefold()
        if key in result:
            raise ValueError(f"语料清单重复声明来源：{resolved}")

        metadata = source.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError(f"{label}.metadata 必须是对象")
        base = {
            plural: semantic_values(metadata, plural, f"{label}.metadata")
            for plural in SEMANTIC_FIELDS
        }
        period = source.get("period", "")
        if not isinstance(period, str):
            raise ValueError(f"{label}.period 必须是字符串")
        segments = source.get("segments", [])
        if not isinstance(segments, list):
            raise ValueError(f"{label}.segments 必须是数组")
        normalized_segments = []
        for segment_index, segment in enumerate(segments, 1):
            segment_label = f"{label}.segments[{segment_index}]"
            if not isinstance(segment, dict):
                raise ValueError(f"{segment_label} 必须是对象")
            start = segment.get("paragraph_start")
            end = segment.get("paragraph_end")
            if isinstance(start, bool) or not isinstance(start, int) or start < 1:
                raise ValueError(f"{segment_label}.paragraph_start 必须是正整数")
            if isinstance(end, bool) or not isinstance(end, int) or end < start:
                raise ValueError(f"{segment_label}.paragraph_end 必须不小于起点")
            normalized = {
                "paragraph_start": start,
                "paragraph_end": end,
                "holdout": bool(segment.get("holdout", False)),
            }
            for plural in SEMANTIC_FIELDS:
                normalized[plural] = semantic_values(segment, plural, segment_label)
            normalized_segments.append(normalized)

        result[key] = {
            "work_id": work_id.strip(),
            "period": period.strip(),
            "base": base,
            "segments": normalized_segments,
        }
    return result, file_sha256(path)


def build_manifest(paths: Sequence[Path]) -> dict:
    """Create an editable manifest scaffold without claiming inferred scene metadata."""
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "sources": [
            {
                "path": str(path.resolve()),
                "work_id": path.stem,
                "period": "",
                "metadata": {
                    "sample_ids": [],
                    "chapter_ids": [],
                    "scene_ids": [],
                    "scene_types": [],
                    "viewpoints": [],
                    "characters": [],
                    "relationship_states": [],
                    "emotions": [],
                    "chapter_positions": [],
                },
                "segments": [],
            }
            for path in paths
        ],
    }


def metadata_for_chunk(source_metadata: dict, paragraph_start: int, paragraph_end: int) -> dict:
    values = {field: list(source_metadata["base"].get(field, [])) for field in SEMANTIC_FIELDS}
    holdout = False
    for segment in source_metadata["segments"]:
        overlaps = segment["paragraph_start"] <= paragraph_end and segment["paragraph_end"] >= paragraph_start
        if not overlaps:
            continue
        holdout = holdout or segment["holdout"]
        for field in SEMANTIC_FIELDS:
            values[field].extend(segment[field])
    return {
        "work_id": source_metadata["work_id"],
        "period": source_metadata["period"],
        **{field: list(dict.fromkeys(items)) for field, items in values.items()},
        "holdout": holdout,
    }


def build_index(
    paths: Sequence[Path],
    chunk_chars: int = 1800,
    reflow_hard_wrap: bool = False,
    strip_annotations: bool = False,
    manifest: Path | None = None,
) -> list[dict]:
    records: list[dict] = []
    manifest_sources: dict[str, dict] = {}
    manifest_hash = ""
    if manifest is not None:
        manifest_sources, manifest_hash = load_manifest(manifest)

    for path, label in zip(paths, unique_labels(paths)):
        text, encoding = read_text(path)
        prepared = prepare_text(text, reflow_hard_wrap, strip_annotations)
        source_hash = file_sha256(path)
        source_key = str(path.resolve()).casefold()
        if manifest is not None and source_key not in manifest_sources:
            raise ValueError(f"语料清单缺少来源：{path.resolve()}")
        source_metadata = manifest_sources.get(source_key, {
            "work_id": label,
            "period": "",
            "base": {field: [] for field in SEMANTIC_FIELDS},
            "segments": [],
        })
        metadata_status = "manifest" if manifest is not None else "file_fallback"
        preprocessing = {
            "chunk_chars": chunk_chars,
            "reflow_hard_wrap": reflow_hard_wrap,
            "strip_annotations": strip_annotations,
            "manifest_sha256": manifest_hash,
        }
        fingerprint_input = json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "source_sha256": source_hash,
                "source_identity": str(path.resolve()).casefold(),
                "work_id": source_metadata["work_id"],
                **preprocessing,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        preprocessing_fingerprint = hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()
        break_after = {
            segment["paragraph_end"]
            for segment in source_metadata.get("segments", [])
        }
        for number, chunk in enumerate(
            split_chunks(prepared, chunk_chars, break_after_paragraphs=break_after), 1
        ):
            metrics = analyze_text(chunk["text"])
            semantic_metadata = metadata_for_chunk(
                source_metadata,
                chunk["paragraph_start"],
                chunk["paragraph_end"],
            )
            records.append({
                "schema_version": SCHEMA_VERSION,
                "chunk_id": f"{source_hash[:12]}-{preprocessing_fingerprint[:12]}-{number:05d}",
                "source": label,
                "source_path": str(path.resolve()),
                "source_sha256": source_hash,
                "preprocessing": preprocessing,
                "preprocessing_fingerprint": preprocessing_fingerprint,
                "encoding": encoding,
                "metadata_status": metadata_status,
                **semantic_metadata,
                "chunk_number": number,
                "paragraph_start": chunk["paragraph_start"],
                "paragraph_end": chunk["paragraph_end"],
                "content_char_start": chunk["content_char_start"],
                "content_char_end": chunk["content_char_end"],
                "metrics": metrics,
                "text": chunk["text"],
            })
    return records


def write_jsonl(records: Iterable[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_json(value: object, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("schema_version") != SCHEMA_VERSION:
                raise ValueError(f"第 {line_number} 行的索引版本不受支持；请重建索引")
            records.append(record)
    return records


def metric_vector(metrics: dict) -> list[float]:
    punctuation = metrics["punctuation"]
    return [
        metrics["sentence_length"]["mean"] / 30,
        math.log1p(metrics["paragraph_length"]["mean"]) / 5,
        metrics["sentence_bands"]["short_le_15"]["ratio"],
        metrics["sentence_bands"]["long_ge_40"]["ratio"],
        metrics["dialogue"]["content_ratio"] * 2,
        punctuation["逗号，"]["per_1000"] / 60,
        punctuation["句号。"]["per_1000"] / 40,
        punctuation["问号？"]["per_1000"] / 12,
        punctuation["分号；"]["per_1000"] / 12,
        punctuation["引号组"]["per_1000"] / 25,
    ]


def style_distance(left: dict, right: dict) -> float:
    return sum(abs(a - b) for a, b in zip(metric_vector(left), metric_vector(right)))


def metadata_matches(record: dict, field: str, query: str | None) -> bool:
    if not query:
        return True
    query_folded = query.casefold()
    values = record.get(field, [])
    if isinstance(values, str):
        values = [values]
    return any(query_folded in str(value).casefold() for value in values)


def search_records(
    records: Sequence[dict],
    query_text: str | None = None,
    contains: Sequence[str] = (),
    source: str | None = None,
    top: int = 5,
    work_id: str | None = None,
    semantic_filters: dict[str, str | None] | None = None,
    exclude_holdout: bool = False,
) -> list[dict]:
    query_metrics = analyze_text(query_text) if query_text else None
    terms = [term for term in contains if term]
    filters = semantic_filters or {}
    scored: list[tuple[float, int, str, dict]] = []
    for record in records:
        if source and source.casefold() not in record["source"].casefold():
            continue
        if work_id and work_id.casefold() != str(record.get("work_id", "")).casefold():
            continue
        if exclude_holdout and record.get("holdout") is True:
            continue
        if any(not metadata_matches(record, field, value) for field, value in filters.items()):
            continue
        term_hits = sum(record["text"].count(term) for term in terms)
        if terms and term_hits == 0:
            continue
        distance = style_distance(query_metrics, record["metrics"]) if query_metrics else 0.0
        stable_id = str(record.get("chunk_id") or f"{record.get('source', '')}|{record.get('chunk_number', '')}")
        stable = hashlib.sha256(stable_id.encode("utf-8")).hexdigest()
        scored.append((distance, -term_hits, stable, record))
    scored.sort(key=lambda item: (item[0], item[1], item[2]))
    return [record for _, _, _, record in scored[: max(top, 0)]]


def render_matches(records: Sequence[dict], include_text: bool = False) -> str:
    lines = ["# 语料证据检索", ""]
    for rank, record in enumerate(records, 1):
        locator = (
            f"段落 {record['paragraph_start']}–{record['paragraph_end']}，"
            f"内容字符 {record['content_char_start']}–{record['content_char_end']}"
        )
        semantic = []
        for field, label in (
            ("sample_ids", "样本"),
            ("chapter_ids", "章节"),
            ("scene_ids", "场景编号"),
            ("scene_types", "场景"),
            ("viewpoints", "视角"),
            ("characters", "角色"),
            ("relationship_states", "关系"),
            ("emotions", "情绪"),
            ("chapter_positions", "章节位置"),
        ):
            values = record.get(field, [])
            if values:
                semantic.append(f"{label}：{'、'.join(values)}")
        lines.extend([
            f"## {rank}. {record['source']} · {record['chunk_id']}",
            "",
            f"- 作品：{record.get('work_id', record['source'])}",
            f"- 定位：{locator}",
            f"- 来源 SHA-256：`{record['source_sha256']}`",
            f"- 语义元数据：{'；'.join(semantic) if semantic else '未标注'}",
            f"- 留出：{'是' if record.get('holdout') else '否'}",
            "",
        ])
        text = record["text"] if include_text else record["text"][:240].replace("\n", " ")
        lines.extend([text, ""])
    if not records:
        lines.append("没有符合条件的文本块。")
    return "\n".join(lines).rstrip() + "\n"


def stable_record_key(record: dict, seed: int) -> str:
    return hashlib.sha256(f"{seed}|{record['chunk_id']}".encode("utf-8")).hexdigest()


def sampling_values(record: dict, field: str) -> list[str]:
    values = record.get(field, [])
    if isinstance(values, str):
        values = [values]
    normalized = sorted({str(value) for value in values if str(value)})
    return normalized or ["unknown"]


def novelty_score(record: dict, coverage_counts: dict[tuple[str, str], int]) -> float:
    """Reward under-covered values without favoring records that carry more labels."""
    score = 0.0
    for field in SAMPLING_FIELDS:
        values = sampling_values(record, field)
        score += sum(1 / (1 + coverage_counts[(field, value)]) for value in values) / len(values)
    return score


def balanced_select(records: Sequence[dict], count: int, seed: int) -> list[dict]:
    """Balance works, then greedily cover all annotated semantic strata."""
    if count <= 0:
        return []
    by_work: dict[str, list[dict]] = {}
    for record in records:
        work_id = str(record.get("work_id") or record.get("source") or "unknown")
        by_work.setdefault(work_id, []).append(record)
    for candidates in by_work.values():
        candidates.sort(key=lambda record: stable_record_key(record, seed))

    selected: list[dict] = []
    coverage_counts: dict[tuple[str, str], int] = defaultdict(int)
    work_ids = sorted(by_work)
    while len(selected) < min(count, len(records)) and any(by_work[work] for work in work_ids):
        for work_id in work_ids:
            candidates = by_work[work_id]
            if not candidates or len(selected) >= count:
                continue
            chosen = min(
                candidates,
                key=lambda record: (-novelty_score(record, coverage_counts), stable_record_key(record, seed)),
            )
            candidates.remove(chosen)
            selected.append(chosen)
            for field in SAMPLING_FIELDS:
                for value in sampling_values(chosen, field):
                    coverage_counts[(field, value)] += 1
    return selected


def group_records_by_scene(records: Sequence[dict]) -> list[list[dict]]:
    """Keep chunks sharing a scene ID in the same atomic sampling group."""
    items = list(records)
    parents = list(range(len(items)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    first_by_scene: dict[tuple[str, str], int] = {}
    for index, record in enumerate(items):
        work_id = str(record.get("work_id") or record.get("source") or "unknown")
        scene_ids = sampling_values(record, "scene_ids")
        if scene_ids == ["unknown"]:
            continue
        for scene_id in scene_ids:
            key = (work_id, scene_id)
            if key in first_by_scene:
                union(index, first_by_scene[key])
            else:
                first_by_scene[key] = index

    grouped: dict[int, list[dict]] = defaultdict(list)
    for index, record in enumerate(items):
        grouped[find(index)].append(record)
    groups = [sorted(group, key=lambda item: str(item["chunk_id"])) for group in grouped.values()]
    groups.sort(key=lambda group: min(str(item["chunk_id"]) for item in group))
    return groups


def summarize_scene_group(group: Sequence[dict]) -> dict:
    first = group[0]
    work_id = str(first.get("work_id") or first.get("source") or "unknown")
    values = {
        field: sorted({value for record in group for value in sampling_values(record, field) if value != "unknown"})
        for field in SAMPLING_FIELDS
    }
    identity = json.dumps(
        {
            "work_id": work_id,
            "scene_ids": values["scene_ids"],
            "chunk_ids": sorted(str(record["chunk_id"]) for record in group),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    group_id = f"scene-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:16]}"
    return {
        "chunk_id": group_id,
        "scene_group_id": group_id,
        "source": first.get("source", ""),
        "work_id": work_id,
        **values,
        "records": list(group),
    }


def recommend_budget(records: Sequence[dict], scene_groups: Sequence[Sequence[dict]] | None = None) -> tuple[int, dict]:
    """Return a corpus-adaptive target number of close-read chunks."""
    items = list(records)
    if not items:
        raise ValueError("索引中没有文本块")
    groups = list(scene_groups) if scene_groups is not None else group_records_by_scene(items)
    available = len(items)
    work_count = len({str(item.get("work_id") or item.get("source") or "unknown") for item in items})
    strata = {
        field: len({value for item in items for value in sampling_values(item, field) if value != "unknown"})
        for field in SAMPLING_FIELDS
        if field != "scene_ids"
    }
    if available <= 48:
        budget = available
    else:
        candidates = [
            48,
            12 * work_count,
            math.ceil(len(groups) * 0.5),
            math.ceil(strata["sample_ids"] * 0.5),
            math.ceil(strata["chapter_ids"] * 0.5),
            3 * strata["scene_types"],
            3 * strata["viewpoints"],
            2 * strata["characters"],
            2 * strata["relationship_states"],
            2 * strata["emotions"],
            3 * strata["chapter_positions"],
        ]
        budget = min(available, max(candidates))
    return budget, {
        "available_chunks": available,
        "work_count": work_count,
        "scene_group_count": len(groups),
        "semantic_strata": strata,
        "formula": "min(A, max(48, 12N, ceil(0.5G), ceil(0.5S), ceil(0.5H), 3T, 3V, 2C, 2R, 2E, 3P))",
    }


def select_scene_groups(groups: Sequence[Sequence[dict]], chunk_budget: int, seed: int) -> list[list[dict]]:
    """Select whole scene groups until the requested chunk budget is reached."""
    summaries = [summarize_scene_group(group) for group in groups]
    ordered = balanced_select(summaries, len(summaries), seed)
    selected: list[list[dict]] = []
    selected_chunks = 0
    for summary in ordered:
        if selected_chunks >= chunk_budget:
            break
        group = list(summary["records"])
        selected.append(group)
        selected_chunks += len(group)
    return selected


def coverage_summary(records: Sequence[dict]) -> dict:
    def unique(field: str) -> list[str]:
        values = []
        for record in records:
            current = record.get(field, [])
            if isinstance(current, str):
                current = [current]
            values.extend(str(value) for value in current if str(value))
        return sorted(set(values))

    return {
        "chunk_count": len(records),
        "work_ids": sorted({str(record.get("work_id", "")) for record in records if record.get("work_id")}),
        "sample_ids": unique("sample_ids"),
        "chapter_ids": unique("chapter_ids"),
        "scene_ids": unique("scene_ids"),
        "scene_group_ids": sorted({str(record.get("scene_group_id", "")) for record in records if record.get("scene_group_id")}),
        "scene_types": unique("scene_types"),
        "viewpoints": unique("viewpoints"),
        "characters": unique("characters"),
        "relationship_states": unique("relationship_states"),
        "emotions": unique("emotions"),
        "chapter_positions": unique("chapter_positions"),
    }


def build_sampling_ledger(
    records: Sequence[dict],
    index_sha256: str,
    budget: int | None = None,
    holdout_ratio: float = 0.2,
    seed: int = 20260831,
) -> dict:
    if budget is not None and budget < 1:
        raise ValueError("budget 必须至少为 1")
    if not 0 <= holdout_ratio < 1:
        raise ValueError("holdout_ratio 必须在 0（含）到 1（不含）之间")
    if not records:
        raise ValueError("索引中没有文本块")

    scene_groups = group_records_by_scene(records)
    group_summaries = [summarize_scene_group(group) for group in scene_groups]
    manually_held_group_ids = {
        summary["scene_group_id"]
        for summary in group_summaries
        if any(record.get("holdout") is True for record in summary["records"])
    }
    if manually_held_group_ids:
        holdout_groups = [
            list(summary["records"])
            for summary in group_summaries
            if summary["scene_group_id"] in manually_held_group_ids
        ]
    elif len(scene_groups) >= 10 and holdout_ratio > 0:
        holdout_group_count = min(len(scene_groups) - 1, max(2, round(len(scene_groups) * holdout_ratio)))
        selected_summaries = balanced_select(group_summaries, holdout_group_count, seed + 1)
        selected_group_ids = {summary["scene_group_id"] for summary in selected_summaries}
        holdout_groups = [
            list(summary["records"])
            for summary in group_summaries
            if summary["scene_group_id"] in selected_group_ids
        ]
    else:
        holdout_groups = []
    holdout_group_ids = {summarize_scene_group(group)["scene_group_id"] for group in holdout_groups}
    analysis_groups_available = [
        group for group in scene_groups if summarize_scene_group(group)["scene_group_id"] not in holdout_group_ids
    ]
    analysis_candidates = [record for group in analysis_groups_available for record in group]
    if not analysis_candidates:
        raise ValueError("留出设置覆盖了全部场景组，至少保留一个场景组用于分析")
    recommended_budget, budget_basis = recommend_budget(analysis_candidates, analysis_groups_available)
    target_budget = recommended_budget if budget is None else min(budget, len(analysis_candidates))
    analysis_groups = select_scene_groups(analysis_groups_available, target_budget, seed)

    def expand(groups: Sequence[Sequence[dict]]) -> list[dict]:
        expanded = []
        for group in groups:
            group_id = summarize_scene_group(group)["scene_group_id"]
            for record in group:
                expanded.append({**record, "scene_group_id": group_id})
        return expanded

    analysis = expand(analysis_groups)
    holdout = expand(holdout_groups)

    work_chunk_counts: dict[str, int] = defaultdict(int)
    for record in records:
        work_chunk_counts[str(record.get("work_id") or record.get("source") or "unknown")] += 1
    coarse_groups = []
    for group in scene_groups:
        summary = summarize_scene_group(group)
        work_id = summary["work_id"]
        coarse_limit = max(12, math.ceil(work_chunk_counts[work_id] * 0.15))
        if len(group) > coarse_limit:
            coarse_groups.append({
                "scene_group_id": summary["scene_group_id"],
                "work_id": work_id,
                "chunk_count": len(group),
                "limit": coarse_limit,
                "scene_ids": summary["scene_ids"],
                "review_status": "pending",
                "review_note": "",
            })

    def item(record: dict, role: str) -> dict:
        return {
            "chunk_id": record["chunk_id"],
            "scene_group_id": record["scene_group_id"],
            "source": record["source"],
            "work_id": record.get("work_id", record["source"]),
            "sample_ids": record.get("sample_ids", []),
            "chapter_ids": record.get("chapter_ids", []),
            "scene_ids": record.get("scene_ids", []),
            "scene_types": record.get("scene_types", []),
            "viewpoints": record.get("viewpoints", []),
            "characters": record.get("characters", []),
            "relationship_states": record.get("relationship_states", []),
            "emotions": record.get("emotions", []),
            "chapter_positions": record.get("chapter_positions", []),
            "role": role,
            "status": "holdout" if role == "holdout" else "pending",
            "paragraph_start": record["paragraph_start"],
            "paragraph_end": record["paragraph_end"],
            "notes": [],
        }

    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "index_schema_version": SCHEMA_VERSION,
        "index_sha256": index_sha256,
        "holdout_separation": "combined",
        "holdout_index_sha256": None,
        "holdout_commitment_sha256": None,
        "seed": seed,
        "budget_mode": "auto" if budget is None else "manual",
        "budget_requested": budget,
        "budget_effective": target_budget,
        "budget_recommended": recommended_budget,
        "budget_basis": budget_basis,
        "budget_overshoot_chunks": max(0, len(analysis) - target_budget),
        "holdout_ratio": holdout_ratio,
        "selection_method": "scene_group_atomic_then_work_round_robin_then_semantic_novelty_then_stable_hash",
        "scene_grouping_status": (
            "complete" if all(record.get("scene_ids") for record in records)
            else "partial" if any(record.get("scene_ids") for record in records)
            else "unavailable"
        ),
        "scene_granularity_status": "coarse" if coarse_groups else "acceptable",
        "coarse_scene_groups": coarse_groups,
        "analysis_scene_group_count": len(analysis_groups),
        "holdout_scene_group_count": len(holdout_groups),
        "analysis_coverage": coverage_summary(analysis),
        "holdout_coverage": coverage_summary(holdout),
        "items": [item(record, "analysis") for record in analysis] + [item(record, "holdout") for record in holdout],
        "updates": [],
    }


def prepare_separated_corpus(
    paths: Sequence[Path],
    manifest: Path,
    analysis_index_path: Path,
    holdout_index_path: Path,
    commitment_path: Path,
    ledger_path: Path,
    chunk_chars: int = 1800,
    reflow_hard_wrap: bool = False,
    strip_annotations: bool = False,
    budget: int | None = None,
    holdout_ratio: float = 0.2,
    seed: int = 20260831,
) -> tuple[dict, dict]:
    """Build analysis and holdout indexes without ever writing a combined index."""
    records = build_index(
        paths,
        chunk_chars=chunk_chars,
        reflow_hard_wrap=reflow_hard_wrap,
        strip_annotations=strip_annotations,
        manifest=manifest,
    )
    ledger = build_sampling_ledger(records, "0" * 64, budget, holdout_ratio, seed)
    holdout_ids = {
        item["chunk_id"] for item in ledger["items"] if item.get("role") == "holdout"
    }
    analysis_records = [record for record in records if record.get("chunk_id") not in holdout_ids]
    holdout_records = [record for record in records if record.get("chunk_id") in holdout_ids]
    analysis_samples = {sample for record in analysis_records for sample in record.get('sample_ids', [])}
    holdout_samples = {sample for record in holdout_records for sample in record.get('sample_ids', [])}
    if analysis_samples & holdout_samples:
        raise ValueError('sample_id 跨越分析与留出场景；请在清单中按可分离场景分配独立样本编号')
    for record in analysis_records:
        record["holdout"] = False
    for record in holdout_records:
        record["holdout"] = True
    write_jsonl(analysis_records, analysis_index_path)
    write_jsonl(holdout_records, holdout_index_path)

    manifest_hash = file_sha256(manifest)
    holdout_index_hash = file_sha256(holdout_index_path)
    commitment = {
        "schema_version": HOLDOUT_COMMITMENT_SCHEMA_VERSION,
        "index_schema_version": SCHEMA_VERSION,
        "manifest_sha256": manifest_hash,
        "holdout_index_sha256": holdout_index_hash,
        "chunk_ids": sorted(holdout_ids),
        "sample_ids": sorted({
            sample_id
            for record in holdout_records
            for sample_id in record.get("sample_ids", [])
            if isinstance(sample_id, str)
        }),
        "scene_ids": sorted({
            scene_id
            for record in holdout_records
            for scene_id in record.get("scene_ids", [])
            if isinstance(scene_id, str)
        }),
        "source_hashes": sorted({
            record["source_sha256"] for record in holdout_records
            if isinstance(record.get("source_sha256"), str)
        }),
    }
    write_json(commitment, commitment_path)
    ledger["index_sha256"] = file_sha256(analysis_index_path)
    ledger["holdout_separation"] = "separate"
    ledger["holdout_index_sha256"] = holdout_index_hash
    ledger["holdout_commitment_sha256"] = file_sha256(commitment_path)
    write_json(ledger, ledger_path)
    return ledger, commitment


def create_holdout_reveal(
    holdout_index_path: Path,
    commitment_path: Path,
    provisional_profile_path: Path,
) -> dict:
    commitment = json.loads(commitment_path.read_text(encoding="utf-8-sig"))
    if not isinstance(commitment, dict) or commitment.get("schema_version") != HOLDOUT_COMMITMENT_SCHEMA_VERSION:
        raise ValueError("留出承诺文件 schema_version 不受支持")
    holdout_hash = file_sha256(holdout_index_path)
    if commitment.get("holdout_index_sha256") != holdout_hash:
        raise ValueError("留出索引与承诺文件不一致")
    read_jsonl(holdout_index_path)
    provisional = json.loads(provisional_profile_path.read_text(encoding="utf-8-sig"))
    if not isinstance(provisional, dict) or not provisional.get('profile_id') or not provisional.get('rules'):
        raise ValueError('解封前必须保存含 profile_id 和非空 rules 的初稿')
    return {
        "schema_version": HOLDOUT_REVEAL_SCHEMA_VERSION,
        "commitment_sha256": file_sha256(commitment_path),
        "holdout_index_sha256": holdout_hash,
        "provisional_profile_sha256": file_sha256(provisional_profile_path),
        "revealed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def read_ledger(path: Path) -> dict:
    ledger = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(ledger, dict) or ledger.get("schema_version") != LEDGER_SCHEMA_VERSION:
        raise ValueError(f"取样账本 schema_version 必须是 {LEDGER_SCHEMA_VERSION}")
    items = ledger.get("items")
    if not isinstance(items, list):
        raise ValueError("取样账本 items 必须是数组")
    budget_mode = ledger.get("budget_mode")
    if budget_mode not in {"auto", "manual"}:
        raise ValueError("取样账本 budget_mode 必须是 auto/manual")
    budget_requested = ledger.get("budget_requested")
    if budget_mode == "auto" and budget_requested is not None:
        raise ValueError("自动预算的 budget_requested 必须为 null")
    if budget_mode == "manual" and (
        isinstance(budget_requested, bool) or not isinstance(budget_requested, int) or budget_requested < 1
    ):
        raise ValueError("手工预算的 budget_requested 必须是正整数")
    for field in ("budget_effective", "budget_recommended"):
        value = ledger.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"取样账本 {field} 必须是正整数")
    overshoot = ledger.get("budget_overshoot_chunks")
    if isinstance(overshoot, bool) or not isinstance(overshoot, int) or overshoot < 0:
        raise ValueError("取样账本 budget_overshoot_chunks 必须是非负整数")
    if not isinstance(ledger.get("budget_basis"), dict):
        raise ValueError("取样账本 budget_basis 必须是对象")
    separation = ledger.get("holdout_separation")
    if separation not in {"combined", "separate"}:
        raise ValueError("取样账本 holdout_separation 必须是 combined/separate")
    for field in ("holdout_index_sha256", "holdout_commitment_sha256"):
        value = ledger.get(field)
        if separation == "separate":
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", value):
                raise ValueError(f"取样账本 {field} 必须是 SHA-256")
        elif value is not None:
            raise ValueError(f"combined 账本的 {field} 必须为 null")
    if ledger.get("scene_grouping_status") not in {"complete", "partial", "unavailable"}:
        raise ValueError("取样账本 scene_grouping_status 不受支持")
    if ledger.get("scene_granularity_status") not in {"acceptable", "coarse"}:
        raise ValueError("取样账本 scene_granularity_status 不受支持")
    coarse_groups = ledger.get("coarse_scene_groups")
    if not isinstance(coarse_groups, list):
        raise ValueError("取样账本 coarse_scene_groups 必须是数组")
    pending_coarse_groups = []
    for index, group in enumerate(coarse_groups, 1):
        if not isinstance(group, dict):
            raise ValueError(f"coarse_scene_groups[{index}] 必须是对象")
        if group.get("review_status") not in {"pending", "confirmed"}:
            raise ValueError(f"coarse_scene_groups[{index}].review_status 不受支持")
        if group.get("review_status") == "confirmed" and not str(group.get("review_note", "")).strip():
            raise ValueError(f"coarse_scene_groups[{index}] 确认后必须记录复核说明")
        if group.get("review_status") == "pending":
            pending_coarse_groups.append(group)
    if ledger.get("scene_granularity_status") == "coarse" and not pending_coarse_groups:
        raise ValueError("粗粒度场景状态必须存在待复核的 coarse_scene_groups")
    if ledger.get("scene_granularity_status") == "acceptable" and pending_coarse_groups:
        raise ValueError("可接受场景粒度不能保留待复核的 coarse_scene_groups")
    ids = []
    roles_by_group: dict[str, set[str]] = defaultdict(set)
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"取样账本 items[{index}] 必须是对象")
        chunk_id = item.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            raise ValueError(f"取样账本 items[{index}].chunk_id 必须是非空字符串")
        scene_group_id = item.get("scene_group_id")
        if not isinstance(scene_group_id, str) or not scene_group_id.strip():
            raise ValueError(f"取样账本 items[{index}].scene_group_id 必须是非空字符串")
        if not isinstance(item.get("role"), str) or item.get("role") not in {"analysis", "holdout"}:
            raise ValueError(f"取样账本 items[{index}].role 不受支持")
        if not isinstance(item.get("status"), str) or item.get("status") not in LEDGER_STATUSES:
            raise ValueError(f"取样账本 items[{index}].status 不受支持")
        if item.get("role") == "holdout" and item.get("status") != "holdout":
            raise ValueError(f"取样账本 items[{index}] 的留出状态不能被修改")
        if item.get("role") == "analysis" and item.get("status") == "holdout":
            raise ValueError(f"取样账本 items[{index}] 的分析角色不能使用 holdout 状态")
        roles_by_group[scene_group_id].add(item["role"])
        ids.append(chunk_id)
    if len(ids) != len(set(ids)):
        raise ValueError("取样账本包含重复 chunk_id")
    mixed_groups = sorted(group_id for group_id, roles in roles_by_group.items() if len(roles) > 1)
    if mixed_groups:
        raise ValueError(f"同一场景组不能同时进入分析和留出：{', '.join(mixed_groups)}")
    observed_analysis_groups = len({
        item["scene_group_id"] for item in items if item.get("role") == "analysis"
    })
    observed_holdout_groups = len({
        item["scene_group_id"] for item in items if item.get("role") == "holdout"
    })
    if ledger.get("analysis_scene_group_count") != observed_analysis_groups:
        raise ValueError("取样账本 analysis_scene_group_count 与 items 不一致")
    if ledger.get("holdout_scene_group_count") != observed_holdout_groups:
        raise ValueError("取样账本 holdout_scene_group_count 与 items 不一致")
    analysis_item_count = sum(item.get("role") == "analysis" for item in items)
    holdout_item_count = sum(item.get("role") == "holdout" for item in items)
    for field, expected in (
        ("analysis_coverage", analysis_item_count),
        ("holdout_coverage", holdout_item_count),
    ):
        coverage = ledger.get(field)
        if not isinstance(coverage, dict) or coverage.get("chunk_count") != expected:
            raise ValueError(f"取样账本 {field}.chunk_count 与 items 不一致")
    if overshoot != max(0, analysis_item_count - ledger["budget_effective"]):
        raise ValueError("取样账本 budget_overshoot_chunks 与实际分析块数不一致")
    updates = ledger.get('updates')
    if not isinstance(updates, list):
        raise ValueError('取样账本 updates 必须是数组')
    for sequence, update in enumerate(updates, 1):
        if not isinstance(update, dict) or update.get('sequence') != sequence or isinstance(update.get('sequence'), bool):
            raise ValueError('取样账本更新 sequence 必须从 1 开始连续且不重复')
        if update.get('action') not in {'mark', 'extend', 'confirm_scene_granularity'}:
            raise ValueError('取样账本更新 action 不受支持')
        if update.get('action') == 'extend':
            for field in ('added_chunk_ids', 'added_sample_ids'):
                values = update.get(field)
                if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values) or len(set(values)) != len(values):
                    raise ValueError(f'extend 更新 {field} 必须是唯一字符串数组')
    return ledger


def mark_ledger(ledger: dict, chunk_ids: Sequence[str], status: str, note: str = "") -> dict:
    if status not in LEDGER_STATUSES - {"holdout"}:
        raise ValueError("status 必须是 pending/analyzed/skipped/needs_followup")
    requested = set(chunk_ids)
    found: set[str] = set()
    for item in ledger["items"]:
        chunk_id = item.get("chunk_id")
        if chunk_id not in requested:
            continue
        found.add(chunk_id)
        if item.get("role") == "holdout":
            raise ValueError(f"不能把留出样本标记为分析样本：{chunk_id}")
        item["status"] = status
        if note:
            item.setdefault("notes", []).append(note)
    missing = sorted(requested - found)
    if missing:
        raise ValueError(f"取样账本中不存在 chunk_id：{', '.join(missing)}")
    ledger.setdefault("updates", []).append({
        "sequence": len(ledger.get("updates", [])) + 1,
        "action": "mark",
        "chunk_ids": sorted(requested),
        "status": status,
        "note": note,
    })
    return ledger


def extend_ledger(
    ledger: dict,
    index_records: Sequence[dict],
    chunk_ids: Sequence[str],
    note: str = "",
) -> dict:
    """Add requested chunks and their complete scene groups to the analysis ledger."""
    requested = set(chunk_ids)
    if not requested:
        raise ValueError("至少提供一个 chunk_id")
    indexed_ids = {record.get("chunk_id") for record in index_records}
    missing = sorted(requested - indexed_ids)
    if missing:
        raise ValueError(f"索引中不存在 chunk_id：{', '.join(missing)}")

    selected_groups: list[tuple[str, list[dict]]] = []
    for group in group_records_by_scene(index_records):
        summary = summarize_scene_group(group)
        if any(record.get("chunk_id") in requested for record in group):
            selected_groups.append((summary["scene_group_id"], list(group)))

    holdout_group_ids = {
        item.get("scene_group_id")
        for item in ledger.get("items", [])
        if item.get("role") == "holdout"
    }
    blocked = sorted(group_id for group_id, _ in selected_groups if group_id in holdout_group_ids)
    if blocked:
        raise ValueError(f"不能把留出场景组加入分析：{', '.join(blocked)}")

    existing_ids = {item.get("chunk_id") for item in ledger.get("items", [])}
    additions = []
    for group_id, group in selected_groups:
        for record in group:
            if record.get("chunk_id") in existing_ids:
                continue
            item = {
                "chunk_id": record["chunk_id"],
                "scene_group_id": group_id,
                "source": record["source"],
                "work_id": record.get("work_id", record["source"]),
                "sample_ids": record.get("sample_ids", []),
                "chapter_ids": record.get("chapter_ids", []),
                "scene_ids": record.get("scene_ids", []),
                "scene_types": record.get("scene_types", []),
                "viewpoints": record.get("viewpoints", []),
                "characters": record.get("characters", []),
                "relationship_states": record.get("relationship_states", []),
                "emotions": record.get("emotions", []),
                "chapter_positions": record.get("chapter_positions", []),
                "role": "analysis",
                "status": "pending",
                "paragraph_start": record["paragraph_start"],
                "paragraph_end": record["paragraph_end"],
                "notes": [note] if note else [],
            }
            additions.append(item)
            existing_ids.add(record["chunk_id"])
    if not additions:
        raise ValueError("所选文本块及其场景组已在取样账本中")

    analysis_items = [item for item in ledger["items"] if item.get("role") == "analysis"] + additions
    holdout_items = [item for item in ledger["items"] if item.get("role") == "holdout"]
    ledger["items"] = analysis_items + holdout_items
    ledger["analysis_scene_group_count"] = len({item["scene_group_id"] for item in analysis_items})
    ledger["analysis_coverage"] = coverage_summary(analysis_items)
    ledger["budget_overshoot_chunks"] = max(0, len(analysis_items) - ledger["budget_effective"])
    ledger.setdefault("updates", []).append({
        "sequence": len(ledger.get("updates", [])) + 1,
        "action": "extend",
        "requested_chunk_ids": sorted(requested),
        "added_chunk_ids": sorted(item["chunk_id"] for item in additions),
        "added_sample_ids": sorted({
            sample_id
            for item in additions
            for sample_id in item.get("sample_ids", [])
            if isinstance(sample_id, str)
        }),
        "note": note,
    })
    return ledger


def confirm_scene_granularity(ledger: dict, scene_group_ids: Sequence[str], note: str) -> dict:
    """Confirm that heuristic coarse groups are genuine reviewed scenes."""
    if not note.strip():
        raise ValueError("确认过大场景组时必须提供复核说明")
    requested = set(scene_group_ids)
    if not requested:
        raise ValueError("至少提供一个 scene_group_id")
    groups = {
        group.get("scene_group_id"): group
        for group in ledger.get("coarse_scene_groups", [])
        if isinstance(group, dict) and isinstance(group.get("scene_group_id"), str)
    }
    missing = sorted(requested - set(groups))
    if missing:
        raise ValueError(f"coarse_scene_groups 中不存在场景组：{', '.join(missing)}")
    for group_id in requested:
        groups[group_id]["review_status"] = "confirmed"
        groups[group_id]["review_note"] = note
    ledger["scene_granularity_status"] = (
        "acceptable"
        if all(group.get("review_status") == "confirmed" for group in groups.values())
        else "coarse"
    )
    ledger.setdefault("updates", []).append({
        "sequence": len(ledger.get("updates", [])) + 1,
        "action": "confirm_scene_granularity",
        "scene_group_ids": sorted(requested),
        "note": note,
    })
    return ledger


def verify_ledger_index(ledger: dict, index_path: Path) -> None:
    """Reject resume updates when the ledger no longer matches the exact index."""
    read_jsonl(index_path)
    if file_sha256(index_path) != ledger.get("index_sha256"):
        raise ValueError("索引内容已变化，不能继续更新旧取样账本；请重新生成账本")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="索引、标注、检索并分层取样中文小说语料")
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest = subparsers.add_parser("manifest", help="生成可编辑的作品与场景元数据清单")
    manifest.add_argument("paths", nargs="+", help=".txt/.md 文件、目录或通配符")
    manifest.add_argument("--output", type=Path, required=True)

    build = subparsers.add_parser("build", help="建立 JSONL 语料索引")
    build.add_argument("paths", nargs="+", help=".txt/.md 文件、目录或通配符")
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--manifest", type=Path)
    build.add_argument("--chunk-chars", type=int, default=1800)
    build.add_argument("--reflow-hard-wrap", action="store_true")
    build.add_argument("--strip-annotations", action="store_true")

    prepare = subparsers.add_parser("prepare", help="分离建立分析索引、留出索引和无正文承诺")
    prepare.add_argument("paths", nargs="+")
    prepare.add_argument("--manifest", type=Path, required=True)
    prepare.add_argument("--analysis-index", type=Path, required=True)
    prepare.add_argument("--holdout-index", type=Path, required=True)
    prepare.add_argument("--commitment", type=Path, required=True)
    prepare.add_argument("--ledger", type=Path, required=True)
    prepare.add_argument("--chunk-chars", type=int, default=1800)
    prepare.add_argument("--reflow-hard-wrap", action="store_true")
    prepare.add_argument("--strip-annotations", action="store_true")
    prepare.add_argument("--budget", type=int)
    prepare.add_argument("--holdout-ratio", type=float, default=0.2)
    prepare.add_argument("--seed", type=int, default=20260831)

    reveal = subparsers.add_parser("reveal-holdout", help="记录初稿哈希后解封留出验证")
    reveal.add_argument("--holdout-index", type=Path, required=True)
    reveal.add_argument("--commitment", type=Path, required=True)
    reveal.add_argument("--provisional-profile", type=Path, required=True)
    reveal.add_argument("--output", type=Path, required=True)

    search = subparsers.add_parser("search", help="按文本、作品和语义元数据检索文本块")
    search.add_argument("index", type=Path)
    search.add_argument("--query-file", type=Path)
    search.add_argument("--contains", action="append", default=[])
    search.add_argument("--source")
    search.add_argument("--work-id")
    search.add_argument("--sample-id")
    search.add_argument("--chapter-id")
    search.add_argument("--scene-type")
    search.add_argument("--viewpoint")
    search.add_argument("--character")
    search.add_argument("--relationship-state")
    search.add_argument("--emotion")
    search.add_argument("--chapter-position")
    search.add_argument("--exclude-holdout", action="store_true")
    search.add_argument("--top", type=int, default=5)
    search.add_argument("--include-text", action="store_true")
    search.add_argument("--output", type=Path)

    sample = subparsers.add_parser("sample", help="建立可复现的精读与留出取样账本")
    sample.add_argument("index", type=Path)
    sample.add_argument("--output", type=Path, required=True)
    sample.add_argument("--budget", type=int, help="精读文本块目标数；省略时按语料覆盖自动计算")
    sample.add_argument("--holdout-ratio", type=float, default=0.2)
    sample.add_argument("--seed", type=int, default=20260831)

    mark = subparsers.add_parser("mark", help="更新取样账本中的分析进度")
    mark.add_argument("ledger", type=Path)
    mark.add_argument("--index", type=Path, required=True, help="核对账本绑定的原始索引")
    mark.add_argument("--chunk-id", action="append", required=True)
    mark.add_argument("--status", choices=sorted(LEDGER_STATUSES - {"holdout"}), required=True)
    mark.add_argument("--note", default="")
    mark.add_argument("--output", type=Path)

    extend = subparsers.add_parser("extend", help="把补读文本块及其完整场景组加入取样账本")
    extend.add_argument("ledger", type=Path)
    extend.add_argument("--index", type=Path, required=True, help="核对账本绑定并读取原始索引")
    extend.add_argument("--chunk-id", action="append", required=True)
    extend.add_argument("--note", default="")
    extend.add_argument("--output", type=Path)

    confirm_scene = subparsers.add_parser("confirm-scene", help="确认启发式判定为过大的真实场景组")
    confirm_scene.add_argument("ledger", type=Path)
    confirm_scene.add_argument("--index", type=Path, required=True, help="核对账本绑定的原始索引")
    confirm_scene.add_argument("--scene-group-id", action="append", required=True)
    confirm_scene.add_argument("--note", required=True)
    confirm_scene.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "prepare":
            paths = resolve_inputs(args.paths)
            if not paths:
                raise ValueError("未找到可读取的 .txt 或 .md 文件")
            outputs = [args.analysis_index, args.holdout_index, args.commitment, args.ledger]
            resolved = [path.resolve() for path in outputs]
            if len(set(resolved)) != len(resolved) or set(resolved) & {path.resolve() for path in paths + [args.manifest]}:
                raise ValueError("输出路径必须互不相同且不能覆盖输入语料或清单")
            ledger, commitment = prepare_separated_corpus(
                paths, args.manifest, *outputs, args.chunk_chars,
                args.reflow_hard_wrap, args.strip_annotations,
                args.budget, args.holdout_ratio, args.seed,
            )
            print(f"已分离索引；计划精读 {ledger['analysis_coverage']['chunk_count']} 块，留出 {len(commitment['chunk_ids'])} 块。")
            return 0

        if args.command == "reveal-holdout":
            if args.output.resolve() in {path.resolve() for path in (args.holdout_index, args.commitment, args.provisional_profile)}:
                raise ValueError("解封记录不能覆盖输入文件")
            write_json(create_holdout_reveal(args.holdout_index, args.commitment, args.provisional_profile), args.output)
            print(f"已记录初稿哈希并允许留出验证：{args.output}")
            return 0

        if args.command == "manifest":
            paths = resolve_inputs(args.paths)
            if not paths:
                raise ValueError("未找到可读取的 .txt 或 .md 文件")
            write_json(build_manifest(paths), args.output)
            print(f"已写入 {len(paths)} 个来源的语料清单：{args.output}")
            return 0

        if args.command == "build":
            paths = resolve_inputs(args.paths)
            if not paths:
                raise ValueError("未找到可读取的 .txt 或 .md 文件")
            records = build_index(
                paths,
                chunk_chars=args.chunk_chars,
                reflow_hard_wrap=args.reflow_hard_wrap,
                strip_annotations=args.strip_annotations,
                manifest=args.manifest,
            )
            write_jsonl(records, args.output)
            print(f"已写入 {len(records)} 个文本块：{args.output}")
            return 0

        if args.command == "search":
            records = read_jsonl(args.index)
            query_text = None
            if args.query_file:
                query_text, _ = read_text(args.query_file)
                query_text = prepare_text(query_text)
            filters = {
                "sample_ids": args.sample_id,
                "chapter_ids": args.chapter_id,
                "scene_types": args.scene_type,
                "viewpoints": args.viewpoint,
                "characters": args.character,
                "relationship_states": args.relationship_state,
                "emotions": args.emotion,
                "chapter_positions": args.chapter_position,
            }
            matches = search_records(
                records,
                query_text,
                args.contains,
                args.source,
                args.top,
                args.work_id,
                filters,
                args.exclude_holdout,
            )
            rendered = render_matches(matches, args.include_text)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8")
            else:
                print(rendered, end="")
            return 0

        if args.command == "sample":
            records = read_jsonl(args.index)
            ledger = build_sampling_ledger(
                records,
                file_sha256(args.index),
                args.budget,
                args.holdout_ratio,
                args.seed,
            )
            write_json(ledger, args.output)
            analysis_count = sum(item["role"] == "analysis" for item in ledger["items"])
            holdout_count = sum(item["role"] == "holdout" for item in ledger["items"])
            print(
                f"已选择精读 {analysis_count} 块/{ledger['analysis_scene_group_count']} 个场景组、"
                f"留出 {holdout_count} 块/{ledger['holdout_scene_group_count']} 个场景组：{args.output}"
            )
            return 0

        ledger = read_ledger(args.ledger)
        verify_ledger_index(ledger, args.index)
        if args.command == "extend":
            before = len(ledger["items"])
            updated = extend_ledger(ledger, read_jsonl(args.index), args.chunk_id, args.note)
            changed = len(updated["items"]) - before
            unit = "个文本块"
        elif args.command == "confirm-scene":
            updated = confirm_scene_granularity(ledger, args.scene_group_id, args.note)
            changed = len(args.scene_group_id)
            unit = "个场景组"
        else:
            updated = mark_ledger(ledger, args.chunk_id, args.status, args.note)
            changed = len(args.chunk_id)
            unit = "个文本块"
        output = args.output or args.ledger
        write_json(updated, output)
        print(f"已更新 {changed} {unit}：{output}")
        return 0
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
