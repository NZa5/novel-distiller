from __future__ import annotations

import codecs
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "analyze_style.py"
SPEC = importlib.util.spec_from_file_location("analyze_style", SCRIPT)
assert SPEC and SPEC.loader
STYLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STYLE)


class AnalyzeStyleTests(unittest.TestCase):
    def test_basic_chinese_metrics(self) -> None:
        text = "雨停了。\n\n他说：“别去！”她没有回答。"
        result = STYLE.analyze_text(text)

        self.assertEqual(result["paragraphs"], 2)
        self.assertEqual(result["sentences"], 3)
        self.assertEqual(result["dialogue"]["spans"], 1)
        self.assertEqual(result["dialogue"]["content_chars"], 2)
        self.assertGreater(result["dialogue"]["content_ratio"], 0)

    def test_markdown_metadata_is_not_counted(self) -> None:
        text = "---\ntitle: 示例\n---\n# 第一章\n\n正文在这里。"
        prepared = STYLE.prepare_text(text)

        self.assertNotIn("title", prepared)
        self.assertNotIn("第一章", prepared)
        self.assertIn("正文在这里", prepared)

    def test_dash_and_ellipsis_groups_are_not_double_counted(self) -> None:
        result = STYLE.analyze_text("他停住——没有回头……然后走了。")

        self.assertEqual(result["punctuation"]["破折号"]["count"], 1)
        self.assertEqual(result["punctuation"]["省略号"]["count"], 1)

    def test_directory_resolution_and_gb18030(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "b.md").write_text("# 标题\n\n乙。", encoding="utf-8")
            (root / "a.txt").write_bytes("甲。".encode("gb18030"))
            (root / "skip.json").write_text("{}", encoding="utf-8")

            paths = STYLE.resolve_inputs([str(root)])
            report = STYLE.build_report(paths)

        self.assertEqual([path.name for path in paths], ["a.txt", "b.md"])
        self.assertEqual(len(report["sources"]), 2)
        self.assertIn("gb18030", {source["encoding"] for source in report["sources"]})

    def test_big5_is_not_misread_as_gb18030(self) -> None:
        text = "繁體中文小說測試：他說：「風來了。」"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "traditional.txt"
            path.write_bytes(text.encode("big5"))
            decoded, encoding = STYLE.read_text(path)

        self.assertEqual(decoded, text)
        self.assertEqual(encoding, "big5")

    def test_utf16_bom_variants(self) -> None:
        text = "窗外下着雨。他没有回头。"
        for encoding, expected in (("utf-16-le", "utf-16-le"), ("utf-16-be", "utf-16-be")):
            with self.subTest(encoding=encoding), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "sample.txt"
                bom = codecs.BOM_UTF16_LE if encoding.endswith("le") else codecs.BOM_UTF16_BE
                path.write_bytes(bom + text.encode(encoding))
                decoded, detected = STYLE.read_text(path)

                self.assertEqual(decoded, text)
                self.assertEqual(detected, expected)

    def test_json_report_is_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.txt"
            path.write_text("风来。风停。", encoding="utf-8")
            report = STYLE.build_report([path])

        rendered = json.dumps(report, ensure_ascii=False)
        self.assertIn("全部语料", rendered)
        self.assertEqual(report["aggregate"]["sentences"], 2)

    def test_sentence_bands_and_markdown_report(self) -> None:
        text = "短句。" + "中" * 20 + "。" + "长" * 40 + "。"
        metrics = STYLE.analyze_text(text)

        self.assertEqual(metrics["sentence_bands"]["short_le_15"]["count"], 1)
        self.assertEqual(metrics["sentence_bands"]["medium_16_39"]["count"], 1)
        self.assertEqual(metrics["sentence_bands"]["long_ge_40"]["count"], 1)

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.txt"
            path.write_text(text, encoding="utf-8")
            report = STYLE.build_report([path])
        markdown = STYLE.render_markdown(report)
        self.assertIn("## 标点频率", markdown)
        self.assertIn("sample.txt", markdown)

    def test_hard_wrapped_ebook_reflow(self) -> None:
        text = (
            "甲" * 36 + "\n\n" + "乙" * 36 + "\n\n" + "丙" * 36 + "\n\n" + "丁" * 12 + "。\n\n"
            + "戊" * 36 + "\n\n" + "己" * 36 + "\n\n" + "庚" * 36 + "\n\n" + "辛" * 8 + "。"
        )

        plain = STYLE.analyze_text(text)
        reflowed = STYLE.analyze_text(text, reflow_hard_wrap=True)

        self.assertEqual(plain["paragraphs"], 8)
        self.assertEqual(reflowed["paragraphs"], 2)
        self.assertEqual(plain["content_chars"], reflowed["content_chars"])
        self.assertTrue(reflowed["preprocessing"]["hard_wrap_reflow_applied"])

    def test_normal_paragraphs_are_not_reflowed(self) -> None:
        paragraphs = ["段" * length + "。" for length in (9, 14, 21, 29, 38, 12, 25, 33)]
        text = "\n\n".join(paragraphs)

        plain = STYLE.analyze_text(text)
        requested = STYLE.analyze_text(text, reflow_hard_wrap=True)

        self.assertEqual(plain["paragraphs"], requested["paragraphs"])
        self.assertFalse(requested["preprocessing"]["hard_wrap_reflow_applied"])

    def test_indented_fixed_width_ebook_is_detected(self) -> None:
        lengths = [24, 27, 30, 33, 28, 31, 25, 34, 29, 32] * 2
        text = "\n\n".join("    " + "文" * length for length in lengths)

        result = STYLE.analyze_text(text, reflow_hard_wrap=True)

        self.assertTrue(result["preprocessing"]["hard_wrap_reflow_applied"])
        self.assertLess(result["paragraphs"], len(lengths))

    def test_batch_report_preserves_preprocessing_detection(self) -> None:
        text = (
            "甲" * 36 + "\n\n" + "乙" * 36 + "\n\n" + "丙" * 36 + "\n\n" + "丁" * 12 + "。\n\n"
            + "戊" * 36 + "\n\n" + "己" * 36 + "\n\n" + "庚" * 36 + "\n\n" + "辛" * 8 + "。"
            + "\n\n□注釋\n\n編者說明。"
        )
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "wrapped.txt"
            path.write_text(text, encoding="utf-8")
            report = STYLE.build_report(
                [path],
                reflow_hard_wrap=True,
                strip_annotations=True,
            )

        source = report["sources"][0]
        self.assertTrue(source["preprocessing"]["hard_wrap_reflow_applied"])
        self.assertTrue(source["preprocessing"]["annotations_stripped"])
        self.assertEqual(source["paragraphs"], 2)
        markdown = STYLE.render_markdown(report)
        self.assertIn("硬换行重排、去篇末注释", markdown)

    def test_old_style_colon_and_single_quotes(self) -> None:
        result = STYLE.analyze_text("他說︰‘去罷。’")

        self.assertEqual(result["punctuation"]["冒号："]["count"], 1)
        self.assertEqual(result["dialogue"]["spans"], 1)

    def test_editorial_annotations_can_be_excluded(self) -> None:
        text = "正文。\n\n□注釋\n\n這是編者說明，不是小說。"

        plain = STYLE.analyze_text(text)
        cleaned = STYLE.analyze_text(text, strip_annotations=True)

        self.assertGreater(plain["content_chars"], cleaned["content_chars"])
        self.assertEqual(cleaned["content_chars"], 2)
        self.assertEqual(cleaned["sentences"], 1)


if __name__ == "__main__":
    unittest.main()
