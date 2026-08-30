<div align="center">

# Novel Distiller｜作者风格蒸馏与写作引擎

**从小说样本提取作者写作规律，再把这些规律用于新小说创作。**

</div>

Novel Distiller 是一个面向中文小说的 Agent Skill。它分析用户提供的小说语料，把作者的稳定规律、场景变化和角色差异整理成可复用画像，再用画像控制大纲、场景、章节和改稿。

## 工作流程

```text
作者样本 → 分场景分析 → 表层数据统计 → 作者画像
                                      ↓
新故事要求 → 场景风格简报 → 分场景写作 → 风格对照 → 定向重写
```

它会分析：

- 叙述者姿态、视角距离、信息释放和场景转折；
- 句子运动、段落组织、用词语域、描写与情绪表达；
- 人物塑造、角色对白、关系推进和章节节奏；
- 跨样本稳定特征、特定场景才出现的变化，以及容易发生的风格漂移。
- 目标作者与用户提供的对照作者之间真正有区分度的差异。

## 使用

把整个 `novel-distiller` 文件夹放进 Agent 支持的 Skill 目录，然后重新加载 Agent。

### 1. 蒸馏作者画像

```text
使用 $novel-distiller 分析这些小说样本，建立可直接用于写作的作者画像。
区分稳定风格、场景条件风格、角色语言和暂时无法确定的特征，主要结论附原文定位。
```

### 2. 根据画像写作

```text
使用 $novel-distiller 和已经生成的作者画像，按照这份大纲写第一章。
先匹配场景模式和人物说话方式，写完后完成一次风格对照和定向重写，最终只给我正文。
```

### 3. 检查风格漂移

```text
使用 $novel-distiller 对照作者画像和同类型原文，检查这篇草稿最明显的风格偏差，
修正最关键的三处，同时保持剧情事实不变。
```

## 样本准备

优先提供同一作者、同一创作阶段的完整章节，并覆盖叙述、对白、动作、抒情、开篇和章节结尾等不同场景。样本只有一个片段时，输出会标记为片段画像；多个作品中的分离样本才能支持作者级规律。

本地 `.txt` 和 `.md` 样本可以先运行轻量统计。支持 UTF-8、带 BOM 的 UTF-16、GB18030 和 Big5：

```powershell
python .\scripts\analyze_style.py .\samples --format markdown --output .\style-metrics.md
```

如果电子书把每个固定宽度的排版行都隔成空行，增加 `--reflow-hard-wrap`。工具会逐文件检查高频行宽特征，只重排检测到硬换行的文件，因此可以与正常段落草稿一起比较。
如果每篇正文后附有独立的“注释/注釋”章节，增加 `--strip-annotations`，避免把编辑说明算入作者文风。

统计结果包括句长、段落、对白比例和标点密度。Agent 会把这些数据与原文细读结合起来，而不是仅凭数字判断文风。

### 长篇索引与证据检索

```powershell
python .\scripts\corpus_index.py build .\samples --output .\work\corpus-index.jsonl
python .\scripts\corpus_index.py search .\work\corpus-index.jsonl --query-file .\draft.txt --top 4 --include-text
```

索引保存每个文本块的来源哈希、段落/字符定位、原文和指标，便于长篇分批分析和回查证据。

### 作者差异与草稿对照

```powershell
python .\scripts\compare_style.py contrast --target .\target-author --control .\control-authors --output .\work\author-contrast.md
python .\scripts\compare_style.py draft --reference .\matched-source --draft .\draft.txt --output .\work\draft-comparison.md
```

第一条寻找目标作者相对对照作者更有区分度的候选规律；第二条排列草稿相对匹配原文的表层偏差。两种结果都需要回到原文解释。

### 盲测

```powershell
python .\scripts\blind_style_test.py prepare --original .\holdout --generated .\drafts --output-dir .\blind-test --seed 20260830
python .\scripts\blind_style_test.py score --key .\blind-test\blind-key.json --responses .\blind-test\blind-responses.csv --output .\blind-test\blind-score.md
```

工具生成匿名测试包、隐藏答案键和答题表，并统计生成稿被当作原文的比例、真正原文识别情况、辨识正确率、信心和文字理由。

## 目录

```text
novel-distiller/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── sampling-and-analysis.md
│   ├── author-profile.md
│   ├── writing-engine.md
│   └── style-review.md
├── scripts/analyze_style.py
├── scripts/corpus_index.py
├── scripts/compare_style.py
├── scripts/blind_style_test.py
└── tests/
```

## License

[MIT](LICENSE)
