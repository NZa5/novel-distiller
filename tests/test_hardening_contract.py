import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_release_builder_supports_nested_output_and_rejects_forbidden_files(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("release", ROOT / "scripts/build_skill_release.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = tmp_path / "nested" / "artifact.zip"
    digest = module.build_release(ROOT, output)
    assert output.is_file() and len(digest) == 64
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
    assert all(not n.endswith(".py") and "/tests/" not in n and ".env" not in n for n in names)


def test_root_surface_does_not_offer_provider_configuration():
    for path in [ROOT / ".env.example", ROOT / "README.md", ROOT / "README.zh-CN.md"]:
        text = path.read_text("utf-8")
        assert "OPENAI_API_KEY=" not in text
    setup = (ROOT / "setup.py").read_text("utf-8")
    assert "optional-tooling/python" in setup


def test_complex_fixtures_cover_distinct_security_and_fiction_cases():
    cases = {
        "injection_privacy_zh": ["SYSTEM", "shell", "CANARY"],
        "nonlinear_unreliable_en": ["flashback", "contradicted"],
        "partial_excerpt_bilingual": ["excerpt", "unseen ending"],
        "alias_collision_zh": ["笔名", "称号"],
        "foreshadow_overlap_zh": ["重复", "误导"],
    }
    for case, markers in cases.items():
        source = (ROOT / "tests/fixtures/agent" / case / "source.md").read_text("utf-8").lower()
        assert all(marker.lower() in source for marker in markers), case


def test_intermediate_state_examples_are_readable_and_versioned():
    state = json.loads((ROOT / "examples/state/checkpoint-committed.json").read_text("utf-8"))
    assert "state_version" in state
    assert "\n" in (ROOT / "examples/state/checkpoint-committed.json").read_text("utf-8")
    assert state["checkpoint"]["status"] == "committed"


def test_ci_has_required_offline_and_manual_live_boundaries():
    skill = (ROOT / ".github/workflows/skill-ci.yml").read_text("utf-8")
    tooling = (ROOT / ".github/workflows/python-tooling-ci.yml").read_text("utf-8")
    assert "git diff --check" in skill and "build_skill_release.py" in skill
    assert "release.yml" in {p.name for p in (ROOT / ".github/workflows").iterdir()}
    assert "live-provider" in tooling and "workflow_dispatch" in tooling
    assert "--strict-markers" in tooling and "--cov-fail-under=35" in tooling
    assert "windows-latest" in tooling and "python -m build optional-tooling/python" in tooling
    assert "actions/upload-artifact@" in (ROOT / ".github/workflows/release.yml").read_text("utf-8")
    checkout_sha = "11bd71901bbe5b1630ceea73d27597364c9af683"
    checkout_refs = re.findall(r"actions/checkout@([0-9a-f]{40})", tooling)
    assert checkout_refs == [checkout_sha, checkout_sha, checkout_sha]
