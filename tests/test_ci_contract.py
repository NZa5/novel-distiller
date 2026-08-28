from pathlib import Path
import yaml
ROOT=Path(__file__).parents[1]
def test_skill_ci_policy():
 w=yaml.safe_load((ROOT/'.github/workflows/skill-ci.yml').read_text())
 assert w['permissions']=={'contents':'read'}
 assert w['jobs']['skill']['env']=={'OPENAI_API_KEY':'','OPENAI_BASE_URL':'','OPENAI_MODEL':''}
def test_optional_ci_offline():
 t=(ROOT/'.github/workflows/python-tooling-ci.yml').read_text()
 assert '-m "not live_api"' in t or "not live_api" in t
 assert 'workflow_dispatch' in t
