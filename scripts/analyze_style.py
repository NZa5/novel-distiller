#!/usr/bin/env python3
"""Measure reliable surface features of Chinese fiction without dependencies."""

from __future__ import annotations

import argparse
import codecs
import glob
import hashlib
import json
import math
import re
import statistics
import sys
from pathlib import Path
from typing import Iterable, Sequence


VALID_SUFFIXES = {".txt", ".md"}
REPORT_SCHEMA_VERSION = "1.1"
SENTENCE_SPLIT_RE = re.compile(r'(?:[。！？!?]+|…{2,})(?:[”’」』】》）"])?')
QUOTE_PAIR_SPECS = (
    ("中文弯双引号", "“", "”", re.compile(r"“([^”\r\n]*)”")),
    ("中文弯单引号", "‘", "’", re.compile(r"‘([^’\r\n]*)’")),
    ("中文直角引号", "「", "」", re.compile(r"「([^」\r\n]*)」")),
    ("中文双直角引号", "『", "』", re.compile(r"『([^』\r\n]*)』")),
    ("ASCII 直双引号", '"', '"', re.compile(r'"([^"\r\n]*)"')),
)
DIALOGUE_RE = re.compile("|".join(pattern.pattern for _, _, _, pattern in QUOTE_PAIR_SPECS))
ASCII_DIALOGUE_RE = QUOTE_PAIR_SPECS[-1][3]
MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
ANNOTATION_HEADING_RE = re.compile(r"^\s*(?:□\s*)?注[釋释]\s*$")
PUNCTUATION_PATTERNS = {
    "逗号，": re.compile("，"),
    "句号。": re.compile("。"),
    "问号？": re.compile(r"[？?]"),
    "叹号！": re.compile(r"[！!]"),
    "分号；": re.compile(r"[；;]"),
    "冒号：": re.compile(r"[：:︰]"),
    "顿号、": re.compile("、"),
    "破折号": re.compile(r"—{2,}|-{2,}"),
    "省略号": re.compile(r"…{2,}|\.{3,}"),
    "引号组": re.compile(r"[“‘「『]"),
}


def read_text(path: Path) -> tuple[str, str]:
    """Read common Chinese encodings and return text plus the chosen encoding."""
    raw = path.read_bytes()
    if raw.startswith(codecs.BOM_UTF8):
        return raw.decode("utf-8-sig"), "utf-8-sig"
    if raw.startswith(codecs.BOM_UTF16_LE):
        return raw.decode("utf-16"), "utf-16-le"
    if raw.startswith(codecs.BOM_UTF16_BE):
        return raw.decode("utf-16"), "utf-16-be"
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass

    candidates: list[tuple[int, str, str]] = []
    for encoding in ("gb18030", "big5"):
        try:
            decoded = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        candidates.append((decode_penalty(decoded), encoding, decoded))
    if candidates:
        _, encoding, decoded = min(candidates, key=lambda item: (item[0], item[1] != "gb18030"))
        return decoded, encoding
    raise UnicodeError("无法用 UTF-8、GB18030 或 Big5 解码")


def decode_penalty(text: str) -> int:
    """Penalize strong mojibake signals when legacy encodings both decode."""
    penalty = 0
    for char in text:
        codepoint = ord(char)
        if char == "\ufffd":
            penalty += 100
        elif 0xE000 <= codepoint <= 0xF8FF:
            penalty += 20
        elif codepoint < 32 and char not in "\n\r\t":
            penalty += 20
        elif 0x3040 <= codepoint <= 0x30FF:
            penalty += 2
    for marker in ("锟斤拷", "烫烫烫", "鈥", "銆", "螟", "�"):
        penalty += text.count(marker) * 10
    return penalty


def detect_hard_wrap(text: str) -> tuple[bool, int]:
    """Detect fixed-width eBook lines from a strong repeated line-length signature."""
    raw_lines = [line for line in text.split("\n") if line.strip()]
    lines = [line.strip() for line in raw_lines]
    if len(lines) < 8:
        return False, 0

    lengths = [content_length(line) for line in lines if content_length(line)]
    if not lengths:
        return False, 0
    frequencies: dict[int, int] = {}
    for length in lengths:
        frequencies[length] = frequencies.get(length, 0) + 1
    wrap_width = max(frequencies, key=lambda length: (frequencies[length], length))
    modal_count = frequencies[wrap_width]
    near_width_count = sum(abs(length - wrap_width) <= 2 for length in lengths)
    concentrated_width = (
        wrap_width >= 20
        and modal_count >= max(3, math.ceil(len(lengths) * 0.15))
        and near_width_count / len(lengths) >= 0.52
    )
    ordered = sorted(lengths)
    p90 = ordered[min(len(ordered) - 1, math.ceil(len(ordered) * 0.90) - 1)]
    indented_lines = sum((len(line) - len(line.lstrip(" "))) >= 4 for line in raw_lines)
    indented_fixed_width = (
        len(lengths) >= 20
        and indented_lines / len(raw_lines) >= 0.80
        and max(lengths) <= 50
        and p90 >= 20
        and max(lengths) - p90 <= 8
    )
    detected = concentrated_width or indented_fixed_width
    return detected, wrap_width


def reflow_hard_wrapped_text(text: str) -> str:
    """Approximately restore paragraphs only when fixed-width wrapping is detected."""
    detected, wrap_width = detect_hard_wrap(text)
    if not detected:
        return text

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    break_below = max(10, wrap_width * 0.92)

    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        current.append(line)
        if content_length(line) < break_below:
            paragraphs.append("".join(current))
            current = []
    if current:
        paragraphs.append("".join(current))
    return "\n\n".join(paragraphs)


def prepare_text(
    text: str,
    reflow_hard_wrap: bool = False,
    strip_annotations: bool = False,
) -> str:
    """Normalize line endings and remove Markdown-only headings/frontmatter."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    if lines and lines[0].strip() == "---":
        for index in range(1, min(len(lines), 100)):
            if lines[index].strip() == "---":
                lines = lines[index + 1 :]
                break

    if strip_annotations:
        for index, line in enumerate(lines):
            if ANNOTATION_HEADING_RE.match(line):
                lines = lines[:index]
                break

    kept: list[str] = []
    for line in lines:
        if MARKDOWN_HEADING_RE.match(line):
            continue
        kept.append(line.rstrip())
    prepared = "\n".join(kept).strip()
    return reflow_hard_wrapped_text(prepared) if reflow_hard_wrap else prepared


def content_length(text: str) -> int:
    return sum(1 for char in text if char.isalnum())


def non_whitespace_length(text: str) -> int:
    return sum(1 for char in text if not char.isspace())


def split_paragraphs(text: str) -> list[str]:
    """Treat each non-empty prepared line as a Chinese-fiction paragraph."""
    blocks = re.split(r"\n+", text)
    return [re.sub(r"\s+", "", block) for block in blocks if block.strip()]


def split_sentences(text: str) -> list[str]:
    sentences = [part.strip() for part in SENTENCE_SPLIT_RE.split(text)]
    return [part for part in sentences if content_length(part)]


def percentile(values: Sequence[int | float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def describe(values: Sequence[int]) -> dict[str, float | int]:
    if not values:
        return {
            "count": 0,
            "min": 0,
            "q1": 0.0,
            "median": 0.0,
            "mean": 0.0,
            "q3": 0.0,
            "p90": 0.0,
            "max": 0,
        }
    return {
        "count": len(values),
        "min": min(values),
        "q1": round(percentile(values, 0.25), 2),
        "median": round(float(statistics.median(values)), 2),
        "mean": round(float(statistics.fmean(values)), 2),
        "q3": round(percentile(values, 0.75), 2),
        "p90": round(percentile(values, 0.90), 2),
        "max": max(values),
    }


def analyze_text(
    text: str,
    label: str = "sample",
    reflow_hard_wrap: bool = False,
    strip_annotations: bool = False,
) -> dict:
    normalized_for_detection = text.replace("\r\n", "\n").replace("\r", "\n")
    hard_wrap_detected, _ = detect_hard_wrap(normalized_for_detection)
    annotation_heading_found = any(
        ANNOTATION_HEADING_RE.match(line)
        for line in normalized_for_detection.split("\n")
    )
    prepared = prepare_text(
        text,
        reflow_hard_wrap=reflow_hard_wrap,
        strip_annotations=strip_annotations,
    )
    paragraphs = split_paragraphs(prepared)
    sentences = split_sentences(prepared)
    sentence_lengths = [content_length(sentence) for sentence in sentences]
    paragraph_lengths = [content_length(paragraph) for paragraph in paragraphs]
    content_chars = content_length(prepared)
    non_whitespace_chars = non_whitespace_length(prepared)

    dialogue_chars = 0
    dialogue_spans = 0
    for match in DIALOGUE_RE.finditer(prepared):
        dialogue_spans += 1
        dialogue_chars += content_length(next(group for group in match.groups() if group is not None))
    quote_pair_warnings = []
    for quote_label, opening, closing, pattern in QUOTE_PAIR_SPECS:
        matched_spans = len(pattern.findall(prepared))
        if opening == closing:
            anomalous = prepared.count(opening) != matched_spans * 2
        else:
            anomalous = prepared.count(opening) != matched_spans or prepared.count(closing) != matched_spans
        if anomalous:
            quote_pair_warnings.append(quote_label)
    ascii_quote_chars = prepared.count('"')
    ascii_dialogue_spans = len(ASCII_DIALOGUE_RE.findall(prepared))
    ascii_quote_warning = "ASCII 直双引号" in quote_pair_warnings

    punctuation = {}
    for name, pattern in PUNCTUATION_PATTERNS.items():
        count = dialogue_spans if name == "引号组" else len(pattern.findall(prepared))
        per_thousand = (count * 1000 / non_whitespace_chars) if non_whitespace_chars else 0.0
        punctuation[name] = {"count": count, "per_1000": round(per_thousand, 2)}

    sentence_count = len(sentence_lengths)
    short_count = sum(length <= 15 for length in sentence_lengths)
    long_count = sum(length >= 40 for length in sentence_lengths)
    medium_count = max(sentence_count - short_count - long_count, 0)

    def ratio(count: int, total: int) -> float:
        return round(count / total, 4) if total else 0.0

    return {
        "label": label,
        "preprocessing": {
            "hard_wrap_detected": hard_wrap_detected,
            "hard_wrap_reflow_requested": reflow_hard_wrap,
            "hard_wrap_reflow_applied": bool(reflow_hard_wrap and hard_wrap_detected),
            "annotations_stripped": bool(strip_annotations and annotation_heading_found),
            "ascii_quote_chars": ascii_quote_chars,
            "ascii_dialogue_spans": ascii_dialogue_spans,
            "ascii_quote_warning": ascii_quote_warning,
            "quote_pair_warnings": quote_pair_warnings,
        },
        "non_whitespace_chars": non_whitespace_chars,
        "content_chars": content_chars,
        "paragraphs": len(paragraphs),
        "sentences": sentence_count,
        "sentence_length": describe(sentence_lengths),
        "paragraph_length": describe(paragraph_lengths),
        "sentence_bands": {
            "short_le_15": {"count": short_count, "ratio": ratio(short_count, sentence_count)},
            "medium_16_39": {"count": medium_count, "ratio": ratio(medium_count, sentence_count)},
            "long_ge_40": {"count": long_count, "ratio": ratio(long_count, sentence_count)},
        },
        "dialogue": {
            "spans": dialogue_spans,
            "content_chars": dialogue_chars,
            "content_ratio": ratio(dialogue_chars, content_chars),
        },
        "punctuation": punctuation,
    }


def resolve_inputs(inputs: Iterable[str]) -> list[Path]:
    found: list[Path] = []
    for value in inputs:
        candidates: list[Path]
        if any(char in value for char in "*?["):
            candidates = [Path(item) for item in glob.glob(value, recursive=True)]
        else:
            candidates = [Path(value)]

        for candidate in candidates:
            if candidate.is_file() and candidate.suffix.lower() in VALID_SUFFIXES:
                found.append(candidate.resolve())
            elif candidate.is_dir():
                for path in candidate.rglob("*"):
                    relative_parts = path.relative_to(candidate).parts
                    if any(part.startswith(".") for part in relative_parts):
                        continue
                    if path.is_file() and path.suffix.lower() in VALID_SUFFIXES:
                        found.append(path.resolve())

    return sorted(dict.fromkeys(found), key=lambda path: str(path).casefold())


def unique_labels(paths: Sequence[Path]) -> list[str]:
    counts: dict[str, int] = {}
    for path in paths:
        counts[path.name.casefold()] = counts.get(path.name.casefold(), 0) + 1
    labels = []
    for path in paths:
        labels.append(path.name if counts[path.name.casefold()] == 1 else f"{path.parent.name}/{path.name}")
    return labels


def source_ranges(sources: Sequence[dict]) -> dict:
    fields = {
        "sentence_mean": [item["sentence_length"]["mean"] for item in sources],
        "sentence_median": [item["sentence_length"]["median"] for item in sources],
        "paragraph_mean": [item["paragraph_length"]["mean"] for item in sources],
        "dialogue_ratio": [item["dialogue"]["content_ratio"] for item in sources],
    }
    result = {
        name: {"min": round(min(values), 4), "max": round(max(values), 4)}
        for name, values in fields.items()
        if values
    }
    result["punctuation_per_1000"] = {
        name: {
            "min": min(item["punctuation"][name]["per_1000"] for item in sources),
            "max": max(item["punctuation"][name]["per_1000"] for item in sources),
        }
        for name in PUNCTUATION_PATTERNS
    }
    return result


def report_sha256(report: dict) -> str:
    payload = {key: value for key, value in report.items() if key != "report_sha256"}
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_report(
    paths: Sequence[Path],
    reflow_hard_wrap: bool = False,
    strip_annotations: bool = False,
) -> dict:
    texts: list[str] = []
    sources: list[dict] = []
    errors: list[dict[str, str]] = []

    for path, label in zip(paths, unique_labels(paths)):
        try:
            text, encoding = read_text(path)
            prepared = prepare_text(
                text,
                reflow_hard_wrap=reflow_hard_wrap,
                strip_annotations=strip_annotations,
            )
            metrics = analyze_text(
                text,
                label,
                reflow_hard_wrap=reflow_hard_wrap,
                strip_annotations=strip_annotations,
            )
            metrics["encoding"] = encoding
            metrics["source_path"] = str(path.resolve())
            metrics["source_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            sources.append(metrics)
            texts.append(prepared)
        except (OSError, UnicodeError) as exc:
            errors.append({"label": label, "error": str(exc)})

    if not sources:
        raise ValueError("没有可分析的文本")

    return assemble_report(texts, sources, errors, reflow_hard_wrap, strip_annotations)


def assemble_report(texts: list[str], sources: list[dict], errors: list[dict],
                    reflow_hard_wrap: bool = False, strip_annotations: bool = False) -> dict:
    aggregate = analyze_text("\n\n".join(texts), "全部分析语料")
    warnings = []
    for source in sources:
        preprocessing = source["preprocessing"]
        if preprocessing["hard_wrap_detected"] and not preprocessing["hard_wrap_reflow_applied"]:
            warnings.append(
                f"{source['label']}：检测到疑似固定宽度硬换行；请检查原文，并在确认后使用 --reflow-hard-wrap 重新统计。"
            )
        if preprocessing["quote_pair_warnings"]:
            warnings.append(
                f"{source['label']}：检测到未成对、顺序异常或跨行的引号（{'、'.join(preprocessing['quote_pair_warnings'])}）；"
                "部分对白可能无法可靠识别，请核对引号配对和换行。"
            )
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "input_mode": "source_files",
        "measurement": {
            "character_unit": "非空白字符；句长和段长只计算字母、数字与汉字",
            "paragraph": "预处理后的每个非空行视为一个段落；固定行宽电子书应先启用硬换行重排",
            "sentence_bands": "短句 <= 15；中句 16-39；长句 >= 40 个内容字符",
            "dialogue": "统计成对的中文弯引号、直角引号以及同一行内成对的 ASCII 直双引号中的内容字符",
            "punctuation": "每千非空白字符出现次数；连续破折号或省略号按一组计算",
            "hard_wrap_reflow": "已请求；只对检测到固定行宽特征的文件近似恢复段落" if reflow_hard_wrap else "未启用电子书硬换行重排",
            "annotations": "已在篇末注释标题处停止统计" if strip_annotations else "保留原文件全部内容",
        },
        "aggregate": aggregate,
        "source_ranges": source_ranges(sources),
        "sources": sources,
        "warnings": warnings,
        "errors": errors,
    }
    report["report_sha256"] = report_sha256(report)
    return report


def build_report_from_index(index_path: Path) -> dict:
    """Measure only analysis-index text; do not reopen full source documents."""
    groups: dict[tuple[str, str], list[dict]] = {}
    seen: set[str] = set()
    for number, line in enumerate(index_path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict) or not isinstance(record.get("text"), str):
            raise ValueError(f"索引第 {number} 行缺少正文")
        if record.get("holdout") is True:
            raise ValueError("统计输入不能包含留出正文")
        chunk_id = record.get("chunk_id")
        if not isinstance(chunk_id, str) or chunk_id in seen:
            raise ValueError("索引 chunk_id 缺失或重复")
        seen.add(chunk_id)
        source_path, source_hash = record.get("source_path"), record.get("source_sha256")
        if not isinstance(source_path, str) or not isinstance(source_hash, str):
            raise ValueError("索引缺少来源路径或哈希")
        groups.setdefault((source_path, source_hash), []).append(record)
    if not groups:
        raise ValueError("没有可分析的索引文本")
    texts, sources = [], []
    for (source_path, source_hash), records in sorted(groups.items()):
        records.sort(key=lambda record: record.get("content_char_start", 0))
        text = "\n\n".join(record["text"] for record in records)
        metrics = analyze_text(text, Path(source_path).name)
        metrics.update(encoding="indexed-utf-8", source_path=source_path, source_sha256=source_hash)
        sources.append(metrics)
        texts.append(text)
    report = assemble_report(texts, sources, [])
    report["input_mode"] = "analysis_index"
    report["index_sha256"] = hashlib.sha256(index_path.read_bytes()).hexdigest()
    report["measurement"]["input"] = "仅统计分析索引中的预处理正文；排除留出场景；不跨块推断连续叙事"
    report["report_sha256"] = report_sha256(report)
    return report


def render_markdown(report: dict) -> str:
    aggregate = report["aggregate"]
    lines = [
        f"<!-- novel-distiller-metrics {json.dumps({'schema_version': report.get('schema_version'), 'report_sha256': report.get('report_sha256')}, ensure_ascii=False, sort_keys=True)} -->",
        "# 文风表层统计",
        "",
        "## 统计口径",
        "",
        *[f"- {value}" for value in report["measurement"].values()],
        "",
        "## 当前统计语料",
        "",
        "| 非空白字符 | 段落 | 句子 | 平均句长 | 中位句长 | 句长四分位 | 平均段长 | 对白内容占比 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
        (
            f"| {aggregate['non_whitespace_chars']} | {aggregate['paragraphs']} | {aggregate['sentences']} | "
            f"{aggregate['sentence_length']['mean']:.2f} | {aggregate['sentence_length']['median']:.2f} | "
            f"{aggregate['sentence_length']['q1']:.2f}–{aggregate['sentence_length']['q3']:.2f} | "
            f"{aggregate['paragraph_length']['mean']:.2f} | {aggregate['dialogue']['content_ratio']:.1%} |"
        ),
        "",
        "## 分文件",
        "",
        "| 样本 | 预处理 | 字符 | 段落 | 句子 | 平均句长 | 中位句长 | 平均段长 | 短/中/长句 | 对白占比 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for source in report["sources"]:
        bands = source["sentence_bands"]
        preprocessing = []
        if source["preprocessing"]["hard_wrap_reflow_applied"]:
            preprocessing.append("硬换行重排")
        elif source["preprocessing"]["hard_wrap_detected"]:
            preprocessing.append("疑似硬换行未重排")
        if source["preprocessing"]["quote_pair_warnings"]:
            preprocessing.append("引号待核对")
        if source["preprocessing"]["annotations_stripped"]:
            preprocessing.append("去篇末注释")
        preprocessing_text = "、".join(preprocessing) if preprocessing else "—"
        lines.append(
            f"| {source['label']} | {preprocessing_text} | {source['non_whitespace_chars']} | {source['paragraphs']} | "
            f"{source['sentences']} | {source['sentence_length']['mean']:.2f} | "
            f"{source['sentence_length']['median']:.2f} | {source['paragraph_length']['mean']:.2f} | "
            f"{bands['short_le_15']['ratio']:.0%}/{bands['medium_16_39']['ratio']:.0%}/"
            f"{bands['long_ge_40']['ratio']:.0%} | {source['dialogue']['content_ratio']:.1%} |"
        )

    lines.extend([
        "",
        "## 标点频率",
        "",
        "| 标点 | 全部语料（每千字符） | 分文件范围 |",
        "|---|---:|---:|",
    ])
    punctuation_ranges = report["source_ranges"]["punctuation_per_1000"]
    for name in PUNCTUATION_PATTERNS:
        value = aggregate["punctuation"][name]["per_1000"]
        range_value = punctuation_ranges[name]
        lines.append(f"| {name} | {value:.2f} | {range_value['min']:.2f}–{range_value['max']:.2f} |")

    if report["warnings"]:
        lines.extend(["", "## 警告", ""])
        lines.extend(f"- {warning}" for warning in report["warnings"])

    if report["errors"]:
        lines.extend(["", "## 未读取文件", ""])
        lines.extend(f"- {item['label']}：{item['error']}" for item in report["errors"])

    lines.extend([
        "",
        "> 这些数值用于定位值得回看原文的差异；作者画像还需要结合场景条件和文本机制判断。",
        "",
    ])
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="统计中文小说的句段、对白和标点表层特征")
    parser.add_argument("paths", nargs="*", help=".txt/.md 文件、目录或通配符")
    parser.add_argument("--index", type=Path, help="仅统计分析索引，禁止混入留出正文")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="写入结果文件；省略时输出到终端")
    parser.add_argument(
        "--reflow-hard-wrap",
        action="store_true",
        help="合并电子书中由固定行宽造成的空行，并近似恢复真实段落",
    )
    parser.add_argument(
        "--strip-annotations",
        action="store_true",
        help="遇到独立的‘注释/注釋’标题后停止统计",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.index:
            if args.paths or args.reflow_hard_wrap or args.strip_annotations:
                raise ValueError("--index 不能与来源路径或二次预处理选项同时使用")
            report = build_report_from_index(args.index)
        else:
            paths = resolve_inputs(args.paths)
            if not paths:
                raise ValueError("未找到可读取的 .txt 或 .md 文件。")
            report = build_report(paths, args.reflow_hard_wrap, args.strip_annotations)
    except (OSError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    output = render_markdown(report) if args.format == "markdown" else json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        try:
            print(output, end="")
        except UnicodeEncodeError:
            sys.stdout.buffer.write(output.encode("utf-8"))
    return 0


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
