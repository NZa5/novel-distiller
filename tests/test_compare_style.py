from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("compare_style", SCRIPTS / "compare_style.py")
assert SPEC and SPEC.loader
COMPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPARE)


def sample(text: str) -> dict:
    return {"source": "sample", "work_id": "sample-work", "chunk": 1, "content_chars": len(text), "values": COMPARE.flatten_metrics(text)}


def metric_sample(source: str, work_id: str, value: float) -> dict:
    values = {key: value for key, _, _ in COMPARE.METRICS}
    return {"source": source, "work_id": work_id, "chunk": 1, "content_chars": 100, "values": values}


class CompareStyleTests(unittest.TestCase):
    def test_contrast_ranks_obvious_dialogue_difference(self) -> None:
        target = [sample("“去吗？”“不去！”“为什么？”" * 15), sample("“来。”“不来。”" * 20)]
        control = [sample("天渐渐黑了。门外没有人。" * 20), sample("雨停了。路上很静。" * 20)]
        report = COMPARE.contrast_report(target, control, top=10)

        top_metrics = {item["key"] for item in report["differences"][:5]}
        self.assertTrue({"dialogue_ratio", "punct_quote"} & top_metrics)
        self.assertIn("目标作者与对照语料差异", COMPARE.render_markdown(report))

    def test_function_word_frequency_is_reported(self) -> None:
        values = COMPARE.flatten_metrics("他却没有走，却只是看着门。")
        self.assertGreater(values["word_却"], 0)
        self.assertIn("word_只是", values)

    def test_longer_function_word_does_not_double_count(self) -> None:
        counts = COMPARE.count_function_words("然而他走了，而她留下。")

        self.assertEqual(counts["然而"], 1)
        self.assertEqual(counts["而"], 1)

    def test_ascii_and_curly_quotes_produce_the_same_dialogue_metrics(self) -> None:
        ascii_values = COMPARE.flatten_metrics('他说："去吗？"她说："不去！"')
        curly_values = COMPARE.flatten_metrics("他说：“去吗？”她说：“不去！”")

        self.assertEqual(ascii_values["dialogue_ratio"], curly_values["dialogue_ratio"])
        self.assertEqual(ascii_values["punct_quote"], curly_values["punct_quote"])

    def test_each_work_has_equal_weight_even_when_split_across_files(self) -> None:
        samples = [
            metric_sample("chapter-1.txt", "long-work", 0.0),
            metric_sample("chapter-2.txt", "long-work", 0.0),
            metric_sample("chapter-3.txt", "long-work", 0.0),
            metric_sample("short-work.txt", "short-work", 10.0),
        ]

        summary = COMPARE.summarize(samples)

        self.assertEqual(summary["sentence_mean"]["median"], 5.0)

    def test_equal_contrast_is_not_reported_as_lower(self) -> None:
        report = COMPARE.contrast_report([sample("雨停了。")], [sample("雨停了。")], top=50)

        self.assertTrue(all(item["direction"] == "中位数相同" for item in report["differences"]))


if __name__ == "__main__":
    unittest.main()
