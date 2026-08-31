from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("corpus_index", SCRIPTS / "corpus_index.py")
assert SPEC and SPEC.loader
INDEX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEX)


class CorpusIndexTests(unittest.TestCase):
    def test_split_chunks_keeps_all_content_and_locators(self) -> None:
        text = "\n\n".join(("甲" * 120 + "。", "乙" * 130 + "。", "丙" * 110 + "。"))
        chunks = INDEX.split_chunks(text, target_chars=200)

        self.assertEqual("".join(chunk["text"].replace("\n", "") for chunk in chunks), text.replace("\n", ""))
        self.assertEqual(chunks[0]["paragraph_start"], 1)
        self.assertEqual(chunks[-1]["paragraph_end"], 3)
        self.assertEqual(chunks[-1]["content_char_end"], 360)

    def test_build_roundtrip_and_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "novel.txt"
            source.write_text("第一段。\n\n第二段。", encoding="utf-8")
            records = INDEX.build_index([source], chunk_chars=200)
            output = root / "index.jsonl"
            INDEX.write_jsonl(records, output)
            loaded = INDEX.read_jsonl(output)

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["text"], "第一段。\n\n第二段。")
        self.assertEqual(len(loaded[0]["source_sha256"]), 64)
        self.assertEqual(loaded[0]["schema_version"], 3)
        self.assertIn("preprocessing_fingerprint", loaded[0])
        self.assertIn("metrics", loaded[0])

    def test_chunk_id_changes_when_preprocessing_contract_changes(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "novel.txt"
            source.write_text(
                "\n\n".join(("甲" * 120 + "。", "乙" * 120 + "。", "丙" * 120 + "。")),
                encoding="utf-8",
            )
            small = INDEX.build_index([source], chunk_chars=200)
            large = INDEX.build_index([source], chunk_chars=400)

        self.assertNotEqual(small[0]["chunk_id"], large[0]["chunk_id"])
        self.assertNotEqual(small[0]["preprocessing_fingerprint"], large[0]["preprocessing_fingerprint"])

    def test_search_by_keyword_and_style(self) -> None:
        quiet = INDEX.analyze_text("天黑了。\n\n门关了。")
        dialogue = INDEX.analyze_text("“你来？”\n\n“我不来！”\n\n“为什么？”")
        records = [
            {"chunk_id": "quiet-1", "source": "quiet.txt", "chunk_number": 1, "text": "天黑了。门关了。", "metrics": quiet},
            {"chunk_id": "talk-1", "source": "talk.txt", "chunk_number": 1, "text": "“你来？”“我不来！”“为什么？”", "metrics": dialogue},
        ]

        matches = INDEX.search_records(records, query_text="“去吗？”“不去！”", top=1)
        keyword = INDEX.search_records(records, contains=["门关"], top=2)

        self.assertEqual(matches[0]["source"], "talk.txt")
        self.assertEqual(keyword[0]["source"], "quiet.txt")

    def test_manifest_adds_work_and_scene_metadata_for_search(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "chapter-01.txt"
            source.write_text("他推门进去。\n\n她没有回头。", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "1.0",
                "sources": [{
                    "path": "chapter-01.txt",
                    "work_id": "W01",
                    "period": "early",
                    "metadata": {"viewpoint": "limited-third"},
                    "segments": [{
                        "paragraph_start": 1,
                        "paragraph_end": 2,
                        "scene_id": "SC01",
                        "scene_type": "confrontation",
                        "characters": ["甲", "乙"],
                        "relationship_state": "estranged",
                        "emotion": "tension",
                        "chapter_position": "opening",
                    }],
                }],
            }, ensure_ascii=False), encoding="utf-8")
            records = INDEX.build_index([source], chunk_chars=200, manifest=manifest)

        self.assertEqual(records[0]["work_id"], "W01")
        self.assertEqual(records[0]["scene_types"], ["confrontation"])
        matches = INDEX.search_records(
            records,
            top=5,
            semantic_filters={"relationship_states": "estranged", "emotions": "tension"},
        )
        self.assertEqual([record["chunk_id"] for record in matches], [records[0]["chunk_id"]])

    def test_sampling_ledger_is_balanced_reproducible_and_resumable(self) -> None:
        records = []
        strata = {
            1: ("close-third", "甲", "allied", "calm", "opening"),
            2: ("first-person", "乙", "strained", "anger", "middle"),
            3: ("distant-third", "丙", "broken", "grief", "ending"),
        }
        for work in ("W01", "W02"):
            for number, scene in enumerate(("action", "dialogue", "reflection"), 1):
                viewpoint, character, relationship, emotion, chapter_position = strata[number]
                records.append({
                    "chunk_id": f"{work}-{number}",
                    "source": f"{work}.txt",
                    "work_id": work,
                    "scene_ids": [f"S-{work}-{number}"],
                    "scene_types": [scene],
                    "viewpoints": [viewpoint],
                    "characters": [character],
                    "relationship_states": [relationship],
                    "emotions": [emotion],
                    "chapter_positions": [chapter_position],
                    "paragraph_start": number,
                    "paragraph_end": number,
                })

        first = INDEX.build_sampling_ledger(records, "a" * 64, budget=4, holdout_ratio=0, seed=7)
        second = INDEX.build_sampling_ledger(records, "a" * 64, budget=4, holdout_ratio=0, seed=7)
        self.assertEqual(first, second)
        self.assertEqual(first["analysis_coverage"]["work_ids"], ["W01", "W02"])
        self.assertEqual(len(first["analysis_coverage"]["scene_types"]), 3)
        self.assertEqual(len(first["analysis_coverage"]["viewpoints"]), 3)
        self.assertEqual(len(first["analysis_coverage"]["characters"]), 3)
        self.assertEqual(len(first["analysis_coverage"]["relationship_states"]), 3)
        self.assertEqual(len(first["analysis_coverage"]["emotions"]), 3)
        self.assertEqual(len(first["analysis_coverage"]["chapter_positions"]), 3)

        chosen = first["items"][0]["chunk_id"]
        updated = INDEX.mark_ledger(first, [chosen], "analyzed", "完成精读")
        marked = next(item for item in updated["items"] if item["chunk_id"] == chosen)
        self.assertEqual(marked["status"], "analyzed")
        self.assertEqual(marked["notes"], ["完成精读"])

    def test_resume_rejects_changed_index(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            index_path = root / "index.jsonl"
            index_path.write_text('{"schema_version":3}\n', encoding="utf-8")
            ledger = {"index_sha256": INDEX.file_sha256(index_path)}
            INDEX.verify_ledger_index(ledger, index_path)
            index_path.write_text('{"schema_version":3,"changed":true}\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "索引内容已变化"):
                INDEX.verify_ledger_index(ledger, index_path)


if __name__ == "__main__":
    unittest.main()
