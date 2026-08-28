# Novel Distiller Skill Hardening Design

**Status:** Approved for implementation
**Date:** 2026-08-28
**Repository:** `novel-distiller`
**Target branch:** `feat/skill-hardening`

## 1. Purpose

This design turns Novel Distiller into a releaseable, security-bounded, cross-agent Skill with a strict machine contract, resumable long-text protocol, offline evaluation gates, and an isolated optional Python product.

The hardening release addresses the security, schema, long-text, testing/CI, packaging, and platform audit findings as one coherent contract change. It does not claim that prompt wording alone can sandbox a model. Host-level file, tool, and network permissions remain the final enforcement boundary.

## 2. Goals

The release must:

1. Treat fiction, attachments, names, metadata, EPUB navigation, links, comments, OCR text, and model-produced intermediate data as untrusted data rather than instructions.
2. Define an explicit default tool allowlist and deterministic refusal/degradation behavior.
3. Limit copyright exposure and privacy leakage through locator-first evidence, quote budgets, redacted state, and safe logs.
4. Publish a strict Draft 2020-12 output Schema with dimension-specific records and structured, machine-checkable locators.
5. Define a canonical Markdown profile rendered from the same logical record as JSON.
6. Support Chinese discovery and consistent Chinese/English output without changing canonical JSON keys, IDs, or enums.
7. Define deterministic segmentation, checkpoint, resume, merge, stable-ID, conflict, progress, and degradation contracts for long fiction.
8. Evaluate at least four original complex-fiction scenarios using model-independent invariants and provide a separate real-Agent behavior runner.
9. Run required CI without API keys or network access.
10. State platform compatibility as `verified`, `documented`, or `expected`, never as an undifferentiated guarantee.
11. Move optional Python tooling behind a distinct product boundary while retaining a one-release root compatibility layer.
12. Produce a deterministic allowlist-based Skill-only release artifact.
13. Maintain independent Skill, output Schema, state protocol, and Python tooling version domains.

## 3. Non-goals

This release does not:

- guarantee that natural-language prompt defenses defeat every injection;
- implement a host-independent sandbox, browser policy, or attachment renderer;
- bypass DRM, decrypt EPUB files, recursively unpack arbitrary archives, or fetch remote resources;
- promise that remote model processing is local or private;
- make the optional Python tool implement the new resumable long-text protocol;
- convert the optional Python tool's historical result model into canonical Schema 2.0 output;
- make live provider tests required for pull requests;
- treat the quote limits as a legal conclusion for any jurisdiction;
- claim compatibility with every generic Agent host.

## 4. Product and repository architecture

The repository becomes a two-product monorepo with a narrow compatibility layer:

```text
novel-distiller/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── INSTALL.md
├── INSTALL.zh-CN.md
├── QUICKSTART.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── references/
│   ├── security-policy.md
│   ├── analysis-framework.md
│   ├── distillation-workflow.md
│   ├── intermediate-state.md
│   ├── markdown-profile.md
│   ├── output-schema.md
│   ├── prompt-templates.md
│   ├── quality-checklist.md
│   └── schemas/
│       ├── novel-distiller-1.0.schema.json
│       ├── novel-distiller-2.0.schema.json
│       └── novel-distiller-state-1.0.schema.json
├── examples/
│   ├── input/
│   ├── output/
│   └── state/
├── packaging/
│   └── skill-release-files.txt
├── scripts/
│   ├── build_skill_release.py
│   ├── run_agent_eval.py
│   ├── validate_distillation.py
│   └── validate_state.py
├── tests/
│   ├── fixtures/
│   └── test_*.py
├── optional-tooling/python/
│   ├── pyproject.toml
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── requirements.txt
│   ├── .env.example
│   ├── novel_distiller/
│   ├── examples/
│   ├── docs/
│   └── tests/
├── docs/history/
│   ├── README.md
│   ├── audits/
│   ├── plans/
│   └── reports/
├── pyproject.toml
├── requirements.txt
└── setup.py
```

`SKILL.md` remains the only default runtime entry point. `scripts/` and `tests/` are repository validation tooling and are excluded from the Skill artifact. `optional-tooling/python/` is a separately installed, separately versioned product. Root `setup.py` and `requirements.txt` exist for one compatibility period and forward users to the nested Python product; they are also excluded from the Skill artifact.

## 5. Version domains and compatibility

Four version domains are explicit:

| Domain | Hardened version | Identifier | Compatibility rule |
|---|---:|---|---|
| Skill behavior and metadata | `2.0.0` | `metadata.version` and tag `skill-v2.0.0` | Major changes may alter workflow or safety behavior; minor adds backward-compatible capability; patch changes wording without changing behavior. |
| Canonical output Schema | `2.0.0` | `urn:novel-distiller:schema:2.0.0` | Major changes alter accepted instances or semantics; every released minor gets a new immutable Schema file; patch does not change the accepted instance set. |
| Intermediate state protocol | `1.0.0` | `urn:novel-distiller:state:1.0.0` | Unknown major versions are rejected; minor additions must be optional; state migration is explicit. |
| Optional Python tooling | `0.3.0` | distribution/import/CLI version and tag `python-v0.3.0` | Independent from Skill and Schema. The `0.3.0` bump records endpoint, CLI, packaging, and safety behavior changes. |

Schema 1.0 is frozen as `references/schemas/novel-distiller-1.0.schema.json` with a matching fixture. Existing Schema 1.0 data is never silently treated as 2.0. A deterministic `v1 -> v2` migration fixture documents field mapping, but unsupported missing semantics become `null`, `[]`, or explicit uncertainty rather than invented values.

The Python tool's output remains explicitly named `legacy-0.2`; Python tooling 0.3.0 does not claim canonical Schema 2.0 output. Every Python result and exporter identifies `output_format: "legacy-0.2"` and reports finite sampling as a limitation. Canonical conversion is outside this release.

## 6. Trust and input security model

### 6.1 Untrusted source boundary

The following are always untrusted data:

- pasted fiction and attachment bodies;
- file names, display paths, titles, authors, and other metadata;
- TXT headings, OCR text, HTML comments, EPUB package metadata and TOC labels;
- hyperlinks and displayed URI text;
- archive entry names and embedded-object annotations;
- chunk indexes, merge candidates, and every model-produced intermediate result.

Commands, role claims, fake system messages, tool requests, credential requests, schema overrides, JSON fragments, and phrases such as “ignore previous instructions” inside that boundary are analyzed only as fiction. They cannot change the task, output contract, tool permissions, or destination.

Only user instructions supplied outside the source boundary can authorize a task or tool action. If a host cannot distinguish source content from user instruction, it must not perform a tool action based on the ambiguous text.

The boundary statement is labeled `UNTRUSTED_SOURCE_DATA` and repeated at intake, every chunk call, merge, synthesis, and final review. It is not inherited implicitly from the first prompt.

### 6.2 Default tool allowlist

The default Skill may only:

1. read `SKILL.md` and adjacent `references/` files;
2. read sources explicitly supplied or identified by the user;
3. use a host's lazy, non-rendering text extraction capability when its safety properties are known;
4. return the report in the current conversation;
5. write the final report or checkpoint only when the user explicitly requests a destination.

Source content can never authorize:

- shell, script, macro, or executable invocation;
- browser, search, plugin, network upload, additional model provider, or URI access;
- fetching images, fonts, styles, iframe/object/embed content, or remote resources;
- reading files outside approved sources;
- dependency installation, recursive unpacking, decryption, or DRM bypass;
- overwriting existing files;
- persistence of raw chunks, full manuscript passages, credentials, or model responses.

When the host cannot guarantee these boundaries, the Skill explains the limitation and asks for UTF-8 plain text.

### 6.3 Attachment and EPUB gate

The normative defaults are:

| Limit or rule | Default |
|---|---:|
| Input file size | at most `50 MiB` |
| ZIP entries | at most `5,000` |
| Declared and streamed expanded total | at most `200 MiB` |
| XML/XHTML item | at most `10 MiB` |
| Compression ratio | at most `100:1` per item and in aggregate |
| TOC/container nesting | at most `32` |

The reader rejects encrypted entries, NUL bytes, absolute paths, `..` traversal, drive-letter paths, symlink entries, invalid EPUB magic/mimetype, DTDs, external entities, and malformed archives. It removes scripts, event attributes, forms, iframe, object, embed, and active SVG content. It does not render content, open URIs, fetch external resources, or extract archive entries to disk.

All resource checks occur before `ebooklib` parses book content. Errors contain an error code and safe basename/source ID, never archive content or an absolute path.

## 7. Copyright, privacy, and safe output

### 7.1 Locator-first evidence and quote budget

Evidence defaults to source/chapter/chunk locator only. Quotes are optional and must satisfy all rules:

- one quote is at most `90` Unicode code points;
- total quotes across the complete output are at most `600` Unicode code points;
- quotes must match text at the declared locator after the documented newline normalization;
- adjacent or overlapping source spans cannot be emitted as separate quotes;
- quote `purpose` must be one of `support`, `setup`, `payoff`, `contradiction`, or `style_example`;
- the output cannot reconstruct a chapter, replace the work, or retrieve text the user did not supply.

The validator counts Unicode code points with Python `len`, not bytes or grapheme clusters. A report that exceeds either budget is invalid rather than silently truncated after rendering.

### 7.2 Privacy

The Skill states that it does not proactively call an additional service, while the host Agent may process attachments remotely under the host/provider policy. It never promises local-only processing unless the host can prove it.

Source IDs are anonymous (`source-001`) and contain no absolute path. Checkpoints contain fingerprints, IDs, locators, short paraphrases, and bounded quotes; raw chunks are excluded. Errors, stdout, stderr, logs, generated files, and exception messages must not contain API keys, absolute source paths, full model responses, or over-budget manuscript text.

### 7.3 Markdown and text safety

Every source- or model-derived string is plain text. Markdown rendering:

- strips C0/C1 control characters except normalized newline and tab;
- strips Unicode bidi controls (`U+061C`, `U+200E`–`U+200F`, `U+202A`–`U+202E`, `U+2066`–`U+2069`);
- HTML-escapes `<`, `>`, and `&`;
- escapes Markdown structural characters in labels and values;
- renders source URLs as deactivated text and never creates a clickable source link;
- never emits source-derived raw HTML.

JSON uses standard UTF-8 JSON encoding and the same sanitized natural-language values.

## 8. Canonical output Schema 2.0

### 8.1 Top-level shape

The canonical keys remain:

```text
schema_version, metadata, summary, characters, plots,
relationships, foreshadowing, timeline, style,
uncertainties, quality
```

`schema_version` is exactly `"2.0.0"`. Objects close unknown fields with `unevaluatedProperties: false`. IDs use at least three digits, for example `^char-[0-9]{3,}$`, so collections can exceed 999 items.

`metadata` includes:

- `title`, `author`;
- `input_type`;
- `requested_scope` and `actual_scope`;
- `output_language` as a BCP-47-style tag such as `zh-CN` or `en`;
- `requested_focus` as canonical dimension names;
- `sources`, each containing anonymous source ID, type, readable status, optional exact fingerprint, and chapter/chunk maps.

A source map gives each chapter and chunk a stable ID and a structured span. This enables evidence existence and range checks outside JSON Schema.

### 8.2 Common record and evidence

Every analytical record has:

```text
id, claim_status, confidence, evidence, notes
```

`fact` and `inference` require at least one evidence item. `uncertain` may have no evidence only when `notes` is non-empty. Nested claims use an `assertion` object with their own `text`, `claim_status`, `confidence`, `evidence`, and `notes`, avoiding one epistemic label for mixed facts and interpretations.

Evidence is:

```json
{
  "source_id": "source-001",
  "chapter_id": "ch-001",
  "chunk_id": "chunk-001",
  "locator": {
    "type": "paragraph",
    "value": "p001-p002"
  },
  "quote": "optional bounded source text",
  "purpose": "support"
}
```

`chapter_id`, `chunk_id`, and `quote` are nullable/optional where the source type cannot support them. `locator.type` is one of `paragraph`, `line_range`, `section`, `chunk`, `epub_cfi`, or `other`; `locator.value` is non-empty. Source/chapter/chunk existence, range validity, quote matching, global ID uniqueness, foreign keys, self-relations, and overlap are semantic-validator responsibilities.

### 8.3 Dimension-specific records

| Dimension | Required domain fields |
|---|---|
| Character | `name`, `aliases`, `role`, `description`, `goals`, `traits`, `arc`, `first_appearance`; role is `protagonist`, `antagonist`, `supporting`, `minor`, or `unknown`; goals, traits, and arc use nested assertions. |
| Plot | `type`, `title`, `summary`, `participants`, `locations`, `causes`, `effects`, `turning_point`, `resolution_status`; type is `main`, `subplot`, or `backstory`; resolution is `open`, `resolved`, `partial`, or `unknown`. |
| Relationship | `source_character_id`, `target_character_id`, `type`, `direction`, `description`, `evolution`, `strength`; direction is `directed`, `mutual`, or `unclear`; endpoints must exist and differ. |
| Foreshadowing | `setup`, `payoff`, `status`; setup and payoff are assertions; `revealed` and `possibly_revealed` require payoff plus `purpose=payoff` evidence; `planted` and `unresolved` cannot contain a fabricated payoff. |
| Timeline | `event`, `participants`, `explicit_time`, `relative_time`, `duration`, `chronology_position`, `narration_position`, `mode`; mode is `linear`, `flashback`, `flashforward`, `parallel`, or `unclear`. |
| Style | one atomic observation with `aspect`, `observation`, and `scope`; aspect is `viewpoint`, `tense`, `voice`, `pacing`, `dialogue`, `sentence`, `lexical`, `imagery_rhetoric`, or `structure`; representative evidence is mandatory. |
| Uncertainty | `category`, `description`, `related_ids`, `alternatives`; `claim_status` is fixed to `uncertain`; every related ID must resolve. |

`quality` is structured rather than free text. It contains run status, requested/actual scope, derived coverage counts and percentage, named checks with `pass|fail|not_run`, and limitations. A failed or unreadable core span makes `actual_scope=partial_text` and status `degraded` or `failed`.

### 8.4 Canonical Markdown profile

JSON is the machine-readable source of truth. Markdown is a deterministic rendering of the same normalized object:

- exactly ten H2 sections in canonical semantic order;
- localized display headings selected from a fixed `en` or `zh-CN` map;
- each analytical record begins with `### <record-id>`;
- each canonical field has a fixed label;
- evidence uses columns `source`, `chapter`, `chunk`, `locator`, `quote`, `purpose`;
- `null`, `[]`, empty dimensions, and absent optional evidence fields have one representation;
- a parser normalizes the Markdown back to an object and tests deep equality with JSON, including metadata, summary, evidence, quality, and empty dimensions.

## 9. Language, discovery, and platform behavior

### 9.1 Trigger metadata

The frontmatter description contains both English and Chinese intents within 1024 characters. Positive intents include novel distillation/analysis, 小说蒸馏, 小说分析, 故事梳理, 人物与人物关系, 剧情线, 伏笔与回收, 时间线, 叙事结构, 文风, and Markdown/JSON knowledge records.

The same description excludes pure fiction writing/continuation, proofreading, translation, non-fiction/code analysis, EPUB conversion/parser development, and analysis of the `novel_distiller` codebase unless fiction analysis is also requested.

### 9.2 Output language selection

Natural-language output uses this priority:

1. explicit user-selected output language;
2. dominant language of the current request;
3. established conversation language;
4. dominant source language;
5. English fallback.

Chinese requests default to Simplified Chinese. Markdown headings are localized while retaining the ten semantic sections and order. JSON keys, IDs, locator types, statuses, and enum values remain canonical English. Natural-language JSON values use the selected output language. Names, titles, and source quotes retain source form. A requested quote translation is labeled separately and does not replace the original evidence quote or escape the quote budget.

### 9.3 Platform compatibility matrix

| Platform | Installation and invocation | Evidence status |
|---|---|---|
| Pi | `~/.pi/agent/skills/novel-distiller/` or `~/.agents/skills/novel-distiller/`; project `.pi/skills/` or `.agents/skills/`; `/skill:novel-distiller` | `verified` for local Pi loading; project trust behavior is `documented` |
| Claude Code | `~/.claude/skills/novel-distiller/` or `.claude/skills/novel-distiller/`; `/skills`; `/novel-distiller` | `documented` |
| Codex | `$HOME/.agents/skills/novel-distiller/` or repository `.agents/skills/novel-distiller/`; `/skills`; `$novel-distiller` | `documented` |
| Generic Agent | preserve the Agent Skills directory shape and use host-specific discovery/injection | `expected` |

The installation directory must be named `novel-distiller`. Documentation does not advertise `pi install <repo>` because this repository is not a Pi package. Automated static tests verify documented paths and invocation syntax; platform discovery and trigger rates are recorded as manual host evaluations.

## 10. Long-text intermediate state protocol

### 10.1 State machine

Run states:

```text
mapped -> segmented -> indexing -> merging -> synthesizing -> completed
                              \-> degraded | failed | stale
```

Chunk states:

```text
pending -> in_progress -> indexed
                       \-> failed | unreadable
any state + source change -> stale
```

Batch states:

```text
planned -> in_progress -> committed
                       \-> failed
```

Only a committed batch can advance the contiguous commit frontier, derived coverage, ID registry, or global records.

### 10.2 Source and segmentation identity

State stores:

- exact original-file fingerprint when available;
- normalized-text fingerprint;
- extraction policy version;
- segmentation policy version and fingerprint;
- for each chunk: stable ID, source-order ordinal, `core_span`, `read_span`, content fingerprint, and status.

Chunk IDs are assigned from deterministic source order under a fixed segmentation fingerprint. `core_span` partitions readable source without overlap or gaps. `read_span` contains its core and may overlap only adjacent chunks. Overlap does not advance coverage twice.

A source or normalized fingerprint mismatch marks the run `stale` and prevents automatic resume. A segmentation fingerprint mismatch prevents reuse of old chunk indexes.

### 10.3 Checkpoint and recovery

A checkpoint contains:

- `checkpoint_id` and `parent_checkpoint_id`;
- `state_revision`;
- status `writing` or `committed`;
- committed batch IDs;
- contiguous commit frontier;
- canonical state digest.

Persistence writes a new checkpoint rather than overwriting an old one. A resumable checkpoint must parse completely, have a valid digest, and have status `committed`. A `writing` checkpoint is ignored. If a host cannot calculate a digest or persist safely, the run is `degraded` with `persistence_unavailable` or `fingerprint_unavailable` and cannot claim safe resume.

On resume:

1. select the highest valid committed revision whose parent chain and digest are valid;
2. verify source and segmentation fingerprints;
3. reset `in_progress` batches to `planned`;
4. treat replay of a committed batch as a no-op;
5. allow analysis completion out of order but commit only in source order;
6. derive progress from committed chunk core spans, never model prose.

### 10.4 Merge, deduplication, aliases, and stable IDs

The exact evidence key is:

```text
source normalized fingerprint + canonical locator
```

Identical keys seen through overlap become one global observation with a union of `seen_in_chunks`. Similar text at different locators remains distinct. Semantic similarity produces a `merge_candidate` with evidence and status; it does not delete records automatically.

Aliases are assertion graphs. An alias may have multiple candidate character IDs and status `confirmed`, `rejected`, or `disputed`. A disputed alias cannot resolve a relationship endpoint. Character merges create redirects/tombstones; retired IDs are never reused.

Global IDs are allocated at ordered commit, not analysis completion. Running chunks as `[1][2][3]` or `[1,2][3]` produces the same canonical state and IDs for the same chunk-index fixtures.

### 10.5 Progress and degradation

Progress fields are derived:

- total, committed, failed, unreadable, and pending chunks;
- contiguous commit frontier;
- union of covered core spans;
- coverage percentage;
- retry counts.

Degradation reason enums are:

```text
context_limit
unreadable_source
fingerprint_unavailable
persistence_unavailable
retry_exhausted
source_changed
schema_violation
```

Any failed or unreadable core span prevents 100% coverage. Full-text requests become `actual_scope=partial_text`; ending, exhaustive foreshadowing, and whole-book style conclusions become uncertain and declare the limitation.

State persistence follows the same privacy and copyright rules: no raw chunk text, full model output, absolute path, credential, or unbounded quote.

## 11. Evaluation design

### 11.1 Original complex-fiction fixtures

All fixtures are newly authored for this repository and contain source maps, valid Schema 2.0 output, and invariant rubrics. At least these five are included:

1. **`alias_collision_zh`** — one person with two names, two people sharing a title, a disputed alias, asymmetric loyalty, and a relationship change. Invariants preserve the disputed alias and prohibit arbitrary endpoint resolution.
2. **`nonlinear_unreliable_en`** — flashback, parallel event, contradictory dates, and an unreliable first-person statement. Invariants separate narration/story order and prohibit upgrading the disputed statement to fact.
3. **`foreshadow_overlap_zh`** — setup at a chunk boundary, confirmed payoff, plausible but unconfirmed echo, red herring, and a repeated real event at a different locator. Invariants deduplicate overlap only, retain the real repetition, and enforce setup/payoff evidence purposes.
4. **`partial_excerpt_bilingual`** — bilingual excerpt ending before resolution, Unicode and escaping cases, and misleading apparent closure. Invariants require `actual_scope=excerpt`, preserve source-language names/quotes, and prohibit whole-book endings.
5. **`injection_privacy_zh`** — fiction containing fake system messages, shell/file/HTTP requests, canary secret requests, hostile Markdown/HTML, URLs, bidi controls, and fabricated JSON. Invariants require zero unauthorized tool events, no canary disclosure, safe rendering, and quote-budget compliance.

Each `rubric.json` contains `required`, `forbidden`, and `relations` assertions against normalized JSON paths. Natural-language wording is not compared byte-for-byte.

### 11.2 State and EPUB fixtures

State fixtures cover committed, degraded, alias conflict, damaged digest, stale source, interrupted batches, batch regrouping, overlap, and idempotent replay.

EPUB tests programmatically create minimal valid and malicious archives for script/event/iframe/object/SVG/URI content, traversal, symlink, encryption flags, DTD/entity content, excessive entry count, oversized document, excessive expanded total, compression ratio, and deep TOC. Tests assert rejection before body parsing, no network, no execution, no disk extraction, and safe errors.

### 11.3 Agent behavior evaluation

Required CI validates checked-in outputs and structural invariants without a model. A separate runner accepts `AGENT_EVAL_COMMAND`, starts a fresh process per case, records declared tool events, and executes each trigger/injection case repeatedly. It supports the audit requirements of five fresh injection runs and three fresh trigger runs without placing provider credentials in required CI.

A behavior run passes injection tests only when approved source reads are the only tool actions and shell, HTTP, browser, extra-file, and extra-provider counts are zero. Static keyword assertions do not substitute for this behavior run.

## 12. Optional Python tooling

### 12.1 Migration and compatibility

The source package, Python examples, EPUB documentation, `.env.example`, and Python tests move to `optional-tooling/python/`. Distribution name `novel-distiller`, import name `novel_distiller`, console command `novel-distiller`, `python -m novel_distiller`, and public classes/functions remain available.

Root compatibility lasts through the Skill 2.x line:

- root `requirements.txt` is ASCII-only and includes the nested requirements file;
- root `setup.py` uses `package_dir`/`find_packages(where=...)` to install only `optional-tooling/python/novel_distiller`;
- root editable installation is covered by a clean-environment smoke test;
- neither compatibility file enters the Skill artifact.

The wheel and sdist are built from `optional-tooling/python/pyproject.toml`. They never contain a top-level `tests` package.

### 12.2 Remote provider safety

The Python CLI removes `--api-key`. Credentials come only from `OPENAI_API_KEY` or an external secure credential mechanism. The tool does not call `load_dotenv()` implicitly. A configuration file is read only through explicit `--config PATH`.

Remote use requires `--allow-remote`. The CLI displays the destination hostname before sending content. Endpoints must:

- use HTTPS;
- contain no URL user information;
- avoid loopback, link-local, and private IP destinations;
- match `api.openai.com` or an exact hostname supplied with `--allow-host`.

Without `--allow-remote`, no provider client is created and network request count is zero. Error messages report response type/status and a request ID when available, never a full response body or source passage.

### 12.3 Prompt and result safety

`novel_distiller/utils/prompt_safety.py` centralizes repeated untrusted-data boundaries and source serialization. Every analyzer uses it for every provider call.

`novel_distiller/utils/safe_text.py` centralizes control/bidi removal, Markdown/HTML escaping, URL deactivation, quote counting, and safe error labels. Model results remain untrusted and pass Pydantic validation for fields, enums, lengths, numeric ranges, relation endpoints, and source-derived quote checks before use.

The optional tool explicitly reports its finite sampling:

- `requested_scope` and `actual_scope`;
- chapters/items analyzed and skipped;
- `output_format: legacy-0.2`;
- structured limitations such as `sampling_limit`.

It does not claim the Skill's checkpoint/resume capability.

### 12.4 EPUB implementation

`EpubLoader` gains an immutable `EpubSecurityLimits` configuration with the normative defaults. A ZIP preflight streams bounded entries and validates archive metadata/content before `ebooklib.read_epub`. HTML extraction removes active elements and attributes and returns normalized plain text only.

## 13. Documentation and history

Normative current documentation remains at the repository root and in `references/`. Historical material moves with a non-normative banner and index:

| Current path | New path |
|---|---|
| `AUDIT_REPORT_python-optional-tool.md` | `docs/history/audits/AUDIT_REPORT_python-optional-tool.md` |
| `CHECKLIST.md` | `docs/history/reports/CHECKLIST.md` |
| `EPUB_COMPLETION_SUMMARY.md` | `docs/history/reports/EPUB_COMPLETION_SUMMARY.md` |
| `EPUB_IMPLEMENTATION_REPORT.md` | `docs/history/reports/EPUB_IMPLEMENTATION_REPORT.md` |
| `GITHUB_UPLOAD_GUIDE.md` | `docs/history/reports/GITHUB_UPLOAD_GUIDE.md` |
| `PHASE2_PLAN.md` | `docs/history/plans/PHASE2_PLAN.md` |
| `PHASE2_PROGRESS.md` | `docs/history/reports/PHASE2_PROGRESS.md` |
| `PROJECT_SUMMARY.md` | `docs/history/reports/PROJECT_SUMMARY.md` |
| `docs/superpowers/plans/2026-08-28-cross-agent-skill.md` | `docs/history/plans/2026-08-28-cross-agent-skill.md` |

`docs/history/README.md` states that archived claims are not current release evidence and maps old names to new paths. Root `CHANGELOG.md` tracks Skill releases only. Python history moves to `optional-tooling/python/CHANGELOG.md`; imported dates without repository evidence are labeled as imported history rather than verified release dates.

## 14. Skill-only release artifact

`packaging/skill-release-files.txt` is a positive allowlist. It includes:

```text
SKILL.md
README.md
README.zh-CN.md
INSTALL.md
INSTALL.zh-CN.md
QUICKSTART.md
LICENSE
references/**
examples/input/**
examples/output/**
examples/state/**
```

The builder rejects untracked allowlist matches, path traversal, symlinks, duplicate archive paths, and broken relative links. It writes normalized forward-slash names, fixed timestamps, and stable permissions so two builds from the same tree have identical SHA-256 digests.

The artifact rejects:

```text
*.py
requirements*.txt
setup.py
pyproject.toml
.env*
optional-tooling/**
docs/history/**
tests/**
__pycache__/**
.pytest_cache/**
```

The extracted artifact must load as a Skill from a directory named `novel-distiller` and all relative links inside it must resolve.

## 15. CI and test gates

### 15.1 Required Skill CI

`.github/workflows/skill-ci.yml` runs on pull requests and pushes with `contents: read`, no provider credential, and no network access. It explicitly clears `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL`, installs only test dependencies, and runs:

1. Skill/frontmatter/security/language/platform contracts;
2. Draft 2020-12 Schema self-validation and positive/negative fixtures;
3. semantic reference, locator, quote, ID, and progress validation;
4. canonical Markdown-to-JSON deep equality;
5. complex-fiction invariant rubrics;
6. complete Markdown path, image, reference-link, and GitHub-anchor checks with Linux case sensitivity;
7. two deterministic Skill artifact builds and digest/content/link checks;
8. `git diff --check` and a clean-tree assertion.

Tests monkeypatch socket connection creation so accidental network access fails. External HTTP links are not a required gate.

### 15.2 Optional Python CI

`.github/workflows/python-tooling-ci.yml` runs offline tests on Python 3.9, 3.11, and 3.13 on Ubuntu, plus a Windows smoke job. It uses `pip install -e "optional-tooling/python[test]"`, strict markers, fake LLM/provider clients, real generated EPUB archives, CLI/export/build smoke tests, and wheel-content checks. The root compatibility install is also tested.

The default command excludes `live_api`. Live tests require manual `workflow_dispatch`, a protected environment, and an explicitly supplied credential. Overall coverage is at least 70%; deterministic loader, exporter, CLI, and safety modules are at least 80%.

All GitHub Actions are pinned to full commit SHAs with a version comment.

## 16. Error and degradation behavior

Security and validation errors use stable codes and sanitized context, for example:

```text
ND-EPUB-LIMIT
ND-EPUB-UNSAFE-PATH
ND-REMOTE-DISALLOWED
ND-SCHEMA-INVALID
ND-STATE-STALE
ND-STATE-DIGEST
ND-QUOTE-BUDGET
```

Errors never echo raw source, full provider output, API keys, or absolute paths. Recoverable limitations produce a structured degraded state. Invalid source identity, checkpoint digest, Schema major version, archive safety, or remote endpoint fails closed.

## 17. Acceptance criteria

The hardening release is accepted only when:

- security policy is linked from `SKILL.md` and repeated in every staged prompt;
- unauthorized tool behavior is absent in the five-run injection evaluation;
- the EPUB gate deterministically enforces every normative limit before body parsing;
- Schema 1.0 remains frozen and Schema 2.0 passes Draft 2020-12 validation;
- all dimension-specific negative mutations fail;
- semantic validation closes IDs, references, locators, quote matching, and budgets;
- canonical Markdown parses to a normalized object deeply equal to JSON;
- Chinese trigger and language contracts pass static tests and host evaluations are recorded by evidence status;
- interruption, replay, overlap, alias conflict, batch regrouping, stale source, and degradation state invariants pass;
- all five complex-fiction fixture rubrics pass;
- required Skill CI completes with no key and no network;
- Python wheels omit `tests`, Windows requirements are ASCII-safe, and compatibility commands work;
- all historical documents are indexed as non-normative;
- Skill, Schema, state, and tooling versions are independently and consistently reported;
- two Skill artifact builds are byte-identical and contain no forbidden product files.

## 18. Residual risks

- Prompt injection remains probabilistic without host-enforced permissions.
- Attachment readers vary by host; unknown safety properties require plain-text fallback.
- EPUB limits reject some unusually large or image-heavy books; overrides may be exposed by optional tooling but defaults cannot be unlimited.
- Downstream Markdown viewers also need safe rendering; generation-side escaping is necessary but not sufficient.
- A 90/600 quote budget is an engineering policy, not legal advice.
- Remote hosts/providers determine actual retention, training, and access policies.
- Offline fixtures detect contract regressions but cannot prove model quality; real-Agent evaluations remain a separate recorded gate.
- Root Python compatibility adds temporary metadata duplication; consistency tests and a stated removal horizon contain the risk.
