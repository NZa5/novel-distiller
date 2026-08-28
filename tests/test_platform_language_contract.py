import re,json
from pathlib import Path
R=Path(__file__).parents[1]
def test_description_and_docs():
 d=re.search(r'^description:\s*(.+)$',(R/'SKILL.md').read_text('utf8'),re.M).group(1);assert len(d)<1024
 for x in ['novel','characters','小说蒸馏','人物关系','伏笔','时间线','文风','续写','翻译','proofreading','EPUB parser','code analysis']:assert x.lower() in d.lower()
 t=(R/'INSTALL.md').read_text('utf8')+(R/'INSTALL.zh-CN.md').read_text('utf8')
 for x in ['~/.pi/agent/skills/novel-distiller','/skill:novel-distiller','~/.claude/skills/novel-distiller','/novel-distiller','$HOME/.agents/skills/novel-distiller','$novel-distiller','verified','documented','expected']:assert x in t
def test_cases():
 x=json.loads((R/'tests/fixtures/trigger_cases.json').read_text('utf8'));assert len(x['positive'])>=10 and len(x['negative'])>=10
