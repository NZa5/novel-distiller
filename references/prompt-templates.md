# Prompt Templates

Optional staged instructions for the host Agent; no external API or package is required.

## Intake
> Read the supplied fiction using `SKILL.md`. Record input type, scope, source IDs, boundaries, requested focus, and unreadable material. Do not analyze beyond supplied coverage or install dependencies.

## Chunk index
> Analyze `[chunk ID and span]`. Return characters/aliases, events/causality, relationships, foreshadowing candidates, time markers, style observations, open threads, boundary state, and contradictions. Every item must use `fact|inference|uncertain`, `high|medium|low`, and evidence.

## Merge
> Merge these chunk indexes. Preserve stable IDs, deduplicate overlap, retain disputed aliases, connect only supported causal/temporal links, update relationship evolution, and retain an uncertainty ledger. Use canonical statuses.

## Synthesis and rendering
> Synthesize the supplied scope across all six dimensions, recheck major claims against locators, and produce the canonical Markdown report. Then render the same records as strict JSON with every required top-level key, no comments, and no trailing commas.

## Final review
> Apply every item in `references/quality-checklist.md`; correct unsupported facts, broken references, invalid enums, cross-format mismatches, and unstated limitations.
