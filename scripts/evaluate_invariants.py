from dataclasses import dataclass
@dataclass(frozen=True)
class InvariantFailure: code:str; path:str; message:str
def values(d,path):
 xs=[d]
 for p in path.split('.'):
  ys=[]
  for x in xs:
   if p=='*' and isinstance(x,list):ys+=x
   elif isinstance(x,dict) and p in x:ys.append(x[p])
  xs=ys
 return xs
def evaluate(document,rubric,manifest):
 out=[]
 for kind in ('required','forbidden'):
  for i,r in enumerate(rubric.get(kind,[])):
   v=values(document,r['path']);ok=bool(v) if r['op']=='exists' else any(x==r.get('value') for x in v)
   if (kind=='required' and not ok) or (kind=='forbidden' and ok):out.append(InvariantFailure('ND-RUBRIC',r['path'],'invariant failed'))
 return out
