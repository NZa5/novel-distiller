# Intermediate State, Checkpoint, Resume, and Merge Protocol

State version is `1.0.0`; its Draft 2020-12 schema is [novel-distiller-state-1.0.schema.json](schemas/novel-distiller-state-1.0.schema.json).

Runs move mapped→segmented→indexing→merging→synthesizing→completed, or degraded/failed/stale. Chunks move pending→in_progress→indexed or failed/unreadable; batches planned→in_progress→committed or failed. Only committed batches advance coverage and the ordered commit frontier.

Bind state to original and normalized SHA-256 fingerprints, extraction policy, segmentation policy/fingerprint, stable source-order chunk IDs, gap-free non-overlapping `core_span`, and adjacent-only containing `read_span`. A mismatch is stale and forbids resume.

Write a new `writing` checkpoint then atomically mark `committed`; never overwrite. Resume only the highest fully parsed committed revision with valid digest and parent chain. Reset interrupted batches to planned; committed replay is a no-op. Parallel analysis may finish out of order, but commits and global IDs follow source order. `[1][2][3]` and `[1,2][3]` must project identically.

Deduplicate only exact `normalized fingerprint + canonical locator` evidence, unioning `seen_in_chunks`; similar observations at different locators remain. Semantic merges are retained as candidates. Alias assertions may be confirmed/rejected/disputed; disputed aliases never resolve endpoints. Merges preserve redirects/tombstones and never reuse IDs.

Progress is derived from committed core spans and chunk states. Failed/unreadable spans force degraded `partial_text` and uncertainty for endings/exhaustive conclusions. Checkpoints contain IDs, fingerprints, locators and necessary paraphrases only—no raw chunks, absolute paths, credentials, full responses or unbounded quotes. If hashing/persistence is unavailable, declare degradation and do not claim safe resume.
