# Contributing

Contributions should preserve the default promise: the Skill is cross-agent, Markdown-based, and dependency-free.

## Two contribution areas

1. **Skill/docs:** edit `SKILL.md`, `references/`, examples, or contract tests. Keep fields, enum values, section order, and status labels synchronized.
2. **Optional tooling:** edit `optional-tooling/python/novel_distiller/` and its tests. Keep it clearly optional; never make its Python/provider dependencies part of the Skill instructions.

## Local checks

The default documentation path needs no setup. If Python is available, run:

```bash
pytest
python -m compileall -q optional-tooling/python/novel_distiller tests scripts
 git diff --check
```

Do not commit `.env`, API keys, caches, `__pycache__`, generated output, or temporary scripts. Add examples only when they contain fictional/non-sensitive data and parse cleanly.

## Documentation rules

Use repository-relative links that resolve from the file containing them. Avoid placeholder URLs, unverified version/accuracy claims, and language such as “唯一” or “production-ready” unless demonstrably supported. Describe `optional-tooling/python/novel_distiller/` as optional tooling.

## Pull requests

Explain the user-visible behavior, list files changed, include test output, and call out any schema or enum changes. Keep Markdown and JSON examples aligned. Use focused commits and the MIT license terms in [LICENSE](LICENSE).
