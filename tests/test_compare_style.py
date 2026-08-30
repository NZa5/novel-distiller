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
    return {"source": "sample", "chunk": 1, "content_chars": len(text), "values": COMPARE.flatten_metrics(text)}


class CompareStyleTests(unittest.TestCase):
    def test_contrast_ranks_obvious_dialogue_difference(self) -> None:
        target = [sample("“去吗？”“不去！”“为什么？”" * 15), sample("“来。”“不来。”" * 20)]
        control = [sample("天渐渐黑了。门外没有人。" * 20), sample("雨停了。路上很静。" * 20)]
        report = COMPARE.contrast_report(target, control, top=10)

        top_metrics = {item["key"] for item in report["differences"][:5]}
        self.assertTrue({"dialogue_ratio", "punct_quote"} & top_metrics)
        self.assertIn("目标作者与对照语料差异", COMPARE.render_markdown(report))

    def test_draft_report_marks_large_drift(self) -> None:
        reference = [sample("他走了。天黑了。门也关了。" * 20), sample("雨停了。人散了。" * 20)]
        draft = [sample("“你为什么还不回来？”她大声问道！" * 30)]
        report = COMPARE.draft_report(reference, draft, top=20)

        statuses = {item["key"]: item["status"] for item in report["deviations"]}
        self.assertEqual(statuses["dialogue_ratio"], "drift")
        self.assertEqual(statuses["punct_exclamation"], "drift")
        self.assertIn("偏差不是相似度", COMPARE.render_markdown(report))

    def test_function_word_frequency_is_reported(self) -> None:
        values = COMPARE.flatten_metrics("他却没有走，却只是看着门。")
        self.assertGreater(values["word_却"], 0)
        self.assertIn("word_只是", values)


if __name__ == "__main__":
    unittest.main()
