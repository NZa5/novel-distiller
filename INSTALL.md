# Installation and evidence
The directory must be named `novel-distiller`.
- **Pi — verified** locally: `~/.pi/agent/skills/novel-distiller/` (shared `~/.agents/skills/novel-distiller/`); invoke `/skill:novel-distiller`. Project `.pi/skills/` and `.agents/skills/` are trust-sensitive and documented.
- **Claude Code — documented**: `~/.claude/skills/novel-distiller/` or `.claude/skills/novel-distiller/`; inspect `/skills`, invoke `/novel-distiller`.
- **Codex — documented**: `$HOME/.agents/skills/novel-distiller/` or repository `.agents/skills/novel-distiller/`; inspect `/skills`, invoke `$novel-distiller`.
- **Generic Agent — expected**: preserve Agent Skills layout and use host discovery/injection. This is not a universal compatibility guarantee.

Copy only the Skill release artifact. `pi install <repo>` is not supported. Verify that the host discovers `SKILL.md`; no Python or API key is required.
