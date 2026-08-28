from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, re
@dataclass(frozen=True)
class InvariantFailure:
    code:str; path:str; message:str
def values(document, path):
    current=[document]
    for part in path.strip('.').split('.') if path else []:
        nxt=[]
        for value in current:
            if part=='*' and isinstance(value,list): nxt.extend(value)
            elif isinstance(value,dict) and part in value: nxt.append(value[part])
        current=nxt
    return current
def _check(op, actual, rule):
    expected=rule.get('value')
    if op=='exists': return bool(actual)
    if op=='equals': return any(v==expected for v in actual)
    if op=='not_equals': return bool(actual) and all(v!=expected for v in actual)
    if op=='contains': return any(expected in v for v in actual if isinstance(v,(str,list,dict)))
    if op=='count': return len(actual)==expected
    if op=='all_in': return bool(actual) and all(v in expected for v in actual)
    if op=='reference_exists': return bool(actual)
    if op=='zero_tool_events': return len(actual)==0
    raise ValueError(f'unknown invariant operation: {op}')
def evaluate(document:dict,rubric:dict,manifest:dict)->list[InvariantFailure]:
    failures=[]
    for group in ('required','forbidden','relations'):
        for rule in rubric.get(group,[]):
            path=rule.get('path',''); op=rule.get('op','exists')
            try: ok=_check(op,values(document,path),rule)
            except ValueError: raise
            if (group=='required' and not ok) or (group!='required' and ok): failures.append(InvariantFailure(rule.get('code','ND-RUBRIC'),path,'invariant failed'))
    return failures
