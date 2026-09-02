from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import compare_style  # noqa: E402
import corpus_index  # noqa: E402


class CliWorkflowTests(unittest.TestCase):
    def test_manifest_index_sample_resume_search_and_contrast(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "target"
            control = root / "control"
            target.mkdir()
            control.mkdir()
            target_source = target / "chapter-01.txt"
            control_source = control / "control.txt"
            target_source.write_text(("他却没有回答。\n\n门慢慢关了。\n\n" * 80), encoding="utf-8")
            control_source.write_text(("“为什么？”她问！\n\n“我偏要去！”\n\n" * 80), encoding="utf-8")

            work = root / "work"
            target_manifest = work / "target-manifest.json"
            control_manifest = work / "control-manifest.json"
            index_path = work / "corpus-index.jsonl"
            ledger_path = work / "sampling-ledger.json"
            matches_path = work / "matches.md"
            contrast_path = work / "contrast.md"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(corpus_index.main(["manifest", str(target), "--output", str(target_manifest)]), 0)
                self.assertEqual(corpus_index.main(["manifest", str(control), "--output", str(control_manifest)]), 0)

            manifest_data = json.loads(target_manifest.read_text(encoding="utf-8"))
            manifest_data["sources"][0]["work_id"] = "W01"
            manifest_data["sources"][0]["segments"] = [{
                "paragraph_start": 1,
                "paragraph_end": 160,
                "sample_id": "S01",
                "chapter_id": "C01",
                "scene_id": "SC01",
                "scene_type": "confrontation",
                "emotion": "tension",
                "characters": ["甲", "乙"],
            }]
            target_manifest.write_text(json.dumps(manifest_data, ensure_ascii=False), encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                self.assertEqual(corpus_index.main([
                    "build", str(target), "--manifest", str(target_manifest),
                    "--output", str(index_path), "--chunk-chars", "300",
                ]), 0)
                self.assertEqual(corpus_index.main([
                    "sample", str(index_path), "--output", str(ledger_path),
                    "--holdout-ratio", "0", "--seed", "11",
                ]), 0)

            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            chunk_id = next(item["chunk_id"] for item in ledger["items"] if item["role"] == "analysis")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(corpus_index.main([
                    "mark", str(ledger_path), "--index", str(index_path),
                    "--chunk-id", chunk_id, "--status", "analyzed", "--note", "完成精读",
                ]), 0)
                self.assertEqual(corpus_index.main([
                    "search", str(index_path), "--scene-type", "confrontation",
                    "--emotion", "tension", "--exclude-holdout", "--output", str(matches_path),
                ]), 0)
                self.assertEqual(compare_style.main([
                    "contrast", "--target", str(target), "--control", str(control),
                    "--target-manifest", str(target_manifest), "--control-manifest", str(control_manifest),
                    "--chunk-chars", "300", "--output", str(contrast_path),
                ]), 0)

            updated = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["budget_mode"], "auto")
            marked = next(item for item in updated["items"] if item["chunk_id"] == chunk_id)
            self.assertEqual(marked["status"], "analyzed")
            self.assertIn("场景：confrontation", matches_path.read_text(encoding="utf-8"))
            contrast_text = contrast_path.read_text(encoding="utf-8")
            self.assertIn("目标作者与对照语料差异", contrast_text)
            self.assertIn("目标作者作品：1", contrast_text)


if __name__ == "__main__":
    unittest.main()
