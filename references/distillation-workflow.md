# Distillation Workflow

## Intake and map
Identify input type (`pasted_text`, `txt`, `epub`, `attachment`) and scope (`full_text`, `partial_text`, `excerpt`). Preserve order, assign `ch-NNN` and `chunk-NNN` IDs, and record title/author only when supported. Report inaccessible material instead of installing a parser.

## Segmentation
Prefer volume, chapter, scene, then paragraph boundaries. Keep chunks small enough for careful reading; use marked boundary overlap only when a scene crosses chunks. Record each chunk's source span.

## Chunk index
For every chunk capture summary; characters and alias candidates; events, causes, effects, conflicts, and open threads; relationship observations; foreshadowing candidates; time markers; style examples; and boundary state. Each item immediately gets status, confidence, and evidence.

## Merge and synthesize
Merge stable entities, deduplicate overlap, connect supported links, update relationship evolution, and carry unresolved items forward. Never silently overwrite conflicts. Build the global synthesis from indexes, then recheck major turns, ending/resolution, relationships, setup/payoff pairs, and chronology against source passages. Do not infer unseen endings.

## Output and recovery
Render Markdown and/or strict JSON using `output-schema.md`, then apply `quality-checklist.md`. For missing headings use neutral IDs; for broken encoding list unreadable ranges; for context pressure persist the current index and uncertainty ledger before continuing.
