# 快速开始指南

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/novel-distiller.git
cd novel-distiller
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或者安装为开发模式：

```bash
pip install -e .
```

### 3. 配置环境变量

复制示例配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Key：

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### 4. 运行测试

```bash
python examples/basic_usage.py
```

## 基础使用

### Python API

```python
from novel_distiller import NovelDistiller

# 初始化
distiller = NovelDistiller()

# 蒸馏小说
result = distiller.distill_novel(
    file_path="your_novel.txt",
    output_dir="output",
    verbose=True
)

# 查看结果
print(result.summary)
print(f"提取到 {len(result.characters)} 个人物")
print(f"提取到 {len(result.plots)} 条情节线")
```

### 命令行

```bash
# 基础使用
python -m novel_distiller distill novel.txt

# 详细模式
python -m novel_distiller distill novel.txt --verbose

# 指定输出目录
python -m novel_distiller distill novel.txt --output my_output/

# 只提取人物
python -m novel_distiller distill novel.txt --no-plots

# 批量处理
python -m novel_distiller batch novel1.txt novel2.txt novel3.txt
```

## 输出结果

蒸馏完成后，会在输出目录生成以下文件：

```
output/
├── novel_meta.json          # 小说元数据
├── chapters.json            # 章节列表
├── characters.json          # 人物档案
├── plots.json              # 情节脉络
├── quality_metrics.json    # 质量评估
├── full_result.json        # 完整结果
└── report.md               # Markdown 报告
```

## 支持的 API 提供商

### OpenAI

```env
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### DeepSeek

```env
OPENAI_API_KEY=your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

### OpenRouter

```env
OPENAI_API_KEY=your-openrouter-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=anthropic/claude-3.5-haiku
```

### 硅基流动

```env
OPENAI_API_KEY=your-siliconflow-key
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_MODEL=Qwen/Qwen2.5-7B-Instruct
```

## 常见问题

### Q: 提示 API Key 未设置

确保 `.env` 文件存在且包含正确的 `OPENAI_API_KEY`。

### Q: 文件编码错误

支持 UTF-8、GBK、GB2312 编码。如果仍有问题，请转换文件为 UTF-8。

### Q: Token 消耗过大

- 使用便宜的模型（如 gpt-4o-mini）
- 减少分析的章节数（默认前 30 章）
- 只提取人物或情节（使用 `--no-plots` 或 `--no-characters`）

### Q: 提取准确率不高

- 使用更好的模型（如 GPT-4）
- 确保小说格式规范（章节标题清晰）
- 手动校验并修正 JSON 输出

## 下一步

- 查看 [完整文档](README.md)
- 阅读 [Skill 定义](SKILL.md)
- 运行 [测试用例](tests/)
- 查看 [示例代码](examples/)

## 获取帮助

遇到问题？

1. 查看 [GitHub Issues](https://github.com/yourusername/novel-distiller/issues)
2. 提交新的 Issue
3. 查看项目文档

## License

MIT License - 详见 [LICENSE](LICENSE)
