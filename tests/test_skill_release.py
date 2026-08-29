import importlib.util,zipfile
from pathlib import Path
R=Path(__file__).parents[1];s=importlib.util.spec_from_file_location('b',R/'scripts/build_skill_release.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
def test_release(tmp_path):
 a=tmp_path/'a.zip';c=tmp_path/'b.zip';assert b.build_release(R,a)==b.build_release(R,c) and a.read_bytes()==c.read_bytes()
 with zipfile.ZipFile(a) as z:n=z.namelist();assert 'novel-distiller/SKILL.md' in n and not any(x.endswith('.py') or '/tests/' in x or 'optional-tooling' in x for x in n)
