import json,re
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_versions():
 assert 'version: "2.0.0"' in (ROOT/'SKILL.md').read_text(encoding='utf-8')
 assert json.loads((ROOT/'references/schemas/novel-distiller-2.0.schema.json').read_text())['$id']=='urn:novel-distiller:schema:2.0.0'
 assert 'version = "0.3.0"' in (ROOT/'optional-tooling/python/pyproject.toml').read_text()
def test_changelog_domains():
 assert 'Skill 2.0.0' in (ROOT/'CHANGELOG.md').read_text(encoding='utf-8') and 'Python 0.3.0' not in (ROOT/'CHANGELOG.md').read_text(encoding='utf-8')
 assert 'Python 0.3.0' in (ROOT/'optional-tooling/python/CHANGELOG.md').read_text(encoding='utf-8')
