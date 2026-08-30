<div align="center">

# Novel Distiller

**Turn long-form fiction into an evidence-linked story map your Agent can reason over.**

[English](README.md) · [简体中文](README.zh-CN.md)

[![GitHub stars](https://img.shields.io/github/stars/NZa5/novel-distiller?style=flat-square&logo=github)](https://github.com/NZa5/novel-distiller/stargazers)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-cross--agent-blue?style=flat-square)](SKILL.md)
[![Default dependencies](https://img.shields.io/badge/default%20dependencies-none-brightgreen?style=flat-square)](SKILL.md)

A cross-agent Skill for distilling novels and fiction into characters, plots, relationships, foreshadowing, timelines, structure, and writing-style analysis. It runs through the host Agent's own reading and reasoning capabilities: **No API key, No Python, no package installation, and no external model service are required by the default workflow.**

[Quick Start](#quick-start) · [Example](#example-output) · [Installation](INSTALL.md) · [Skill Instructions](SKILL.md) · [Output Schema](references/output-schema.md)

</div>

## Why Novel Distiller?

A summary tells you what happened. Novel Distiller builds a reusable, traceable model of **who did what, why it mattered, when it happened, how clues paid off, and how the story was written**.

| Common problem | Novel Distiller's approach |
|---|---|
| Long novels exceed a single context window | Split by volume, chapter, scene, or paragraph; build intermediate indexes; merge and recheck globally |
| Names, aliases, and identities drift across chapters | Maintain stable character IDs, alias mappings, and unresolved conflicts |
| Model interpretations are presented as facts | Label every analytical record as `fact`, `inference`, or `uncertain` with confidence |
| Plot summaries lose their textual basis | Attach chapter, paragraph, line, or chunk locators to substantive claims |
| Foreshadowing is easy to overclaim | Separate planted, possible, revealed, unresolved, and non-applicable states |
| Different Agents produce incompatible reports | Use one canonical Markdown/JSON contract with stable IDs and enums |

## Features

| Dimension | What the Skill extracts |
|---|---|
| **Characters** | Names, aliases, roles, goals, traits, arcs, and important appearances |
| **Plot & structure** | Main plots, subplots, conflicts, stakes, causality, turning points, and resolution state |
| **Relationships** | Direction, type, strength, evolution, asymmetry, and supporting evidence |
| **Foreshadowing** | Setups, possible or confirmed payoffs, unresolved clues, and evidence at both ends |
| **Timeline** | Event order, explicit and relative time, duration, flashbacks, flash-forwards, and contradictions |
| **Writing style** | Viewpoint, tense, voice, pacing, dialogue, syntax, vocabulary, imagery, rhetoric, and structure |

Additional safeguards include:

- evidence locators for analytical claims;
- explicit confidence and uncertainty labels;
- long-text chunking with cross-chapter state;
- alias merging without silently deleting conflicts;
- aligned Markdown and strict JSON output;
- coverage, consistency, and limitation checks before delivery.

## How It Works

```text
Novel / excerpt / readable attachment
                  │
                  ▼
       Scope and source mapping
                  │
                  ▼
      Chapter-aware text chunking
                  │
                  ▼
 Character · event · clue · time · style indexes
                  │
                  ▼
       Global merge and source recheck
                  │
                  ▼
 Characters · plots · relationships · foreshadowing
          · timeline · writing style
                  │
                  ▼
      Quality gate → Markdown and/or JSON
```

For short inputs, the Agent can complete this in one pass. For long inputs, it preserves stable IDs and unresolved state across chunks before producing the global synthesis. See the full [distillation workflow](references/distillation-workflow.md).

## Quick Start

### 1. Install the Skill

There is no build step. Keep `SKILL.md` and `references/` together in a directory your Agent can read.

For Pi, one option is:

```bash
mkdir -p ~/.pi/agent/skills
git clone https://github.com/NZa5/novel-distiller.git ~/.pi/agent/skills/novel-distiller
```

Restart or reload Pi after cloning so it discovers the new Skill. For Claude Code, Codex, and generic Agent setups, follow [INSTALL.md](INSTALL.md).

### 2. Provide the story

Attach or point the Agent to one of the following:

- pasted fiction;
- a TXT file;
- an EPUB the host Agent can read;
- another readable text attachment;
- an excerpt or selected chapter range.

### 3. Ask for a distillation

```text
Use the novel-distiller Skill to analyze this novel.
Cover characters, plot, relationships, foreshadowing, timeline, and writing style.
For every major claim, include a source locator and label it as fact, inference,
or uncertain. Return a Markdown report and strict JSON with matching IDs.
```

For focused or staged requests, see the ready-to-use [prompt templates](references/prompt-templates.md).

## Example Output

Given the short fictional sample [《雨站》](examples/input/sample_novel.md), the Skill produces records such as:

```markdown
## Foreshadowing
- **fore-001** Blue button and crescent motif — `possibly_revealed`;
  `inference`, `medium`; evidence: ch-001 ¶1, ch-002 ¶1.

## Uncertainties & contradictions
- **uncertain-001** Lin Yao's current whereabouts are unknown;
  `uncertain`, `high`; evidence: ch-003 ¶1.
```

Explore the complete examples:

- [Sample input](examples/input/sample_novel.md)
- [Markdown distillation](examples/output/sample_distillation.md)
- [JSON distillation](examples/output/sample_distillation.json)

## Supported Inputs and Scope

| Input | Default behavior |
|---|---|
| Pasted text | Analyze directly and preserve paragraph-level locators where possible |
| TXT | Detect chapter headings and preserve source order |
| EPUB | Use the host Agent's attachment reader; never install a parser by default |
| Other readable attachments | Use the Agent's native reader and report unreadable sections |
| Excerpt or partial novel | Set scope to `excerpt` or `partial_text`; avoid whole-book claims |

Input support depends on the host Agent's ability to read the supplied attachment. When a format is unreadable, the Skill asks for TXT or pasted text instead of installing software.

## Output Contract

The canonical record contains:

```text
schema_version · metadata · summary · characters · plots
relationships · foreshadowing · timeline · style
uncertainties · quality
```

Every analytical item uses a stable ID, `claim_status`, `confidence`, and `evidence`. Markdown and JSON represent the same record; empty dimensions remain present, and limitations are stated explicitly.

- [Canonical output schema](references/output-schema.md)
- [Analysis definitions](references/analysis-framework.md)
- [Quality checklist](references/quality-checklist.md)

## Agent Compatibility

| Agent environment | Integration model |
|---|---|
| **Pi / pi-coding-agent** | Place the repository in a Pi skills directory and invoke it naturally |
| **Claude Code** | Keep the Skill in a readable project or configured skills directory and reference `SKILL.md` |
| **OpenAI Codex** | Add the folder to the project or configured skills location and instruct Codex to use `SKILL.md` |
| **Other Agents** | Use `SKILL.md` as a system/project instruction and preserve the adjacent `references/` directory |

The core uses portable Markdown instructions rather than a platform-specific SDK. Exact installation details are in [INSTALL.md](INSTALL.md).

## Repository Structure

```text
novel-distiller/
├── SKILL.md                    # Default runtime entry point
├── README.md                   # English documentation
├── README.zh-CN.md             # 简体中文文档
├── references/                 # Workflow, schema, prompts, and quality rules
├── examples/
│   ├── input/                  # Fictional sample input
│   └── output/                 # Matching Markdown and JSON output
└── tests/                      # Skill contract tests
```

## Documentation

| Document | Purpose |
|---|---|
| [SKILL.md](SKILL.md) | Runtime instructions and quality gate |
| [INSTALL.md](INSTALL.md) | Installation across supported Agent environments |
| [QUICKSTART.md](QUICKSTART.md) | Short usage walkthrough |
| [Distillation workflow](references/distillation-workflow.md) | Long-text staging, indexing, merging, and rechecking |
| [Analysis framework](references/analysis-framework.md) | Definitions for all analysis dimensions |
| [Output schema](references/output-schema.md) | Canonical Markdown and JSON contract |
| [Prompt templates](references/prompt-templates.md) | Reusable full and focused prompts |
| [Quality checklist](references/quality-checklist.md) | Pre-delivery validation rules |
| [Contributing guide](CONTRIBUTING.md) | Contribution and test requirements |

## Roadmap

The current priority is improving the portable Skill contract rather than adding mandatory runtime dependencies. Useful future contributions include broader fixture coverage, cross-Agent installation verification, multilingual output examples, and carefully reviewed analysis rubrics.

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing schema or enum changes.

## Contributing

Issues and pull requests are welcome. Please preserve the central promise: the default Skill remains cross-agent, evidence-first, and dependency-free. Keep examples fictional or non-sensitive, and keep Markdown and JSON records aligned.

## License

Novel Distiller is available under the [MIT License](LICENSE).

## Acknowledgements

The project draws on common Agent Skill patterns: a small runtime entry point, progressive disclosure through references, stable structured output, and explicit quality checks. Thanks to the open-source Agent ecosystem for making these patterns easy to study and improve.
