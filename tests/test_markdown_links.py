import re
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_tracked_markdown_links_resolve():
    for path in ROOT.rglob('*.md'):
        if any(part in {'.git','.worktrees'} for part in path.parts): continue
        text=path.read_text(encoding='utf-8')
        for target in re.findall(r'!?\[[^]]*\]\(([^)#]+)',text):
            if re.match(r'^[a-z][a-z0-9+.-]*:',target,re.I) or target.startswith('#'): continue
            assert (path.parent/target).exists(), f'{path}: {target}'
