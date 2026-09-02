# Novel Distiller

English | [简体中文](README.zh-CN.md)

<p align="center">
  <strong>Evidence-backed author analysis for user-supplied Chinese fiction.</strong>
  <br />
  Turn supplied novels into a traceable, machine-readable author profile for a separate writing AI.
</p>

<p align="center">
  <a href="https://github.com/NZa5/novel-distiller/stargazers"><img src="https://img.shields.io/github/stars/NZa5/novel-distiller?style=flat-square" alt="GitHub stars" /></a>
  <a href="https://github.com/NZa5/novel-distiller/releases/latest"><img src="https://img.shields.io/github/v/release/NZa5/novel-distiller?style=flat-square" alt="Latest release" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/NZa5/novel-distiller?style=flat-square" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/Agent-Skill-111111?style=flat-square" alt="Agent Skill" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" />
</p>

Novel Distiller turns user-supplied Chinese novel text and metadata into a detailed author profile. It separates stable author choices from scene-conditioned variation, character voice, work-specific traits, and uncertain observations. Every major rule points back to short source evidence and reproducible locators.

## Why Novel Distiller

Recognizable prose is more than favorite words or average sentence length. Novel Distiller examines the decisions behind the text:

- narrator stance, viewpoint, knowledge, evaluation, and information release;
- sentence movement, paragraph function, diction, rhetoric, sound, and Chinese-specific language features;
- topic and reference chains, ellipsis, information structure, modality, evidentiality, negation, dialogue pragmatics, repair, humor, irony, and satire;
- character introduction, agency, emotion channels, relationship power, and distinct voices;
- event selection, causality, conflict, plot movement, time, transitions, and endings;
- multi-thread and chapter rhythm, viewpoint transitions, relationship-network evolution, foreshadowing/payoff, motif trajectories, and period drift;
- setting, social systems, motifs, themes, genre expectations, and reader knowledge;
- stable patterns, conditional patterns, variable choices, counterexamples, and evidence gaps.

The result is a reusable analysis interface rather than a list of vague adjectives.

## What It Produces

| Artifact | Purpose |
|---|---|
| `author-analysis.md` | Complete human-readable analysis, coverage matrix, limitations, and unresolved questions |
| `author-profile.json` | Canonical machine-readable profile with rules, conditions, confidence basis, scene modes, voices, and precedence |
| `evidence-map.jsonl` | One traceable evidence record per line with source hash, locator, short excerpt, and evidence role |
| `writing-packet.md` | Compact prompt-ready extraction for a separate writing AI |
| `corpus-manifest.json` | Reviewed work, sample, chapter, scene, viewpoint, character, and holdout metadata |
| `corpus-index.jsonl` | Hash-bound chunks and source locators used by evidence records |
| `sampling-ledger.json` | Deterministic analysis plan, progress, coverage, and scene-granularity status |
| `style-metrics.json` | Machine-readable surface measurements, source hashes, and input warnings |

The profile distinguishes passage-, work-, period-, and author-level claims. Author-level claims require separated evidence across multiple supplied works.

## Quick Start

### Install

This repository follows the portable Agent Skills folder format with `SKILL.md` as its entry point.

For a stable packaged version, open the [latest release](https://github.com/NZa5/novel-distiller/releases/latest), download `novel-distiller-skill-<version>.zip` and its `.sha256` file, verify the checksum, then extract the included `novel-distiller/` directory into the skills location configured by your Agent Skills-compatible host.

To follow the latest development version instead, clone the default branch:

```bash
git clone https://github.com/NZa5/novel-distiller.git /path/to/skills/novel-distiller
```

Keep `SKILL.md`, `scripts/`, and `references/` together. Reload or rescan skills according to the host's normal procedure. Release ZIP files are fixed snapshots and do not change when the default branch receives later commits.

### First request

```text
Use the novel-distiller skill to analyze these Chinese novels.
Build a complete evidence-backed analysis bundle, distinguish stable and conditional patterns from variable or uncertain findings, and save all reusable artifacts and their validation support files.
```

## Workflow

```text
User-supplied novels
        │
        ├─ corpus inventory and provenance
        ├─ reviewed work/sample/chapter/scene metadata manifest
        ├─ complete surface measurement
        ├─ deterministic first-round ledger across works and real scenes
        ├─ resumable progress with an index-integrity check
        ├─ multi-pass semantic close reading
        ├─ evidence cards, full counterexample search, and counts
        ├─ strict holdout challenge and optional control evidence
        ├─ saturation rounds or complete-corpus close reading
        └─ complete-bundle validation
        ▼
analysis artifacts + manifest + index + ledger + metrics
```

For long corpora, the skill measures all supplied files, close-reads a balanced first-round sample, then targets uncovered strata, contradictions, and counterexamples until the declared saturation condition is met. A complete-corpus mode is also available. The longest work and earliest batch must not silently dominate the profile.

## Prepare the Corpus

Use `.txt` or `.md` files. Complete chapters from the same creative period are the strongest starting point. Include different scene types, viewpoints, characters, and chapter positions rather than only adjacent passages.

If fiction is pasted directly into a conversation, the skill first saves it verbatim as UTF-8 under `work/corpus/`. This gives pasted text the same hashes, chunk IDs, and evidence locators as uploaded files.

```text
corpus/
├── target-author/
│   ├── novel-a.txt
│   └── novel-b.txt
├── comparison-authors/       # optional; supplied by the user
│   └── author-b.txt
└── holdout/                  # optional; excluded from rule construction
    └── unseen-scenes.txt
```

One excerpt supports a passage profile. One novel supports a work profile. Multiple works are required for an author-level profile.

The helper scripts accept UTF-8, UTF-16 with BOM, GB18030, and Big5 and use only the Python standard library.

## Deterministic Tools

The Agent performs semantic analysis. The scripts make preprocessing, measurement, evidence indexing, optional supplied-corpus contrast, and artifact validation reproducible.

### 1. Surface metrics

```bash
python scripts/analyze_style.py corpus/target-author --format markdown --output work/style-metrics.md
python scripts/analyze_style.py corpus/target-author --format json --output work/style-metrics.json
```

Each non-empty prepared line is treated as a normal Chinese-fiction paragraph. Paired ASCII straight double quotes on one line are recognized as dialogue alongside Chinese quote styles. Add `--reflow-hard-wrap` for fixed-width eBook line wrapping and `--strip-annotations` for a separate trailing 注释/注釋 section.

If suspected fixed-width wrapping or unpaired, reversed, or cross-line quote pairs are detected in any supported Chinese or ASCII quote style, the Markdown and JSON reports surface a warning instead of silently trusting distorted paragraph or dialogue metrics. Quote matching is line-bounded so one missing closing quote cannot consume later paragraphs.

### 2. Long-corpus index

```bash
python scripts/corpus_index.py manifest corpus/target-author --output work/corpus-manifest.json
# Review work_id and add supported sample/chapter/scene/viewpoint/character metadata.
python scripts/corpus_index.py build corpus/target-author --manifest work/corpus-manifest.json --output work/corpus-index.jsonl
python scripts/corpus_index.py sample work/corpus-index.jsonl --output work/sampling-ledger.json --seed 20260831
python scripts/corpus_index.py extend work/sampling-ledger.json --index work/corpus-index.jsonl --chunk-id CHUNK_ID --note "SAT03 targeted follow-up"
python scripts/corpus_index.py mark work/sampling-ledger.json --index work/corpus-index.jsonl --chunk-id CHUNK_ID --status analyzed
python scripts/corpus_index.py confirm-scene work/sampling-ledger.json --index work/corpus-index.jsonl --scene-group-id SCENE_GROUP_ID --note "Verified as one continuous long scene"
python scripts/corpus_index.py search work/corpus-index.jsonl --sample-id SAMPLE_ID --chapter-id CHAPTER_ID --scene-type confrontation --character 人物名 --exclude-holdout --top 4 --include-text
```

The manifest skeleton must be reviewed: files from the same novel need the same `work_id`; `sample_id` identifies a supplied excerpt, `chapter_id` identifies a chapter, and `scene_id` is reserved for an actual narrative scene. Unsupported metadata stays empty. Schema-v4 chunks store those identifiers plus period, viewpoint, character, relationship, emotion, chapter-position, holdout status, text, source SHA-256, preprocessing fingerprint, and locators. A chunk boundary is forced at every reviewed segment boundary, so one chunk cannot cross two annotated scenes. Chunks sharing a reviewed `scene_id` remain atomic across analysis and holdout; the ledger reports suspiciously coarse scene groups for review. Split a chapter-sized group, or use `confirm-scene` with a review note only when it is genuinely one continuous long scene. The ledger keeps pending/completed state across sessions and is bound to the exact index hash, so stale progress cannot be applied after an index change.

Omit `--budget` to derive a stronger first-round target from available chunks, works, scene groups, and semantic-strata breadth. A manual `--budget B` remains a target rather than a hard split point because a complete scene group is never divided; any overshoot is recorded in the ledger. Missing or coarse scene IDs are surfaced as limitations. First-round completion is not saturation: `extend` adds each targeted follow-up and its complete scene group to the bound ledger before reading, and later rounds record newly found rules, newly found counterexamples, and unresolved dimensions until the declared saturation or complete-corpus condition is satisfied.

### 3. Optional supplied-author contrast

```bash
python scripts/compare_style.py contrast --target corpus/target-author --control corpus/comparison-authors --target-manifest work/target-manifest.json --control-manifest work/control-manifest.json --output work/author-contrast.md
python scripts/corpus_index.py build corpus/comparison-authors --manifest work/control-manifest.json --output work/comparison-index.jsonl
```

The report first summarizes chunks within each work and then gives works equal weight. Splitting one novel across many chapter files therefore does not multiply its influence. Without manifests, each file is only a fallback work, which is valid only for a true one-file-per-work corpus. Ranked differences are close-reading candidates, not a style-similarity percentage. A distinctiveness claim becomes traceable only when its control evidence resolves against the separate comparison index.

### 4. Complete analysis-bundle validation

```bash
python scripts/validate_bundle.py \
  work/author-profile.json \
  --evidence work/evidence-map.jsonl \
  --index work/corpus-index.jsonl \
  --manifest work/corpus-manifest.json \
  --ledger work/sampling-ledger.json \
  --metrics work/style-metrics.json \
  --analysis work/author-analysis.md \
  --packet work/writing-packet.md
```

Append `--comparison-index work/comparison-index.jsonl` when the profile contains control evidence. The gate first validates the profile and evidence schemas, all 35 registered analysis dimensions, rule/evidence/packet references, scene modes, voices, controlled values, counts, strict holdout outcomes, and optional control evidence. It then verifies manifest, index, ledger, metrics, source hashes, analysis coverage, saturation status, JSON Pointer metric references, warning-sensitive claims, and Markdown identifiers as one bound bundle. Fake paths, unknown chunk IDs, changed hashes, unanalyzed evidence, out-of-range locators, absent excerpts, unresolved metric references, and stale support files fail validation. Passing these deterministic checks still does not prove that the semantic interpretation is correct.

## Profile Contract

Every major rule records:

1. claimed level and classification;
2. trigger, observable behavior, mechanism, effect, action, and limits;
3. source evidence IDs, short excerpts, hashes, and locators;
4. support sample, work, and scene-type counts;
5. the searched counterexample pool, eligible/reviewed sample IDs, matching counts, and notes;
6. strict holdout eligible/matched counts and per-item outcomes;
7. cross-author distinctiveness status and traceable control evidence when used;
8. confidence and a written confidence basis.

Findings remain **stable**, **conditional**, **variable**, or **uncertain**. Confidence is **high**, **medium**, or **low**, but the label is invalid without its evidence basis.

## Runtime Structure

```text
novel-distiller/
├── SKILL.md
├── references/
│   ├── sampling-and-analysis.md
│   ├── analysis-dimensions.md
│   └── author-profile.md
├── scripts/
│   ├── analyze_style.py
│   ├── corpus_index.py
│   ├── compare_style.py
│   ├── validate_profile.py
│   └── validate_bundle.py
└── tests/
```

`SKILL.md` is the runtime entry point. The three active references contain the scene-grouped sampling method, 35-dimension analysis framework, and human/machine output contract.

## Development

Run the complete test suite:

```bash
python -X utf8 -B -m unittest discover -s tests
```

When the host provides an Agent Skills format validator, run it against the repository root in addition to the tests.

The tests cover Chinese encodings, paired and unpaired ASCII/Chinese dialogue quotes, visible input warnings, paragraph handling, source-bound metrics, collision-resistant chunk IDs, sample/chapter/scene metadata, deterministic/resumable sampling, coarse-scene detection, work-level weighting, supplied-corpus contrast, strict holdout and control evidence, saturation rules, complete-bundle validation, and the end-to-end command-line workflow. These are deterministic contract checks, not human proof of author recognition or semantic fidelity.

## License

[MIT](LICENSE)
