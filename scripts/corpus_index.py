#!/usr/bin/env python3
"""Build, enrich, search, sample, and resume Chinese-fiction corpus indexes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
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


SCHEMA_VERSION = 3
MANIFEST_SCHEMA_VERSION = "1.0"
LEDGER_SCHEMA_VERSION = "1.0"
SEMANTIC_FIELDS = {
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


def split_chunks(text: str, target_chars: int = 1800) -> list[dict]:
    """Group prepared paragraphs into stable chunks near the requested size."""
    if target_chars < 200:
        raise ValueError("chunk_chars 必须至少为 200")
    units = paragraph_units(text, target_chars)
    chunks: list[dict] = []
    current: list[tuple[int, str]] = []
    current_size = 0
    content_offset = 0

    def flush() -> None:
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
        })
        content_offset += size
        current = []
        current_size = 0

    for paragraph_number, unit in units:
        unit_size = content_length(unit)
        if current and current_size + unit_size > target_chars and current_size >= target_chars * 0.55:
            flush()
        current.append((paragraph_number, unit))
        current_size += unit_size
        if current_size >= target_chars * 1.25:
            flush()
    flush()

    if len(chunks) > 1 and content_length(chunks[-1]["text"]) < target_chars * 0.25:
        tail = chunks.pop()
        previous = chunks[-1]
        previous["text"] += "\n\n" + tail["text"]
        previous["paragraph_end"] = tail["paragraph_end"]
        previous["content_char_end"] = tail["content_char_end"]
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
        for number, chunk in enumerate(split_chunks(prepared, chunk_chars), 1):
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
    budget: int,
    holdout_ratio: float = 0.2,
    seed: int = 20260831,
) -> dict:
    if budget < 1:
        raise ValueError("budget 必须至少为 1")
    if not 0 <= holdout_ratio < 1:
        raise ValueError("holdout_ratio 必须在 0（含）到 1（不含）之间")
    if not records:
        raise ValueError("索引中没有文本块")

    manual_holdout = [record for record in records if record.get("holdout") is True]
    if manual_holdout:
        holdout = sorted(manual_holdout, key=lambda record: stable_record_key(record, seed))
    elif len(records) >= 10 and holdout_ratio > 0:
        holdout_count = min(len(records) - 1, max(2, round(len(records) * holdout_ratio)))
        holdout = balanced_select(records, holdout_count, seed + 1)
    else:
        holdout = []
    holdout_ids = {record["chunk_id"] for record in holdout}
    candidates = [record for record in records if record["chunk_id"] not in holdout_ids]
    analysis = balanced_select(candidates, min(budget, len(candidates)), seed)

    def item(record: dict, role: str) -> dict:
        return {
            "chunk_id": record["chunk_id"],
            "source": record["source"],
            "work_id": record.get("work_id", record["source"]),
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
        "seed": seed,
        "budget_requested": budget,
        "holdout_ratio": holdout_ratio,
        "selection_method": "work_round_robin_then_semantic_novelty_then_stable_hash",
        "analysis_coverage": coverage_summary(analysis),
        "holdout_coverage": coverage_summary(holdout),
        "items": [item(record, "analysis") for record in analysis] + [item(record, "holdout") for record in holdout],
        "updates": [],
    }


def read_ledger(path: Path) -> dict:
    ledger = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(ledger, dict) or ledger.get("schema_version") != LEDGER_SCHEMA_VERSION:
        raise ValueError(f"取样账本 schema_version 必须是 {LEDGER_SCHEMA_VERSION}")
    items = ledger.get("items")
    if not isinstance(items, list):
        raise ValueError("取样账本 items 必须是数组")
    ids = []
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"取样账本 items[{index}] 必须是对象")
        chunk_id = item.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            raise ValueError(f"取样账本 items[{index}].chunk_id 必须是非空字符串")
        if not isinstance(item.get("role"), str) or item.get("role") not in {"analysis", "holdout"}:
            raise ValueError(f"取样账本 items[{index}].role 不受支持")
        if not isinstance(item.get("status"), str) or item.get("status") not in LEDGER_STATUSES:
            raise ValueError(f"取样账本 items[{index}].status 不受支持")
        if item.get("role") == "holdout" and item.get("status") != "holdout":
            raise ValueError(f"取样账本 items[{index}] 的留出状态不能被修改")
        ids.append(chunk_id)
    if len(ids) != len(set(ids)):
        raise ValueError("取样账本包含重复 chunk_id")
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
        "chunk_ids": sorted(requested),
        "status": status,
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

    search = subparsers.add_parser("search", help="按文本、作品和语义元数据检索文本块")
    search.add_argument("index", type=Path)
    search.add_argument("--query-file", type=Path)
    search.add_argument("--contains", action="append", default=[])
    search.add_argument("--source")
    search.add_argument("--work-id")
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
    sample.add_argument("--budget", type=int, required=True)
    sample.add_argument("--holdout-ratio", type=float, default=0.2)
    sample.add_argument("--seed", type=int, default=20260831)

    mark = subparsers.add_parser("mark", help="更新取样账本中的分析进度")
    mark.add_argument("ledger", type=Path)
    mark.add_argument("--index", type=Path, required=True, help="核对账本绑定的原始索引")
    mark.add_argument("--chunk-id", action="append", required=True)
    mark.add_argument("--status", choices=sorted(LEDGER_STATUSES - {"holdout"}), required=True)
    mark.add_argument("--note", default="")
    mark.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
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
            print(f"已选择精读 {analysis_count} 块、留出 {holdout_count} 块：{args.output}")
            return 0

        ledger = read_ledger(args.ledger)
        verify_ledger_index(ledger, args.index)
        updated = mark_ledger(ledger, args.chunk_id, args.status, args.note)
        output = args.output or args.ledger
        write_json(updated, output)
        print(f"已更新 {len(args.chunk_id)} 个文本块：{output}")
        return 0
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
