---
name: novel-distiller
description: >
  小说蒸馏 Skill - 从小说中提取和分析核心信息。
  
  主要功能：
  - 自动章节分割
  - 人物提取（主角、配角、姓名、别名、简介）
  - 情节提取（主线事件、冲突点、转折点）
  - 结构分析（章节、卷、篇）
  - 报告生成（JSON + Markdown）
  
  适用场景：
  - 网文作者学习对标作品
  - 快速了解小说脉络
  - 提取参考书的写作风格
  - 批量分析小说数据

triggers:
  - 蒸馏: 蒸馏这本小说/distill novel/提取小说信息/分析小说结构
  - 分析: 分析小说/analyze novel/小说分析
  - 提取: 提取人物/extract characters/提取情节/extract plots

metadata:
  version: "0.1.0"
  author: "Novel Distiller Team"
  repository: "https://github.com/yourusername/novel-distiller"
---

# Novel Distiller Skill

## 触发词

当用户说以下关键词时，激活本 Skill：

- **蒸馏小说**：`蒸馏这本小说`、`distill novel`、`提取小说信息`
- **分析小说**：`分析小说结构`、`analyze novel`、`小说分析`
- **提取元素**：`提取人物`、`提取情节`、`extract characters`

## 使用流程

### 1. 接收输入

支持以下输入方式：

```
用户：蒸馏这本小说 [文件路径]
用户：分析这段小说内容：[粘贴文本]
```

### 2. 执行蒸馏

系统自动完成：

1. **文本加载**：读取文件内容
2. **章节分割**：识别章节边界
3. **人物提取**：识别主要人物及其信息
4. **情节提取**：提取关键事件和冲突
5. **报告生成**：输出结构化结果

### 3. 输出结果

生成以下文件：

```
output/
├── novel_meta.json          # 元数据
├── characters.json          # 人物档案
├── plots.json              # 情节脉络
└── report.md               # Markdown 报告
```

## 配置要求

### 环境变量

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选
OPENAI_MODEL=gpt-4o-mini                    # 推荐
```

### Python 依赖

```bash
pip install langchain openai pydantic python-dotenv
```

## 命令示例

```python
from novel_distiller import NovelDistiller

# 初始化
distiller = NovelDistiller()

# 蒸馏小说
result = distiller.distill_novel(
    file_path="novel.txt",
    output_dir="output"
)

# 查看摘要
print(result.summary)

# 导出报告
result.export_markdown("report.md")
result.export_json("result.json")
```

## 高级选项

### 自定义提取深度

```python
# 仅提取人物
result = distiller.distill_novel(
    file_path="novel.txt",
    extract_characters=True,
    extract_plots=False
)

# 详细模式
result = distiller.distill_novel(
    file_path="novel.txt",
    verbose=True  # 显示提取过程
)
```

### 批量处理

```python
# 批量蒸馏多本小说
novels = ["novel1.txt", "novel2.txt", "novel3.txt"]
results = distiller.batch_distill(novels)
```

## 输出示例

### Markdown 报告

```markdown
# 《小说标题》蒸馏报告

## 基本信息
- 总章节：120章
- 总字数：250,000字
- 蒸馏时间：2024-01-01

## 主要人物
### 主角：张三
- 别名：阿三、三哥
- 简介：普通青年，机缘巧合下获得系统
- 首次出现：第1章

### 配角：李四
- 别名：四爷
- 简介：主角的好友
- 首次出现：第3章

## 情节脉络
### 主线
1. 第1-10章：获得系统，初期成长
2. 第11-30章：遇到第一个大危机
3. 第31-50章：实力提升，结识伙伴
```

### JSON 结构

```json
{
  "meta": {
    "title": "小说标题",
    "total_chapters": 120,
    "total_words": 250000
  },
  "characters": [
    {
      "name": "张三",
      "role": "protagonist",
      "description": "主角简介"
    }
  ],
  "plots": [
    {
      "type": "main",
      "title": "获得系统",
      "chapters": [1, 2, 3]
    }
  ]
}
```

## 注意事项

1. **Token 消耗**：长篇小说（10万字+）会消耗较多 Token，建议使用便宜模型
2. **准确率**：人物识别准确率约 85-90%，情节提取约 80%
3. **处理时间**：10万字小说约需 3-5 分钟
4. **文件格式**：当前仅支持 UTF-8 编码的 TXT 文件

## 错误处理

```python
try:
    result = distiller.distill_novel("novel.txt")
except FileNotFoundError:
    print("文件不存在")
except UnicodeDecodeError:
    print("文件编码错误，请使用 UTF-8")
except Exception as e:
    print(f"蒸馏失败：{e}")
```

## 质量评估

蒸馏完成后，系统会自动评估：

- **完整性**：是否提取了所有主要人物
- **一致性**：人物信息是否矛盾
- **覆盖度**：蒸馏了多少百分比的内容

评分示例：

```
完整性：90%（提取了 9/10 个主要人物）
一致性：95%（无明显矛盾）
覆盖度：85%（覆盖了 85% 的章节）
```

## 常见问题

### Q: 支持哪些文件格式？
A: 当前支持 TXT（UTF-8）。EPUB 和 PDF 支持将在 Phase 2 添加。

### Q: 如何降低 Token 成本？
A: 使用便宜模型（如 gpt-4o-mini、claude-3.5-haiku），或只提取部分内容。

### Q: 提取准确率如何提高？
A: 使用更好的模型（GPT-4），或手动校验后修正。

## 版本历史

- **v0.1.0** (2024-01): MVP Phase 1 - 基础蒸馏功能
  - TXT 文件支持
  - 章节分割
  - 人物和情节提取
  - JSON/Markdown 导出

## 未来计划

- **v0.2.0**: Phase 2 - 深度分析
  - 人物关系图谱
  - 时间线重建
  - 伏笔检测

- **v0.3.0**: Phase 3 - 高级功能
  - EPUB 支持
  - 网文爬虫
  - Web 可视化
