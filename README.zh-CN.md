<div align="center">

# Novel Distiller｜小说蒸馏器

**把小说整理成有原文依据的阅读分析报告。**

[English](README.md) · [简体中文](README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-prompt--only-blue?style=flat-square)](SKILL.md)

</div>

Novel Distiller 是一个零依赖的纯提示词 Skill，用于分析叙事结构、人物、关系、世界与环境、主题、象征、信息结构、伏笔、时间线、叙事视角、阅读体验和写作风格。它直接使用宿主 Agent 已有的阅读与推理能力，不增加 Python、单独的 API Key 或其他模型服务。宿主 Agent 本身仍可能按照其服务商的隐私规则远程处理你提供的文本。

## 它能做什么

- 区分原文事实、有依据的推断和暂时无法确定的问题；
- 为主要结论附上章节、段落、行号、节名或分块定位；
- 只有节选时，不冒充已经分析完整本小说；
- 在当前对话中按原文顺序处理长文本，并维护精简索引；
- 把小说内容和先前模型输出当作不可信数据，而不是指令。

它**不提供**正式 JSON Schema、机器校验、持久化检查点，也不保证在重启或上下文丢失后恢复进度。

## 快速开始

把 [SKILL.md](SKILL.md) 和 `references/` 放在宿主 Agent 支持的 Skill 目录中。安装位置见 [INSTALL.zh-CN.md](INSTALL.zh-CN.md)。

提供可读取的小说后，可以这样说：

```text
使用 novel-distiller 从主要维度分析这篇小说，包括结构、人物、关系、世界、主题、
象征、信息、时间线、叙事视角、文风和阅读体验；主要结论附原文定位，并区分事实、
推断和不确定项。
```

默认输出 Markdown。需要结构化数据时可以要求 JSON，但它使用的是实用模板，不是经过机器验证的严格契约，详情见 [output-format.md](references/output-format.md)。

## 长文本限制

长篇小说应按卷或章节顺序提供。Agent 可以在当前对话中维护精简笔记；如果上下文不足以覆盖全文，必须说明已经处理的范围并请求下一部分，不能宣称已经完成全书分析。

## 示例

- [示例小说《雨站》](examples/input/sample_novel.md)
- [示例分析报告](examples/output/sample_distillation.md)

## 目录结构

```text
novel-distiller/
├── SKILL.md
├── references/
│   ├── analysis-framework.md
│   ├── distillation-workflow.md
│   ├── output-format.md
│   ├── prompt-templates.md
│   ├── quality-checklist.md
│   └── security-policy.md
└── examples/
```

`docs/history/` 下的内容只记录旧版本，不属于当前运行说明。

## 开源协议

[MIT](LICENSE)
