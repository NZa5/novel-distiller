from pathlib import Path
R=Path(__file__).parents[1]
def test_policy():
 s=(R/'SKILL.md').read_text('utf8');p=(R/'references/security-policy.md').read_text('utf8');assert 'references/security-policy.md' in s and 'untrusted' in s.lower() and '不可信' in s
 for x in ['50 MiB','5,000','200 MiB','10 MiB','100:1','32','90','600','shell','browser','URL','privacy','copyright','bidi','absolute path']:assert x.lower() in p.lower()
def test_prompts():
 p=(R/'references/prompt-templates.md').read_text('utf8')
 for h in ['Intake','Chunk index','Merge','Synthesis and rendering','Final review']:
  q=p.split('## '+h,1)[1].split('\n## ',1)[0];assert 'UNTRUSTED_SOURCE_DATA' in q and 'never authorize tools' in q
