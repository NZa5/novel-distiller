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
        self.assertEqual(loaded[0]["schema_version"], 4)
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
                "schema_version": "2.0",
                "sources": [{
                    "path": "chapter-01.txt",
                    "work_id": "W01",
                    "period": "early",
                    "metadata": {"viewpoint": "limited-third"},
                    "segments": [{
                        "paragraph_start": 1,
                        "paragraph_end": 2,
                        "sample_id": "S01",
                        "chapter_id": "C01",
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
        self.assertEqual(records[0]["sample_ids"], ["S01"])
        self.assertEqual(records[0]["chapter_ids"], ["C01"])
        self.assertEqual(records[0]["scene_types"], ["confrontation"])
        matches = INDEX.search_records(
            records,
            top=5,
            semantic_filters={"relationship_states": "estranged", "emotions": "tension"},
        )
        self.assertEqual([record["chunk_id"] for record in matches], [records[0]["chunk_id"]])

    def test_manifest_segment_boundaries_prevent_cross_scene_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "novel.txt"
            source.write_text("甲" * 120 + "。\n\n" + "乙" * 120 + "。\n\n" + "丙" * 120 + "。", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "2.0",
                "sources": [{
                    "path": source.name,
                    "work_id": "W01",
                    "period": "",
                    "metadata": {},
                    "segments": [
                        {"paragraph_start": 1, "paragraph_end": 1, "sample_id": "S01", "chapter_id": "C01", "scene_id": "SC01"},
                        {"paragraph_start": 2, "paragraph_end": 3, "sample_id": "S02", "chapter_id": "C01", "scene_id": "SC02"},
                    ],
                }],
            }, ensure_ascii=False), encoding="utf-8")
            records = INDEX.build_index([source], chunk_chars=300, manifest=manifest)

        self.assertEqual(records[0]["paragraph_end"], 1)
        self.assertTrue(all(len(record["scene_ids"]) == 1 for record in records))
        self.assertEqual({value for record in records for value in record["sample_ids"]}, {"S01", "S02"})

    def test_coarse_scene_group_is_reported(self) -> None:
        records = [{
            "chunk_id": f"W01-{number:02d}",
            "source": "W01.txt",
            "work_id": "W01",
            "sample_ids": ["S01"],
            "chapter_ids": ["C01"],
            "scene_ids": ["SC01"],
            "scene_types": ["scene"],
            "viewpoints": [],
            "characters": [],
            "relationship_states": [],
            "emotions": [],
            "chapter_positions": [],
            "paragraph_start": number,
            "paragraph_end": number,
        } for number in range(1, 21)]

        ledger = INDEX.build_sampling_ledger(records, "a" * 64, budget=20, holdout_ratio=0)

        self.assertEqual(ledger["scene_granularity_status"], "coarse")
        self.assertEqual(ledger["coarse_scene_groups"][0]["chunk_count"], 20)
        group_id = ledger["coarse_scene_groups"][0]["scene_group_id"]
        confirmed = INDEX.confirm_scene_granularity(
            ledger,
            [group_id],
            "逐段复核后确认这是一个连续的长场景，没有时空、目标或视角切换。",
        )
        self.assertEqual(confirmed["scene_granularity_status"], "acceptable")
        self.assertEqual(confirmed["coarse_scene_groups"][0]["review_status"], "confirmed")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ledger.json"
            path.write_text(json.dumps(confirmed, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(INDEX.read_ledger(path)["scene_granularity_status"], "acceptable")

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

    def test_scene_groups_are_atomic_across_analysis_and_holdout(self) -> None:
        records = []
        for scene_number in range(1, 11):
            chunk_count = 2 if scene_number == 1 else 1
            for chunk_number in range(1, chunk_count + 1):
                records.append({
                    "chunk_id": f"W01-S{scene_number:02d}-{chunk_number}",
                    "source": "W01.txt",
                    "work_id": "W01",
                    "scene_ids": [f"S{scene_number:02d}"],
                    "scene_types": ["dialogue" if scene_number % 2 else "action"],
                    "viewpoints": ["close-third"],
                    "characters": ["甲"],
                    "relationship_states": ["strained"],
                    "emotions": ["tension"],
                    "chapter_positions": ["middle"],
                    "paragraph_start": scene_number,
                    "paragraph_end": scene_number,
                })

        ledger = INDEX.build_sampling_ledger(records, "b" * 64, budget=4, holdout_ratio=0.2, seed=9)
        roles_by_scene: dict[str, set[str]] = {}
        for item in ledger["items"]:
            for scene_id in item["scene_ids"]:
                roles_by_scene.setdefault(scene_id, set()).add(item["role"])

            self.assertEqual(ledger["schema_version"], "1.3")
        self.assertTrue(all(len(roles) == 1 for roles in roles_by_scene.values()))
        self.assertFalse(
            set(ledger["analysis_coverage"]["scene_group_ids"])
            & set(ledger["holdout_coverage"]["scene_group_ids"])
        )

    def test_extend_ledger_adds_complete_scene_group_for_saturation_round(self) -> None:
        records = []
        for scene_number in range(1, 5):
            for chunk_number in (1, 2):
                records.append({
                    "chunk_id": f"S{scene_number}-{chunk_number}",
                    "source": "W01.txt",
                    "work_id": "W01",
                    "sample_ids": [f"SAMPLE-{scene_number}"],
                    "chapter_ids": ["C01"],
                    "scene_ids": [f"SCENE-{scene_number}"],
                    "scene_types": ["dialogue"],
                    "viewpoints": ["close-third"],
                    "characters": ["甲"],
                    "relationship_states": ["strained"],
                    "emotions": ["tension"],
                    "chapter_positions": ["middle"],
                    "paragraph_start": scene_number * 2 + chunk_number,
                    "paragraph_end": scene_number * 2 + chunk_number,
                })
        ledger = INDEX.build_sampling_ledger(records, "a" * 64, budget=2, holdout_ratio=0, seed=4)
        existing = {item["chunk_id"] for item in ledger["items"]}
        target_scene = next(
            scene_number
            for scene_number in range(1, 5)
            if not {f"S{scene_number}-1", f"S{scene_number}-2"} & existing
        )

        updated = INDEX.extend_ledger(
            ledger,
            records,
            [f"S{target_scene}-1"],
            "SAT03 targeted counterexample search",
        )
        added = [item for item in updated["items"] if item["chunk_id"].startswith(f"S{target_scene}-")]

        self.assertEqual({item["chunk_id"] for item in added}, {f"S{target_scene}-1", f"S{target_scene}-2"})
        self.assertTrue(all(item["status"] == "pending" for item in added))
        self.assertEqual(updated["analysis_scene_group_count"], 2)
        self.assertEqual(updated["analysis_coverage"]["chunk_count"], 4)
        self.assertEqual(updated["budget_overshoot_chunks"], 2)
        self.assertEqual(updated["updates"][-1]["action"], "extend")

    def test_manual_holdout_expands_to_the_whole_scene_group(self) -> None:
        shared = [{
            "chunk_id": f"shared-{number}",
            "source": "W01.txt",
            "work_id": "W01",
            "scene_ids": ["S01"],
            "scene_types": ["dialogue"],
            "viewpoints": [],
            "characters": [],
            "relationship_states": [],
            "emotions": [],
            "chapter_positions": [],
            "holdout": number == 1,
            "paragraph_start": number,
            "paragraph_end": number,
        } for number in (1, 2)]
        other = {
            **shared[0],
            "chunk_id": "other-1",
            "scene_ids": ["S02"],
            "holdout": False,
            "paragraph_start": 3,
            "paragraph_end": 3,
        }

        ledger = INDEX.build_sampling_ledger(shared + [other], "c" * 64, budget=1, holdout_ratio=0, seed=3)
        held_ids = {item["chunk_id"] for item in ledger["items"] if item["role"] == "holdout"}

        self.assertEqual(held_ids, {"shared-1", "shared-2"})

    def test_ledger_reader_rejects_scene_group_role_leakage(self) -> None:
        records = [{
            "chunk_id": f"shared-{number}",
            "source": "W01.txt",
            "work_id": "W01",
            "scene_ids": ["S01"],
            "scene_types": ["dialogue"],
            "viewpoints": [],
            "characters": [],
            "relationship_states": [],
            "emotions": [],
            "chapter_positions": [],
            "holdout": number == 1,
            "paragraph_start": number,
            "paragraph_end": number,
        } for number in (1, 2)]
        records.append({
            **records[0],
            "chunk_id": "other-1",
            "scene_ids": ["S02"],
            "holdout": False,
            "paragraph_start": 3,
            "paragraph_end": 3,
        })
        ledger = INDEX.build_sampling_ledger(records, "e" * 64, budget=1, holdout_ratio=0, seed=3)
        leaked = next(item for item in ledger["items"] if item["chunk_id"] == "shared-2")
        leaked["role"] = "analysis"
        leaked["status"] = "pending"

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ledger.json"
            path.write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "同一场景组不能同时进入分析和留出"):
                INDEX.read_ledger(path)

    def test_ledger_reader_rejects_inconsistent_status_and_budget_metadata(self) -> None:
        records = [{
            "chunk_id": "only-1",
            "source": "W01.txt",
            "work_id": "W01",
            "scene_ids": ["S01"],
            "scene_types": ["dialogue"],
            "viewpoints": [],
            "characters": [],
            "relationship_states": [],
            "emotions": [],
            "chapter_positions": [],
            "paragraph_start": 1,
            "paragraph_end": 1,
        }]
        ledger = INDEX.build_sampling_ledger(records, "f" * 64, holdout_ratio=0, seed=3)

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ledger.json"
            ledger["items"][0]["status"] = "holdout"
            path.write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "分析角色不能使用 holdout 状态"):
                INDEX.read_ledger(path)

            ledger["items"][0]["status"] = "pending"
            ledger["budget_overshoot_chunks"] = 1
            path.write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "budget_overshoot_chunks 与实际分析块数不一致"):
                INDEX.read_ledger(path)

    def test_automatic_budget_scales_with_work_count(self) -> None:
        records = []
        for work_number in range(1, 21):
            for scene_number in range(1, 11):
                records.append({
                    "chunk_id": f"W{work_number:02d}-S{scene_number:02d}",
                    "source": f"W{work_number:02d}.txt",
                    "work_id": f"W{work_number:02d}",
                    "scene_ids": [f"S{scene_number:02d}"],
                    "scene_types": ["scene"],
                    "viewpoints": ["viewpoint"],
                    "characters": ["character"],
                    "relationship_states": ["relationship"],
                    "emotions": ["emotion"],
                    "chapter_positions": ["middle"],
                    "paragraph_start": scene_number,
                    "paragraph_end": scene_number,
                })

        ledger = INDEX.build_sampling_ledger(records, "d" * 64, budget=None, holdout_ratio=0, seed=5)

        self.assertEqual(ledger["budget_mode"], "auto")
        self.assertIsNone(ledger["budget_requested"])
        self.assertEqual(ledger["budget_effective"], 200)
        self.assertEqual(ledger["budget_recommended"], 200)
        self.assertEqual(len(ledger["items"]), 200)

    def test_resume_rejects_changed_index(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            index_path = root / "index.jsonl"
            index_path.write_text('{"schema_version":4}\n', encoding="utf-8")
            ledger = {"index_sha256": INDEX.file_sha256(index_path)}
            INDEX.verify_ledger_index(ledger, index_path)
            index_path.write_text('{"schema_version":4,"changed":true}\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "索引内容已变化"):
                INDEX.verify_ledger_index(ledger, index_path)


if __name__ == "__main__":
    unittest.main()
