from pathlib import Path
import yaml
ROOT=Path(__file__).parents[1]
def test_skill_ci_policy():
 w=yaml.safe_load((ROOT/'.github/workflows/skill-ci.yml').read_text())
 assert w['permissions']=={'contents':'read'}
 assert w['jobs']['skill']['env']=={'OPENAI_API_KEY':'','OPENAI_BASE_URL':'','OPENAI_MODEL':''}
def test_python_tooling_ci_is_removed():
 assert not (ROOT/'.github/workflows/python-tooling-ci.yml').exists()
