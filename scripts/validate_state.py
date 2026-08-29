from dataclasses import dataclass
import copy,hashlib,json
@dataclass(frozen=True)
class StateIssue: code:str; path:str; message:str
def canonical_state_digest(s):
 d=copy.deepcopy(s);d['checkpoint']['state_digest']='';return hashlib.sha256(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def validate_state(s):
 out=[]
 if s.get('run',{}).get('status')=='stale':out.append(StateIssue('ND-STATE-STALE','/run/status','source identity changed'))
 if s.get('checkpoint',{}).get('state_digest')!=canonical_state_digest(s):out.append(StateIssue('ND-STATE-DIGEST','/checkpoint/state_digest','digest mismatch'))
 chunks=s.get('segmentation',{}).get('chunks',[]); committed={x for b in s.get('batches',[]) if b['status']=='committed' for x in b['chunk_ids']}
 derived=sum(c['id'] in committed and c['status']=='indexed' for c in chunks)
 if s.get('progress',{}).get('chunks_committed')!=derived:out.append(StateIssue('ND-STATE-PROGRESS','/progress','progress is not derived'))
 if any(c['status'] in ('failed','unreadable') for c in chunks) and not s.get('degradation',{}).get('active'):out.append(StateIssue('ND-STATE-DEGRADED','/degradation','failure must propagate'))
 return out
def canonical_projection(s):return {k:s[k] for k in ['source','segmentation','identity_registry','deduplication','progress','degradation']}
def recoverable_revision(states,source_fingerprint,segmentation_fingerprint):
 valid=[s for s in states if not validate_state(s) and s['checkpoint']['status']=='committed' and s['source']['normalized_fingerprint']['value']==source_fingerprint and s['segmentation']['fingerprint']==segmentation_fingerprint]
 if not valid:raise ValueError('ND-STATE-STALE')
 return copy.deepcopy(max(valid,key=lambda s:s['run']['state_revision']))
