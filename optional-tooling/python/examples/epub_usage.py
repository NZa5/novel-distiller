"""
EPUB 加载器使用示例
"""

from novel_distiller.loaders import EpubLoader, ChapterSplitter


def basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例 1: 基本文本提取")
    print("=" * 60)

    # 创建加载器
    loader = EpubLoader()

    # 加载 EPUB 文件
    file_path = "path/to/your/novel.epub"

    # 方法 1: 提取纯文本
    content = loader.load(file_path)
    print(f"提取文本长度: {len(content)} 字符")
    print(f"前 200 字符:\n{content[:200]}\n")


def load_with_chapters():
    """使用内置章节识别"""
    print("=" * 60)
    print("示例 2: 使用 EPUB 内置章节结构")
    print("=" * 60)

    loader = EpubLoader()
    file_path = "path/to/your/novel.epub"

    # 方法 2: 使用 EPUB 内置章节信息
    chapters = loader.load_with_chapters(file_path)

    print(f"检测到 {len(chapters)} 个章节:\n")
    for i, (title, content) in enumerate(chapters[:5], 1):
        word_count = len(content.replace("\n", "").replace(" ", ""))
        print(f"{i}. {title} ({word_count} 字)")

    if len(chapters) > 5:
        print(f"... 以及其他 {len(chapters) - 5} 章")


def use_with_chapter_splitter():
    """配合 ChapterSplitter 使用"""
    print("=" * 60)
    print("示例 3: 配合 ChapterSplitter 使用")
    print("=" * 60)

    loader = EpubLoader()
    splitter = ChapterSplitter(min_chapter_length=500)

    file_path = "path/to/your/novel.epub"

    # 方法 3: 先提取文本，再用 ChapterSplitter 分割
    # 适用于 EPUB 章节结构不清晰的情况
    content = loader.load(file_path)
    chapters = splitter.split(content)

    print(f"分割出 {len(chapters)} 个章节:\n")
    for chapter in chapters[:5]:
        print(f"{chapter.index}. {chapter.title} ({chapter.word_count} 字)")

    if len(chapters) > 5:
        print(f"... 以及其他 {len(chapters) - 5} 章")

    # 获取统计信息
    summary = splitter.get_chapter_summary(chapters)
    print(f"\n章节统计:")
    print(f"- 总章节数: {summary['total_chapters']}")
    print(f"- 总字数: {summary['total_words']:,}")
    print(f"- 平均每章: {summary['avg_words_per_chapter']:,} 字")
    print(f"- 最短章节: {summary['min_words']:,} 字")
    print(f"- 最长章节: {summary['max_words']:,} 字")


def get_metadata():
    """获取 EPUB 元数据"""
    print("=" * 60)
    print("示例 4: 获取元数据")
    print("=" * 60)

    loader = EpubLoader()
    file_path = "path/to/your/novel.epub"

    # 获取元数据
    metadata = loader.get_metadata(file_path)

    print("EPUB 元数据:")
    for key, value in metadata.items():
        if key == "file_size":
            print(f"- {key}: {value:,} 字节 ({value / 1024 / 1024:.2f} MB)")
        else:
            print(f"- {key}: {value}")

    print()

    # 获取统计信息
    stats = loader.get_file_stats(file_path)
    print("文件统计:")
    for key, value in stats.items():
        if key == "file_size":
            print(f"- {key}: {value:,} 字节")
        elif isinstance(value, int):
            print(f"- {key}: {value:,}")
        else:
            print(f"- {key}: {value}")


def complete_workflow():
    """完整工作流程"""
    print("=" * 60)
    print("示例 5: 完整工作流程")
    print("=" * 60)

    file_path = "path/to/your/novel.epub"

    # 步骤 1: 创建加载器并获取元数据
    loader = EpubLoader()
    metadata = loader.get_metadata(file_path)
    print(f"正在处理: 《{metadata.get('title', '未知')}》")
    print(f"作者: {metadata.get('creator', '未知')}\n")

    # 步骤 2: 尝试使用 EPUB 内置章节
    chapters_data = loader.load_with_chapters(file_path)

    if len(chapters_data) > 1:
        print(f"✓ 使用 EPUB 内置章节结构 ({len(chapters_data)} 章)")

        # 转换为 Chapter 对象（如果需要）
        from novel_distiller.models.schemas import Chapter
        chapters = []
        for idx, (title, content) in enumerate(chapters_data, 1):
            chapter = Chapter(
                index=idx,
                title=title,
                content=content,
                word_count=len(content.replace("\n", "").replace(" ", "")),
                start_line=0,  # EPUB 不适用行号
                end_line=0,
            )
            chapters.append(chapter)
    else:
        print("✗ EPUB 章节结构不清晰，使用 ChapterSplitter")

        # 步骤 3: 回退到文本分割
        content = loader.load(file_path)
        splitter = ChapterSplitter(min_chapter_length=500)
        chapters = splitter.split(content)
        print(f"✓ 分割完成 ({len(chapters)} 章)")

    # 显示结果
    print(f"\n章节列表:")
    for chapter in chapters[:3]:
        print(f"{chapter.index}. {chapter.title} ({chapter.word_count:,} 字)")

    if len(chapters) > 3:
        print(f"... 以及其他 {len(chapters) - 3} 章")

    print(f"\n总字数: {sum(ch.word_count for ch in chapters):,} 字")


if __name__ == "__main__":
    print("\nEPUB 加载器使用示例\n")

    # 取消注释想要运行的示例:

    # basic_usage()
    # load_with_chapters()
    # use_with_chapter_splitter()
    # get_metadata()
    # complete_workflow()

    print("\n提示: 请将 'path/to/your/novel.epub' 替换为实际文件路径")
    print("然后取消注释想要运行的示例函数")
