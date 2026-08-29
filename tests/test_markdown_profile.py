import importlib.util,json
from pathlib import Path
R=Path(__file__).parents[1];s=importlib.util.spec_from_file_location('m',R/'scripts/canonical_markdown.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);D=json.loads((R/'examples/output/sample_distillation.json').read_text('utf8'))
def test_roundtrip():
 x=m.render_markdown(D); assert m.parse_markdown(x)==D; assert x==(R/'examples/output/sample_distillation.md').read_text('utf8')
def test_safe():
 d=json.loads(json.dumps(D));d['characters'][0]['name']='<img src=x> [go](javascript:alert(1))\u202e';x=m.render_markdown(d);assert '<img' not in x and 'javascript:' not in x and '\u202e' not in x
