# Novel Distiller Project Summary

## Current design

Novel Distiller is primarily a dependency-free, cross-agent Skill. `SKILL.md` is the sole default runtime entry point. It instructs an Agent to read fiction, segment long text, build evidence-backed intermediate indexes, analyze characters, plot, relationships, foreshadowing, timeline, and style, and emit consistent Markdown/JSON with fact, inference, and uncertainty labels.

## Repository areas

- `SKILL.md`: trigger, input protocol, workflow, output, and quality gate.
- `references/`: detailed workflow, framework, schema, checklist, and templates.
- `examples/`: fictional input and canonical output examples.
- `tests/`: contract tests plus tests for retained tooling.
- `novel_distiller/`: optional historical Python package/CLI; not required by the Skill.

## Scope and claims

The Skill works with text the host Agent can read: pasted text, TXT, EPUB, or attachments. Coverage depends on supplied/readable content. It makes no fixed accuracy, speed, maximum-size, or completeness claim. Partial input is labeled and unresolved questions remain explicit.

## Optional tooling

The Python package is retained for users who choose local programmatic processing. Its dependencies and provider configuration are separate from the default Skill and are documented only as optional tooling in [INSTALL.md](INSTALL.md) and [QUICKSTART.md](QUICKSTART.md).
