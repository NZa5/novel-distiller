# 安装与证据等级
目录必须命名为 `novel-distiller`。
- **Pi — verified（本机验证）**：`~/.pi/agent/skills/novel-distiller/`，调用 `/skill:novel-distiller`；项目路径受信任设置影响。
- **Claude Code — documented（官方文档支持）**：`~/.claude/skills/novel-distiller/`，调用 `/novel-distiller`。
- **Codex — documented**：`$HOME/.agents/skills/novel-distiller/`，调用 `$novel-distiller`。
- **通用 Agent — expected（预期）**：保持标准目录结构，按宿主机制发现；不保证所有宿主兼容。
