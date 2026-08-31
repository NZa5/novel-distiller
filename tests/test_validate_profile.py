from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
VALIDATE_SPEC = importlib.util.spec_from_file_location("validate_profile", SCRIPTS / "validate_profile.py")
assert VALIDATE_SPEC and VALIDATE_SPEC.loader
VALIDATE = importlib.util.module_from_spec(VALIDATE_SPEC)
VALIDATE_SPEC.loader.exec_module(VALIDATE)

INDEX_SPEC = importlib.util.spec_from_file_location("corpus_index_for_validation", SCRIPTS / "corpus_index.py")
assert INDEX_SPEC and INDEX_SPEC.loader
INDEX = importlib.util.module_from_spec(INDEX_SPEC)
INDEX_SPEC.loader.exec_module(INDEX)


def valid_profile(records: list[dict]) -> dict:
    return {
        "schema_version": "1.0",
        "profile_id": "profile-test",
        "profile_scope": "author",
        "corpus": {
            "supplied_only": True,
            "target_label": "测试作者",
            "work_ids": ["W01", "W02"],
            "sample_ids": ["S01", "S02", "S03"],
            "source_hashes": sorted({record["source_sha256"] for record in records}),
            "comparison_supplied": False,
            "holdout_sample_ids": [],
            "preprocessing": {"reflow_hard_wrap": False, "strip_annotations": False},
        },
        "coverage": [{
            "dimension": "narrative_discourse",
            "status": "analyzed",
            "evidence_count": 3,
            "uncovered": [],
        }],
        "master_voice": "叙述保持有限知识边界。",
        "rules": [{
            "rule_id": "R01",
            "level": "author",
            "classification": "conditional",
            "category": "narrative_distance",
            "trigger": "对峙场景",
            "observable": "动作先于判断",
            "mechanism": "延后心理解释",
            "effect": "维持压力",
            "action": "先写动作再写判断",
            "limits": "内心独白不适用",
            "evidence_ids": ["E0001", "E0002", "E0003"],
            "support_sample_count": 2,
            "support_work_count": 2,
            "support_scene_type_count": 1,
            "counterexample_count": 1,
            "holdout_status": "not_tested",
            "distinctiveness_status": "not_tested",
            "confidence": "medium",
            "confidence_basis": "跨两部作品重复，但场景覆盖有限",
        }],
        "scene_modes": [{
            "mode_id": "M01",
            "name": "对峙模式",
            "triggers": ["角色目标冲突"],
            "rule_ids": ["R01"],
            "evidence_ids": ["E0001", "E0002"],
        }],
        "character_voices": [{
            "voice_id": "V01",
            "character_label": "叙述焦点人物",
            "conditions": ["有限视角"],
            "rule_ids": ["R01"],
            "evidence_ids": ["E0001"],
        }],
        "rule_precedence": ["R01"],
        "surface_ranges": {},
        "writing_packet": {
            "master_voice": "叙述保持有限知识边界。",
            "active_rule_ids": ["R01"],
            "scene_mode_ids": ["M01"],
            "character_voice_ids": ["V01"],
            "rule_precedence": ["R01"],
            "drift_corrections": ["先核对场景条件，再调整句段表层"],
        },
        "limitations": ["未提供对照作者"],
    }


def build_artifacts(root: Path) -> tuple[dict, list[dict], list[dict]]:
    sources = []
    for work_id in ("W01", "W02"):
        source = root / f"{work_id}.txt"
        source.write_text("他停在门边。\n\n她没有回头。", encoding="utf-8")
        sources.append(source)
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({
        "schema_version": "1.0",
        "sources": [{
            "path": source.name,
            "work_id": source.stem,
            "period": "",
            "metadata": {},
            "segments": [{
                "paragraph_start": 1,
                "paragraph_end": 2,
                "scene_type": "confrontation",
            }],
        } for source in sources],
    }, ensure_ascii=False), encoding="utf-8")
    records = INDEX.build_index(sources, chunk_chars=200, manifest=manifest)
    by_work = {record["work_id"]: record for record in records}

    def evidence_record(evidence_id: str, sample_id: str, work_id: str, role: str, excerpt: str) -> dict:
        record = by_work[work_id]
        return {
            "schema_version": "1.0",
            "profile_id": "profile-test",
            "evidence_id": evidence_id,
            "rule_id": "R01",
            "dimension": "narrative_discourse",
            "sample_id": sample_id,
            "work_id": work_id,
            "scene_type": "confrontation",
            "source_path": record["source_path"],
            "source_sha256": record["source_sha256"],
            "chunk_id": record["chunk_id"],
            "paragraph_start": record["paragraph_start"],
            "paragraph_end": record["paragraph_end"],
            "content_char_start": record["content_char_start"],
            "content_char_end": record["content_char_end"],
            "evidence_role": role,
            "excerpt": excerpt,
            "observation": "动作先于判断。",
            "eligibility": "视角和场景条件匹配。",
        }

    evidence = [
        evidence_record("E0001", "S01", "W01", "support", "他停在门边。"),
        evidence_record("E0002", "S02", "W02", "support", "他停在门边。"),
        evidence_record("E0003", "S03", "W02", "counterexample", "她没有回头。"),
    ]
    return valid_profile(records), evidence, records


class ValidateProfileTests(unittest.TestCase):
    def test_valid_profile_evidence_index_and_sources_pass(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records = build_artifacts(Path(folder))
            self.assertEqual(VALIDATE.validate_profile(profile, evidence, records), [])

    def test_missing_evidence_and_wrong_counts_fail(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records = build_artifacts(Path(folder))
            profile["rules"][0]["support_work_count"] = 3
            errors = VALIDATE.validate_profile(profile, evidence[:1], records)

        self.assertTrue(any("不存在的证据" in error for error in errors))
        self.assertTrue(any("support_work_count" in error for error in errors))
        self.assertTrue(any("evidence_count" in error for error in errors))

    def test_fake_path_chunk_hash_and_excerpt_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records = build_artifacts(Path(folder))
            evidence[0]["source_path"] = "Z:/definitely/missing.txt"
            evidence[1]["chunk_id"] = "invented-chunk"
            evidence[2]["excerpt"] = "原文中不存在的句子。"
            errors = VALIDATE.validate_profile(profile, evidence, records)

        self.assertTrue(any("source_path 与索引不一致" in error for error in errors))
        self.assertTrue(any("chunk_id 不存在于索引" in error for error in errors))
        self.assertTrue(any("excerpt 不存在" in error for error in errors))

    def test_invalid_scene_and_packet_references_fail(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records = build_artifacts(Path(folder))
            profile["scene_modes"][0]["rule_ids"] = ["R404"]
            profile["writing_packet"]["character_voice_ids"] = ["V404"]
            errors = VALIDATE.validate_profile(profile, evidence, records)

        self.assertTrue(any("scene_modes[1].rule_ids" in error for error in errors))
        self.assertTrue(any("writing_packet.character_voice_ids" in error for error in errors))

    def test_malformed_controlled_values_report_errors_instead_of_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records = build_artifacts(Path(folder))
            profile["profile_scope"] = []
            profile["rules"][0]["classification"] = {"bad": True}
            evidence[0]["evidence_role"] = ["support"]
            errors = VALIDATE.validate_profile(profile, evidence, records)

        self.assertTrue(any("profile_scope" in error for error in errors))
        self.assertTrue(any("classification" in error for error in errors))
        self.assertTrue(any("evidence_role" in error for error in errors))

    def test_outside_corpus_flag_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            profile, _, records = build_artifacts(Path(folder))
            profile["corpus"]["supplied_only"] = False
            errors = VALIDATE.validate_profile(profile, index_records=records)

        self.assertIn("corpus.supplied_only 必须为 true", errors)

    def test_cli_requires_and_validates_index(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records = build_artifacts(root)
            profile_path = root / "author-profile.json"
            evidence_path = root / "evidence-map.jsonl"
            index_path = root / "corpus-index.jsonl"
            profile_path.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
            evidence_path.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in evidence) + "\n",
                encoding="utf-8",
            )
            INDEX.write_jsonl(records, index_path)
            with redirect_stdout(io.StringIO()):
                result = VALIDATE.main([
                    str(profile_path), "--evidence", str(evidence_path), "--index", str(index_path),
                ])

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
