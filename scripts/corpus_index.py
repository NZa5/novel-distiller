#!/usr/bin/env python3
"""Build and search a reproducible chunk index for long Chinese fiction corpora."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
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


SCHEMA_VERSION = 1


def paragraph_units(text: str, target_chars: int) -> list[tuple[int, str]]:
    """Return paragraph-numbered units, splitting only exceptionally long blocks."""
    paragraphs = [block.strip() for block in re.split(r"\n\s*\n+", text) if block.strip()]
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


def build_index(
    paths: Sequence[Path],
    chunk_chars: int = 1800,
    reflow_hard_wrap: bool = False,
    strip_annotations: bool = False,
) -> list[dict]:
    records: list[dict] = []
    for path, label in zip(paths, unique_labels(paths)):
        text, encoding = read_text(path)
        prepared = prepare_text(text, reflow_hard_wrap, strip_annotations)
        source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        for number, chunk in enumerate(split_chunks(prepared, chunk_chars), 1):
            metrics = analyze_text(chunk["text"])
            records.append({
                "schema_version": SCHEMA_VERSION,
                "chunk_id": f"{source_hash[:12]}-{number:05d}",
                "source": label,
                "source_path": str(path.resolve()),
                "source_sha256": source_hash,
                "encoding": encoding,
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


def read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("schema_version") != SCHEMA_VERSION:
                raise ValueError(f"第 {line_number} 行的索引版本不受支持")
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


def search_records(
    records: Sequence[dict],
    query_text: str | None = None,
    contains: Sequence[str] = (),
    source: str | None = None,
    top: int = 5,
) -> list[dict]:
    query_metrics = analyze_text(query_text) if query_text else None
    terms = [term for term in contains if term]
    scored: list[tuple[float, int, dict]] = []
    for record in records:
        if source and source.casefold() not in record["source"].casefold():
            continue
        term_hits = sum(record["text"].count(term) for term in terms)
        if terms and term_hits == 0:
            continue
        distance = style_distance(query_metrics, record["metrics"]) if query_metrics else 0.0
        scored.append((distance, -term_hits, record))
    scored.sort(key=lambda item: (item[0], item[1], item[2]["source"], item[2]["chunk_number"]))
    return [record for _, _, record in scored[: max(top, 0)]]


def render_matches(records: Sequence[dict], include_text: bool = False) -> str:
    lines = ["# 语料证据检索", ""]
    for rank, record in enumerate(records, 1):
        locator = (
            f"段落 {record['paragraph_start']}–{record['paragraph_end']}，"
            f"内容字符 {record['content_char_start']}–{record['content_char_end']}"
        )
        lines.extend([
            f"## {rank}. {record['source']} · {record['chunk_id']}",
            "",
            f"- 定位：{locator}",
            f"- 来源 SHA-256：`{record['source_sha256']}`",
            "",
        ])
        text = record["text"] if include_text else record["text"][:240].replace("\n", " ")
        lines.extend([text, ""])
    if not records:
        lines.append("没有符合条件的文本块。")
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="切块、索引并检索长篇中文小说语料")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="建立 JSONL 语料索引")
    build.add_argument("paths", nargs="+", help=".txt/.md 文件、目录或通配符")
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--chunk-chars", type=int, default=1800)
    build.add_argument("--reflow-hard-wrap", action="store_true")
    build.add_argument("--strip-annotations", action="store_true")

    search = subparsers.add_parser("search", help="按草稿节奏或关键词检索文本块")
    search.add_argument("index", type=Path)
    search.add_argument("--query-file", type=Path)
    search.add_argument("--contains", action="append", default=[])
    search.add_argument("--source")
    search.add_argument("--top", type=int, default=5)
    search.add_argument("--include-text", action="store_true")
    search.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "build":
            paths = resolve_inputs(args.paths)
            if not paths:
                raise ValueError("未找到可读取的 .txt 或 .md 文件")
            records = build_index(
                paths,
                chunk_chars=args.chunk_chars,
                reflow_hard_wrap=args.reflow_hard_wrap,
                strip_annotations=args.strip_annotations,
            )
            write_jsonl(records, args.output)
            print(f"已写入 {len(records)} 个文本块：{args.output}")
            return 0

        records = read_jsonl(args.index)
        query_text = None
        if args.query_file:
            query_text, _ = read_text(args.query_file)
            query_text = prepare_text(query_text)
        matches = search_records(records, query_text, args.contains, args.source, args.top)
        rendered = render_matches(matches, args.include_text)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
