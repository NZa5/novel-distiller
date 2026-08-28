"""Contract checks for the dependency-free cross-agent Skill."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
REFS = [
    "distillation-workflow.md",
    "analysis-framework.md",
    "output-schema.md",
    "quality-checklist.md",
    "prompt-templates.md",
]
REQUIRED = ["metadata", "summary", "characters", "plots", "relationships", "foreshadowing", "timeline", "style", "uncertainties", "quality"]
CLAIM_STATUS = {"fact", "inference", "uncertain"}
CONFIDENCE = {"high", "medium", "low"}
ID_PREFIXES = {"characters": "char", "plots": "plot", "relationships": "rel", "foreshadowing": "fore", "timeline": "time", "style": "style", "uncertainties": "uncertain"}
MARKDOWN_HEADINGS = ["Scope & metadata", "Executive summary", "Characters", "Plot", "Relationships", "Foreshadowing", "Timeline", "Style", "Uncertainties & contradictions", "Coverage & quality check"]


def test_skill_is_dependency_free_default_entrypoint():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "only default runtime entry point" in text
    assert "API key" in text and "pip" in text and "Python" in text
    assert "references/" in text


def test_all_reference_documents_exist_and_are_linked():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for name in REFS:
        assert (ROOT / "references" / name).is_file()
        assert f"references/{name}" in skill


def test_example_json_is_parseable_and_has_canonical_fields():
    data = json.loads((ROOT / "examples/output/sample_distillation.json").read_text(encoding="utf-8"))
    assert set(REQUIRED).issubset(data)
    assert data["schema_version"] == "1.0"
    assert {"title", "author", "input_type", "scope", "source_ids"}.issubset(data["metadata"])
    assert {"coverage", "checks", "limitations"}.issubset(data["quality"])

    ids = set()
    for dimension, prefix in ID_PREFIXES.items():
        for item in data[dimension]:
            assert {"id", "claim_status", "confidence", "evidence"}.issubset(item)
            assert item["claim_status"] in CLAIM_STATUS
            assert item["confidence"] in CONFIDENCE
            assert re.fullmatch(rf"{prefix}-\d{{3}}", item["id"])
            assert item["id"] not in ids
            ids.add(item["id"])
            assert item["evidence"]
            for evidence in item["evidence"]:
                assert {"source_id", "locator"}.issubset(evidence)
                assert evidence["source_id"] in data["metadata"]["source_ids"]

    for item in data["plots"]:
        assert item["resolution"] in {"open", "resolved", "partial", "unknown"}
    for item in data["foreshadowing"]:
        assert item["status"] in {"planted", "possibly_revealed", "revealed", "unresolved", "not_applicable"}
    for item in data["timeline"]:
        assert item["mode"] in {"linear", "flashback", "flashforward", "parallel", "unclear"}


def test_example_markdown_uses_the_same_record_ids():
    markdown = (ROOT / "examples/output/sample_distillation.md").read_text(encoding="utf-8")
    data = json.loads((ROOT / "examples/output/sample_distillation.json").read_text(encoding="utf-8"))
    assert all(f"## {heading}" in markdown for heading in MARKDOWN_HEADINGS)
    json_ids = {item["id"] for dimension in ID_PREFIXES for item in data[dimension]}
    markdown_ids = set(re.findall(r"\b(?:char|plot|rel|fore|time|style|uncertain)-\d{3}\b", markdown))
    assert markdown_ids == json_ids


def test_relative_markdown_links_resolve():
    for path in [ROOT / "SKILL.md", ROOT / "README.md", ROOT / "QUICKSTART.md", ROOT / "INSTALL.md", ROOT / "CONTRIBUTING.md", ROOT / "PROJECT_SUMMARY.md"]:
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)", path.read_text(encoding="utf-8")):
            assert (path.parent / target).exists(), f"broken link in {path}: {target}"
