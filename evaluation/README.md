# External reader evaluation

This repository-only harness evaluates analysis reuse outside the Skill runtime. It is not included in the portable Skill ZIP. It prepares and scores supplied texts; it does not generate fiction or recruit readers.

## What to compare

Prepare matched sets with three arms: unseen original text (`original`), text produced using the saved analysis (`profile_guided`), and the same generation task without the analysis (`no_profile`). Use public-domain or authorized works. Keep original sources outside the analysis corpus. Use the same factual scene outline, model/version, generation settings, length budget, and editing budget for both generated arms. Do not cherry-pick the best generation: pre-register the seed/sample policy and preserve every attempt.

Before testing, remove titles, author names, signature character names, and uniquely identifying setting clues consistently across all three arms. Record transformations. Two reviewers should check fact equivalence and remaining cues; the script only checks declared fact hashes and lengths, not semantic equivalence. The 1.25 maximum length ratio is a configurable engineering guard, not a validated scientific threshold.

Choose and record the reader roster, scene set, primary outcome, exclusion rules, and decision threshold before collecting answers. Include different works and scene types; readers must know the target author's work but must not see arm labels, the profile, or answer key. A practical pilot is at least ten scene sets and five independent readers; this is a pilot suggestion, not a power calculation. Keep private records under ignored `work/evaluation/`.

## Input and commands

`experiment.json` has `schema_version: "1.0"`, `experiment_id`, anonymous `reader_ids`, and `items`. Every item has:

- `item_id`, factual outline `facts`, `cue_audit`, `original_source`, canonical `profile_sha256`, and recorded `generation_settings` (strings);
- `candidates` with exactly the three arm keys above;
- each candidate contains `text` and `facts_sha256 = blind_eval.digest(item["facts"])`.

The hash means all three candidates refer to the same declared outline. It does not prove the candidates actually preserve it. Automated fixtures in `tests/test_blind_eval.py` are not real author evidence.

```text
python evaluation/blind_eval.py prepare work/evaluation/experiment.json --blind work/evaluation/blind.json --key work/evaluation/private-key.json --seed 42
python evaluation/blind_eval.py score --blind work/evaluation/blind.json --key work/evaluation/private-key.json --responses work/evaluation/responses.jsonl --output work/evaluation/result.json
```

Distribute only each reader's own trials from `blind.json`. Keep `private-key.json` with the experiment administrator. Every response line is an object such as `{"trial_id":"T000001","reader_id":"reader1","choice":"B"}`. Candidate order and scene order are randomized per reader. Duplicate trials, unknown readers/options, altered blind text, and incomplete responses are detected; missing answers produce `incomplete`, not success.

## Interpretation and real-corpus gate

Report the counts and rates of selecting each arm as original, the profile-guided minus baseline selection-rate difference, missing responses, and per-reader/per-scene counts. These are not a style-similarity percentage. Repeated answers from one reader and related scenes are dependent; the harness does not invent confidence intervals or significance. Generalization needs new works, new scenes and independent readers, not another run on the same items.

Before claiming real author recognition, retain: corpus provenance and permission, frozen analysis bundle and hashes, generation logs for both arms, cue/fact reviews, blinded trials, raw anonymous responses, scoring output, and a written interpretation including failures. Do not replace reader data with model self-ratings. No reader-recognition claim is established by this repository's deterministic tests alone.
