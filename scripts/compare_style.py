#!/usr/bin/env python3
"""Contrast author corpora and compare drafts with matched source passages."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Sequence

from analyze_style import analyze_text, content_length, prepare_text, read_text, resolve_inputs
from corpus_index import split_chunks


FUNCTION_WORDS = (
    "的", "了", "着", "过", "地", "得", "而", "却", "但", "于是", "然而", "只是",
    "便", "就", "又", "仍", "已经", "也", "都", "还", "才", "竟", "仿佛", "似乎",
)

METRICS = [
    ("sentence_mean", "平均句长", 2.0),
    ("sentence_median", "中位句长", 2.0),
    ("paragraph_mean", "平均段长", 6.0),
    ("short_ratio", "短句比例", 0.04),
    ("long_ratio", "长句比例", 0.03),
    ("dialogue_ratio", "对白内容占比", 0.04),
    ("punct_comma", "逗号/千字符", 3.0),
    ("punct_period", "句号/千字符", 2.0),
    ("punct_question", "问号/千字符", 1.0),
    ("punct_exclamation", "叹号/千字符", 1.0),
    ("punct_semicolon", "分号/千字符", 1.0),
    ("punct_colon", "冒号/千字符", 1.0),
    ("punct_dash", "破折号/千字符", 0.6),
    ("punct_ellipsis", "省略号/千字符", 0.6),
    ("punct_quote", "引号组/千字符", 1.5),
]
METRICS.extend((f"word_{word}", f"功能词‘{word}’/千字", 0.8) for word in FUNCTION_WORDS)
METRIC_LABELS = {key: label for key, label, _ in METRICS}
METRIC_FLOORS = {key: floor for key, _, floor in METRICS}


def flatten_metrics(text: str) -> dict[str, float]:
    metrics = analyze_text(text)
    punctuation = metrics["punctuation"]
    size = max(content_length(text), 1)
    result = {
        "sentence_mean": metrics["sentence_length"]["mean"],
        "sentence_median": metrics["sentence_length"]["median"],
        "paragraph_mean": metrics["paragraph_length"]["mean"],
        "short_ratio": metrics["sentence_bands"]["short_le_15"]["ratio"],
        "long_ratio": metrics["sentence_bands"]["long_ge_40"]["ratio"],
        "dialogue_ratio": metrics["dialogue"]["content_ratio"],
        "punct_comma": punctuation["逗号，"]["per_1000"],
        "punct_period": punctuation["句号。"]["per_1000"],
        "punct_question": punctuation["问号？"]["per_1000"],
        "punct_exclamation": punctuation["叹号！"]["per_1000"],
        "punct_semicolon": punctuation["分号；"]["per_1000"],
        "punct_colon": punctuation["冒号："]["per_1000"],
        "punct_dash": punctuation["破折号"]["per_1000"],
        "punct_ellipsis": punctuation["省略号"]["per_1000"],
        "punct_quote": punctuation["引号组"]["per_1000"],
    }
    for word in FUNCTION_WORDS:
        result[f"word_{word}"] = round(text.count(word) * 1000 / size, 3)
    return result


def collect_chunks(
    paths: Sequence[Path],
    chunk_chars: int,
    reflow_hard_wrap: bool = False,
    strip_annotations: bool = False,
) -> list[dict]:
    samples: list[dict] = []
    for path in paths:
        text, _ = read_text(path)
        prepared = prepare_text(text, reflow_hard_wrap, strip_annotations)
        for number, chunk in enumerate(split_chunks(prepared, chunk_chars), 1):
            samples.append({
                "source": path.name,
                "chunk": number,
                "content_chars": content_length(chunk["text"]),
                "values": flatten_metrics(chunk["text"]),
            })
    return samples


def percentile(values: Sequence[float], fraction: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def summarize(samples: Sequence[dict]) -> dict[str, dict[str, float]]:
    if not samples:
        raise ValueError("没有可比较的文本块")
    result: dict[str, dict[str, float]] = {}
    for key, _, _ in METRICS:
        values = [sample["values"][key] for sample in samples]
        result[key] = {
            "min": min(values),
            "q1": percentile(values, 0.25),
            "median": float(statistics.median(values)),
            "q3": percentile(values, 0.75),
            "max": max(values),
        }
    return result


def robust_scale(key: str, summary: dict[str, float]) -> float:
    return max(summary["q3"] - summary["q1"], METRIC_FLOORS[key])


def contrast_report(target: Sequence[dict], control: Sequence[dict], top: int = 15) -> dict:
    target_summary = summarize(target)
    control_summary = summarize(control)
    differences = []
    for key, label, _ in METRICS:
        left = target_summary[key]
        right = control_summary[key]
        scale = max((robust_scale(key, left) + robust_scale(key, right)) / 2, METRIC_FLOORS[key])
        score = abs(left["median"] - right["median"]) / scale
        direction = "目标作者更高" if left["median"] > right["median"] else "目标作者更低"
        differences.append({
            "key": key,
            "metric": label,
            "target": left,
            "control": right,
            "direction": direction,
            "distinctiveness": round(score, 3),
        })
    differences.sort(key=lambda item: (-item["distinctiveness"], item["metric"]))
    return {
        "mode": "contrast",
        "target_chunks": len(target),
        "control_chunks": len(control),
        "differences": differences[: max(top, 0)],
    }


def draft_report(reference: Sequence[dict], drafts: Sequence[dict], top: int = 15) -> dict:
    reference_summary = summarize(reference)
    draft_summary = summarize(drafts)
    deviations = []
    for key, label, _ in METRICS:
        baseline = reference_summary[key]
        value = draft_summary[key]["median"]
        if baseline["q1"] <= value <= baseline["q3"]:
            score = 0.0
        else:
            edge = baseline["q1"] if value < baseline["q1"] else baseline["q3"]
            score = abs(value - edge) / robust_scale(key, baseline)
        status = "close" if score <= 0.5 else "partial" if score <= 1.5 else "drift"
        deviations.append({
            "key": key,
            "metric": label,
            "reference": baseline,
            "draft": draft_summary[key],
            "status": status,
            "deviation": round(score, 3),
        })
    deviations.sort(key=lambda item: (-item["deviation"], item["metric"]))
    return {
        "mode": "draft",
        "reference_chunks": len(reference),
        "draft_chunks": len(drafts),
        "deviations": deviations[: max(top, 0)],
    }


def format_value(key: str, value: float) -> str:
    if key.endswith("_ratio"):
        return f"{value:.1%}"
    return f"{value:.2f}"


def format_iqr(key: str, summary: dict[str, float]) -> str:
    return f"{format_value(key, summary['q1'])}–{format_value(key, summary['q3'])}"


def render_markdown(report: dict) -> str:
    if report["mode"] == "contrast":
        lines = [
            "# 目标作者与对照语料差异",
            "",
            f"目标作者文本块：{report['target_chunks']}；对照文本块：{report['control_chunks']}。",
            "",
            "| 区分度 | 指标 | 目标作者中位数（IQR） | 对照中位数（IQR） | 方向 |",
            "|---:|---|---:|---:|---|",
        ]
        for item in report["differences"]:
            key = item["key"]
            lines.append(
                f"| {item['distinctiveness']:.2f} | {item['metric']} | "
                f"{format_value(key, item['target']['median'])}（{format_iqr(key, item['target'])}） | "
                f"{format_value(key, item['control']['median'])}（{format_iqr(key, item['control'])}） | "
                f"{item['direction']} |"
            )
        lines.extend([
            "",
            "> 区分度用于排列回看顺序。只有能回到原文解释其场景条件和写作机制的差异，才能进入作者画像。",
            "",
        ])
        return "\n".join(lines)

    lines = [
        "# 草稿与匹配原文对照",
        "",
        f"匹配原文文本块：{report['reference_chunks']}；草稿文本块：{report['draft_chunks']}。",
        "",
        "| 状态 | 偏差 | 指标 | 草稿中位数 | 原文中位数（IQR） |",
        "|---|---:|---|---:|---:|",
    ]
    for item in report["deviations"]:
        key = item["key"]
        lines.append(
            f"| {item['status']} | {item['deviation']:.2f} | {item['metric']} | "
            f"{format_value(key, item['draft']['median'])} | "
            f"{format_value(key, item['reference']['median'])}（{format_iqr(key, item['reference'])}） |"
        )
    lines.extend([
        "",
        "> 偏差不是相似度。先检查场景条件，再把能对应到具体文本机制的 drift/partial 用于定向修订。",
        "",
    ])
    return "\n".join(lines)


def add_shared_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--chunk-chars", type=int, default=1800)
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reflow-hard-wrap", action="store_true")
    parser.add_argument("--strip-annotations", action="store_true")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="比较作者语料差异或检查草稿表层漂移")
    subparsers = parser.add_subparsers(dest="command", required=True)
    contrast = subparsers.add_parser("contrast", help="比较目标作者与对照作者")
    contrast.add_argument("--target", nargs="+", required=True)
    contrast.add_argument("--control", nargs="+", required=True)
    add_shared_options(contrast)
    draft = subparsers.add_parser("draft", help="比较草稿与匹配原文")
    draft.add_argument("--reference", nargs="+", required=True)
    draft.add_argument("--draft", nargs="+", required=True)
    add_shared_options(draft)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        left_values = args.target if args.command == "contrast" else args.reference
        right_values = args.control if args.command == "contrast" else args.draft
        left_paths = resolve_inputs(left_values)
        right_paths = resolve_inputs(right_values)
        if not left_paths or not right_paths:
            raise ValueError("两组都必须包含可读取的 .txt 或 .md 文件")
        options = (args.chunk_chars, args.reflow_hard_wrap, args.strip_annotations)
        left = collect_chunks(left_paths, *options)
        right = collect_chunks(right_paths, *options)
        report = contrast_report(left, right, args.top) if args.command == "contrast" else draft_report(left, right, args.top)
        rendered = render_markdown(report) if args.format == "markdown" else json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
