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
    for dimension in REQUIRED[2:-1]:
        for item in data[dimension]:
            assert {"id", "claim_status", "confidence", "evidence"}.issubset(item)


def test_relative_markdown_links_resolve():
    for path in [ROOT / "SKILL.md", ROOT / "README.md", ROOT / "QUICKSTART.md", ROOT / "INSTALL.md", ROOT / "CONTRIBUTING.md", ROOT / "PROJECT_SUMMARY.md"]:
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)", path.read_text(encoding="utf-8")):
            assert (path.parent / target).exists(), f"broken link in {path}: {target}"
