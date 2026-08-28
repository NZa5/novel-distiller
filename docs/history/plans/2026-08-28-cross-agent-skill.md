# Cross-Agent Novel Distiller Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Novel Distiller 重构为安装后可直接交给 Agent 使用、无需 API Key 或 Python 依赖的跨 Agent Skill。

**Architecture:** `SKILL.md` 是唯一运行时入口，使用通用 Markdown 指令驱动 Agent 完成小说读取、分块、结构化蒸馏和质量检查。`references/` 存放详细规则与模板，`examples/` 展示输入输出；现有 Python 实现仅作为可选工具，不参与默认使用路径。

**Tech Stack:** Markdown、JSON Schema、纯自然语言 Agent 指令；不要求 Python、LangChain、NetworkX、ebooklib 或外部 API Key。

**Spec:** 已在对话中确认的“跨 Agent 通用 Skill、Agent 使用自身模型、无运行时依赖”设计。

## Global Constraints

- 默认安装和使用不得要求 API Key、环境变量、Python 或 pip。
- 核心 Skill 必须使用跨 Agent 通用 Markdown 和 JSON 结构。
- 所有事实、推断和不确定项必须明确区分。
- 长文本必须采用分块、索引、汇总和复核流程。
- 现有 Python 工具不得阻塞 Skill 的直接使用。
- 不提交 `.env`、缓存或生成输出。

---

### Task 1: 重写 Skill 主入口

**Files:**
- Modify: `SKILL.md`

- [ ] 删除 API Key、pip、Python API 作为默认配置和用法。
- [ ] 增加跨 Agent 元数据、触发条件、输入协议、执行阶段、输出协议和质量门禁。
- [ ] 明确 TXT、EPUB、粘贴文本和 Agent 可读取附件的处理方式。
- [ ] 明确长文本分块和中间索引策略。

### Task 2: 创建参考资料

**Files:**
- Create: `references/distillation-workflow.md`
- Create: `references/analysis-framework.md`
- Create: `references/output-schema.md`
- Create: `references/quality-checklist.md`
- Create: `references/prompt-templates.md`

- [ ] 分离详细工作流、分析维度、JSON Schema、质量检查和提示模板。
- [ ] 保证所有字段、状态值和章节引用规则互相一致。

### Task 3: 重写安装与使用文档

**Files:**
- Modify: `README.md`
- Modify: `QUICKSTART.md`
- Modify: `CONTRIBUTING.md`
- Create: `INSTALL.md`
- Create: `CHANGELOG.md`（如不存在则保留并修正）

- [ ] 以“复制 Skill 目录/安装 Skill 后直接对 Agent 下指令”为主流程。
- [ ] 分别给出 Pi、Claude Code、Codex 和通用 Agent 的安装说明，避免绑定实现。
- [ ] 将 Python CLI 明确标记为 optional legacy/tooling。

### Task 4: 清理仓库入口与旧内容

**Files:**
- Modify: `.gitignore`
- Modify: `setup.py`（仅加入 optional 说明或不再作为默认安装入口）
- Modify: `PROJECT_SUMMARY.md`
- Modify: `PHASE2_PROGRESS.md`
- Delete: 临时测试脚本、缓存和误生成文件
- Move or retain: `novel_distiller/` 作为 `optional-tool/` 的决定需在文档中明确

- [ ] 删除根目录临时测试文件和缓存。
- [ ] 不删除有价值的历史代码，避免破坏可选工具；但 README 不得把它当作 Skill 必需依赖。
- [ ] 修正过期版本、占位 GitHub URL 和“唯一/生产就绪”等未经验证表述。

### Task 5: 示例与验证

**Files:**
- Create: `examples/input/sample_novel.md`
- Create: `examples/output/sample_distillation.md`
- Create: `examples/output/sample_distillation.json`
- Create: `tests/test_skill_contract.py`

- [ ] 用文件内容测试 Skill 契约：入口存在、无 API Key 强制要求、参考文档可达、输出字段一致。
- [ ] 检查 Markdown 链接、JSON 有效性、敏感信息和生成文件。
- [ ] 运行现有 Python 测试，确保可选工具没有被破坏。

### Task 6: 提交与推送

- [ ] 运行 `git diff --check`、完整测试、敏感信息扫描。
- [ ] 提交信息使用 `refactor: make novel distiller a dependency-free cross-agent skill`。
- [ ] 推送 `origin/master`。
- [ ] 记录 commit hash 和仓库状态。
