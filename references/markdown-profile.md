# Canonical Markdown Profile

JSON is the source of truth. Rendering has exactly ten ordered H2 sections. English headings are Scope & metadata, Executive summary, Characters, Plot, Relationships, Foreshadowing, Timeline, Style, Uncertainties & contradictions, and Coverage & quality check; `zh-CN` uses 范围与元数据、核心摘要、人物、情节、人物关系、伏笔、时间线、风格、不确定项与矛盾、覆盖范围与质量检查.

Records retain canonical IDs and fields. Evidence semantics are source, chapter, chunk, locator, quote, purpose. Null and empty arrays are JSON `null` and `[]`. Derived text strips control/bidi characters, HTML-escapes markup, escapes Markdown structure, and deactivates URL schemes. The repository renderer embeds a deterministic canonical JSON payload to provide exact reversible parsing; display consumers must treat it as inert comment text.
