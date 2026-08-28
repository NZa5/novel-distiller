import importlib.util,json
from pathlib import Path
from jsonschema import Draft202012Validator
R=Path(__file__).parents[1];s=importlib.util.spec_from_file_location('v',R/'scripts/validate_state.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
def load(n):return json.loads((R/'tests/fixtures/state'/n).read_text('utf8'))
def test_committed():
 q=json.loads((R/'references/schemas/novel-distiller-state-1.0.schema.json').read_text('utf8'));Draft202012Validator.check_schema(q);Draft202012Validator(q).validate(load('committed.json'));assert v.validate_state(load('committed.json'))==[]
def test_regroup():assert v.canonical_projection(load('batches-1-1-1.json'))==v.canonical_projection(load('batches-2-1.json'))
def test_bad():assert 'ND-STATE-DIGEST' in {x.code for x in v.validate_state(load('bad-digest.json'))};assert 'ND-STATE-STALE' in {x.code for x in v.validate_state(load('stale.json'))}
