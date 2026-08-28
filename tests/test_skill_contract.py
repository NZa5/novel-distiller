"""Contract checks for the dependency-free cross-agent Skill."""
import json
import re
import subprocess
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
README_SECTIONS = {
    "README.md": [
        "Why Novel Distiller?", "Features", "How It Works", "Quick Start",
        "Example Output", "Supported Inputs and Scope", "Output Contract",
        "Agent Compatibility", "Repository Structure", "Optional Python Tooling",
        "Documentation", "Roadmap", "Contributing", "License",
    ],
    "README.zh-CN.md": [
        "为什么选择 Novel Distiller？", "核心能力", "工作原理", "快速开始",
        "输出示例", "支持的输入与分析范围", "输出规范", "Agent 兼容性",
        "仓库结构", "可选 Python 工具", "文档导航", "路线图", "参与贡献",
        "开源协议",
    ],
}


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


def test_example_markdown_uses_the_same_record_ids_and_statuses():
    markdown = (ROOT / "examples/output/sample_distillation.md").read_text(encoding="utf-8")
    data = json.loads((ROOT / "examples/output/sample_distillation.json").read_text(encoding="utf-8"))
    assert all(f"## {heading}" in markdown for heading in MARKDOWN_HEADINGS)
    json_ids = {item["id"] for dimension in ID_PREFIXES for item in data[dimension]}
    markdown_ids = set(re.findall(r"\b(?:char|plot|rel|fore|time|style|uncertain)-\d{3}\b", markdown))
    assert markdown_ids == json_ids

    for dimension in ID_PREFIXES:
        for item in data[dimension]:
            line = next(line for line in markdown.splitlines() if item["id"] in line)
            assert f'`{item["claim_status"]}`' in line
            assert f'`{item["confidence"]}`' in line
            for evidence in item["evidence"]:
                if evidence.get("chapter"):
                    assert evidence["chapter"] in line


def test_documented_json_schema_is_parseable_and_matches_example_contract():
    document = (ROOT / "references/output-schema.md").read_text(encoding="utf-8")
    match = re.search(r"```json\s*(.*?)\s*```", document, re.DOTALL)
    assert match, "output-schema.md must contain a fenced JSON Schema"
    schema = json.loads(match.group(1))
    example = json.loads((ROOT / "examples/output/sample_distillation.json").read_text(encoding="utf-8"))

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(example)
    assert set(REQUIRED).issubset(schema["properties"])


def test_bilingual_readmes_have_navigation_and_release_sections():
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

    assert "[English](README.md)" in english and "[简体中文](README.zh-CN.md)" in english
    assert "[English](README.md)" in chinese and "[简体中文](README.zh-CN.md)" in chinese
    assert "No API key" in english and "No Python" in english
    assert "no package installation" in english and "default workflow" in english
    assert "无需 API Key" in chinese and "无需 Python" in chinese
    assert "无需安装依赖" in chinese and "默认流程" in chinese
    assert "mkdir -p ~/.pi/agent/skills" in english
    assert "mkdir -p ~/.pi/agent/skills" in chinese
    assert "restart" in english.lower() or "reload" in english.lower()
    assert "重启" in chinese or "重新加载" in chinese

    for filename, headings in README_SECTIONS.items():
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert all(f"## {heading}" in text for heading in headings)
        assert "SKILL.md" in text
        assert "examples/input/sample_novel.md" in text
        assert "examples/output/sample_distillation.md" in text
        assert "examples/output/sample_distillation.json" in text


def test_only_published_example_outputs_are_exempt_from_gitignore():
    if not (ROOT / ".git").exists():
        return
    published = ["examples/output/sample_distillation.md", "examples/output/sample_distillation.json"]
    for relative_path in published:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", relative_path],
            cwd=ROOT,
            check=False,
        )
        assert result.returncode == 1, f"published example is ignored: {relative_path}"

    unpublished = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "examples/output/unpublished.tmp"],
        cwd=ROOT,
        check=False,
    )
    assert unpublished.returncode == 0, "other generated example output must remain ignored"


def test_relative_markdown_links_resolve():
    paths = [ROOT / "SKILL.md", ROOT / "README.md", ROOT / "README.zh-CN.md", ROOT / "QUICKSTART.md", ROOT / "INSTALL.md", ROOT / "CONTRIBUTING.md", ROOT / "PROJECT_SUMMARY.md"]
    for path in paths:
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)", path.read_text(encoding="utf-8")):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                continue
            assert (path.parent / target).exists(), f"broken link in {path}: {target}"
