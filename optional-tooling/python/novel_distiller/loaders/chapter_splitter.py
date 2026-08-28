"""
章节分割器
"""

import re
from typing import List, Tuple, Optional
from ..models.schemas import Chapter


class ChapterSplitter:
    """章节分割器"""

    # 常见章节标题模式
    CHAPTER_PATTERNS = [
        r"^第[零一二三四五六七八九十百千万0-9]+章",  # 第一章、第01章
        r"^第[零一二三四五六七八九十百千万0-9]+节",  # 第一节
        r"^第[零一二三四五六七八九十百千万0-9]+回",  # 第一回
        r"^Chapter\s*\d+",  # Chapter 1
        r"^CHAPTER\s*\d+",  # CHAPTER 1
        r"^\d+\.",  # 1.
        r"^\d+、",  # 1、
        r"^[零一二三四五六七八九十百千万0-9]+、",  # 一、
    ]

    def __init__(self, min_chapter_length: int = 500):
        """
        初始化分割器

        Args:
            min_chapter_length: 最小章节长度（字符数）
        """
        self.min_chapter_length = min_chapter_length
        self.patterns = [re.compile(p, re.MULTILINE) for p in self.CHAPTER_PATTERNS]

    def split(self, content: str) -> List[Chapter]:
        """
        分割章节

        Args:
            content: 小说内容

        Returns:
            章节列表
        """
        lines = content.splitlines()
        chapters = []
        current_chapter_lines = []
        current_title = None
        current_start_line = 0
        chapter_index = 0
        detected_chapter_title = False

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 检查是否是章节标题
            is_chapter_title = self._is_chapter_title(line)

            if is_chapter_title:
                detected_chapter_title = True
                if current_chapter_lines:
                    self._append_chapter(
                        chapters, current_chapter_lines, current_title,
                        current_start_line, i - 1, chapter_index
                    )
                    chapter_index = len(chapters)
                current_chapter_lines = []
                current_title = line
                current_start_line = i
            else:
                current_chapter_lines.append(line)

        # 保存最后一章
        if current_chapter_lines:
            self._append_chapter(
                chapters, current_chapter_lines, current_title,
                current_start_line, len(lines) - 1, chapter_index
            )

        if not detected_chapter_title and len(chapters) == 1:
            chapters[0].title = "全文"

        # 如果没有检测到章节，将整个内容作为单章
        if not chapters:
            chapters.append(
                Chapter(
                    index=1,
                    title="全文",
                    content=content.strip(),
                    word_count=len(content.replace("\n", "").replace(" ", "")),
                    start_line=0,
                    end_line=len(lines) - 1,
                )
            )

        return chapters

    def _append_chapter(
        self,
        chapters: List[Chapter],
        content_lines: List[str],
        title: Optional[str],
        start_line: int,
        end_line: int,
        previous_index: int,
    ) -> None:
        """Append a chapter when its body (or title plus body) meets the threshold."""
        body = "\n".join(content_lines).strip()
        # Include the heading in the threshold so short, valid chapters are not lost.
        measured_length = len("\n".join(filter(None, [title, body])))
        if measured_length < self.min_chapter_length:
            return
        chapter_index = previous_index + 1
        chapters.append(
            Chapter(
                index=chapter_index,
                title=title or f"第{chapter_index}章",
                content=body,
                word_count=len(body.replace("\n", "").replace(" ", "")),
                start_line=start_line,
                end_line=end_line,
            )
        )

    def _is_chapter_title(self, line: str) -> bool:
        """
        判断是否是章节标题

        Args:
            line: 行内容

        Returns:
            是否是章节标题
        """
        if not line or len(line) > 50:  # 标题通常不会太长
            return False

        for pattern in self.patterns:
            if pattern.match(line):
                return True

        return False

    def detect_chapter_pattern(self, content: str) -> Optional[str]:
        """
        检测章节标题模式

        Args:
            content: 小说内容

        Returns:
            检测到的模式（正则表达式字符串），如果未检测到则返回 None
        """
        lines = content.splitlines()

        for pattern_str, pattern in zip(self.CHAPTER_PATTERNS, self.patterns):
            matches = 0
            for line in lines:
                if pattern.match(line.strip()):
                    matches += 1

            # 如果匹配到多个，认为这是章节模式
            if matches >= 3:
                return pattern_str

        return None

    def get_chapter_summary(self, chapters: List[Chapter]) -> dict:
        """
        获取章节统计摘要

        Args:
            chapters: 章节列表

        Returns:
            统计信息
        """
        if not chapters:
            return {
                "total_chapters": 0,
                "total_words": 0,
                "avg_words_per_chapter": 0,
                "min_words": 0,
                "max_words": 0,
            }

        word_counts = [ch.word_count for ch in chapters]

        return {
            "total_chapters": len(chapters),
            "total_words": sum(word_counts),
            "avg_words_per_chapter": sum(word_counts) // len(word_counts),
            "min_words": min(word_counts),
            "max_words": max(word_counts),
        }
