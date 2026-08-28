import zipfile
from pathlib import Path
import pytest
from novel_distiller.utils.safe_text import escape_markdown,QuoteBudget
from novel_distiller.utils.llm_client import RemotePolicy,validate_endpoint
def test_text():
 x=escape_markdown('<script>x</script> [x](javascript:go)\u202e');assert '<script>' not in x and 'javascript:' not in x and '\u202e' not in x
 b=QuoteBudget();b.add('x'*90,'p001');
 with pytest.raises(ValueError):b.add('x'*91,'p002')
def test_remote():
 with pytest.raises(ValueError,match='ND-REMOTE-DISALLOWED'):validate_endpoint('https://api.openai.com/v1',RemotePolicy())
