# Quickstart

1. Copy or clone the `novel-distiller` folder into a Skill location supported by your Agent.
2. Keep `SKILL.md` and `references/` together.
3. Paste fiction or provide a readable TXT, EPUB, or other text attachment.
4. Ask:

   > 使用 novel-distiller 从主要维度分析这篇小说，包括结构、人物、关系、世界、主题、象征、信息、时间线、叙事视角、文风和阅读体验；主要结论附原文定位，并区分事实、推断和不确定项。

Markdown is the default output. Ask for JSON only when you need structured interchange; it follows a suggested format rather than a formal validated schema.

For long text, provide sections in source order. The Skill can maintain a compact running index in the current conversation, but it does not guarantee resume after a restart or context loss.

See [INSTALL.md](INSTALL.md) for placement and [sample_distillation.md](examples/output/sample_distillation.md) for an example.
