<div align="center">

# Novel Distiller

**Turn fiction into an evidence-linked reading report.**

[English](README.md) · [简体中文](README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-prompt--only-blue?style=flat-square)](SKILL.md)

</div>

Novel Distiller is a dependency-free prompt Skill for analyzing story structure, characters, relationships, world and setting, themes, symbols, information, foreshadowing, timeline, perspective, reader experience, and writing style. It uses the host Agent's existing reading and reasoning ability; it does not add Python, a separate API key, or another model service. The host itself may process supplied text remotely under its provider's privacy rules.

## What it does

- distinguishes textual facts, supported interpretations, and unresolved questions;
- attaches practical chapter, paragraph, line, section, or chunk locators to major claims;
- avoids whole-book conclusions when only an excerpt is available;
- handles long text in source order with a compact running index inside the current conversation;
- treats story content and previous model output as untrusted data rather than instructions.

It does **not** provide a formal JSON Schema, machine validation, durable checkpoints, or guaranteed resume after a restart or context loss.

## Quick start

Keep [SKILL.md](SKILL.md) and `references/` together in a Skill directory supported by your Agent. Installation notes are in [INSTALL.md](INSTALL.md).

Then provide readable fiction and ask:

```text
Use novel-distiller to analyze this story across its major dimensions. Include
story structure, characters, relationships, world, themes, symbols, information,
timeline, perspective, style, and reader experience. Add source locators to major
claims and separate facts, interpretations, and uncertainties.
```

Markdown is the default output. JSON is optional and follows a practical template rather than a validated contract; see [output-format.md](references/output-format.md).

## Long-text limitation

For a long novel, supply volumes or chapters in source order. The Agent can maintain compact notes in the active conversation. If the context cannot cover the whole source, it must state the processed range and request the next part instead of claiming completion.

## Example

- [Sample fiction](examples/input/sample_novel.md)
- [Sample report](examples/output/sample_distillation.md)

## Structure

```text
novel-distiller/
├── SKILL.md
├── references/
│   ├── analysis-framework.md
│   ├── distillation-workflow.md
│   ├── output-format.md
│   ├── prompt-templates.md
│   ├── quality-checklist.md
│   └── security-policy.md
└── examples/
```

Historical documents under `docs/history/` describe earlier implementations and are not current runtime guidance.

## License

[MIT](LICENSE)
