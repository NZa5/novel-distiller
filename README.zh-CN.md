# Novel Distiller

[English](README.md) | 简体中文

<p align="center">
  <strong>基于证据的中文小说作者风格分析与写作引擎。</strong>
  <br />
  把用户提供的小说语料转化为可复用作者画像，再用于新小说写作、对照、回炉和盲测。
</p>

<p align="center">
  <a href="https://github.com/NZa5/novel-distiller/stargazers"><img src="https://img.shields.io/github/stars/NZa5/novel-distiller?style=flat-square" alt="GitHub stars" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/NZa5/novel-distiller?style=flat-square" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/Agent-Skill-111111?style=flat-square" alt="Agent Skill" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" />
</p>

Novel Distiller 是一个分析用户所提供中文小说的 Agent Skill。它把作者的稳定规律与场景变化、角色语言和偶发现象分开，将主要结论连接到原文证据，再压缩成适合反复注入的写作包，让长篇生成能够持续遵循作者的叙事决策，而不是逐渐变成通用文风。

## 为什么使用 Novel Distiller

有辨识度的文风不只是常用词和平均句长。Novel Distiller 分析的是文字背后的选择：

- 叙述者站在哪里，知道多少，又选择透露什么；
- 句子、段落、场景和章节怎样推进与收束；
- 不同人物在不同关系和压力下怎样说话；
- 情绪怎样通过动作、沉默、感觉、判断或反讽传递；
- 哪些规律属于作者，哪些来自时代、题材、场景或角色。

最终结果不是一组空泛形容词，而是证据地图、场景模式、人物语音卡、表层数据范围、漂移纠正表和紧凑写作包。

## 能做什么

| 能力 | 结果 |
|---|---|
| 作者风格蒸馏 | 带证据和可信度的片段、作品、阶段或作者级画像 |
| 条件风格建模 | 分开保存叙述、对白、行动、反思、开篇、结尾等真实语料模式 |
| 长篇语料处理 | 带来源哈希、段落范围、字符范围、指标和原文的可检索文本块 |
| 作者对照 | 排列目标作者与用户所提供对照作者之间的差异 |
| 画像指导写作 | 场景简报、匹配样本、人物语音卡和逐场景重新注入 |
| 草稿回炉 | 排列表层偏差，并细读叙述、结构、情绪和对白机制 |
| 盲测验证 | 固定随机种子的匿名测试包、隐藏答案、答题记录和结果汇总 |

## 30 秒开始

### 使用 Agent Skills CLI 安装

```bash
npx skills add NZa5/novel-distiller -g -a codex
```

仓库只包含一个 Skill：`novel-distiller`。安装前可以先查看识别结果：

```bash
npx skills add NZa5/novel-distiller --list
```

### 手动安装到 Codex

```powershell
git clone https://github.com/NZa5/novel-distiller.git "$env:USERPROFILE\.codex\skills\novel-distiller"
```

安装后重新加载 Codex。

### 第一次使用

```text
使用 $novel-distiller 分析这些中文小说文件，建立可直接指导新小说写作的作者画像。
区分稳定规律、场景条件规律、角色语言、可变特征和不确定结论；每条主要规则附原文定位。
```

根据画像写作：

```text
使用 $novel-distiller 和作者画像，按照这份大纲写第一章。
先匹配场景模式和人物声音，写完后做一次风格对照与定向回炉，最终只给我正文。
```

检查现有草稿：

```text
使用 $novel-distiller 对照作者画像和同类型原文，检查这篇草稿。
修正最能暴露“换了一个作者”的三项偏差，同时保持所有剧情事实不变。
```

## 工作流程

```text
用户提供的语料
    │
    ├─ 清点与规范化
    ├─ 按作品、场景、视角和角色分组
    ├─ 统计表层特征
    ├─ 为长篇建立索引并保留证据定位
    ├─ 使用留出样本和对照作者检验稳定规则
    ▼
有证据的作者画像
    │
    ├─ Master Voice
    ├─ 场景模式矩阵
    ├─ 人物语音卡
    ├─ 招牌动作与数据范围
    └─ 紧凑写作包
    ▼
场景简报 → 草稿 → 匹配原文对照 → 定向回炉 → 盲测
```

## 准备语料

使用 `.txt` 或 `.md` 文件。优先提供同一创作阶段的完整章节，并覆盖不同场景，不要只提供大量相邻且同质的段落。

```text
corpus/
├── target-author/
│   ├── novel-a.txt
│   └── novel-b.txt
├── comparison-authors/       # 可选，由用户提供
│   ├── author-b.txt
│   └── author-c.txt
└── holdout/                  # 不参与画像归纳
    └── unseen-scenes.txt
```

辅助脚本支持 UTF-8、带 BOM 的 UTF-16、GB18030 和 Big5，只使用 Python 标准库。

## 可复现工具

Agent 负责语义分析；脚本负责让预处理、统计、检索、对照和评估可重复执行。

### 1. 表层统计

```powershell
python .\scripts\analyze_style.py .\corpus\target-author --format markdown --output .\work\style-metrics.md
```

固定宽度电子书排版使用 `--reflow-hard-wrap`；正文后存在独立“注释/注釋”章节时使用 `--strip-annotations`。

### 2. 长篇索引与证据检索

```powershell
python .\scripts\corpus_index.py build .\corpus\target-author --output .\work\corpus-index.jsonl
python .\scripts\corpus_index.py search .\work\corpus-index.jsonl --query-file .\draft.txt --top 4 --include-text
```

每个索引块保存原文、来源文件、SHA-256、段落范围、内容字符范围和表层指标。

### 3. 目标作者与对照作者

```powershell
python .\scripts\compare_style.py contrast --target .\corpus\target-author --control .\corpus\comparison-authors --output .\work\author-contrast.md
```

报告排列句段、对白、标点和功能词差异。这些结果用于确定回看顺序，不是风格相似度百分比。

### 4. 草稿自动对照

```powershell
python .\scripts\compare_style.py draft --reference .\matched-source --draft .\draft.txt --output .\work\draft-comparison.md
```

匹配原文时应尽量保持视角、场景功能、情绪压力、关系阶段和章节位置相近。

### 5. 盲测

```powershell
python .\scripts\blind_style_test.py prepare --original .\corpus\holdout --generated .\drafts --output-dir .\blind-test --seed 20260830
python .\scripts\blind_style_test.py score --key .\blind-test\blind-key.json --responses .\blind-test\blind-responses.csv --output .\blind-test\blind-score.md
```

把 `blind-pack.md` 和答题表交给读者，同时隐藏 `blind-key.json`。结果报告会记录生成稿被当作原文的比例、真正原文能否被识别、整体辨识正确率、信心和文字理由。

## 作者画像怎样工作

每条主要规则记录：

1. 适用范围和场景条件；
2. 可观察现象；
3. 写作机制与读者效果；
4. 原文 chunk ID 和定位；
5. 反例及其解释；
6. 存在对照语料时的作者差异证据；
7. 高、中或低可信度。

所有结论保持为**稳定**、**条件**、**可变**或**不确定**。单个节选只能支持片段画像，一部小说支持作品画像，作者级结论需要跨作品的分离证据。

## 项目结构

```text
novel-distiller/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── sampling-and-analysis.md
│   ├── author-profile.md
│   ├── writing-engine.md
│   └── style-review.md
├── scripts/
│   ├── analyze_style.py
│   ├── corpus_index.py
│   ├── compare_style.py
│   └── blind_style_test.py
└── tests/
```

`SKILL.md` 是运行入口；四个 reference 文件分别保存取样分析、作者画像、写作和回炉的详细流程。

## 开发与测试

运行完整测试：

```powershell
python -B -m unittest discover -s tests
```

测试覆盖中文编码、电子书清理、表层统计、切块定位、证据检索、作者对照、草稿偏差、盲测生成与评分，以及完整命令行工作流。

## License

[MIT](LICENSE)
