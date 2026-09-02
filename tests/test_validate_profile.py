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


def valid_profile(records: list[dict], manifest_hash: str) -> dict:
    target_dimension = "narrator_evaluative_stance"
    return {
        "schema_version": "2.1",
        "profile_id": "profile-test",
        "profile_scope": "author",
        "corpus": {
            "supplied_only": True,
            "target_label": "测试作者",
            "work_ids": ["W01", "W02"],
            "sample_ids": ["S01", "S02"],
            "source_hashes": sorted({record["source_sha256"] for record in records}),
            "comparison_supplied": False,
            "comparison_work_ids": [],
            "comparison_sample_ids": [],
            "comparison_source_hashes": [],
            "holdout_sample_ids": [],
            "provisional_profile_sha256": None,
            "preprocessing": {"reflow_hard_wrap": False, "strip_annotations": False},
            "manifest_sha256": manifest_hash,
        },
        "coverage": [{
            "dimension": dimension,
            "status": "analyzed" if dimension == target_dimension else "no_stable_finding",
            "evidence_count": 3 if dimension == target_dimension else 0,
            "reviewed_sample_ids": ["S01", "S02"],
            "finding_summary": "动作先于判断。" if dimension == target_dimension else "两段样本已核查，未形成稳定结论。",
            "uncovered": [],
        } for dimension in VALIDATE.ANALYSIS_DIMENSIONS],
        "master_voice": "叙述保持有限知识边界。",
        "rules": [{
            "rule_id": "R01",
            "dimension": target_dimension,
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
            "metric_refs": [],
            "metric_claims": [],
            "support_sample_count": 2,
            "support_work_count": 2,
            "support_scene_type_count": 1,
            "counterexample_count": 1,
            "counterexample_search": {
                "status": "complete",
                "eligible_sample_count": 2,
                "reviewed_sample_count": 2,
                "eligible_sample_ids": ["S01", "S02"],
                "reviewed_sample_ids": ["S01", "S02"],
                "notes": "已检查全部适用样本。",
            },
            "holdout_status": "not_tested",
            "holdout_evaluation": {
                "eligible": 0,
                "matched": 0,
                "missed": 0,
                "contradicted": 0,
                "not_applicable": 0,
            },
            "distinctiveness_status": "not_tested",
            "distinctiveness_evidence_ids": [],
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
        "surface_ranges": {"metrics_sha256": "a" * 64},
        "analysis_saturation": {
            "status": "full_corpus",
            "ledger_sha256": "a" * 64,
            "rounds": [],
            "unresolved_dimension_ids": [],
            "stop_reason": "测试语料已全读。",
        },
        "writing_packet": {
            "master_voice": "叙述保持有限知识边界。",
            "selector_order": ["scene_mode", "viewpoint", "relationship"],
            "shared_rule_ids": [],
            "packets": [{
                "packet_id": "P01",
                "name": "对峙场景包",
                "triggers": ["角色目标冲突"],
                "active_dimension_ids": [target_dimension],
                "active_rule_ids": ["R01"],
                "scene_mode_ids": ["M01"],
                "character_voice_ids": ["V01"],
                "rule_precedence": ["R01"],
                "evidence_ids": ["E0001", "E0002"],
                "surface_range_refs": [],
                "drift_corrections": ["先核对场景条件，再调整句段表层"],
            }],
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
        "schema_version": "2.0",
        "sources": [{
            "path": source.name,
            "work_id": source.stem,
            "period": "",
            "metadata": {},
            "segments": [{"paragraph_start": 1, "paragraph_end": 2, "sample_id": f"S0{number}",
                          "chapter_id": "C01", "scene_id": "SC01", "scene_type": "confrontation"}],
        } for number, source in enumerate(sources, 1)],
    }, ensure_ascii=False), encoding="utf-8")
    records = INDEX.build_index(sources, chunk_chars=200, manifest=manifest)
    by_work = {record["work_id"]: record for record in records}

    def evidence_record(evidence_id: str, sample_id: str, work_id: str, role: str, excerpt: str) -> dict:
        record = by_work[work_id]
        return {
            "schema_version": "2.1", "profile_id": "profile-test", "evidence_id": evidence_id,
            "rule_id": "R01", "dimension": "narrator_evaluative_stance", "corpus_role": "target",
            "sample_id": sample_id, "work_id": work_id, "scene_type": "confrontation",
            "source_path": record["source_path"], "source_sha256": record["source_sha256"],
            "chunk_id": record["chunk_id"], "paragraph_start": record["paragraph_start"],
            "paragraph_end": record["paragraph_end"], "content_char_start": record["content_char_start"],
            "content_char_end": record["content_char_end"], "evidence_role": role,
            "evaluation_outcome": "not_applicable", "excerpt": excerpt, "observation": "动作先于判断。",
            "eligibility": "视角和场景条件匹配。",
        }

    evidence = [
        evidence_record("E0001", "S01", "W01", "support", "他停在门边。"),
        evidence_record("E0002", "S02", "W02", "support", "他停在门边。"),
        evidence_record("E0003", "S02", "W02", "counterexample", "她没有回头。"),
    ]
    return valid_profile(records, INDEX.file_sha256(manifest)), evidence, records


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
        self.assertTrue(any("chunk_id 不存在于对应索引" in error for error in errors))
        self.assertTrue(any("excerpt 不存在" in error for error in errors))

    def test_invalid_scene_and_packet_references_fail(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records = build_artifacts(Path(folder))
            profile["scene_modes"][0]["rule_ids"] = ["R404"]
            packet = profile["writing_packet"]["packets"][0]
            packet["character_voice_ids"] = ["V404"]
            packet["active_dimension_ids"] = ["invented_dimension"]
            errors = VALIDATE.validate_profile(profile, evidence, records)
        self.assertTrue(any("scene_modes[1].rule_ids" in error for error in errors))
        self.assertTrue(any("character_voice_ids" in error for error in errors))
        self.assertTrue(any("active_dimension_ids" in error for error in errors))

    def test_all_canonical_dimensions_are_required_and_controlled(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records = build_artifacts(Path(folder))
            profile["coverage"].pop()
            profile["coverage"][0]["dimension"] = "invented_dimension"
            errors = VALIDATE.validate_profile(profile, evidence, records)
        self.assertTrue(any("coverage 缺少固定分析维度" in error for error in errors))
        self.assertTrue(any("invented_dimension" in error for error in errors))

    def test_saturation_and_counterexample_search_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records = build_artifacts(Path(folder))
            profile["analysis_saturation"].update(status="saturated", rounds=[
                {"round_id": "SAT01", "ledger_update_sequences": [1], "added_sample_ids": ["S01"], "new_rule_count": 0,
                 "new_counterexample_count": 0, "unresolved_dimension_ids": [], "note": "补读。"},
                {"round_id": "SAT02", "ledger_update_sequences": [2], "added_sample_ids": ["S02"], "new_rule_count": 1,
                 "new_counterexample_count": 0, "unresolved_dimension_ids": [], "note": "补读。"},
            ])
            profile["rules"][0]["confidence"] = "high"
            profile["rules"][0]["counterexample_search"]["status"] = "partial"
            profile["rules"][0]["counterexample_search"]["reviewed_sample_count"] = 1
            profile["rules"][0]["counterexample_search"]["reviewed_sample_ids"] = ["S01"]
            errors = VALIDATE.validate_profile(profile, evidence, records)
        self.assertTrue(any("最后两轮" in error for error in errors))
        self.assertTrue(any("high 可信度" in error for error in errors))

    def test_counterexample_search_ids_are_traceable_and_counted(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records = build_artifacts(Path(folder))
            search = profile["rules"][0]["counterexample_search"]
            search["reviewed_sample_ids"] = ["S01", "S404"]
            errors = VALIDATE.validate_profile(profile, evidence, records)
        self.assertTrue(any("reviewed_sample_ids 必须是适用样本子集" in error for error in errors))

    def test_distinctiveness_requires_traceable_control_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records = build_artifacts(root)
            control_source = root / "control.txt"
            control_source.write_text("他立刻作出判断。", encoding="utf-8")
            control_manifest = root / "control-manifest.json"
            control_manifest.write_text(json.dumps({
                "schema_version": "2.0",
                "sources": [{
                    "path": control_source.name,
                    "work_id": "CW01",
                    "period": "",
                    "metadata": {},
                    "segments": [{"paragraph_start": 1, "paragraph_end": 1, "sample_id": "CS01",
                                  "chapter_id": "CC01", "scene_id": "CSC01", "scene_type": "confrontation"}],
                }],
            }, ensure_ascii=False), encoding="utf-8")
            control_records = INDEX.build_index([control_source], chunk_chars=200, manifest=control_manifest)
            control = control_records[0]
            profile["corpus"].update({
                "comparison_supplied": True,
                "comparison_work_ids": ["CW01"],
                "comparison_sample_ids": ["CS01"],
                "comparison_source_hashes": [control["source_sha256"]],
            })
            profile["rules"][0]["distinctiveness_status"] = "supported"
            profile["rules"][0]["distinctiveness_evidence_ids"] = ["EC01"]
            evidence.append({
                "schema_version": "2.1", "profile_id": "profile-test", "evidence_id": "EC01",
                "rule_id": "R01", "dimension": "narrator_evaluative_stance", "corpus_role": "control",
                "sample_id": "CS01", "work_id": "CW01", "scene_type": "confrontation",
                "source_path": control["source_path"], "source_sha256": control["source_sha256"],
                "chunk_id": control["chunk_id"], "paragraph_start": control["paragraph_start"],
                "paragraph_end": control["paragraph_end"], "content_char_start": control["content_char_start"],
                "content_char_end": control["content_char_end"], "evidence_role": "control",
                "evaluation_outcome": "not_applicable", "excerpt": "他立刻作出判断。",
                "observation": "对照文本先给判断。", "eligibility": "同类场景对照。",
            })
            self.assertEqual(VALIDATE.validate_profile(profile, evidence, records, control_records), [])
            profile["rules"][0]["distinctiveness_evidence_ids"] = []
            errors = VALIDATE.validate_profile(profile, evidence, records, control_records)
        self.assertTrue(any("缺少对照证据" in error for error in errors))

    def test_holdout_pass_requires_all_eligible_samples_to_match(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records = build_artifacts(Path(folder))
            holdout_record = dict(records[-1])
            holdout_record["chunk_id"] = holdout_record["chunk_id"] + "-holdout"
            holdout_record["sample_ids"] = ["S03"]
            holdout_record["scene_ids"] = ["SC02"]
            holdout_record["holdout"] = True
            profile["corpus"]["sample_ids"].append("S03")
            profile["corpus"]["holdout_sample_ids"] = ["S03"]
            profile["corpus"]["provisional_profile_sha256"] = "b" * 64
            profile["rules"][0]["evidence_ids"].append("EH01")
            profile["rules"][0]["holdout_status"] = "passed"
            profile["rules"][0]["holdout_evaluation"].update({"eligible": 1, "matched": 1})
            profile["coverage"][7]["evidence_count"] = 4
            evidence.append({
                **evidence[1],
                "evidence_id": "EH01",
                "sample_id": "S03",
                "chunk_id": holdout_record["chunk_id"],
                "evidence_role": "holdout",
                "evaluation_outcome": "matched",
            })
            self.assertEqual(VALIDATE.validate_profile(profile, evidence, records, holdout_index_records=[holdout_record]), [])
            evidence[-1]["evaluation_outcome"] = "contradicted"
            errors = VALIDATE.validate_profile(profile, evidence, records, holdout_index_records=[holdout_record])
        self.assertTrue(any("passed 必须全部命中" in error for error in errors))

    def test_outside_corpus_flag_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            profile, _, records = build_artifacts(Path(folder))
            profile["corpus"]["supplied_only"] = False
            errors = VALIDATE.validate_profile(profile, index_records=records)
        self.assertIn("corpus.supplied_only 必须为 true", errors)

    def test_cli_validates_index(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records = build_artifacts(root)
            profile_path = root / "author-profile.json"
            evidence_path = root / "evidence-map.jsonl"
            index_path = root / "corpus-index.jsonl"
            profile_path.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
            evidence_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in evidence) + "\n", encoding="utf-8")
            INDEX.write_jsonl(records, index_path)
            with redirect_stdout(io.StringIO()):
                result = VALIDATE.main([str(profile_path), "--evidence", str(evidence_path), "--index", str(index_path)])
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
