from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("blind_style_test", SCRIPTS / "blind_style_test.py")
assert SPEC and SPEC.loader
BLIND = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BLIND)


class BlindStyleTestTests(unittest.TestCase):
    def test_prepare_is_balanced_and_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original = root / "original.txt"
            generated = root / "generated.txt"
            original.write_text("原文段落。" * 100, encoding="utf-8")
            generated.write_text("生成段落。" * 100, encoding="utf-8")
            first = BLIND.prepare_test([original], [generated], snippet_chars=200, per_group=2, seed=7)
            second = BLIND.prepare_test([original], [generated], snippet_chars=200, per_group=2, seed=7)

        self.assertEqual(first, second)
        labels = [item["label"] for item in first[1]["items"]]
        self.assertEqual(labels.count("original"), 2)
        self.assertEqual(labels.count("generated"), 2)
        self.assertNotIn("original.txt", first[0])
        self.assertIn("item_id,rater_id,label", first[2])

    def test_score_reports_generated_pass_and_accuracy(self) -> None:
        key = {
            "items": [
                {"item_id": "S001", "label": "original"},
                {"item_id": "S002", "label": "generated"},
            ]
        }
        with tempfile.TemporaryDirectory() as folder:
            responses = Path(folder) / "responses.csv"
            responses.write_text(
                "item_id,rater_id,label,confidence,notes\n"
                "S001,A,original,4,像原文\n"
                "S002,A,original,3,没有看出\n",
                encoding="utf-8",
            )
            report = BLIND.score_responses(key, responses)

        self.assertEqual(report["generated_as_original"]["rate"], 1.0)
        self.assertEqual(report["original_as_original"]["rate"], 1.0)
        self.assertEqual(report["distinguish_accuracy"]["rate"], 0.5)
        self.assertIn("生成稿被判断为原文", BLIND.render_score(report))


if __name__ == "__main__":
    unittest.main()
