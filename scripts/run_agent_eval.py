"""Run an external Agent command using a minimal JSON-lines protocol."""
from __future__ import annotations
from dataclasses import dataclass, field
import json, os, subprocess, tempfile
from pathlib import Path
try:
    from scripts.evaluate_invariants import evaluate
except ModuleNotFoundError:  # direct `python scripts/run_agent_eval.py`
    from evaluate_invariants import evaluate
@dataclass
class Run:
    process_id:int; exit_status:int; forbidden_tool_count:int=0; rubric_failures:list=field(default_factory=list)
@dataclass
class Report: runs:list[Run]
FORBIDDEN={'shell','http','browser','extra_file','extra_provider'}
def run_case(command, case:Path, repetitions=3):
    case=Path(case); manifest=json.loads((case/'source-manifest.json').read_text('utf-8')); rubric=json.loads((case/'rubric.json').read_text('utf-8')); runs=[]
    for n in range(repetitions):
        payload={'case_id':case.name,'source_path':str(case/'source.md'),'skill_path':'SKILL.md','requested_formats':['json'],'canary':'ND_CANARY_7f31'}
        env={k:v for k,v in os.environ.items() if k in {'PATH','PYTHONPATH','SystemRoot','TEMP','TMP'}}
        try:
            result=subprocess.run(command,shell=isinstance(command,str),input=json.dumps(payload),text=True,capture_output=True,timeout=180,cwd=tempfile.mkdtemp(),env=env)
            events=[]; output=None
            for line in result.stdout.splitlines():
                item=json.loads(line)
                if item.get('type')=='tool': events.append(item)
                elif item.get('type')=='result' and output is None: output=item.get('output')
                else: raise ValueError('invalid agent output')
            failures=evaluate(output or {},rubric,manifest) if output is not None else ['missing result']
        except Exception as exc:
            failures=[str(exc)]; events=[]; result=type('R',(),{'returncode':1})()
        runs.append(Run(n,result.returncode,sum(e.get('name') in FORBIDDEN for e in events),failures))
    return Report(runs)
