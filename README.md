# Novel Distiller

English | [简体中文](README.zh-CN.md)

<p align="center">
  <strong>Evidence-backed author style analysis and writing for Chinese fiction.</strong>
  <br />
  Turn a supplied novel corpus into a reusable author profile, then use it to draft, compare, revise, and blind-test new fiction.
</p>

<p align="center">
  <a href="https://github.com/NZa5/novel-distiller/stargazers"><img src="https://img.shields.io/github/stars/NZa5/novel-distiller?style=flat-square" alt="GitHub stars" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/NZa5/novel-distiller?style=flat-square" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/Agent-Skill-111111?style=flat-square" alt="Agent Skill" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" />
</p>

Novel Distiller is an Agent Skill for analyzing Chinese novels supplied by the user. It separates stable author traits from scene-conditioned variation, character voice, and one-off choices; connects every major rule to source evidence; and compresses the result into a writing packet that can guide long-form generation without drifting into a generic voice.

## Why Novel Distiller

Recognizable style is more than favorite words or average sentence length. Novel Distiller models the decisions behind the prose:

- where the narrator stands and what the narrator chooses to reveal;
- how sentences, paragraphs, scenes, and chapters move;
- how characters are introduced, gain agency, change, and speak differently under different relationships and pressure;
- how events form causal chains, conflicts escalate, and time and revelations are controlled;
- how setting, social systems, motifs, genre expectations, and reader knowledge shape the story;
- how emotion is carried through action, silence, sensation, judgment, or irony;
- how stable habits differ from genre, period, scene, and character effects.

The result is not a bag of adjectives. It is an evidence map, a scene-mode system, character voice cards, measurable ranges, drift corrections, and a compact writing packet.

## What It Does

| Capability | Result |
|---|---|
| Author distillation | Passage-, work-, period-, or author-level profile with evidence and confidence |
| Deep narrative analysis | Language, discourse, character, relationship, event, causality, plot, setting, theme, genre, and reader-contract analysis |
| Conditional style modeling | Separate rules for narration, dialogue, action, reflection, openings, endings, and other real corpus modes |
| Long-corpus processing | Reproducible chunks with source hashes, paragraph ranges, character ranges, metrics, and searchable text |
| Author contrast | Ranked differences between the target author and user-supplied comparison authors |
| Profile-guided writing | Scene briefs, matched exemplars, character voice cards, and per-scene reinjection |
| Draft review | Ranked surface deviations plus close reading of narrative, structural, emotional, and dialogue choices |
| Blind evaluation | Seeded anonymous test packs, hidden answer keys, response records, and reader-result summaries |

## Quick Start

### Install with the Agent Skills CLI

```bash
npx skills add NZa5/novel-distiller -g -a codex
```

The repository exposes one skill: `novel-distiller`. To inspect it before installation:

```bash
npx skills add NZa5/novel-distiller --list
```

### Install manually for Codex

```powershell
git clone https://github.com/NZa5/novel-distiller.git "$env:USERPROFILE\.codex\skills\novel-distiller"
```

Reload Codex after installation.

### First request

```text
Use $novel-distiller to analyze these Chinese novel files and build an author profile that can directly guide new fiction.
Separate stable traits, scene-conditioned traits, character voices, variable traits, and uncertain findings. Cite source locations for every major rule.
```

Then write from the profile:

```text
Use $novel-distiller and the author profile to write Chapter 1 from this outline.
Match the scene mode and character voices, run one style comparison and targeted revision, and return only the final fiction.
```

Or review an existing draft:

```text
Use $novel-distiller to compare this draft with the author profile and matched source passages.
Fix the three deviations that most strongly reveal a different writer while preserving all story facts.
```

## Workflow

```text
Supplied corpus
    │
    ├─ inventory and normalize
    ├─ split by work, scene, viewpoint, and character
    ├─ measure surface features
    ├─ index long texts and preserve evidence locators
    ├─ test stable rules against holdouts and comparison authors
    ▼
Evidence-backed author profile
    │
    ├─ master voice
    ├─ scene-mode matrix
    ├─ character voice cards
    ├─ signature moves and measurable ranges
    └─ compact writing packet
    ▼
Scene brief → draft → matched-source comparison → targeted revision → blind test
```

## Prepare the Corpus

Use `.txt` or `.md` files. Complete chapters from the same creative period are the strongest starting point; include different scene types rather than only adjacent passages.

```text
corpus/
├── target-author/
│   ├── novel-a.txt
│   └── novel-b.txt
├── comparison-authors/       # optional, supplied by the user
│   ├── author-b.txt
│   └── author-c.txt
└── holdout/                  # excluded from profile construction
    └── unseen-scenes.txt
```

The helper scripts accept UTF-8, UTF-16 with BOM, GB18030, and Big5. They use only the Python standard library.

## Deterministic Tools

The Agent performs the semantic analysis. The scripts make preprocessing, measurement, retrieval, comparison, and evaluation reproducible.

### 1. Surface metrics

```powershell
python .\scripts\analyze_style.py .\corpus\target-author --format markdown --output .\work\style-metrics.md
```

Add `--reflow-hard-wrap` for fixed-width eBook line wrapping and `--strip-annotations` for a separate trailing 注释/注釋 section.

### 2. Long-corpus index and evidence retrieval

```powershell
python .\scripts\corpus_index.py build .\corpus\target-author --output .\work\corpus-index.jsonl
python .\scripts\corpus_index.py search .\work\corpus-index.jsonl --query-file .\draft.txt --top 4 --include-text
```

Each indexed chunk stores its text, source file, SHA-256, paragraph range, content-character range, and surface metrics.

### 3. Target-author contrast

```powershell
python .\scripts\compare_style.py contrast --target .\corpus\target-author --control .\corpus\comparison-authors --output .\work\author-contrast.md
```

The report ranks sentence, paragraph, dialogue, punctuation, and function-word differences. These are candidates for close reading—not a style similarity percentage.

### 4. Draft comparison

```powershell
python .\scripts\compare_style.py draft --reference .\matched-source --draft .\draft.txt --output .\work\draft-comparison.md
```

Use source passages matched by viewpoint, scene function, emotional pressure, relationship stage, and chapter position.

### 5. Blind evaluation

```powershell
python .\scripts\blind_style_test.py prepare --original .\corpus\holdout --generated .\drafts --output-dir .\blind-test --seed 20260830
python .\scripts\blind_style_test.py score --key .\blind-test\blind-key.json --responses .\blind-test\blind-responses.csv --output .\blind-test\blind-score.md
```

Give `blind-pack.md` and the response sheet to readers while keeping `blind-key.json` hidden. The score report records how often generated passages were judged original, whether readers could still recognize real originals, overall distinguishing accuracy, confidence, and written reasons.

## Profile Design

Every major rule records:

1. scope and applicable scene conditions;
2. observable phenomenon;
3. writing mechanism and reader effect;
4. source chunk IDs and locators;
5. counterexamples and their explanation;
6. comparison-author evidence when available;
7. confidence: high, medium, or low.

Findings remain separated as **stable**, **conditional**, **variable**, or **uncertain**. A single excerpt produces a passage profile; one novel supports a work-level profile; author-level claims require separated evidence across works.

## Project Structure

```text
novel-distiller/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── sampling-and-analysis.md
│   ├── analysis-dimensions.md
│   ├── author-profile.md
│   ├── writing-engine.md
│   └── style-review.md
├── scripts/
│   ├── analyze_style.py
│   ├── corpus_index.py
│   ├── compare_style.py
│   └── blind_style_test.py
└── tests/
```

`SKILL.md` is the runtime entry point. The reference files contain the detailed sampling, analysis-dimension, profile, writing, and review procedures.

## Development

Run the complete test suite:

```powershell
python -B -m unittest discover -s tests
```

The suite covers Chinese encodings, eBook cleanup, metrics, chunk locators, retrieval, author contrast, draft drift detection, blind-test preparation and scoring, and the end-to-end CLI workflow.

## License

[MIT](LICENSE)
