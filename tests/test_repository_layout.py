from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_repository_contains_only_the_agent_skill_product():
    for path in [
        ROOT / "optional-tooling",
        ROOT / "novel_distiller",
        ROOT / "setup.py",
        ROOT / "requirements.txt",
        ROOT / "MANIFEST.in",
        ROOT / ".env.example",
        ROOT / ".github/workflows/python-tooling-ci.yml",
    ]:
        assert not path.exists(), f"removed Python tooling surface still exists: {path}"

    for path in [ROOT / "README.md", ROOT / "README.zh-CN.md", ROOT / "QUICKSTART.md", ROOT / "CONTRIBUTING.md"]:
        text = path.read_text("utf-8")
        assert "optional-tooling" not in text
        assert "Python CLI" not in text
