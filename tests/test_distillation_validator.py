import copy, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).parents[1]; spec=importlib.util.spec_from_file_location('validator',ROOT/'scripts/validate_distillation.py'); validator=importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
BASE=json.loads((ROOT/'tests/fixtures/schema/v2-valid.json').read_text('utf8')); MANIFEST={'sources':{'source-001':{'chapters':{'ch-001':{'paragraphs':{'p001':'雨落在站台上'}}},'chunks':['chunk-001']}}}
def codes(d): return {x.code for x in validator.validate_document(d,MANIFEST)}
def test_valid(): assert validator.validate_document(BASE,MANIFEST)==[]
def test_refs():
 d=copy.deepcopy(BASE); d['plots'][0]['id']='char-001'; d['relationships'][0]['target_character_id']='char-999'; assert {'ND-ID-DUPLICATE','ND-REF-DANGLING'}<=codes(d)
def test_quote():
 d=copy.deepcopy(BASE); d['characters'][0]['evidence'][0]['quote']='不存在'; assert 'ND-QUOTE-MISMATCH' in codes(d)
def test_version():
 d=copy.deepcopy(BASE); d['schema_version']='3.0.0'; assert 'ND-SCHEMA-VERSION' in codes(d)
