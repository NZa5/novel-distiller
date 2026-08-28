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
- `unresolved`: checked available later coverage without finding a payof
