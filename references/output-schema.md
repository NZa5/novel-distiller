# Canonical Output Schema

Schema 2.0.0 is the canonical Draft 2020-12 contract: [novel-distiller-2.0.schema.json](schemas/novel-distiller-2.0.schema.json). The frozen legacy accepted set is [Schema 1.0.0](schemas/novel-distiller-1.0.schema.json). Major versions never cross-validate; `schema_version`, Skill version, state version, and tooling version are independent.

The compact contract below mirrors the top-level closure; the immutable file is normative:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:novel-distiller:schema:2.0.0",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "metadata", "summary", "characters", "plots", "relationships", "foreshadowing", "timeline", "style", "uncertainties", "quality"],
  "properties": {
    "schema_version": {"const": "2.0.0"}, "metadata": {"type": "object"}, "summary": {},
    "characters": {"type": "array"}, "plots": {"type": "array"}, "relationships": {"type": "array"},
    "foreshadowing": {"type": "array"}, "timeline": {"type": "array"}, "style": {"type": "array"},
    "uncertainties": {"type": "array"}, "quality": {"type": "object"}
  }
}
```

JSON is the machine-readable source of truth. Every dimension has a closed, dimension-specific record. Evidence uses anonymous `source_id`, optional `chapter_id`/`chunk_id`, structured `locator {type,value}`, optional `quote` (maximum 90 Unicode code points), and `purpose`. Facts and inferences require evidence; evidence-free uncertainty requires notes. Missing scalars use `null`; lists use `[]`.

Canonical fields follow [analysis-framework.md](analysis-framework.md); deterministic Markdown follows [markdown-profile.md](markdown-profile.md). Natural-language values use `metadata.output_language`; keys, IDs and enums remain English.

## Language policy
Natural language follows: explicit user choice, current request, conversation, source, then English. Chinese requests default to Simplified Chinese. JSON keys, IDs, locator/status/enum values stay English; names, titles and quotes retain source form.
