from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_optional_python_product_has_a_single_package_root():
    product = ROOT / "optional-tooling/python"
    assert (product / "pyproject.toml").is_file()
    assert (product / "novel_distiller/__init__.py").is_file()
    assert not (ROOT / "novel_distiller").exists()
    assert not (product / "tests/__init__.py").exists()

def test_requirements_compatibility_files_are_ascii():
    for path in [ROOT / "requirements.txt", ROOT / "optional-tooling/python/requirements.txt"]:
        path.read_bytes().decode("ascii")

def test_versions_and_legacy_output_domain_are_explicit():
    pyproject = (ROOT / "optional-tooling/python/pyproject.toml").read_text("utf-8")
    package = (ROOT / "optional-tooling/python/novel_distiller/__init__.py").read_text("utf-8")
    assert 'version = "0.3.0"' in pyproject
    assert '__version__ = "0.3.0"' in package
    assert "legacy-0.2" in (ROOT / "optional-tooling/python/README.md").read_text("utf-8")
