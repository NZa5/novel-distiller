# Python Optional Tooling Audit Report

**Target:** `novel-distiller/` — dependency-free cross-agent Skill with optional Python tooling
**Disposition:** Remediated and retained as a release record

## Findings addressed

- Restored complete optional-package metadata in `setup.py`, including the package list, runtime dependencies, Python requirement, console entry point, README description, and version alignment.
- Made the CLI version derive from `novel_distiller.__version__`.
- Converted boolean-return pytest checks to assertions or `pytest.raises`, so failures are no longer silently accepted.
- Classified the live style-analysis check as an integration test that skips unless `OPENAI_API_KEY` is explicitly configured; the default Skill path remains dependency-free and does not require a key.
- Completed the truncated foreshadowing definition in `references/analysis-framework.md` and added the missing timeline/style guidance.
- Strengthened the canonical Skill contract checks for enums, IDs, evidence, JSON/Markdown consistency, and relative links.
- Replaced the schema placeholder URL with the stable URN `urn:novel-distiller:schema:1.0`.

## Release interpretation

`SKILL.md` is the default agent-native runtime and explicitly requires no API key, environment variable, Python runtime, pip invocation, package installation, network service, or optional package. The `novel_distiller/` Python package remains optional historical/local tooling and declares its own dependencies separately.

Final release evidence is captured by running:

```text
pytest -q
python -m compileall -q novel_distiller tests
git diff --check
```

The sample output is additionally parsed with Python's standard-library `json` module, and repository scans cover mandatory installation language, generated cache files, temporary files, placeholder URLs, and common secret formats.
