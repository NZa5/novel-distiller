# Install Novel Distiller Skill

The default Skill is Markdown-only: no API key, environment variables, Python, pip, or network setup.

## Pi
Copy this repository (or at minimum `SKILL.md` plus `references/`) into a Pi skills directory, for example `~/.pi/agent/skills/novel-distiller/`, then restart/reload Pi and ask: “蒸馏这份小说附件，同时输出 Markdown 和 JSON。”

## Claude Code
Copy the directory into a location Claude Code can read and reference `SKILL.md` from your project instructions. If your installation supports skill directories, place it in its configured skills directory. Ask Claude to follow `novel-distiller/SKILL.md` for the attached text.

## Codex
Copy the directory into your repository or configured Codex skills directory, then add a project instruction telling Codex to use `novel-distiller/SKILL.md` for fiction-analysis requests.

## Generic Agents
Provide `SKILL.md` as the system/project instruction and keep `references/` beside it so relative links resolve. The Agent only needs to read Markdown and the user's text/attachment.

## Verify
Confirm the Agent can open `SKILL.md` and all five files under `references/`. Try [the sample input](examples/input/sample_novel.md) and compare with [Markdown](examples/output/sample_distillation.md) or [JSON](examples/output/sample_distillation.json).

## Optional Python tooling
`novel_distiller/`, `setup.py`, and `requirements.txt` are retained as optional historical tooling. They have separate Python/package/provider requirements and are not installed or invoked by the Skill's default path.
