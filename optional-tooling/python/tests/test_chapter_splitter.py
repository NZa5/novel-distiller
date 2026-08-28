"""
测试章节分割器
"""

import pytest
from novel_distiller.loaders import ChapterSplitter


def test_chapter_splitter_basic():
    """测试基本章节分割"""
    content = """第一章 开端
这是第一章的内容。
这是更多内容。

第二章 发展
这是第二章的内容。
继续写第二章。

第三章 高潮
这是第三章的内容。
"""
    
    splitter = ChapterSplitter(min_chapter_length=10)
    chapters = splitter.split(content)
    
    assert len(chapters) == 3
    assert chapters[0].title == "第一章 开端"
    assert chapters[1].title == "第二章 发展"
    assert chapters[2].title == "第三章 高潮"


def test_chapter_splitter_no_chapters():
    """测试没有章节标记的情况"""
    content = "这是一段没有章节标记的文本内容。" * 100
    
    splitter = ChapterSplitter()
    chapters = splitter.split(content)
    
    assert len(chapters) == 1
    assert chapters[0].title == "全文"


def test_chapter_pattern_detection():
    """测试章节模式检测"""
    content = """第一章 开端
内容

第二章 发展
内容

第三章 高潮
内容
"""
    
    splitter = ChapterSplitter()
    pattern = splitter.detect_chapter_pattern(content)
    
    assert pattern is not None
    assert "第" in pattern
    assert "章" in pattern


def test_chapter_summary():
    """测试章节统计"""
    content = """第一章 短章
短内容

第二章 长章节
""" + "长内容。" * 100
    
    splitter = ChapterSplitter(min_chapter_length=10)
    chapters = splitter.split(content)
    summary = splitter.get_chapter_summary(chapters)
    
    assert summary["total_chapters"] == 2
    assert summary["total_words"] > 0
    assert summary["min_words"] < summary["max_words"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
