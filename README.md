# Novel Distiller

Novel Distiller is a cross-agent Skill for evidence-based analysis of fiction. Its default runtime is `SKILL.md` plus the Markdown references: an Agent reads the supplied text and returns a unified Markdown and/or JSON distillation. **No API key, environment variable, Python, pip, package, or network service is required.**

## What it covers

Characters, plot and structure, relationships, foreshadowing, timeline, and writing style. Long inputs are chunked, indexed, merged, and rechecked. Facts, inferences, and uncertainties are explicitly labeled with confidence and source locators.

## Install and use

See [INSTALL.md](INSTALL.md) for Pi, Claude Code, Codex, and generic Agent installation. For a quick run, read [QUICKSTART.md](QUICKSTART.md), give the Agent `SKILL.md`, and attach a TXT, EPUB, pasted passage, or readable attachment:

> 蒸馏这份小说，覆盖人物、情节、关系、伏笔、时间线和风格；输出 Markdown 和严格 JSON，并标注事实、推断、不确定性。

See the [sample input](examples/input/sample_novel.md), [sample Markdown](examples/output/sample_distillation.md), and [sample JSON](examples/output/sample_distillation.json).

## Repository map

- `SKILL.md` — only default runtime entry point.
- `references/` — workflow, analysis framework, canonical output schema, quality checklist, and prompt templates.
- `examples/` — input and output examples.
- `novel_distiller/` — optional historical Python tooling, not a Skill dependency.
- `tests/` — contract and optional-tool regression tests.

## Output contract

The canonical output has stable IDs and the same fields/statuses in Markdown and JSON. JSON follows [the output schema](references/output-schema.md); quality gates are in [the checklist](references/quality-checklist.md). Empty dimensions are retained and limitations are stated. The Skill makes no unsupported accuracy, completeness, or processing-time promises.

## Optional tooling

The Python package and CLI remain available for users who explicitly want local tooling. They are optional and may have their own dependencies; they are not the installation or execution path for this Skill. Consult `requirements.txt` and `setup.py` only for that separate use case.

## Development

```bash
pytest
python -m compileall -q novel_distiller tests
 git diff --check
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under [MIT](LICENSE).
