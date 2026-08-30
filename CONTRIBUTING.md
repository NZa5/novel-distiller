# Contributing

Contributions should preserve the default promise: the Skill is cross-agent, Markdown-based, and dependency-free.

## Contribution scope

Edit `SKILL.md`, `references/`, examples, or contract tests. Keep fields, enum values, section order, and status labels synchronized.

## Local checks

The default documentation path needs no setup. If Python is available, run:

```bash
pytest
python -m compileall -q tests scripts
git diff --check
```

Do not commit `.env`, API keys, caches, `__pycache__`, generated output, or temporary scripts. Add examples only when they contain fictional/non-sensitive data and parse cleanly.

## Documentation rules

Use repository-relative links that resolve from the file containing them. Avoid placeholder URLs, unverified version/accuracy claims, and language such as “唯一” or “production-ready” unless demonstrably supported.

## Pull requests

Explain the user-visible behavior, list files changed, include test output, and call out any schema or enum changes. Keep Markdown and JSON examples aligned. Use focused commits and the MIT license terms in [LICENSE](LICENSE).
