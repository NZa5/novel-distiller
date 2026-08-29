# Quickstart

## Zero-dependency path (recommended)

1. Copy or clone the repository.
2. Give your Agent access to `SKILL.md` and its neighboring `references/` directory. Do not create `.env` or install Python packages.
3. Attach a TXT/EPUB, paste text, or provide a readable attachment.
4. Ask:

   > 按 novel-distiller/SKILL.md 蒸馏这份小说，分析人物、情节、关系、伏笔、时间线和风格；输出 Markdown 和严格 JSON。

The Agent will identify scope, chunk long text, preserve source locators, label fact/inference/uncertain, and run the quality gate. See [INSTALL.md](INSTALL.md) for host-specific placement.

## Examples

Use [sample_novel.md](examples/input/sample_novel.md) as input and compare [sample_distillation.md](examples/output/sample_distillation.md) and [sample_distillation.json](examples/output/sample_distillation.json).

## Input notes

TXT, pasted text, and readable attachments work directly. EPUB works when the host Agent can read its contents; otherwise export it to TXT or paste the relevant text. Partial inputs are marked as `partial_text` or `excerpt`, and do not produce whole-book claims.

## Optional Python tooling

Only if you explicitly want the retained local CLI:

```bash
python -m venv .venv
.venv/bin/pip install -e optional-tooling/python
python -m novel_distiller distill novel.txt --output output/
```

This is optional tooling, not a Skill requirement. Provider credentials, if that tool uses them, are configured separately; the default Skill never asks for them.

## Troubleshooting

- **Agent cannot read EPUB:** export to TXT or provide pasted/readable content.
- **Text is too long:** the workflow automatically uses chunk IDs and intermediate indexes; ask for staged continuation if the host context is limited.
- **A claim is uncertain:** inspect its evidence locator; the Skill intentionally does not turn ambiguity into fact.
