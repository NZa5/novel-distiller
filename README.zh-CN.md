# Novel Distiller

[English](README.md) | 简体中文

<p align="center">
  <strong>基于证据的用户自备中文小说作者分析器。</strong>
  <br />
  把用户提供的小说转化为可追溯、机器可读的作者画像，供独立的写作 AI 使用。
</p>

<p align="center">
  <a href="https://github.com/NZa5/novel-distiller/stargazers"><img src="https://img.shields.io/github/stars/NZa5/novel-distiller?style=flat-square" alt="GitHub stars" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/NZa5/novel-distiller?style=flat-square" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/Agent-Skill-111111?style=flat-square" alt="Agent Skill" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" />
</p>

Novel Distiller 只分析用户提供的中文小说正文和元数据。它把作者稳定规律与场景条件变化、角色语言、单部作品特征和不确定观察分开，并让每条主要规则都能回到短例证和可复现的原文定位。

这个 skill 在分析结果交付后停止，不负责大纲、正文、续写、仿写、审稿或修改小说。

## 为什么使用 Novel Distiller

有辨识度的文字不只是常用词和平均句长。Novel Distiller 检查的是文字背后的选择：

- 叙述者姿态、视角、知识边界、评价方式和信息释放；
- 句子运动、段落功能、用词、修辞、声音与中文特有语言现象；
- 人物引入、能动性、情绪通道、关系权力和角色声音差异；
- 事件选择、因果、冲突、情节推进、时间、转场和结尾；
- 空间、社会系统、母题、主题、类型预期和读者知识；
- 稳定规律、条件规律、可变选择、反例和证据缺口。

最终结果是一套可复用的分析接口，而不是一串空泛形容词。

## 输出内容

| 文件 | 用途 |
|---|---|
| `author-analysis.md` | 完整的人类可读分析、覆盖矩阵、限制和未解决问题 |
| `author-profile.json` | 规范的机器可读画像，包含规则、条件、可信度依据、场景模式、人物声音和优先级 |
| `evidence-map.jsonl` | 每行一条可追溯证据，包含来源哈希、定位、短例证和证据角色 |
| `writing-packet.md` | 供独立写作 AI 使用的精简提示包，不包含生成小说 |

画像严格区分片段、作品、阶段和作者层级。作者级结论需要主人所提供多部作品中的分离证据。

## 使用边界

- 只分析用户提供的小说和元数据。
- 不联网寻找或下载其他小说、评论、传记或对照语料。
- 只有用户提供对照作者文本时，才执行作者对照分析。
- 没有对照文本时，可以分析当前语料内部的重复规律，但跨作者区分度必须保持为 `not_tested`。
- 表层统计只辅助精读，不能单独定义作者身份。
- 详细画像能够改善后续写作，但不能保证所有读者都会相信文本由原作者本人写成。

## 30 秒开始

### 安装

本仓库采用可移植的 Agent Skills 文件夹格式，入口为 `SKILL.md`。将完整目录克隆或复制到任意兼容 Agent Skills 的宿主所配置的 skills 位置：

```bash
git clone https://github.com/NZa5/novel-distiller.git /path/to/skills/novel-distiller
```

保持 `SKILL.md`、`scripts/` 和 `references/` 位于同一目录，并按宿主的正常方式重新加载或扫描 skills。

### 第一次使用

```text
使用 novel-distiller skill，只分析我提供的中文小说。
建立带证据的完整作者画像，区分稳定规律、条件规律、可变特征和不确定结论，并保存四个可复用分析文件。
```

## 工作流程

```text
用户提供的小说
        │
        ├─ 语料清单与来源状态
        ├─ 经核对的作品与场景元数据清单
        ├─ 全量表层统计
        ├─ 跨作品和场景类型的确定性取样账本
        ├─ 带索引完整性核对的跨会话进度
        ├─ 多轮语义精读
        ├─ 证据卡、反例和计数
        ├─ 语料足够时用留出样本挑战画像
        └─ 对完整规则账本重新评估
        ▼
author-analysis.md + author-profile.json + evidence-map.jsonl + writing-packet.md
```

处理长篇语料时，skill 会统计全部文件，均衡精读分层样本，再针对未覆盖区域和冲突进行补读。最长作品和最早处理的批次不能在没有说明的情况下支配最终画像。

## 准备语料

使用 `.txt` 或 `.md` 文件。同一创作阶段的完整章节最适合作为起点。优先覆盖不同场景、视角、角色和章节位置，不要只提供大量连续且同质的段落。

如果小说直接粘贴在对话中，skill 会先按原样保存为 `work/corpus/` 下的 UTF-8 文件，使粘贴文本与上传文件一样具有来源哈希、文本块 ID 和证据定位。

```text
corpus/
├── target-author/
│   ├── novel-a.txt
│   └── novel-b.txt
├── comparison-authors/       # 可选，必须由用户提供
│   └── author-b.txt
└── holdout/                  # 可选，不参与规则归纳
    └── unseen-scenes.txt
```

一个片段只能支持片段画像，一部小说支持作品画像，多部作品才能支持作者画像。

辅助脚本支持 UTF-8、带 BOM 的 UTF-16、GB18030 和 Big5，并且只使用 Python 标准库。

## 可复现工具

Agent 负责语义分析；脚本让预处理、统计、证据索引、用户自备语料对照和结果校验可以重复执行。

### 1. 表层统计

```bash
python scripts/analyze_style.py corpus/target-author --format markdown --output work/style-metrics.md
```

预处理后的每个非空行视为一个普通中文小说段落。同一行内成对的 ASCII 直双引号会和中文引号一样识别为对白。固定宽度电子书排版使用 `--reflow-hard-wrap`；正文后存在独立“注释/注釋”章节时使用 `--strip-annotations`。

如果工具检测到疑似固定宽度换行，或任一受支持的中文/ASCII 引号存在未成对、顺序异常或跨行配对，Markdown 与 JSON 报告都会明确警告，不再静默信任失真的段落或对白指标。引号匹配限制在同一行，缺少一个闭引号不会再吞掉后续段落。

### 2. 长篇语料索引

```bash
python scripts/corpus_index.py manifest corpus/target-author --output work/corpus-manifest.json
# 核对 work_id，并在清单中补充有原文依据的场景、视角和角色元数据。
python scripts/corpus_index.py build corpus/target-author --manifest work/corpus-manifest.json --output work/corpus-index.jsonl
python scripts/corpus_index.py sample work/corpus-index.jsonl --output work/sampling-ledger.json --budget <B> --seed 20260831
python scripts/corpus_index.py mark work/sampling-ledger.json --index work/corpus-index.jsonl --chunk-id CHUNK_ID --status analyzed
python scripts/corpus_index.py search work/corpus-index.jsonl --scene-type confrontation --character 人物名 --exclude-holdout --top 4 --include-text
```

清单骨架必须经过核对：同一部小说拆成多个文件时应使用相同 `work_id`，没有依据的元数据保持为空。schema v3 文本块除正文、来源 SHA-256、预处理指纹和定位外，还保存作品、时期、场景、视角、角色、关系、情绪、章节位置与留出标记。取样账本先按作品轮转，再确定性优先补齐欠覆盖的场景、视角、角色、关系、情绪和章节位置，并保存跨会话的待处理/已完成状态；它绑定精确索引哈希，索引变化后不能误用旧进度。

`--budget` 表示需要精读的分析文本块数量，不是全部索引块数，也不包含留出块。令 `A` 为可用非留出块数、`N` 为作品数：`A<=24` 时使用 `B=A`；否则默认 `B=min(A, max(24, min(80, 6*N)))`，除非用户另设限制。

### 3. 可选的用户自备作者对照

```bash
python scripts/compare_style.py contrast --target corpus/target-author --control corpus/comparison-authors --target-manifest work/target-manifest.json --control-manifest work/control-manifest.json --output work/author-contrast.md
```

报告先在每部作品内部汇总文本块，再让作品等权参与作者级比较。同一小说即使拆成很多章节文件，也不会因此获得多倍影响。没有清单时，每个文件只能临时回退为一部作品，因此仅适用于确实“一文件一作品”的语料。排列出的差异只是精读候选，不是风格相似度百分比。

### 4. 画像和证据校验

```bash
python scripts/validate_profile.py work/author-profile.json --evidence work/evidence-map.jsonl --index work/corpus-index.jsonl
```

校验器检查完整的场景模式、角色声音和写作包结构，受控值、计数与引用，覆盖和留出声明，并把每条证据定位与当前索引及原始小说核对。虚构路径、未知文本块、变化后的来源哈希、越界定位和原文中不存在的摘录都会失败。它仍不能证明语义解释本身正确。

## 画像契约

每条主要规则记录：

1. 声称层级和分类；
2. 触发条件、可观察现象、机制、效果、写作动作和限制；
3. 原文证据 ID、短例证、哈希和定位；
4. 支持样本数、作品数和场景类型数；
5. 反例数量和留出验证结果；
6. 跨作者区分度状态；
7. 可信度和文字形式的可信度依据。

结论保持为**稳定**、**条件**、**可变**或**不确定**。可信度使用**高**、**中**或**低**，但没有证据依据时，单独的标签无效。

## 运行结构

```text
novel-distiller/
├── SKILL.md
├── references/
│   ├── sampling-and-analysis.md
│   ├── analysis-dimensions.md
│   └── author-profile.md
├── scripts/
│   ├── analyze_style.py
│   ├── corpus_index.py
│   ├── compare_style.py
│   └── validate_profile.py
└── tests/
```

`SKILL.md` 是运行入口。三个当前使用的 reference 文件分别保存取样方法、24 维分析框架，以及人类/机器输出契约。

## 开发与测试

运行完整测试：

```bash
python -X utf8 -B -m unittest discover -s tests
```

宿主提供 Agent Skills 格式校验器时，除测试外，再用它校验仓库根目录。

测试覆盖中文编码、成对与未成对的 ASCII/中文对白引号、可见的输入警告、段落识别、表层指标、防碰撞文本块 ID、语义元数据检索、可复现且可恢复的取样、作品级等权、用户自备语料对照、与原始小说绑定的画像校验，以及仅分析的命令行流程。测试不能证明作者级语义还原已经达到目标。

## License

[MIT](LICENSE)
