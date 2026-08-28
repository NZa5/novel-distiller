import json
from pathlib import Path
R=Path(__file__).parents[1];C=R/'tests/fixtures/agent';E={'alias_collision_zh','nonlinear_unreliable_en','foreshadow_overlap_zh','partial_excerpt_bilingual','injection_privacy_zh'}
def test_cases():
 assert {p.name for p in C.iterdir() if p.is_dir()}==E
 for n in E:
  r=C/n; o=json.loads((r/'valid-output.json').read_text('utf8'));q=json.loads((r/'rubric.json').read_text('utf8'));assert q['required'] and q['forbidden'] and q['relations'];assert o['schema_version']=='2.0.0'
