# Suggested Output Format

Markdown is the default because it is easier to read and review. Use the section order suggested in `SKILL.md`, adapting it to the user's requested focus.

When JSON is requested, this lightweight shape is recommended:

```json
{
  "scope": {
    "title": null,
    "author": null,
    "coverage": "excerpt, selected chapters, partial text, or full supplied text",
    "limitations": []
  },
  "summary": "",
  "reader_promise": [],
  "characters": [],
  "plots": [],
  "relationships": [],
  "world": [],
  "themes": [],
  "symbols_and_motifs": [],
  "information_structure": [],
  "foreshadowing": [],
  "timeline": [],
  "scenes_and_chapters": [],
  "perspective_and_voice": [],
  "style": [],
  "reader_experience": [],
  "genre_lenses": [],
  "uncertainties": []
}
```

Useful analytical entries may include `status` (`fact`, `inference`, or `uncertain`), `confidence`, `locator`, and `notes`. Include only fields that help the request.

This is a suggested interchange shape, not a formal JSON Schema. Different Agents may vary in optional fields and wording. Check that the JSON parses and honestly represents the same conclusions as the readable report, but do not claim machine validation unless a separate validator was actually run.
