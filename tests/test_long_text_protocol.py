import importlib.util,json
from pathlib import Path
from jsonschema import Draft202012Validator
R=Path(__file__).parents[1];s=importlib.util.spec_from_file_location('v',R/'scripts/validate_state.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
def load(n):return json.loads((R/'tests/fixtures/state'/n).read_text('utf8'))
def test_committed():
 q=json.loads((R/'references/schemas/novel-distiller-state-1.0.schema.json').read_text('utf8'));Draft202012Validator.check_schema(q);Draft202012Validator(q).validate(load('committed.json'));assert v.validate_state(load('committed.json'))==[]
def test_regroup():assert v.canonical_projection(load('batches-1-1-1.json'))==v.canonical_projection(load('batches-2-1.json'))
def test_bad():assert 'ND-STATE-DIGEST' in {x.code for x in v.validate_state(load('bad-digest.json'))};assert 'ND-STATE-STALE' in {x.code for x in v.validate_state(load('stale.json'))}


def test_state_schema_rejects_unknown_nested_fields_and_invalid_status():
    import copy
    schema=json.loads((R/'references/schemas/novel-distiller-state-1.0.schema.json').read_text('utf8'))
    valid=load('committed.json')
    bad=copy.deepcopy(valid); bad['checkpoint']['status']='finished'
    assert list(Draft202012Validator(schema).iter_errors(bad))
    bad=copy.deepcopy(valid); bad['progress']['unexpected']=True
    assert list(Draft202012Validator(schema).iter_errors(bad))


def test_state_schema_rejects_missing_checkpoint_contract():
    q=json.loads((R/'references/schemas/novel-distiller-state-1.0.schema.json').read_text('utf8'))
    bad=load('committed.json'); del bad['checkpoint']['state_digest']
    assert list(Draft202012Validator(q).iter_errors(bad))
