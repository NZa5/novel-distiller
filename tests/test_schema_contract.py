import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator, ValidationError
ROOT=Path(__file__).parents[1]; SCHEMAS=ROOT/'references/schemas'; FIXTURES=ROOT/'tests/fixtures/schema'
def load(p): return json.loads(p.read_text('utf-8'))
@pytest.mark.parametrize('version',['1.0','2.0'])
def test_schema_is_valid_draft_2020_12(version): Draft202012Validator.check_schema(load(SCHEMAS/f'novel-distiller-{version}.schema.json'))
def test_v2_fixture_is_valid(): Draft202012Validator(load(SCHEMAS/'novel-distiller-2.0.schema.json')).validate(load(FIXTURES/'v2-valid.json'))
@pytest.mark.parametrize('path',sorted((FIXTURES/'invalid').glob('*.json')),ids=lambda p:p.stem)
def test_invalid_v2_mutations_are_rejected(path):
 with pytest.raises(ValidationError): Draft202012Validator(load(SCHEMAS/'novel-distiller-2.0.schema.json')).validate(load(path))
def test_versions_do_not_cross_validate():
 with pytest.raises(ValidationError): Draft202012Validator(load(SCHEMAS/'novel-distiller-2.0.schema.json')).validate(load(FIXTURES/'v1-valid.json'))
