from __future__ import annotations
import argparse, json, sys
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class InvariantFailure:
    code: str
    path: str
    message: str

def values(document, path):
    current = [document]
    for part in path.strip('.').split('.') if path else []:
        nxt=[]
        for value in current:
            if part == '*' and isinstance(value, list): nxt.extend(value)
            elif isinstance(value, dict) and part in value: nxt.append(value[part])
        current=nxt
    return current

def _items(actual):
    if len(actual) == 1 and isinstance(actual[0], list):
        return actual[0]
    return actual

def _check(op, actual, rule):
    actual = _items(actual)
    expected=rule.get('value')
    if op == 'exists': return bool(actual)
    if op == 'equals': return any(v == expected for v in actual)
    if op in ('not_equals','forbidden_equals'): return bool(actual) and all(v != expected for v in actual)
    if op == 'contains': return any(expected in v for v in actual if isinstance(v,(str,list,dict)))
    if op == 'not_contains': return all(expected not in v for v in actual if isinstance(v,(str,list,dict)))
    if op == 'count': return len(actual) == expected
    if op == 'min_count': return len(actual) >= expected
    if op == 'all_in': return bool(actual) and all(v in expected for v in actual)
    if op == 'reference_exists': return bool(actual)
    if op == 'zero_tool_events': return len(actual) == 0
    raise ValueError(f'unknown invariant operation: {op}')

def evaluate(document:dict, rubric:dict, manifest:dict)->list[InvariantFailure]:
    failures=[]
    for group in ('required','forbidden','relations'):
        for rule in rubric.get(group,[]):
            path=rule.get('path',''); ok=_check(rule.get('op','exists'), values(document,path), rule)
            should_fail = (group in ('required','relations') and not ok) or (group == 'forbidden' and ok)
            if should_fail: failures.append(InvariantFailure(rule.get('code','ND-RUBRIC'), path, 'invariant failed'))
    return failures

def main(argv=None):
    parser=argparse.ArgumentParser(description='Evaluate checked-in complex-fiction fixtures.')
    parser.add_argument('directory', nargs='?', default='tests/fixtures/agent', type=Path)
    args=parser.parse_args(argv); total=0
    for case in sorted(args.directory.iterdir()):
        if not case.is_dir(): continue
        try:
            output=json.loads((case/'valid-output.json').read_text(encoding='utf-8'))
            rubric=json.loads((case/'rubric.json').read_text(encoding='utf-8'))
            manifest=json.loads((case/'source-manifest.json').read_text(encoding='utf-8'))
            failures=evaluate(output,rubric,manifest)
        except Exception as exc:
            print(f'{case.name}: ERROR {type(exc).__name__}: {exc}'); total += 1; continue
        print(f'{case.name}: {len(failures)} failures')
        for failure in failures: print(f'  {failure.code}: {failure.path}')
        total += len(failures)
    return 1 if total else 0

if __name__ == '__main__': raise SystemExit(main())
