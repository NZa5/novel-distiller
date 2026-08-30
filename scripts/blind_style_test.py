#!/usr/bin/env python3
"""Prepare reproducible blind style tests and score reader responses."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

from analyze_style import content_length, prepare_text, read_text, resolve_inputs
from corpus_index import split_chunks


LABELS = {"original": "original", "generated": "generated", "原文": "original", "生成": "generated"}


def collect_candidates(paths: Sequence[Path], label: str, snippet_chars: int) -> list[dict]:
    candidates: list[dict] = []
    minimum = max(100, int(snippet_chars * 0.35))
    for path in paths:
        text, _ = read_text(path)
        prepared = prepare_text(text)
        for chunk_number, chunk in enumerate(split_chunks(prepared, snippet_chars), 1):
            if content_length(chunk["text"]) < minimum:
                continue
            candidates.append({
                "label": label,
                "source": path.name,
                "source_path": str(path.resolve()),
                "chunk_number": chunk_number,
                "paragraph_start": chunk["paragraph_start"],
                "paragraph_end": chunk["paragraph_end"],
                "text": chunk["text"],
            })
    return candidates


def prepare_test(
    originals: Sequence[Path],
    generated: Sequence[Path],
    snippet_chars: int = 600,
    per_group: int = 6,
    seed: int = 20260830,
) -> tuple[str, dict, str]:
    if per_group < 1:
        raise ValueError("per_group 必须至少为 1")
    original_candidates = collect_candidates(originals, "original", snippet_chars)
    generated_candidates = collect_candidates(generated, "generated", snippet_chars)
    count = min(per_group, len(original_candidates), len(generated_candidates))
    if count < 1:
        raise ValueError("原文和生成稿都至少需要一个达到最小长度的片段")

    rng = random.Random(seed)
    selected = rng.sample(original_candidates, count) + rng.sample(generated_candidates, count)
    rng.shuffle(selected)
    items = []
    pack_lines = [
        "# 文风盲测",
        "",
        "请只根据文字判断每个片段是原文还是生成稿，并在答题表中填写判断、信心和暴露身份的具体特征。",
        "",
    ]
    response_lines = ["item_id,rater_id,label,confidence,notes"]
    for number, candidate in enumerate(selected, 1):
        item_id = f"S{number:03d}"
        text_hash = hashlib.sha256(candidate["text"].encode("utf-8")).hexdigest()
        items.append({
            "item_id": item_id,
            "label": candidate["label"],
            "source": candidate["source"],
            "source_path": candidate["source_path"],
            "chunk_number": candidate["chunk_number"],
            "paragraph_start": candidate["paragraph_start"],
            "paragraph_end": candidate["paragraph_end"],
            "text_sha256": text_hash,
        })
        pack_lines.extend([f"## {item_id}", "", candidate["text"], ""])
        response_lines.append(f"{item_id},reader-1,,,")

    key = {
        "schema_version": 1,
        "seed": seed,
        "snippet_chars": snippet_chars,
        "per_group_requested": per_group,
        "per_group_used": count,
        "items": items,
    }
    return "\n".join(pack_lines).rstrip() + "\n", key, "\n".join(response_lines) + "\n"


def score_responses(key: dict, response_path: Path) -> dict:
    answers = {item["item_id"]: item["label"] for item in key["items"]}
    rows: list[dict] = []
    with response_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), 2):
            item_id = (row.get("item_id") or "").strip()
            raw_label = (row.get("label") or "").strip().casefold()
            if not item_id and not raw_label:
                continue
            if item_id not in answers:
                raise ValueError(f"答题表第 {row_number} 行包含未知 item_id：{item_id}")
            if raw_label not in LABELS:
                raise ValueError(f"答题表第 {row_number} 行的 label 必须是 original/generated 或 原文/生成")
            confidence_text = (row.get("confidence") or "").strip()
            confidence = int(confidence_text) if confidence_text else None
            if confidence is not None and not 1 <= confidence <= 5:
                raise ValueError(f"答题表第 {row_number} 行的 confidence 必须为 1–5")
            predicted = LABELS[raw_label]
            actual = answers[item_id]
            rows.append({
                "item_id": item_id,
                "rater_id": (row.get("rater_id") or "anonymous").strip() or "anonymous",
                "actual": actual,
                "predicted": predicted,
                "correct": actual == predicted,
                "confidence": confidence,
                "notes": (row.get("notes") or "").strip(),
            })
    if not rows:
        raise ValueError("答题表中没有有效答案")

    generated_rows = [row for row in rows if row["actual"] == "generated"]
    original_rows = [row for row in rows if row["actual"] == "original"]
    generated_pass = sum(row["predicted"] == "original" for row in generated_rows)
    original_recognition = sum(row["predicted"] == "original" for row in original_rows)
    correct = sum(row["correct"] for row in rows)
    confidence_values = [row["confidence"] for row in rows if row["confidence"] is not None]
    return {
        "responses": len(rows),
        "raters": sorted({row["rater_id"] for row in rows}),
        "generated_as_original": {
            "count": generated_pass,
            "total": len(generated_rows),
            "rate": generated_pass / len(generated_rows) if generated_rows else 0.0,
        },
        "original_as_original": {
            "count": original_recognition,
            "total": len(original_rows),
            "rate": original_recognition / len(original_rows) if original_rows else 0.0,
        },
        "distinguish_accuracy": {"count": correct, "total": len(rows), "rate": correct / len(rows)},
        "mean_confidence": sum(confidence_values) / len(confidence_values) if confidence_values else None,
        "notes": [row for row in rows if row["notes"]],
        "item_response_counts": dict(Counter(row["item_id"] for row in rows)),
    }


def render_score(report: dict) -> str:
    generated = report["generated_as_original"]
    original = report["original_as_original"]
    accuracy = report["distinguish_accuracy"]
    lines = [
        "# 文风盲测结果",
        "",
        f"- 有效回答：{report['responses']}；评审者：{len(report['raters'])}",
        f"- 生成稿被判断为原文：{generated['count']}/{generated['total']}（{generated['rate']:.1%}）",
        f"- 真正原文被判断为原文：{original['count']}/{original['total']}（{original['rate']:.1%}）",
        f"- 原文/生成稿辨识正确率：{accuracy['count']}/{accuracy['total']}（{accuracy['rate']:.1%}）",
    ]
    if report["mean_confidence"] is not None:
        lines.append(f"- 平均信心：{report['mean_confidence']:.2f}/5")
    if report["notes"]:
        lines.extend(["", "## 暴露身份的具体特征", ""])
        for row in report["notes"]:
            lines.append(f"- {row['item_id']} · {row['rater_id']}：{row['notes']}")
    lines.extend([
        "",
        "> 三项结果必须结合阅读：既看生成稿有多少被当成原文，也检查评审者是否能够正常识别真正原文。",
        "",
    ])
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成可复现的文风盲测并统计答题结果")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="生成盲测包、答案键和答题表")
    prepare.add_argument("--original", nargs="+", required=True)
    prepare.add_argument("--generated", nargs="+", required=True)
    prepare.add_argument("--output-dir", type=Path, required=True)
    prepare.add_argument("--snippet-chars", type=int, default=600)
    prepare.add_argument("--per-group", type=int, default=6)
    prepare.add_argument("--seed", type=int, default=20260830)

    score = subparsers.add_parser("score", help="根据答案键统计答题表")
    score.add_argument("--key", type=Path, required=True)
    score.add_argument("--responses", type=Path, required=True)
    score.add_argument("--output", type=Path)
    score.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "prepare":
            originals = resolve_inputs(args.original)
            generated = resolve_inputs(args.generated)
            if not originals or not generated:
                raise ValueError("原文和生成稿都必须包含可读取的 .txt 或 .md 文件")
            pack, key, responses = prepare_test(
                originals, generated, args.snippet_chars, args.per_group, args.seed
            )
            args.output_dir.mkdir(parents=True, exist_ok=True)
            (args.output_dir / "blind-pack.md").write_text(pack, encoding="utf-8")
            (args.output_dir / "blind-key.json").write_text(
                json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            (args.output_dir / "blind-responses.csv").write_text(responses, encoding="utf-8-sig")
            print(f"已生成 {len(key['items'])} 个盲测片段：{args.output_dir}")
            return 0

        key = json.loads(args.key.read_text(encoding="utf-8-sig"))
        report = score_responses(key, args.responses)
        rendered = render_score(report) if args.format == "markdown" else json.dumps(report, ensure_ascii=False, indent=2) + "\n"
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
