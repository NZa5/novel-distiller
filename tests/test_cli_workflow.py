from __future__ import annotations

import json
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import blind_style_test  # noqa: E402
import compare_style  # noqa: E402
import corpus_index  # noqa: E402


class CliWorkflowTests(unittest.TestCase):
    def test_index_compare_and_blind_test_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "target"
            control = root / "control"
            generated = root / "generated"
            for directory in (target, control, generated):
                directory.mkdir()
            (target / "target.txt").write_text(("他却没有回答。\n\n门慢慢关了。\n\n" * 80), encoding="utf-8")
            (control / "control.txt").write_text(("“为什么？”她问！\n\n“我偏要去！”\n\n" * 80), encoding="utf-8")
            (generated / "draft.txt").write_text(("他没有回答。\n\n门关了。\n\n" * 80), encoding="utf-8")

            index_path = root / "work" / "corpus.jsonl"
            matches_path = root / "work" / "matches.md"
            contrast_path = root / "work" / "contrast.md"
            draft_path = root / "work" / "draft.md"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(corpus_index.main(["build", str(target), "--output", str(index_path), "--chunk-chars", "300"]), 0)
                self.assertEqual(corpus_index.main(["search", str(index_path), "--query-file", str(generated / "draft.txt"), "--output", str(matches_path)]), 0)
                self.assertEqual(compare_style.main(["contrast", "--target", str(target), "--control", str(control), "--chunk-chars", "300", "--output", str(contrast_path)]), 0)
                self.assertEqual(compare_style.main(["draft", "--reference", str(target), "--draft", str(generated), "--chunk-chars", "300", "--output", str(draft_path)]), 0)

            blind_dir = root / "blind"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(blind_style_test.main(["prepare", "--original", str(target), "--generated", str(generated), "--output-dir", str(blind_dir), "--snippet-chars", "300", "--per-group", "1", "--seed", "11"]), 0)
            key = json.loads((blind_dir / "blind-key.json").read_text(encoding="utf-8"))
            response_lines = ["item_id,rater_id,label,confidence,notes"]
            for item in key["items"]:
                response_lines.append(f"{item['item_id']},reader,{item['label']},4,可说明的文本特征")
            (blind_dir / "blind-responses.csv").write_text("\n".join(response_lines) + "\n", encoding="utf-8")
            score_path = blind_dir / "score.md"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(blind_style_test.main(["score", "--key", str(blind_dir / "blind-key.json"), "--responses", str(blind_dir / "blind-responses.csv"), "--output", str(score_path)]), 0)

            self.assertTrue(index_path.is_file())
            self.assertIn("语料证据检索", matches_path.read_text(encoding="utf-8"))
            self.assertIn("目标作者与对照语料差异", contrast_path.read_text(encoding="utf-8"))
            self.assertIn("草稿与匹配原文对照", draft_path.read_text(encoding="utf-8"))
            self.assertIn("文风盲测结果", score_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
