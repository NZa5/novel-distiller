from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import analyze_style  # noqa: E402
import corpus_index  # noqa: E402
import validate_bundle  # noqa: E402
import render_profile  # noqa: E402
from test_validate_profile import build_artifacts  # noqa: E402


def bundle_artifacts(root: Path) -> tuple[dict, list[dict], list[dict], dict, dict]:
    profile, evidence, records = build_artifacts(root)
    index_path = root / "corpus-index.jsonl"
    corpus_index.write_jsonl(records, index_path)
    ledger = corpus_index.build_sampling_ledger(
        records,
        corpus_index.file_sha256(index_path),
        budget=len(records),
        holdout_ratio=0,
    )
    analysis_ids = [item["chunk_id"] for item in ledger["items"] if item["role"] == "analysis"]
    corpus_index.mark_ledger(ledger, analysis_ids, "analyzed", "完成精读")
    ledger_path = root / "sampling-ledger.json"
    corpus_index.write_json(ledger, ledger_path)

    source_paths = [root / "W01.txt", root / "W02.txt"]
    metrics = analyze_style.build_report(source_paths)
    metrics_path = root / "style-metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    profile["surface_ranges"]["metrics_sha256"] = corpus_index.file_sha256(metrics_path)
    profile["analysis_saturation"]["ledger_sha256"] = corpus_index.file_sha256(ledger_path)
    (root / "style-metrics.md").write_text(analyze_style.render_markdown(metrics), encoding="utf-8")
    (root / "author-analysis.md").write_text(render_profile.render_analysis(profile, evidence), encoding="utf-8")
    (root / "writing-packet.md").write_text(render_profile.render_packet(profile, evidence), encoding="utf-8")
    return profile, evidence, records, ledger, metrics


class ValidateBundleTests(unittest.TestCase):
    def test_complete_bundle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, _, _ = bundle_artifacts(root)
            errors = validate_bundle.validate_bundle(
                profile,
                evidence,
                records,
                root / "manifest.json",
                root / "sampling-ledger.json",
                root / "style-metrics.json",
                root / "style-metrics.md",
                root / "author-analysis.md",
                root / "writing-packet.md",
                root / "corpus-index.jsonl",
            )
        self.assertEqual(errors, [])

    def test_pending_chunks_and_missing_markdown_content_fail(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, ledger, _ = bundle_artifacts(root)
            ledger["items"][0]["status"] = "pending"
            corpus_index.write_json(ledger, root / "sampling-ledger.json")
            (root / "writing-packet.md").write_text("profile-test\n", encoding="utf-8")
            errors = validate_bundle.validate_bundle(
                profile,
                evidence,
                records,
                root / "manifest.json",
                root / "sampling-ledger.json",
                root / "style-metrics.json",
                root / "style-metrics.md",
                root / "author-analysis.md",
                root / "writing-packet.md",
                root / "corpus-index.jsonl",
            )
        self.assertTrue(any("pending" in error for error in errors))
        self.assertTrue(any("缺少场景包" in error for error in errors))

    def test_metric_warning_blocks_affected_reference(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, _, metrics = bundle_artifacts(root)
            profile["rules"][0]["metric_refs"] = ["/aggregate/dialogue/content_ratio"]
            metrics["sources"][0]["preprocessing"]["quote_pair_warnings"] = ["中文弯双引号"]
            metrics_path = root / "style-metrics.json"
            metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            profile["surface_ranges"]["metrics_sha256"] = corpus_index.file_sha256(metrics_path)
            errors = validate_bundle.validate_bundle(
                profile,
                evidence,
                records,
                root / "manifest.json",
                root / "sampling-ledger.json",
                metrics_path,
                root / "style-metrics.md",
                root / "author-analysis.md",
                root / "writing-packet.md",
                root / "corpus-index.jsonl",
            )
        self.assertTrue(any("引号警告" in error for error in errors))

    def test_reviewed_counterexample_samples_must_be_analyzed_in_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, ledger, _ = bundle_artifacts(root)
            for item in ledger["items"]:
                if "S02" in item.get("sample_ids", []):
                    item["status"] = "skipped"
                    item["notes"] = ["故意构造未精读样本"]
            corpus_index.write_json(ledger, root / "sampling-ledger.json")
            errors = validate_bundle.validate_bundle(
                profile,
                evidence,
                records,
                root / "manifest.json",
                root / "sampling-ledger.json",
                root / "style-metrics.json",
                root / "style-metrics.md",
                root / "author-analysis.md",
                root / "writing-packet.md",
                root / "corpus-index.jsonl",
            )
        self.assertTrue(any("反例搜索样本未进入已精读账本" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
