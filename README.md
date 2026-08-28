# 📚 Novel Distiller - 小说蒸馏 Skill

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个专注于从小说中提取和分析核心信息的 AI Skill，帮助作者学习参考作品、分析小说结构、提取人物关系和情节脉络。

## ✨ 核心功能

- 📖 **智能章节分割**：自动识别章节边界
- 👥 **人物提取**：识别主角、配角及其基本信息
- 📊 **情节提取**：提取主线事件、冲突点、转折点
- 🗺️ **结构分析**：分析叙事结构、卷/篇划分
- 📝 **报告生成**：输出 JSON 和 Markdown 格式的蒸馏报告
- 🔍 **质量检查**：完整性和一致性验证

## 🚀 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 配置

创建 `.env` 文件：

```env
# OpenAI 兼容接口配置
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，默认 OpenAI
OPENAI_MODEL=gpt-4o-mini  # 推荐使用便宜模型
```

### 使用示例

```python
from novel_distiller import NovelDistiller

# 初始化蒸馏器
distiller = NovelDistiller()

# 蒸馏小说
result = distiller.distill_novel(
    file_path="path/to/novel.txt",
    output_dir="output"
)

# 查看结果
print(result.summary)
```

### 命令行使用

```bash
# 基础蒸馏
python -m novel_distiller distill novel.txt

# 指定输出目录
python -m novel_distiller distill novel.txt --output output/

# 详细模式
python -m novel_distiller distill novel.txt --verbose
```

## 📋 输出格式

### JSON 结构

```json
{
  "meta": {
    "title": "小说标题",
    "author": "作者（如果能识别）",
    "total_chapters": 120,
    "total_words": 250000,
    "distill_date": "2024-01-01T12:00:00"
  },
  "chapters": [
    {
      "index": 1,
      "title": "第一章 开端",
      "word_count": 2500,
      "summary": "章节摘要"
    }
  ],
  "characters": [
    {
      "name": "主角姓名",
      "aliases": ["别名1", "别名2"],
      "role": "protagonist",
      "description": "人物简介",
      "first_appearance": 1
    }
  ],
  "plots": [
    {
      "type": "main",
      "title": "主线情节1",
      "chapters": [1, 5, 10],
      "description": "情节描述"
    }
  ]
}
```

### Markdown 报告

- 小说元数据
- 章节列表
- 人物档案
- 情节脉络
- 统计信息

## 🛠️ 技术架构

```
novel-distiller/
├── novel_distiller/           # 核心包
│   ├── __init__.py
│   ├── distiller.py          # 主入口
│   ├── loaders/              # 文本加载器
│   │   ├── __init__.py
│   │   ├── txt_loader.py
│   │   └── chapter_splitter.py
│   ├── analyzers/            # 分析器
│   │   ├── __init__.py
│   │   ├── character_extractor.py
│   │   ├── plot_extractor.py
│   │   └── structure_analyzer.py
│   ├── exporters/            # 导出器
│   │   ├── __init__.py
│   │   ├── json_exporter.py
│   │   └── markdown_exporter.py
│   ├── models/               # 数据模型
│   │   ├── __init__.py
│   │   └── schemas.py
│   └── utils/                # 工具函数
│       ├── __init__.py
│       └── llm_client.py
├── tests/                    # 测试
├── examples/                 # 示例
├── SKILL.md                  # Skill 定义
├── requirements.txt
└── README.md
```

## 📦 依赖

- **langchain**: LLM 抽象层
- **openai**: OpenAI SDK
- **pydantic**: 数据验证
- **python-dotenv**: 环境变量管理

## 🎯 MVP Phase 1 功能

- ✅ TXT 文件支持
- ✅ 自动章节分割
- ✅ 主要人物提取（姓名、简介）
- ✅ 主线情节提取（关键事件）
- ✅ JSON + Markdown 输出

## 🔮 未来规划

### Phase 2 (深度分析)
- 人物关系图谱
- 时间线重建
- 伏笔检测
- 风格分析

### Phase 3 (高级功能)
- EPUB 支持
- 网文平台爬虫
- 对比分析
- Web 可视化界面

## 📖 使用场景

- **网文作者学习**：分析对标作品的结构和人物设定
- **阅读辅助**：快速了解小说脉络
- **创作辅助**：提取参考书的写作风格
- **数据分析**：批量分析小说数据

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

本项目参考了以下开源项目的设计思路：
- [novel_writer_agent](https://github.com/nonever2109/novel_writer_agent) - 故事记忆结构
- [timeline-novel-agent](https://github.com/kang01037/timeline-novel-agent) - ReAct 模式设计
