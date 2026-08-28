# Canonical Output Schema

Markdown and JSON represent the same canonical record. Required top-level keys are `schema_version`, `metadata`, `summary`, `characters`, `plots`, `relationships`, `foreshadowing`, `timeline`, `style`, `uncertainties`, and `quality`.

## Shared conventions

- Missing scalar values use JSON `null`; lists use `[]`.
- Analytical records use `claim_status` (`fact`, `inference`, `uncertain`), `confidence` (`high`, `medium`, `low`), and `evidence`.
- Evidence fields are `source_id`, `chapter` (optional), `locator`, and `quote` (optional).
- IDs are stable strings such as `char-001`, `plot-001`, `rel-001`, `fore-001`, and `time-001`.
- Foreshadowing statuses: `planted`, `possibly_revealed`, `revealed`, `unresolved`, `not_applicable`.
- Plot resolution: `open`, `resolved`, `partial`, `unknown`. Timeline mode: `linear`, `flashback`, `flashforward`, `parallel`, `unclear`.

## JSON Schema (Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:novel-distiller:schema:1.0",
  "title": "Novel Distiller Output",
  "type": "object",
  "required": ["schema_version", "metadata", "summary", "characters", "plots", "relationships", "foreshadowing", "timeline", "style", "uncertainties", "quality"],
  "properties": {
    "schema_version": {"const": "1.0"},
    "metadata": {"type": "object", "required": ["title", "author", "input_type", "scope", "source_ids"], "properties": {"title": {"type": ["string", "null"]}, "author": {"type": ["string", "null"]}, "input_type": {"enum": ["pasted_text", "txt", "epub", "attachment"]}, "scope": {"enum": ["full_text", "partial_text", "excerpt"]}, "source_ids": {"type": "array", "items": {"type": "string"}}}, "additionalProperties": true},
    "summary": {"type": "string"},
    "characters": {"type": "array", "items": {"$ref": "#/$defs/claim"}},
    "plots": {"type": "array", "items": {"$ref": "#/$defs/claim"}},
    "relationships": {"type": "array", "items": {"$ref": "#/$defs/claim"}},
    "foreshadowing": {"type": "array", "items": {"$ref": "#/$defs/claim"}},
    "timeline": {"type": "array", "items": {"$ref": "#/$defs/claim"}},
    "style": {"type": "array", "items": {"$ref": "#/$defs/claim"}},
    "uncertainties": {"type": "array", "items": {"$ref": "#/$defs/claim"}},
    "quality": {"type": "object", "required": ["coverage", "checks", "limitations"], "properties": {"coverage": {"type": "string"}, "checks": {"type": "array", "items": {"type": "string"}}, "limitations": {"type": "array", "items": {"type": "string"}}}, "additionalProperties": false}
  },
  "$defs": {"evidence": {"type": "object", "required": ["source_id", "locator"], "properties": {"source_id": {"type": "string"}, "chapter": {"type": ["string", "null"]}, "locator": {"type": "string"}, "quote": {"type": "string"}}, "additionalProperties": false}, "claim": {"type": "object", "required": ["id", "claim_status", "confidence", "evidence"], "properties": {"id": {"type": "string"}, "claim_status": {"enum": ["fact", "inference", "uncertain"]}, "confidence": {"enum": ["high", "medium", "low"]}, "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}}, "notes": {"type": "string"}}, "additionalProperties": true}},
  "additionalProperties": false
}
```

## Markdown mapping

Use the ten headings: Scope & metadata, Executive summary, Characters, Plot, Relationships, Foreshadowing, Timeline, Style, Uncertainties & contradictions, and Coverage & quality check. Every item shows its ID, descriptive fields, status, confidence, and evidence. Empty dimensions remain present.
