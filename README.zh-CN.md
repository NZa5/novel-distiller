# Novel Distiller

[English](README.md) | 简体中文

<p align="center">
  <strong>基于证据的用户自备中文小说作者分析器。</strong>
  <br />
  把用户提供的小说转化为可追溯、机器可读的作者画像，供独立的写作 AI 使用。
</p>

<p align="center">
  <a href="https://github.com/NZa5/novel-distiller/stargazers"><img src="https://img.shields.io/github/stars/NZa5/novel-distiller?style=flat-square" alt="GitHub stars" /></a>
  <a href="https://github.com/NZa5/novel-distiller/releases/latest"><img src="https://img.shields.io/github/v/release/NZa5/novel-distiller?style=flat-square" alt="最新版本" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/NZa5/novel-distiller?style=flat-square" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/Agent-Skill-111111?style=flat-square" alt="Agent Skill" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" />
</p>

Novel Distiller 把用户提供的中文小说正文和元数据转化为详细的作者画像。它把作者稳定规律与场景条件变化、角色语言、单部作品特征和不确定观察分开，并让每条主要规则都能回到短例证和可复现的原文定位。

## 为什么使用 Novel Distiller

有辨识度的文字不只是常用词和平均句长。Novel Distiller 检查的是文字背后的选择：

- 叙述者姿态、视角、知识边界、评价方式和信息释放；
- 句子运动、段落功能、用词、修辞、声音与中文特有语言现象；
- 话题与指代链、省略、信息结构、情态、证据性、否定、对话语用与修复、幽默、反讽和讽刺；
- 人物引入、能动性、情绪通道、关系权力和角色声音差异；
- 事件选择、因果、冲突、情节推进、时间、转场和结尾；
- 多线情节与章卷节奏、视角转移、关系网络演化、伏笔回收、母题轨迹和时期漂移；
- 空间、社会系统、母题、主题、类型预期和读者知识；
- 稳定规律、条件规律、可变选择、反例和证据缺口。

最终结果是一套可复用的分析接口，而不是一串空泛形容词。

## 输出内容

| 文件 | 用途 |
|---|---|
| `author-analysis.md` | 完整的人类可读分析、覆盖矩阵、限制和未解决问题 |
| `author-profile.json` | 规范的机器可读画像，包含规则、条件、可信度依据、场景模式、人物声音和优先级 |
| `evidence-map.jsonl` | 每行一条可追溯证据，包含来源哈希、定位、短例证和证据角色 |
| `writing-packet.md` | 供独立写作 AI 使用的精简提示包 |

完整分析包还保存语料清单、schema v4 索引、取样账本和 Markdown/JSON 两种表层指标。画像严格区分片段、作品、阶段和作者层级；作者级结论需要用户提供多部作品中的分离证据。

画像和证据使用 schema **2.1**，清单 **2.0**，索引 **4**，账本 **1.3**，指标 **1.1**。留出运行另保存独立留出索引、承诺文件、冻结初稿和解封记录。

## 30 秒开始

### 安装

本仓库采用可移植的 Agent Skills 文件夹格式，入口为 `SKILL.md`。

需要稳定安装包时，打开[最新 Release](https://github.com/NZa5/novel-distiller/releases/latest)，下载 `novel-distiller-skill-<版本>.zip` 及对应的 `.sha256` 文件，校验后把压缩包中的 `novel-distiller/` 目录解压到兼容 Agent Skills 的宿主所配置的 skills 位置。

需要跟随最新开发版本时，克隆默认分支：

```bash
git clone https://github.com/NZa5/novel-distiller.git /path/to/skills/novel-distiller
```

保持 `SKILL.md`、`scripts/` 和 `references/` 位于同一目录，并按宿主的正常方式重新加载或扫描 skills。Release ZIP 是固定快照，不会随着默认分支之后的提交自动变化。

### 第一次使用

```text
使用 novel-distiller skill 分析这些中文小说。
建立带证据的完整作者画像，区分稳定规律、条件规律、可变特征和不确定结论，并保存可复用的完整分析包。
```

## 工作流程

```text
用户提供的小说
        │
        ├─ 语料清单与来源状态
        ├─ 经核对的作品、样本、章节与真实场景清单
        ├─ 排除留出文本的分析索引统计
        ├─ 跨作品和场景类型的确定性取样账本
        ├─ 带索引完整性核对的跨会话进度
        ├─ 多轮语义精读
        ├─ 证据卡、完整反例搜索和计数
        ├─ 逐规则留出验证与可选对照证据
        ├─ 全量阅读或连续补读饱和证明
        └─ 完整分析包校验
        ▼
author-analysis.md + author-profile.json + evidence-map.jsonl + writing-packet.md
```

处理长篇语料时，skill 会统计非留出分析索引，均衡精读分层样本，再针对未覆盖区域、反例和冲突持续补读。只有完整读完非留出语料，或连续两轮补读都没有新规则、新反例和未解决维度时，才能结束分析。

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

先按下一节建立分析索引。索引模式仅统计已预处理的分析正文，不重新打开含留出内容的完整来源文件；预处理选项在建索引时使用，索引统计时不要重复使用。

```bash
python scripts/analyze_style.py --index work/corpus-index.jsonl --format markdown --output work/style-metrics.md
python scripts/analyze_style.py --index work/corpus-index.jsonl --format json --output work/style-metrics.json
```

预处理后的每个非空行视为一个普通中文小说段落。同一行内成对的 ASCII 直双引号会和中文引号一样识别为对白。固定宽度电子书排版使用 `--reflow-hard-wrap`；正文后存在独立“注释/注釋”章节时使用 `--strip-annotations`。

如果工具检测到疑似固定宽度换行，或任一受支持的中文/ASCII 引号存在未成对、顺序异常或跨行配对，Markdown 与 JSON 报告都会明确警告，不再静默信任失真的段落或对白指标。引号匹配限制在同一行，缺少一个闭引号不会再吞掉后续段落。

### 2. 长篇语料索引

```bash
python scripts/corpus_index.py manifest corpus/target-author --output work/corpus-manifest.json
# 核对 work_id，并为每段补充 sample_id、chapter_id、真实 scene_id 及有依据的语义元数据。
python scripts/corpus_index.py prepare corpus/target-author --manifest work/corpus-manifest.json --analysis-index work/corpus-index.jsonl --holdout-index work/holdout-index.jsonl --commitment work/holdout-commitment.json --ledger work/sampling-ledger.json --seed 20260831
python scripts/corpus_index.py extend work/sampling-ledger.json --index work/corpus-index.jsonl --chunk-id CHUNK_ID --note "SAT03 定向补读"
python scripts/corpus_index.py mark work/sampling-ledger.json --index work/corpus-index.jsonl --chunk-id CHUNK_ID --status analyzed
python scripts/corpus_index.py confirm-scene work/sampling-ledger.json --index work/corpus-index.jsonl --scene-group-id SCENE_GROUP_ID --note "逐段复核后确认为一个连续长场景"
python scripts/corpus_index.py search work/corpus-index.jsonl --sample-id 样本编号 --chapter-id 章节编号 --scene-type confrontation --character 人物名 --exclude-holdout --top 4 --include-text
```

清单骨架必须经过核对：同一部小说拆成多个文件时应使用相同 `work_id`，每个可复用范围必须区分 `sample_id`、`chapter_id` 和真实 `scene_id`。schema v4 会在清单段落边界强制断块，避免一个文本块跨越两个已标注场景。账本会报告过大的 `coarse_scene_groups`；整章包含多个场景时必须细分后重建，确实属于单个连续长场景时则用 `confirm-scene` 保存人工复核说明。索引还保存作品、时期、视角、角色、关系、情绪、章节位置、留出标记、来源 SHA-256、预处理指纹和定位，并绑定精确索引哈希。

省略 `--budget` 时，工具根据可用文本块、作品、样本、章节、场景组和语义分层广度计算第一轮精读目标。手工 `--budget B` 仍是目标而不是强制切分点，因为完整场景组不会被拆开；超出数量会写入账本。第一轮目标不是完成证明；定向补读前用 `extend` 把目标文本块及其完整场景组加入绑定账本，再按缺口和反例补读到全量或饱和。

### 3. 可选的用户自备作者对照

下面的全源文件命令用于无封存留出的运行。解封前比较目标分析索引与独立对照索引中的证据，不能打开含留出的完整目标文件。

```bash
python scripts/compare_style.py contrast --target corpus/target-author --control corpus/comparison-authors --target-manifest work/target-manifest.json --control-manifest work/control-manifest.json --output work/author-contrast.md
python scripts/corpus_index.py build corpus/comparison-authors --manifest work/control-manifest.json --output work/comparison-index.jsonl
```

报告先在每部作品内部汇总文本块，再让作品等权参与作者级比较。同一小说即使拆成很多章节文件，也不会因此获得多倍影响。排列出的差异只是精读候选，不是风格相似度百分比。区分度结论还必须引用对照索引中的可定位 control 证据。

### 4. 冻结、渲染与完整校验

读取留出正文前，保存初稿并记录哈希：

```text
python scripts/corpus_index.py reveal-holdout --holdout-index work/holdout-index.jsonl --commitment work/holdout-commitment.json --provisional-profile work/provisional-profile.json --output work/holdout-reveal.json
```

每条测试过的规则都记录全部留出样本的结果。解封后变化的规则不能沿用 passed。定稿后渲染完整报告与自包含场景包，附加详细跨维度综合分析：

```text
python scripts/render_profile.py work/author-profile.json --evidence work/evidence-map.jsonl --narrative work/analysis-narrative.md --analysis work/author-analysis.md --packet work/writing-packet.md
```

```bash
python scripts/validate_bundle.py work/author-profile.json --evidence work/evidence-map.jsonl --index work/corpus-index.jsonl --manifest work/corpus-manifest.json --ledger work/sampling-ledger.json --metrics work/style-metrics.json --metrics-markdown work/style-metrics.md --analysis work/author-analysis.md --packet work/writing-packet.md
```

有留出集时追加 `--holdout-index work/holdout-index.jsonl --holdout-commitment work/holdout-commitment.json --holdout-reveal work/holdout-reveal.json --provisional-profile work/provisional-profile.json`。画像包含对照证据时，再追加 `--comparison-index work/comparison-index.jsonl`。完整门禁会检查交付文件、账本完成状态、场景粒度、35 个固定维度、分析饱和、反例搜索、逐规则留出结果、可选对照证据、场景包、指标 JSON Pointer、清单/指标/索引哈希，以及每条原文定位。虚构路径、未精读证据、待跟进文本块、未知 ID、失效哈希、越界定位和原文中不存在的摘录都会失败。校验器还会从来源重建索引、重算统计，要求已检查维度的审阅样本和具体结论，把饱和轮次绑定真实补读更新，并核对完整 Markdown 正文；几个 ID 或仅有哈希头的占位文档不能通过。它仍不能证明语义解释本身正确。

## 画像契约

每条主要规则记录：

1. 声称层级和分类；
2. 触发条件、可观察现象、机制、效果、写作动作和限制；
3. 原文证据 ID、短例证、哈希和定位；
4. 支持样本数、作品数和场景类型数；
5. 反例搜索池、适用/已检查样本 ID、对应数量和反例数；
6. 留出样本的适用、命中、漏判、冲突与不适用计数；
7. 跨作者区分度状态及可定位对照证据；
8. 可信度和文字形式的可信度依据；
9. 量化结论对应的数值指标引用及解释。

有留出集时高可信度必须通过验证；没有留出时必须全量阅读，但仍不是独立预测验证。文件隔离记录流程完整性，不证明模型从未见过原文。

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
│   ├── render_profile.py
│   ├── validate_profile.py
│   └── validate_bundle.py
└── tests/
```

`SKILL.md` 是运行入口。三个当前使用的 reference 文件分别保存按场景分组的取样方法、35 维分析框架，以及人类/机器输出契约。

## 开发与测试

运行完整测试：

```bash
python -X utf8 -B -m unittest discover -s tests
```

宿主提供 Agent Skills 格式校验器时，除测试外，再用它校验仓库根目录。

测试覆盖中文编码、可见输入警告、段落与场景边界、表层指标来源、样本/章节/场景绑定、粗场景检测、可复现取样、作品级等权、对照证据、严格留出计数、饱和结构、场景包引用和完整分析包门禁。测试验证确定性约束，不替代人工语义复核。

仓库另有[外部读者盲测工具](https://github.com/NZa5/novel-distiller/tree/master/evaluation)，为原文、使用画像的文本、未使用画像的文本做可复现随机编排和答卷统计，不打进 Skill ZIP。真正的作者辨识结论需要真实盲测读者数据，确定性测试夹具不能替代。

## License

[MIT](LICENSE)
