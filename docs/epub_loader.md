# EPUB 格式支持文档

## 概述

`EpubLoader` 是用于加载和解析 EPUB 格式电子书的工具类，支持提取文本内容、识别章节结构、获取元数据等功能。

## 文件路径

`novel_distiller/loaders/epub_loader.py`

## 核心功能

### 1. 文本提取

从 EPUB 文件中提取纯文本内容，自动处理 HTML 标签和格式。

```python
from novel_distiller.loaders import EpubLoader

loader = EpubLoader()
content = loader.load("novel.epub")
print(f"提取了 {len(content)} 字符")
```

### 2. 章节识别

智能识别 EPUB 的章节结构，支持两种模式：

- **TOC 模式**: 从 EPUB 目录（Table of Contents）提取章节
- **Spine 模式**: 从文档顺序提取章节（回退方案）

```python
loader = EpubLoader()
chapters = loader.load_with_chapters("novel.epub")

for title, content in chapters:
    print(f"{title}: {len(content)} 字符")
```

### 3. 元数据提取

提取 EPUB 文件的元数据信息：

```python
loader = EpubLoader()
metadata = loader.get_metadata("novel.epub")

# 返回字典包含:
# - title: 书名
# - creator: 作者
# - language: 语言
# - publisher: 出版社
# - identifier: ISBN 等标识符
# - file_size: 文件大小
```

### 4. 统计信息

获取文件的详细统计信息：

```python
loader = EpubLoader()
stats = loader.get_file_stats("novel.epub")

# 返回字典包含:
# - file_size: 文件大小（字节）
# - total_lines: 总行数
# - total_chars: 总字符数
# - total_words: 总字数（中文按字计）
# - title: 书名
# - author: 作者
```

### 5. 与 ChapterSplitter 集成

对于章节结构不清晰的 EPUB，可以配合 `ChapterSplitter` 使用：

```python
from novel_distiller.loaders import EpubLoader, ChapterSplitter

loader = EpubLoader()
splitter = ChapterSplitter(min_chapter_length=500)

# 先提取文本
content = loader.load("novel.epub")

# 再用 ChapterSplitter 分割
chapters = splitter.split(content)

for chapter in chapters:
    print(f"{chapter.index}. {chapter.title} ({chapter.word_count} 字)")
```

## 类接口说明

### EpubLoader

#### 构造函数

```python
def __init__(self, extract_images: bool = False)
```

**参数:**
- `extract_images`: 是否提取图片信息（默认 False，当前版本保留接口）

#### 主要方法

##### load(file_path: str) -> str

加载 EPUB 文件并返回纯文本内容。

**参数:**
- `file_path`: EPUB 文件路径

**返回:**
- 提取的纯文本内容

**异常:**
- `FileNotFoundError`: 文件不存在
- `ValueError`: 无效的 EPUB 文件

##### load_with_chapters(file_path: str) -> List[Tuple[str, str]]

加载 EPUB 文件并识别章节结构。

**参数:**
- `file_path`: EPUB 文件路径

**返回:**
- 章节列表，每个元素为 (章节标题, 章节内容) 的元组

**异常:**
- `FileNotFoundError`: 文件不存在
- `ValueError`: 无效的 EPUB 文件

##### get_metadata(file_path: str) -> dict

获取 EPUB 元数据。

**参数:**
- `file_path`: EPUB 文件路径

**返回:**
- 元数据字典

##### get_file_stats(file_path: str) -> dict

获取文件统计信息。

**参数:**
- `file_path`: EPUB 文件路径

**返回:**
- 统计信息字典

## 技术实现细节

### 依赖库

- `ebooklib`: EPUB 文件解析
- `beautifulsoup4`: HTML 内容提取

### HTML 处理

1. 移除 `<script>` 和 `<style>` 标签
2. 提取纯文本内容
3. 清理多余空白和换行
4. 保留段落结构

### 章节识别策略

1. **优先使用 TOC**: 如果 EPUB 包含目录结构，从目录提取章节信息
2. **递归处理嵌套**: 支持嵌套的章节目录结构（如部分 -> 章节）
3. **回退到 Spine**: 如果目录为空或提取失败，按文档顺序提取
4. **标题提取**: 尝试从 HTML 的 `<h1>`、`<h2>`、`<h3>`、`<title>` 标签提取标题
5. **自动命名**: 如果无法提取标题，自动生成"第N章"

### 字符编码处理

- 使用 UTF-8 解码，错误时忽略无效字符
- 确保兼容性和鲁棒性

## 使用场景

### 场景 1: 标准 EPUB 处理

对于结构良好的 EPUB 文件：

```python
loader = EpubLoader()
chapters = loader.load_with_chapters("novel.epub")
# 直接使用提取的章节
```

### 场景 2: 结构不清晰的 EPUB

对于章节标记不明确的 EPUB：

```python
loader = EpubLoader()
content = loader.load("novel.epub")

splitter = ChapterSplitter(min_chapter_length=500)
chapters = splitter.split(content)
# 使用模式匹配分割章节
```

### 场景 3: 与 NovelDistiller 集成

完整的小说处理流程：

```python
from novel_distiller import NovelDistiller
from novel_distiller.loaders import EpubLoader, ChapterSplitter

# 加载 EPUB
loader = EpubLoader()
content = loader.load("novel.epub")

# 分割章节
splitter = ChapterSplitter()
chapters = splitter.split(content)

# 创建蒸馏器处理
distiller = NovelDistiller(api_key="your-api-key")
# ... 后续处理
```

## 注意事项

1. **文件格式**: 仅支持标准的 EPUB 2.0 和 EPUB 3.0 格式
2. **编码问题**: 使用 UTF-8 解码，特殊字符可能被忽略
3. **图片处理**: 当前版本不提取图片，仅提取文本内容
4. **章节识别**: 识别准确度取决于 EPUB 文件的结构质量
5. **文件大小**: 大型 EPUB 文件可能需要较长加载时间

## 错误处理

所有方法都包含完善的错误处理：

- `FileNotFoundError`: 文件不存在时抛出
- `ValueError`: EPUB 文件损坏或格式无效时抛出
- 使用 `errors='ignore'` 处理编码错误，保证程序不会中断

## 性能优化建议

1. **缓存结果**: 对于需要多次访问的文件，可以缓存 `load()` 的结果
2. **按需加载**: 如果只需要元数据，使用 `get_metadata()` 而不是 `load()`
3. **章节分批处理**: 对于大型小说，可以分批处理章节

## 版本信息

- **文档说明**: EPUB 加载器属于可选 Python 工具；默认跨 Agent Skill 不依赖 Python 或外部 API。
- **适配版本**: Novel Distiller 0.2.0
- **依赖版本**: ebooklib>=0.18, beautifulsoup4>=4.12.0
