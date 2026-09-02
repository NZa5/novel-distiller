# 作者画像模板

作者画像是 Novel Distiller 与后续写作 AI 之间的正式接口。使用实际内容替换模板；没有稳定规律的维度仍要在覆盖矩阵中标明“未发现稳定规律”“证据不足”或“不适用”，避免把“没有写”误当成“没有分析”。

四个交付文件和最终回应使用用户指定的语言；用户未指定时，使用用户请求所用语言。稳定 ID、枚举值、字段名和文件名仍保持本模板规定的机器可读形式。

## 必须交付的四个文件

1. `author-analysis.md`：完整的人类可读分析；
2. `author-profile.json`：后续 AI 读取的规范画像；
3. `evidence-map.jsonl`：每行一条可追溯证据；
4. `writing-packet.md`：从规范画像压缩出的提示包。

四个文件必须使用相同的 `profile_id`、规则 ID、场景模式 ID、场景包 ID 和角色语音卡 ID。完整报告负责解释，JSON 负责稳定传递，JSONL 负责证据回查，写作包负责低上下文调用。完整分析包还保存语料清单、索引、取样账本与 Markdown/JSON 两种表层指标。

## 1. 身份与范围

- 画像名称：
- 画像层级：片段、作品、阶段或作者
- 语料范围：
- 覆盖作品、章节、场景与视角：
- 未覆盖的重要场景或作品：
- 可代表的创作阶段、题材、笔名或版本：
- 数据状态：完整文本、节选、OCR、译本、编辑版或其他
- 对照语料与留出语料：
- 当前可信度和适用边界：

### 覆盖矩阵

| 分析层 | 已处理作品/场景 | 主要视角或角色 | 状态 | 证据数量 | 未覆盖内容 |
|---|---|---|---|---:|---|
| 语言与句段 | | | analyzed / no_stable_finding / insufficient / not_applicable | | |
| 叙事话语 | | | | | |
| 人物与关系 | | | | | |
| 事件、因果与情节 | | | | | |
| 空间与世界 | | | | | |
| 主题、类型与读者契约 | | | | | |
| 深层语言与对话语用 | | | | | |
| 宏观叙事动态 | | | | | |
| 时期漂移与负向画像 | | | | | |

人类可读矩阵概括九个分析层；机器画像必须按固定注册表逐项声明全部 35 个维度。每项包含 `dimension`、`status`、`evidence_count`、`reviewed_sample_ids`、`finding_summary`、`uncovered`。`analyzed` 必须有证据；`analyzed/no_stable_finding/insufficient` 必须列出实际检查、已在账本标为 analyzed 的非留出样本，不能用空审阅列表称为未发现规律。`insufficient` 必须列出缺失条件，并进入饱和记录的未解决维度；`not_applicable` 不含证据或审阅样本，在 finding_summary 中说明为什么当前语料不适用。可检查的记录不等于语义审阅已经真实充分。

## 2. Master Voice

用一段紧凑文字说明这个作者面对人物、世界和读者时的基本姿态。覆盖叙述距离、知识与评价边界、情绪温度、注意力落点、信息控制、道德或认识立场。这里描述底层决策，不堆“细腻、克制、电影感”等形容词。

## 3. 证据地图

| rule_id | 层级与类型 | 可执行规则 | 适用条件 | 机制与效果 | 目标作者证据 | 计数与验证 | 可信度及理由 |
|---|---|---|---|---|---|---|---|
| R01 | 句段/场景/作品；稳定/条件/可变/不确定 | 触发条件、具体动作与节制 | 场景、角色、视角、关系、压力 | 如何运作并影响读者 | evidence_id、chunk_id、短例证 | 支持样本/作品/场景、反例、留出与区分度 | 高/中/低及依据 |

每条规则必须能区分“可观察事实”“分析解释”“生成动作”。记录 `support_sample_count`、`support_work_count`、`support_scene_type_count`、`counterexample_count`、`counterexample_search`、`holdout_status`、`holdout_evaluation` 和 `distinctiveness_status`。`counterexample_search` 必须同时列出适用样本 ID 与已检查样本 ID，使“完整搜索”可由账本复核，而不是只写一个数量。使用统计数字时通过 `metric_refs` 引用 `style-metrics.json` 中的 JSON Pointer。没有对照索引与可定位 control 证据时，`distinctiveness_status` 必须是 `not_tested`，不能根据常识或外部印象声称作者独有。

可信度口径：

- **high**：在所声称层级上覆盖充分、分离证据一致、反例池检查完整；有留出集时必须 passed，无留出时必须 full_corpus，且明确未做独立预测验证；
- **medium**：规律重复出现，但只覆盖部分作品、场景或角色，条件较强，或者没有足够语料做留出；
- **low**：样本稀少、文本噪音较大、存在冲突反例，或机制仍可能由偶然造成。

可信度不能只给标签，必须写 `confidence_basis`。发现新的未解释反例时立即降级、拆分或删除规则。

## 4. 语言指纹

按真实证据提炼：

- **句法与节奏**：句子启动、连接、延宕、停顿和收束；长短句组合及条件变化。
- **段落逻辑**：段落功能、内部层次、换段触发点、段首承接与段尾余留。
- **用词与语域**：名词和动词偏好、修饰密度、抽象与具体、书面与口语、方言与术语。
- **衔接方式**：因果、转折、指代、时间和逻辑是显说还是让读者补足。
- **修辞与感官**：比喻来源、观察顺序、感官权重、意象回响和使用节制。
- **声音与重复**：音节、叠词、复沓、排比、回环和标点如何塑造声音。
- **中文特征**：文白比例、四字结构、量词、语气词、标点、对仗排比、典故与引语。

不要把原文高频词直接列为写作指令。说明这些语言选择在何种场景出现、怎样组合、产生什么效果。

## 5. 叙事话语引擎

### 叙述者与视角

- 叙述者身份、知识边界、可靠性、评价频率和读者距离；
- 视角中心、切换信号、内外部信息比例；
- 直接心理、自由间接表达、身体感受、联想与判断的分工。

### 时间与信息释放

- 顺叙、倒叙、插叙、预叙的进入与退出方式；
- 场景、概述、省略、停顿和重复叙述怎样分配时间；
- 读者、视角人物和其他人物之间的信息差；
- 线索显著度、揭示时机、回看效果、解释粒度与留白。

### 言语呈现

- 直接引语、间接引语、概述、沉默和自由间接表达怎样搭配；
- 对话标签、动作节拍、话轮、打断、回避和潜台词的组织规律；
- 对白怎样同时推动事件、关系、信息和人物暴露。

### 开篇、转场与收束

- 开篇先建立什么，又延迟什么；
- 场景通过时间、地点、动作、物件、话题、视角或意象怎样连接；
- 场景和章节落在决定、后果、发现、问题、意象还是情绪余波。

## 6. 人物塑造引擎

先提炼作者跨人物共享的塑造机制：

- 人物以姓名、身份、关系、外貌、动作、声音还是他人评价被引入；
- 外貌、习惯、物件、环境、语言、内心、他人反应和关键选择怎样分工；
- 欲望、恐惧、误解、底线和矛盾特征如何逐步显露；
- 情绪通过命名、身体、动作、感知偏差、沉默或环境投射表达；
- 人物能动性、关键决定、意外后果和变化弧怎样建立；
- 作者如何表现“不改变”的人物，以及这种不变的代价。

再为主要角色建立角色语音与行为卡：

- 词汇层级、常用句式和思考方式；
- 发言长度、主动程度、回避方式与信息权限；
- 称谓、语气词、停顿、打断和动作节拍；
- 公开意图与潜台词之间的距离；
- 面对不同关系对象和压力时怎样变化；
- 触发其关键决定的条件；
- 两到四条带定位的短例证。

## 7. 关系与社会网络引擎

- 关系由亲属、利益、制度、欲望、秘密、照料、竞争还是共同经历建立；
- 权力来自身份、资源、知识、依赖、暴力还是话语控制；
- 请求、拒绝、谈判、试探、欺骗、冲突、修复如何发生；
- 称谓、空间距离、话轮和信息分享怎样显示关系变化；
- 家庭、群体、组织和社区怎样限制或推动人物；
- 作者偏好的关系规模、网络形态和关系转化模式。

## 8. 事件、因果与情节引擎

- 什么会被作者当作事件写出，事件密度和粒度如何随场景改变；
- 动作、决定、发现、谈话、回忆和感受变化各承担什么；
- 人物动机、明确因果、时间相邻、主题并置和偶然怎样连接事件；
- 原因是在行动前解释、行动中暗示，还是后果出现后补充；
- 阻力如何升级，代价如何累积，意外后果如何回流；
- 冲突类型、风险种类、转折来源、高潮触发和解决程度；
- 章节、情节线和全书结构怎样分配建立、升级、逆转、余波与开放性。

把作者惯用的事件和结构选择转成场景级动作，不只给故事套一个宏观曲线名称。

## 9. 空间与世界引擎

- 空间通过整体地图、人物路线、感官碎片、物件或社会功能怎样建立；
- 环境承担气氛、资源、阻力、信息、象征还是因果作用；
- 私人、公共、边界和过渡空间怎样对应关系与权力；
- 经济、职业、技术、法律、礼俗、阶层、家庭和组织规则如何进入正文；
- 设定通过解释、行动后果、争议、程序还是陌生人物提问传递；
- 世界规则的例外、权限与代价如何控制。

## 10. 主题、母题、类型与读者契约

- 被不同人物、事件和意象反复提出的核心问题；
- 母题每次重复时发生的意义变化；
- 叙述者评价、人物立场、情节后果和结构并置之间的一致或冲突；
- 类型信号出现的时机，以及作者对类型惯例的遵循、延迟、混合和反转；
- 典故、互文、历史记忆、元叙事和形式实验的功能；
- 文本默认读者知道什么、解释什么、要求读者补足什么；
- 时代、平台、题材和类型共有规律与作者特有选择的边界。

## 11. 深层语言与宏观动态

### 话题、指代、情态与判断

- 记录话题链怎样建立、保持、切换和重启，零指代与省略如何控制速度、距离和歧义；
- 区分叙述者与人物的可能、必须、听闻、目击、推测、否定和自我修正；
- 标出旧信息与新信息的落点、焦点标记、判断来源和确定性变化。

### 对话语用与幽默机制

- 为关键话轮记录言语行为、邻接回应、面子策略、直接程度、语域适应、打断与修复；
- 说明幽默、反讽或讽刺的目标、知识差、触发信号、回调方式、场景功能和使用节制；
- 不把人物偶发笑话上升为作者规律，必须比较不同说话人和关系压力。

### 多线情节与章卷节奏

| 线索/情节线 | 首次建立 | 中间推进与切线 | 未闭合问题 | 汇合或回收 | 章卷节奏作用 | 证据 |
|---|---|---|---|---|---|---|
| | | | | | | |

### 视角转移矩阵

| 从/到 | 视角 A | 视角 B | 视角 C |
|---|---|---|---|
| 视角 A | 保持条件 | 转移触发、桥接和信息效果 | |
| 视角 B | | 保持条件 | |

只有语料真实出现的转移才能填入矩阵。记录转移成本、章节或场景边界、感知中心确认信号，以及转移增加、隐藏或重新解释的信息。

### 关系网络演化

| 关系边 | 初始状态 | 权力与资源 | 关键转折 | 对第三方/群体的传播 | 当前状态 | 证据 |
|---|---|---|---|---|---|---|
| | | | | | | |

### 伏笔—回收账本

| 线索 ID | 种子与位置 | 强化/变形/误导 | 间隔 | 回收方式 | 重释内容 | 未解决部分 |
|---|---|---|---|---|---|---|
| | | | | | | |

### 意象与母题轨迹

| 轨迹 ID | 初次意义 | 重复载体与感知者 | 中段变化 | 高潮/结尾状态 | 跨作品状态 | 证据 |
|---|---|---|---|---|---|---|
| | | | | | | |

### 时期与作品漂移

| 特征 | 稳定核心 | 早期/作品 A | 中期/作品 B | 后期/作品 C | 可能混杂因素 | 写作包分流 |
|---|---|---|---|---|---|---|
| | | | | | | |

版本、编辑、翻译、连载平台、题材、视角和人物构成必须先作为混杂因素核对，不能把所有差异解释成作者自然演变。

## 12. 场景模式矩阵

| 场景模式 | 叙事距离与视角 | 句段运动 | 人物与关系 | 对白 | 事件与因果 | 描写与感官 | 信息、时间与结尾 |
|---|---|---|---|---|---|---|---|
| 日常/过渡 | | | | | | | |
| 对峙/冲突 | | | | | | | |
| 行动/高潮 | | | | | | | |
| 调查/揭示 | | | | | | | |
| 反思/抒情 | | | | | | | |
| 开篇/章节结尾 | | | | | | | |

根据真实语料增删行。场景矩阵负责保存作者的变化范围，避免把所有场景写成同一种节奏。

## 13. 招牌动作与负向画像

每个招牌动作记录：

- 触发条件；
- 执行顺序；
- 对读者产生的效果；
- 出现频率或使用节制；
- 原文定位与反例；
- 在新文本中的等价实现方式。

招牌动作可以是信息延迟、视线转移、意象回响、冷处理、对话错位、动作替代心理说明或特定章节钩子。复现机制，不复制原文专属句子、意象和事件。

负向画像只记录语料反复证明作者会回避或节制的写法，例如不直接命名某类情绪、不一次讲完背景、不滥用某种修辞。不要套用通用“AI 味”清单，也不要把一次未出现当成稳定禁令。

## 14. 表层数据范围

记录实际统计语料、分组方式与运行日期，再填写典型范围：

- 句长和段长分布；
- 对白占比与话轮形态；
- 关键标点与功能词密度；
- 不同场景、视角和角色之间的明显差异。

保留范围和条件差异，不压成一个全书平均值。数据负责支持或挑战语义结论，不单独定义作者身份。

## 15. 漂移纠正表

| 漂移现象 | 为什么不像 | 应恢复的作者机制 | 修订动作 |
|---|---|---|---|
| 示例：连续解释人物感受 | 原作者主要让动作和停顿承担情绪 | 行为证据先于判断 | 删除解释句，补一个会改变关系或行动的反应 |

这里只记录能够从作者样本证明的高风险漂移：如果后续写作 AI 违反哪些机制，会最明显地失去作者辨识度。每项记录都要注明对应的画像规则和作者样本证据。

## 16. 规则优先级与冲突处理

后续 AI 遇到规则冲突时按以下顺序选择：

1. 当前场景、视角、角色和关系明确命中的条件规则；
2. 有广泛证据的稳定规则；
3. 对应场景的表层数据范围；
4. 中低可信度观察。

在画像中列出 `rule_precedence`。如果两条规则只在特定条件下冲突，记录分流条件，不要简单删除其中一条。

## 17. 留出验证

- 未参与画像归纳的样本：
- 画像成功预测的稳定规律：
- 正确识别的条件模式：
- 无法解释的反例：
- 对照作者中是否出现相同规律：
- 因验证而降级、拆分或删除的规则：
- 画像当前适用边界：

每条规则的 `holdout_evaluation` 记录 `eligible`、`matched`、`missed`、`contradicted` 和 `not_applicable`。测试过的规则必须覆盖全部留出样本，不能只挑命中项；同一样本对同一规则只能有一个结果。`passed` 要求至少一个适用样本且全部命中；有命中也有漏判或冲突时为 `partial`；没有命中且存在漏判或冲突时为 `failed`。保持初稿文件不变，最终 `corpus.provisional_profile_sha256` 绑定初稿与解封记录；无留出时为 null。解封后改动触发条件、可观察现象、机制、动作、维度或限制的规则不能沿用 passed，需要新留出或降级为未验证。

## 18. 分析饱和与停止依据

`analysis_saturation` 必含 `status`、`ledger_sha256`、`rounds`、`unresolved_dimension_ids` 和 `stop_reason`。ledger_sha256 是最终账本文件 SHA-256。每轮必含 `round_id`、`ledger_update_sequences`、`added_sample_ids`、`new_rule_count`、`new_counterexample_count`、`unresolved_dimension_ids`、`note`。sequence 必须指向实际 extend 更新，样本列表与更新新增样本一致且已全部精读，不能跨轮重复补同一批样本。全读非留出文本时使用 full_corpus，可用空 rounds；否则最后连续两轮均有新增样本、无新规则/反例、无未解决维度才可 saturated。语义上的新发现计数仍需诚实记录与人工核查。受限运行用 limited 并降低层级，不能交付为完整 author 画像。

## 19. 写作包

把分析压缩成多个按条件选择的场景包，而不是把所有规则、模式和人物声音同时激活。每个场景包包含：

1. Master Voice；
2. 当前场景需要激活的固定维度 ID；
3. 当前场景模式及叙事话语参数；
4. 当前视角、人物行为卡与关系状态；
5. 事件因果、信息差、时间位置、情节线和场景转折；
6. 五到八条最有区分度的语言与结构规则；
7. 话题/指代、情态、对话语用、伏笔或母题中当前适用的控制项；
8. 两到四个短例证的定位与机制摘要；
9. 当前最容易出现的三项漂移及纠正动作；
10. 本场景适用的表层数据范围和负向约束。

写作包顶层使用 `selector_order` 说明先按场景模式、视角、关系或其他条件选择；`shared_rule_ids` 只放真正跨场景稳定的少数规则。每个 `packet_id` 覆盖一个或一组兼容场景模式，并列出触发条件、激活规则、人物声音、证据、统计范围引用、优先级和漂移纠正。所有场景模式至少被一个包覆盖。写作包应足够短，能反复使用；完整画像保留证据、条件和反例，负责在需要时回查。

## 机器可读画像

`author-profile.json` 至少包含以下顶层字段：

- `schema_version`：当前为 `2.1`，证据 JSONL 同为 `2.1`；清单仍为 `2.0`，索引为 `4`；
- `profile_id`：本次画像的稳定编号；
- `profile_scope`：`passage`、`work`、`period` 或 `author`；
- `corpus`：`supplied_only=true`、目标标签、目标作品/样本/来源哈希、对照作品/样本/来源哈希、留出样本 ID、预处理参数和清单 SHA-256；
- `coverage`：35 个固定分析维度的逐项检查状态；
- `master_voice`：底层叙述姿态；
- `rules`：规范规则数组；
- `scene_modes`：条件场景模式；
- `character_voices`：角色语音和行为卡；
- `rule_precedence`：冲突处理顺序；
- `surface_ranges`：实际统计范围和分组；
- `analysis_saturation`：全量阅读或连续补读饱和的可检查记录；
- `writing_packet`：后续 AI 的紧凑控制项；
- `limitations`：未覆盖和不确定内容。

每条 `rules` 记录至少包含：

```json
{
  "rule_id": "R01",
  "dimension": "narrator_evaluative_stance",
  "level": "author",
  "classification": "conditional",
  "category": "narrative_distance",
  "trigger": "对峙场景且视角人物信息受限",
  "observable": "先写可见动作和空间位置，延后直接心理判断",
  "mechanism": "用观察顺序维持知识边界",
  "effect": "让压力先于解释抵达读者",
  "action": "按动作、感知、判断的顺序展开",
  "limits": "内心独白场景不适用",
  "evidence_ids": ["E0001", "E0002"],
  "metric_refs": ["/aggregate/sentence_length/median"],
  "metric_claims": [{"ref": "/aggregate/sentence_length/median", "interpretation": "只作句长基线；知识边界机制仍由原文动作次序证明"}],
  "support_sample_count": 2,
  "support_work_count": 2,
  "support_scene_type_count": 1,
  "counterexample_count": 1,
  "counterexample_search": {
    "status": "complete",
    "eligible_sample_count": 8,
    "reviewed_sample_count": 8,
    "eligible_sample_ids": ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08"],
    "reviewed_sample_ids": ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08"],
    "notes": "已检查全部同类对峙场景"
  },
  "holdout_status": "passed",
  "holdout_evaluation": {
    "eligible": 2,
    "matched": 2,
    "missed": 0,
    "contradicted": 0,
    "not_applicable": 1
  },
  "distinctiveness_status": "not_tested",
  "distinctiveness_evidence_ids": [],
  "confidence": "medium",
  "confidence_basis": "跨两部作品重复，但目前只覆盖对峙场景"
}
```

示例只规定结构，不是默认分析结论。所有文字和数字都必须由当前语料产生。

`scene_modes` 中每项必须包含 `mode_id`、`name`、非空 `triggers`、`rule_ids` 和 `evidence_ids`。`character_voices` 中每项必须包含 `voice_id`、`character_label`、非空 `conditions`、`rule_ids` 和 `evidence_ids`。所有引用都必须指向当前画像中存在的规则或证据。

`writing_packet` 是机器可读画像内部的条件化控制项，至少包含：

```json
{
  "master_voice": "与顶层 master_voice 完全一致",
  "selector_order": ["scene_mode", "viewpoint", "relationship"],
  "shared_rule_ids": ["R01"],
  "packets": [{
    "packet_id": "P01",
    "name": "对峙场景包",
    "triggers": ["角色目标冲突"],
    "active_dimension_ids": ["narrator_evaluative_stance"],
    "active_rule_ids": ["R02"],
    "scene_mode_ids": ["M01"],
    "character_voice_ids": ["V01"],
    "rule_precedence": ["R01", "R02"],
    "evidence_ids": ["E0001", "E0002"],
    "surface_range_refs": ["/aggregate/sentence_length/median"],
    "drift_corrections": ["先核对场景条件，再修正偏离的叙事机制"]
  }]
}
```

每个场景包的 `rule_precedence` 必须完整排列共享与激活规则。`active_dimension_ids` 只能引用固定机器 ID，其他编号数组也必须引用实际对象；master_voice 不得在压缩时改成另一套结论。surface_range_refs 必须由共享或激活规则的 metric_claims 解释。metric_refs 与 metric_claims.ref 集合须一致，只能指向 `/aggregate` 或 `/source_ranges` 下的数值叶节点，不能引用版本号、字符串或整个对象冒充量化依据。

## 证据 JSONL

`evidence-map.jsonl` 每行是一个完整 JSON 对象，至少包含：

- `schema_version`、`profile_id`、`evidence_id`、`rule_id`、`dimension`；其中 `dimension` 必须与对应规则相同，并引用固定机器 ID；
- `corpus_role`：`target` 或 `control`；`evidence_role`：`support`、`counterexample`、`holdout` 或 `control`；
- `sample_id`、`source_path`、`source_sha256`、`chunk_id`；
- `work_id`、`scene_type`：用于核对跨作品和跨场景计数；
- `paragraph_start`、`paragraph_end`、`content_char_start`、`content_char_end`；
- `evaluation_outcome`：留出证据使用 `matched`、`missed`、`contradicted` 或 `not_applicable`，其他证据固定为 `not_applicable`；
- `excerpt`：足以说明机制的短例证；
- `observation`：例证实际做了什么；
- `eligibility`：为什么这个样本可以支持或挑战该规则。

先保存详细的 `analysis-narrative.md`：按本模板 1–19 节中适用内容写出跨维度综合、场景对比、关系/伏笔/母题轨迹和不确定点，引用规则与证据 ID。没有材料的节说明缺口，不填假表格。再从最终画像与证据渲染标准正文和自包含场景包，附加深度分析。renderer 不会自动产生语义结论。

```bash
python scripts/render_profile.py work/author-profile.json --evidence work/evidence-map.jsonl --narrative work/analysis-narrative.md --analysis work/author-analysis.md --packet work/writing-packet.md
python scripts/validate_bundle.py work/author-profile.json --evidence work/evidence-map.jsonl --index work/corpus-index.jsonl --manifest work/corpus-manifest.json --ledger work/sampling-ledger.json --metrics work/style-metrics.json --metrics-markdown work/style-metrics.md --analysis work/author-analysis.md --packet work/writing-packet.md
```

有留出集时追加 `--holdout-index work/holdout-index.jsonl --holdout-commitment work/holdout-commitment.json --holdout-reveal work/holdout-reveal.json --provisional-profile work/provisional-profile.json`；有对照证据时追加 `--comparison-index work/comparison-index.jsonl`。Markdown 包含画像/证据哈希头与完整标准正文，只放 profile_id 和若干 ID 的占位文档不能通过。可在正文后追加解释；JSON 变化后必须重新渲染。旧 schema 不能只改版本号，须根据真实记录补齐审阅样本、指标解释、饱和绑定和留出文件。

只有交付文件齐全，账本没有待处理或待跟进项，场景粒度合格，饱和或全量阅读成立，必填字段、受控值、计数、指标引用、ID 与交叉引用、目标/对照/留出证据、索引块编号、作品与样本归属、来源路径、来源 SHA-256、定位范围和短摘录全部通过，才算交付完成。校验器还会重新读取原始来源并核对哈希，所以原文、清单、指标或索引变化后旧画像不能继续冒充当前结果。校验器不证明分析解释正确；人工语义复核仍然不可省略。
