# Analysis Framework

This reference defines the six required dimensions. All records use stable IDs, `claim_status` (`fact`, `inference`, `uncertain`), `confidence` (`high`, `medium`, `low`), `evidence`, and optional `notes`.

## Characters

Record `id`, canonical `name`, `aliases`, `role`, `description`, `goals`, `traits`, `arc`, and `first_appearance`. Use `unknown` as the role when the source does not support protagonist/antagonist/supporting/minor. Treat alias merges as inference unless explicit. Separate what a narrator states from what behavior suggests.

## Plot

Record `id`, `type` (`main`, `subplot`, `backstory`), `title`, `summary`, `participants`, `locations`, `causes`, `effects`, `turning_point`, and `resolution_status` (`open`, `resolved`, `partial`, `unknown`). An event needs a source locator. Causal links require more than adjacency; label interpretation as inference.

## Relationships

Record `id`, `source_character_id`, `target_character_id`, `type`, `direction` (`directed`, `mutual`, `unclear`), `description`, `evolution`, and `strength` (`strong`, `moderate`, `weak`, `unknown`). Preserve asymmetry: one character's loyalty does not prove reciprocity. Each evolution stage should identify its event or source.

## Foreshadowing

Record `id`, `setup`, `setup_evidence`, `payoff`, `payoff_evidence`, and `status`:

- `planted`: a setup exists, but later coverage has not yet been checked;
- `possibly_revealed`: a plausible payoff exists but the link is interpretive;
- `revealed`: the text clearly connects or unambiguously resolves setup and payoff;
- `unresolved`: available later coverage was checked without finding a payoff;
- `not_applicable`: the candidate is not foreshadowing after source review.

Use `planted` only before later coverage has been reviewed. A recurring image or unexplained detail is not automatically foreshadowing; identify the anticipated function and lower confidence when the setup/payoff link is interpretive.

## Timeline

Record `id`, event, participants, explicit or relative time, duration, chronology position, narration position, and mode (`linear`, `flashback`, `flashforward`, `parallel`, `unclear`). Keep narration order distinct from story chronology. Preserve conflicting dates or relative markers as uncertainties rather than silently choosing one.

## Style

Record viewpoint, tense, narrative voice, pacing, dialogue use, sentence and lexical tendencies, imagery/rhetoric, and structural patterns. Cite representative passages and declare the analyzed scope. Prefer qualitative comparisons grounded in the source; do not invent percentages or whole-book tendencies from an excerpt.
