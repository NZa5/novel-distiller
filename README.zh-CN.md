<div align="center">

# Novel Distiller｜小说蒸馏器

**将长篇小说转化为 Agent 可推理、可追溯的结构化故事地图。**

[English](README.md) · [简体中文](README.zh-CN.md)

[![GitHub stars](https://img.shields.io/github/stars/NZa5/novel-distiller?style=flat-square&logo=github)](https://github.com/NZa5/novel-distiller/stargazers)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-cross--agent-blue?style=flat-square)](SKILL.md)
[![Default dependencies](https://img.shields.io/badge/default%20dependencies-none-brightgreen?style=flat-square)](SKILL.md)

一个跨 Agent 的小说蒸馏 Skill，可从小说和虚构文本中提取人物、情节、关系、伏笔、时间线、叙事结构与写作风格。默认流程直接使用宿主 Agent 自身的阅读和推理能力：**无需 API Key、无需 Python、无需安装依赖，也无需外部模型服务。**

[快速开始](#快速开始) · [输出示例](#输出示例) · [安装说明](INSTALL.md) · [Skill 指令](SKILL.md) · [输出规范](references/output-schema.md)

</div>

## 为什么选择 Novel Distiller？

普通摘要只告诉你“发生了什么”。Novel Distiller 会构建一套可复用、可追溯的故事模型，回答：**谁做了什么、为什么重要、事件发生在何时、线索如何回收，以及作品是怎样写成的。**

| 常见问题 | Novel Distiller 的处理方式 |
|---|---|
| 长篇小说超出单次上下文窗口 | 按卷、章、场景或段落分块，建立中间索引，最后全局合并并回查原文 |
| 人名、别名和身份跨章节漂移 | 使用稳定人物 ID、别名映射，并保留尚未解决的身份冲突 |
| 模型容易把理解和猜测写成事实 | 每条分析记录标注 `fact`、`inference` 或 `uncertain`，并给出置信度 |
| 情节摘要脱离原文依据 | 为主要结论附上章节、段落、行号或分块定位 |
| 伏笔分析容易过度解读 | 区分已埋设、可能回收、明确回收、未回收和不适用状态 |
| 不同 Agent 的输出难以复用 | 采用统一的 Markdown/JSON 契约、稳定 ID 和枚举值 |

## 核心能力

| 分析维度 | 提取内容 |
|---|---|
| **人物** | 姓名、别名、角色定位、目标、特征、人物弧光和重要出场 |
| **情节与结构** | 主线、支线、冲突、风险、因果、转折点和解决状态 |
| **人物关系** | 方向、类型、强度、变化过程、关系非对称性及证据 |
| **伏笔** | 埋设点、可能或明确的回收点、未回收线索和两端证据 |
| **时间线** | 事件顺序、绝对与相对时间、持续时间、插叙、预叙和时间矛盾 |
| **写作风格** | 视角、时态、叙述声音、节奏、对话、句式、词汇、意象、修辞和结构 |

同时内置以下质量保障：

- 为分析结论保留原文定位；
- 明确标记置信度与不确定性；
- 支持长文本分块和跨章节状态传递；
- 合并人物别名时不静默删除冲突；
- 保持 Markdown 与严格 JSON 输出一致；
- 交付前检查覆盖度、一致性和输入限制。

## 工作原理

```text
小说 / 节选 / 可读取附件
             │
             ▼
       确定范围与来源映射
             │
             ▼
       按章节和场景智能分块
             │
             ▼
  人物 · 事件 · 线索 · 时间 · 风格索引
             │
             ▼
       全局合并并回查原文
             │
             ▼
 人物 · 情节 · 关系 · 伏笔 · 时间线 · 风格
             │
             ▼
      质量门禁 → Markdown 和/或 JSON
```

短文本可以一次完成；长文本则会在多个分块之间保留稳定 ID 和未解决状态，再生成全局报告。完整细节见[蒸馏工作流](references/distillation-workflow.md)。

## 快速开始

### 1. 安装 Skill

无需构建。只需将 `SKILL.md` 和 `references/` 放在同一目录，并确保 Agent 可以读取。

Pi 用户可以直接执行：

```bash
mkdir -p ~/.pi/agent/skills
git clone https://github.com/NZa5/novel-distiller.git ~/.pi/agent/skills/novel-distiller
```

克隆完成后请重启或重新加载 Pi，使其发现新 Skill。Claude Code、Codex 和其他 Agent 的使用方法见 [INSTALL.md](INSTALL.md)。

### 2. 提供小说

可以向 Agent 提供：

- 直接粘贴的小说文本；
- TXT 文件；
- 宿主 Agent 能读取的 EPUB；
- 其他可读取的文本附件；
- 小说节选或指定章节范围。

### 3. 发起蒸馏

```text
请使用 novel-distiller Skill 分析这本小说。
覆盖人物、情节、人物关系、伏笔、时间线和写作风格。
每个主要结论都要附原文定位，并标记为事实、推断或不确定项。
请同时输出 Markdown 报告和严格 JSON，两种格式使用相同 ID。
```

如果只需要某一维度或希望分阶段执行，可直接使用现成的[提示词模板](references/prompt-templates.md)。

## 输出示例

对仓库中的虚构短篇[《雨站》](examples/input/sample_novel.md)执行蒸馏后，会得到类似记录：

```markdown
## Foreshadowing
- **fore-001** 蓝色纽扣与月牙图案 — `possibly_revealed`；
  `inference`，`medium`；证据：ch-001 ¶1、ch-002 ¶1。

## Uncertainties & contradictions
- **uncertain-001** 林遥当前下落未知；
  `uncertain`，`high`；证据：ch-003 ¶1。
```

查看完整示例：

- [示例输入](examples/input/sample_novel.md)
- [Markdown 蒸馏报告](examples/output/sample_distillation.md)
- [JSON 蒸馏结果](examples/output/sample_distillation.json)

## 支持的输入与分析范围

| 输入 | 默认处理方式 |
|---|---|
| 粘贴文本 | 直接分析，并尽可能保留段落级定位 |
| TXT | 识别章节标题并保持原文顺序 |
| EPUB | 使用宿主 Agent 的附件读取能力，默认不安装解析器 |
| 其他可读取附件 | 使用 Agent 原生读取器，并报告无法读取的部分 |
| 小说节选或部分章节 | 将范围标记为 `excerpt` 或 `partial_text`，避免对全书下结论 |

实际格式支持能力取决于宿主 Agent 是否能读取该附件。如果无法读取，Skill 会请求用户转换为 TXT 或粘贴文本，而不是自行安装软件。

## 输出规范

统一记录包含以下顶层字段：

```text
schema_version · metadata · summary · characters · plots
relationships · foreshadowing · timeline · style
uncertainties · quality
```

每条分析记录都使用稳定 ID、`claim_status`、`confidence` 和 `evidence`。Markdown 与 JSON 表示同一份记录；没有结果的维度仍会保留，并明确说明分析限制。

- [统一输出 Schema](references/output-schema.md)
- [分析维度定义](references/analysis-framework.md)
- [质量检查清单](references/quality-checklist.md)

## Agent 兼容性

| Agent 环境 | 接入方式 |
|---|---|
| **Pi / pi-coding-agent** | 将仓库放入 Pi Skill 目录，之后用自然语言调用 |
| **Claude Code** | 将 Skill 放在可读取的项目目录或已配置的 Skill 目录，并引用 `SKILL.md` |
| **OpenAI Codex** | 将目录加入项目或已配置的 Skill 位置，并指示 Codex 使用 `SKILL.md` |
| **其他 Agent** | 将 `SKILL.md` 作为系统或项目指令，并保留相邻的 `references/` 目录 |

核心能力使用可移植的 Markdown 指令，不依赖特定平台 SDK。准确安装方式见 [INSTALL.md](INSTALL.md)。

## 仓库结构

```text
novel-distiller/
├── SKILL.md                    # 默认运行入口
├── README.md                   # English documentation
├── README.zh-CN.md             # 简体中文文档
├── references/                 # 工作流、Schema、提示词和质量规则
├── examples/
│   ├── input/                  # 虚构示例输入
│   └── output/                 # 对应的 Markdown 与 JSON 输出
└── tests/                      # Skill 契约测试
```

## 文档导航

| 文档 | 用途 |
|---|---|
| [SKILL.md](SKILL.md) | Agent 运行指令和质量门禁 |
| [INSTALL.md](INSTALL.md) | 不同 Agent 环境的安装方式 |
| [QUICKSTART.md](QUICKSTART.md) | 简短使用教程 |
| [蒸馏工作流](references/distillation-workflow.md) | 长文本分阶段处理、索引、合并和回查 |
| [分析框架](references/analysis-framework.md) | 所有分析维度的定义 |
| [输出 Schema](references/output-schema.md) | 统一 Markdown 与 JSON 契约 |
| [提示词模板](references/prompt-templates.md) | 可复用的完整和专项提示词 |
| [质量清单](references/quality-checklist.md) | 交付前验证规则 |
| [贡献指南](CONTRIBUTING.md) | 贡献要求和测试方法 |

## 路线图

当前优先级是持续改进跨 Agent 的 Skill 契约，而不是引入强制运行依赖。适合贡献的方向包括：增加测试样本、验证更多 Agent 的安装方式、补充多语言输出示例，以及完善经过审查的分析规则。

修改 Schema 或枚举值前，请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 参与贡献

欢迎提交 Issue 和 Pull Request。请坚持项目的核心承诺：默认 Skill 保持跨 Agent、证据优先、无运行依赖。示例应使用虚构或非敏感内容，并确保 Markdown 与 JSON 记录一致。

## 开源协议

Novel Distiller 使用 [MIT License](LICENSE) 开源。

## 致谢

本项目采用了 Agent Skill 生态中的通用优秀模式：精简的运行入口、通过 references 渐进披露详细规则、稳定的结构化输出，以及明确的交付前质量检查。感谢开放的 Agent 生态让这些模式能够被持续学习和改进。
