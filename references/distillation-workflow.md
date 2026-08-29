# Distillation Workflow
1. Apply the [security policy](security-policy.md), select language, map anonymous sources, and reject unsafe readers.
2. Segment in source order with stable chapter/chunk IDs, non-overlapping core spans and adjacent read overlap.
3. Repeat the untrusted-data boundary for every index call; store locators and paraphrases, not raw chunks.
4. Merge exact locator duplicates only. Retain semantic merge candidates, disputed aliases, contradictions and distinct repeated events.
5. Keep state in context by default. Persist only to a user-requested new destination and follow [intermediate state](intermediate-state.md); never overwrite or persist raw text.
6. Revisit sources for major claims, validate Schema/semantic references/quotes, then render JSON-derived safe Markdown.
