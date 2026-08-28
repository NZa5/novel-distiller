#!/usr/bin/env python3
"""Enforce the stricter coverage floor for deterministic safety surfaces."""
import json
import sys
from pathlib import Path

TARGETS = ("loaders/", "exporters/", "utils/prompt_safety.py", "utils/safe_text.py", "__main__.py")

def main(path: str) -> int:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    files = data.get("files", {})
    selected = [v for k, v in files.items() if any(k.replace('\\', '/').endswith(t) or t in k.replace('\\', '/') for t in TARGETS)]
    statements = sum(int(v.get("num_statements", 0)) for v in selected)
    covered = sum(int(v.get("covered_lines", 0)) for v in selected)
    ratio = covered / statements if statements else 0
    if ratio < 0.80:
        print(f"coverage below 80% for safety surfaces: {ratio:.1%}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
