import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_optional_python_product_has_a_single_package_root():
    product = ROOT / "optional-tooling/python"
    assert (product / "pyproject.toml").is_file()
    assert (product / "novel_distiller/__init__.py").is_file()
    assert not (ROOT / "novel_distiller").exists()
    assert not (product / "tests/__init__.py").exists()
    for readme in (ROOT / "README.md", ROOT / "README.zh-CN.md"):
        text = readme.read_text("utf-8")
        assert "optional-tooling/python/" in text
        assert "└── novel_distiller/" not in text

def test_requirements_compatibility_files_are_ascii():
    for path in [ROOT / "requirements.txt", ROOT / "optional-tooling/python/requirements.txt"]:
        path.read_bytes().decode("ascii")

def test_versions_and_legacy_output_domain_are_explicit():
    pyproject = (ROOT / "optional-tooling/python/pyproject.toml").read_text("utf-8")
    package = (ROOT / "optional-tooling/python/novel_distiller/__init__.py").read_text("utf-8")
    assert 'version = "0.3.0"' in pyproject
    assert '__version__ = "0.3.0"' in package
    assert "legacy-0.2" in (ROOT / "optional-tooling/python/README.md").read_text("utf-8")


def test_coverage_gate_reads_json_summary_fields(tmp_path):
    report = {
        "files": {
            "novel_distiller/utils/safe_text.py": {
                "summary": {"num_statements": 10, "covered_lines": 8}
            },
            "novel_distiller/utils/prompt_safety.py": {
                "summary": {"num_statements": 5, "covered_lines": 4}
            },
        }
    }
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "optional-tooling/python/scripts/check_coverage.py"), str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
