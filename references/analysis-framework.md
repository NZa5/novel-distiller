# Analysis Framework

All records include `id`, `claim_status`, `confidence`, `evidence`, and `notes`.
- Character: `name`, `aliases`, `role`, `description`, `goals`, `traits`, `arc`, `first_appearance`.
- Plot: `type`, `title`, `summary`, `participants`, `locations`, `causes`, `effects`, `turning_point`, `resolution_status`.
- Relationship: `source_character_id`, `target_character_id`, `type`, `direction`, `description`, `evolution`, `strength`.
- Foreshadowing: `setup`, `payoff`, `status` with distinct setup/payoff evidence.
- Timeline: `event`, `participants`, `explicit_time`, `relative_time`, `duration`, `chronology_position`, `narration_position`, `mode`.
- Style: atomic `aspect`, `observation`, `scope` with representative evidence.
- Uncertainty: `category`, `description`, `related_ids`, `alternatives`; status is uncertain.

Nested interpretations use assertions with independent epistemic status. Never invent required semantics: use `null`, `[]`, or explicit uncertainty notes.
