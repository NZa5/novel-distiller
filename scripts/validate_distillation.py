from dataclasses import dataclass
from pathlib import Path
import argparse,json,re
from jsonschema import Draft202012Validator
ROOT=Path(__file__).parents[1]
@dataclass(frozen=True)
class ValidationIssue: code:str; path:str; message:str
def schema_for(v):
 names={'1.0':'novel-distiller-1.0.schema.json','1.0.0':'novel-distiller-1.0.schema.json','2.0.0':'novel-distiller-2.0.schema.json'}
 if v not in names: raise ValueError('ND-SCHEMA-VERSION')
 return json.loads((ROOT/'references/schemas'/names[v]).read_text('utf8'))
def records(d):
 for key in ['characters','plots','relationships','foreshadowing','timeline','style','uncertainties']:
  for x in d.get(key,[]): yield key,x
def evidences(x):
 for e in x.get('evidence',[]): yield e
 for v in x.values():
  if isinstance(v,dict) and 'evidence' in v:
   yield from v['evidence']
  elif isinstance(v,list):
   for a in v:
    if isinstance(a,dict) and 'evidence' in a: yield from a['evidence']
def validate_document(d,source_manifest=None):
 out=[]
 try: schema=schema_for(d.get('schema_version',''))
 except ValueError: return [ValidationIssue('ND-SCHEMA-VERSION','/schema_version','unsupported schema major version')]
 for e in Draft202012Validator(schema).iter_errors(d): out.append(ValidationIssue('ND-SCHEMA-INVALID','/'+('/'.join(map(str,e.absolute_path))),'document violates schema'))
 ids={}; chars={x.get('id') for x in d.get('characters',[])}
 for key,x in records(d):
  i=x.get('id');
  if i in ids: out.append(ValidationIssue('ND-ID-DUPLICATE',f'/{key}','analytical IDs must be globally unique'))
  ids[i]=key
 for i,x in enumerate(d.get('relationships',[])):
  for f in ['source_character_id','target_character_id']:
   if x.get(f) not in chars: out.append(ValidationIssue('ND-REF-DANGLING',f'/relationships/{i}/{f}','character reference does not resolve'))
  if x.get('source_character_id')==x.get('target_character_id'): out.append(ValidationIssue('ND-REF-SELF',f'/relationships/{i}','relationship endpoints must differ'))
 for key,x in records(d):
  refs=[]
  if key in ('plots','timeline'): refs+=x.get('participants',[])
  if key=='uncertainties': refs+=x.get('related_ids',[])
  for ref in refs:
   if ref not in ids: out.append(ValidationIssue('ND-REF-DANGLING',f'/{key}','record reference does not resolve'))
 quotes=[]; spans=set()
 for key,x in records(d):
  for e in evidences(x):
   q=e.get('quote'); loc=e.get('locator',{}).get('value',''); source=e.get('source_id'); chapter=e.get('chapter_id')
   if q:
    quotes.append(q); text=''
    try:
     parts=source_manifest['sources'][source]['chapters'][chapter]['paragraphs']; a,b=(loc.split('-',1)+[loc])[:2]; nums=range(int(a[1:]),int(b[1:])+1); text='\n'.join(parts[f'p{n:03d}'] for n in nums)
    except Exception: pass
    if text and ' '.join(q.split()) not in ' '.join(text.split()): out.append(ValidationIssue('ND-QUOTE-MISMATCH',f'/{key}','quote does not match located source'))
    k=(source,chapter,loc)
    if k in spans: out.append(ValidationIssue('ND-QUOTE-OVERLAP',f'/{key}','quoted source spans overlap'))
    spans.add(k)
 if sum(map(len,quotes))>600: out.append(ValidationIssue('ND-QUOTE-BUDGET','/','aggregate quote budget exceeded'))
 return out
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('document',type=Path);p.add_argument('--source-manifest',type=Path);a=p.parse_args(argv)
 try:d=json.loads(a.document.read_text('utf8'));m=json.loads(a.source_manifest.read_text('utf8')) if a.source_manifest else None
 except Exception: print(f'ND-SCHEMA-INVALID {a.document.name}: unreadable input');return 1
 issues=validate_document(d,m)
 for x in issues: print(f'{x.code} {x.path}: {x.message}')
 return bool(issues)
if __name__=='__main__': raise SystemExit(main())
