# Phase 2 开发计划

## 🎯 目标

在 MVP Phase 1 基础上，增强分析深度和广度，提供更专业的小说分析能力。

## 📊 功能优先级

### P0 - 高优先级（核心功能）
1. **人物关系图谱** - 最有价值，可视化效果好
2. **伏笔检测与回收追踪** - 差异化核心功能

### P1 - 中优先级（增强功能）
3. **时间线重建** - 补充情节分析
4. **风格分析** - 为作者提供参考

### P2 - 低优先级（扩展功能）
5. **EPUB 格式支持** - 扩大适用范围

## 🏗️ 技术方案

### 1. 人物关系图谱

**目标**: 构建人物之间的关系网络

**技术栈**:
- NetworkX: 图数据结构
- Matplotlib: 基础可视化
- Pyvis (可选): 交互式网络图

**数据模型**:
```python
class CharacterRelation(BaseModel):
    source: str  # 人物A
    target: str  # 人物B
    relation_type: str  # 关系类型（亲属/朋友/敌对/师徒等）
    description: str  # 关系描述
    chapters: List[int]  # 关系出现的章节
    strength: float  # 关系强度 0-1
```

**实现步骤**:
1. 扩展 CharacterExtractor，提取人物间的互动
2. 使用 LLM 识别关系类型
3. 构建 NetworkX 图
4. 导出 GraphML/JSON
5. 生成可视化图片

**预估时间**: 2-3 天

---

### 2. 伏笔检测与回收追踪

**目标**: 识别伏笔的埋设位置和回收位置

**数据模型**:
```python
class Foreshadowing(BaseModel):
    id: str
    title: str  # 伏笔标题
    planted_chapter: int  # 埋设章节
    planted_content: str  # 埋设内容
    revealed_chapter: Optional[int]  # 回收章节
    revealed_content: Optional[str]  # 回收内容
    status: str  # planted/revealed/abandoned
    importance: str  # high/medium/low
```

**实现步骤**:
1. 第一遍扫描：识别潜在伏笔（暗示、预告、谜团）
2. 第二遍扫描：寻找伏笔回收（对应、揭示）
3. 关联埋设和回收
4. 生成伏笔追踪表

**预估时间**: 3-4 天

---

### 3. 时间线重建

**目标**: 按时间顺序整理故事事件

**数据模型**:
```python
class TimelineEvent(BaseModel):
    event_id: str
    chapter: int
    timestamp: Optional[str]  # 绝对时间（如果有）
    relative_time: Optional[str]  # 相对时间（"三天后"）
    event_type: str  # major/minor
    description: str
    characters_involved: List[str]
    location: Optional[str]
```

**实现步骤**:
1. 提取时间标记（"三天后"、"次日"、日期等）
2. 提取关键事件
3. 建立事件时间关系
4. 生成时间线图表

**预估时间**: 2-3 天

---

### 4. 风格分析

**目标**: 分析作者的写作风格特征

**分析维度**:
- 叙事视角（第一人称/第三人称/全知视角）
- 叙事节奏（对话/描写/动作比例）
- 常用修辞手法
- 词汇特征（高频词、独特用词）
- 句式特征（平均句长、句式多样性）

**数据模型**:
```python
class WritingStyle(BaseModel):
    perspective: str  # 叙事视角
    pacing: dict  # 节奏分析
    rhetoric: List[str]  # 修辞手法
    vocabulary: dict  # 词汇特征
    sentence_pattern: dict  # 句式特征
    tone: str  # 整体风格（轻松/严肃/幽默等）
```

**实现步骤**:
1. 统计分析（词频、句长）
2. LLM 分析（视角、风格、修辞）
3. 生成风格报告

**预估时间**: 2-3 天

---

### 5. EPUB 格式支持

**目标**: 支持 EPUB 电子书格式的加载

**技术栈**: 
- ebooklib: EPUB 解析

**实现步骤**:
1. 创建 EpubLoader
2. 解析 EPUB 结构
3. 提取文本内容
4. 适配现有章节分割逻辑

**预估时间**: 1-2 天

---

## 📅 开发计划

### Week 1: 人物关系图谱 + 伏笔检测
- Day 1-3: 人物关系图谱
- Day 4-7: 伏笔检测与追踪

### Week 2: 时间线 + 风格分析
- Day 8-10: 时间线重建
- Day 11-13: 风格分析
- Day 14: EPUB 支持

### Week 3: 测试与优化
- Day 15-17: 完整测试
- Day 18-19: 文档更新
- Day 20-21: 性能优化

**总预估**: 3 周（约 21 天）

---

## 🔧 技术准备

### 新增依赖

```txt
# Phase 2 新增
networkx>=3.0
matplotlib>=3.5.0
ebooklib>=0.18
pyvis>=0.3.2  # 可选：交互式图
jieba>=0.42.1  # 中文分词
```

### 项目结构调整

```
novel_distiller/
├── analyzers/
│   ├── character_extractor.py  # 已有
│   ├── plot_extractor.py       # 已有
│   ├── structure_analyzer.py   # 已有
│   ├── relationship_analyzer.py  # 新增：人物关系
│   ├── foreshadowing_detector.py # 新增：伏笔检测
│   ├── timeline_builder.py       # 新增：时间线
│   └── style_analyzer.py         # 新增：风格分析
├── loaders/
│   ├── txt_loader.py           # 已有
│   ├── chapter_splitter.py     # 已有
│   └── epub_loader.py          # 新增：EPUB 加载
├── exporters/
│   ├── json_exporter.py        # 已有
│   ├── markdown_exporter.py    # 已有
│   └── graph_exporter.py       # 新增：图谱导出
└── visualizers/                # 新增：可视化模块
    ├── relationship_visualizer.py
    └── timeline_visualizer.py
```

---

## 🎯 验收标准

### 功能完整性
- [ ] 人物关系图谱可生成并导出
- [ ] 伏笔检测准确率 > 70%
- [ ] 时间线事件完整
- [ ] 风格分析维度齐全
- [ ] EPUB 文件正常加载

### 代码质量
- [ ] 单元测试覆盖新功能
- [ ] 代码注释完整
- [ ] 符合现有代码风格

### 用户体验
- [ ] CLI 命令支持新功能
- [ ] 导出格式友好
- [ ] 错误提示清晰

---

## 🚀 开始开发

从 P0 功能开始：
1. 人物关系图谱
2. 伏笔检测与回收追踪
