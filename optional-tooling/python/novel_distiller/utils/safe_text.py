"""Safe handling for source- and model-derived text."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from html import escape as html_escape

_BIDI = set("\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")
_URL = re.compile(r"(?i)(https?|javascript|file|data):")
_MD = re.compile(r"([\\`*_{}\[\]()#+.!|>~-])")

def sanitize_plain_text(value: str) -> str:
    return "".join(c for c in str(value) if (c in "\n\t" or ord(c) >= 0x20) and not (0x7f <= ord(c) <= 0x9f) and c not in _BIDI)

# Backward-compatible internal name.
sanitize_text = sanitize_plain_text

def deactivate_urls(value: str) -> str:
    return _URL.sub(lambda m: m.group(0).replace(":", "[colon]"), value)

def escape_markdown(value: str) -> str:
    return html_escape(_MD.sub(r"\\\1", deactivate_urls(sanitize_plain_text(value))), quote=False)

@dataclass
class QuoteBudget:
    max_quote: int = 90
    max_total: int = 600
    total: int = 0
    _locators: set[str] = field(default_factory=set)
    def add(self, quote: str, locator_key: str) -> None:
        if len(quote) > self.max_quote or self.total + len(quote) > self.max_total:
            raise ValueError("ND-QUOTE-BUDGET")
        if locator_key in self._locators:
            raise ValueError("ND-QUOTE-DUPLICATE")
        self._locators.add(locator_key)
        self.total += len(quote)
