"""
EPUB 文件加载器
"""

import os
from typing import List, Optional, Tuple
from ebooklib import epub
from ebooklib import ITEM_DOCUMENT
from bs4 import BeautifulSoup
from novel_distiller.utils.safe_text import sanitize_plain_text
from .epub_security import preflight_epub


class EpubLoader:
    """EPUB 文件加载器"""

    def __init__(self, extract_images: bool = False):
        """
        初始化加载器

        Args:
            extract_images: 是否提取图片信息（默认不提取）
        """
        self.extract_images = extract_images

    def load(self, file_path: str) -> str:
        """
        加载 EPUB 文件并返回纯文本内容

        Args:
            file_path: 文件路径

        Returns:
            文件内容（纯文本）

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 无效的 EPUB 文件
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        preflight_epub(file_path)
        try:
            book = epub.read_epub(file_path)
        except Exception as e:
            raise ValueError(f"无法解析 EPUB 文件: {e}")

        # 提取所有文档内容
        content_parts = []

        for item in book.get_items():
            if item.get_type() == ITEM_DOCUMENT:
                # 解析 HTML 内容
                html_content = item.get_content().decode('utf-8', errors='ignore')
                text = self._extract_text_from_html(html_content)
                if text.strip():
                    content_parts.append(text)

        return "\n\n".join(content_parts)

    def load_with_chapters(self, file_path: str) -> List[Tuple[str, str]]:
        """
        加载 EPUB 文件并识别章节结构

        Args:
            file_path: 文件路径

        Returns:
            章节列表，每个元素为 (章节标题, 章节内容) 的元组

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 无效的 EPUB 文件
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        preflight_epub(file_path)
        try:
            book = epub.read_epub(file_path)
        except Exception as e:
            raise ValueError(f"无法解析 EPUB 文件: {e}")

        chapters = []

        # 尝试从目录（TOC）获取章节信息
        toc = book.toc
        if toc:
            chapters = self._extract_from_toc(book, toc)

        # 如果目录为空或提取失败，回退到按文档项提取
        if not chapters:
            chapters = self._extract_from_spine(book)

        return chapters

    def _extract_from_toc(self, book: epub.EpubBook, toc: list) -> List[Tuple[str, str]]:
        """
        从目录结构提取章节

        Args:
            book: EPUB 书籍对象
            toc: 目录结构

        Returns:
            章节列表
        """
        chapters = []

        def process_toc_item(item):
            if isinstance(item, tuple):
                # 嵌套目录
                section, children = item
                if hasattr(section, 'title') and hasattr(section, 'href'):
                    title = section.title
                    content = self._get_content_by_href(book, section.href)
                    if content:
                        chapters.append((title, content))

                for child in children:
                    process_toc_item(child)
            elif hasattr(item, 'title') and hasattr(item, 'href'):
                # 单个章节项
                title = item.title
                content = self._get_content_by_href(book, item.href)
                if content:
                    chapters.append((title, content))

        for item in toc:
            process_toc_item(item)

        return chapters

    def _extract_from_spine(self, book: epub.EpubBook) -> List[Tuple[str, str]]:
        """
        从文档顺序提取章节（无目录时使用）

        Args:
            book: EPUB 书籍对象

        Returns:
            章节列表
        """
        chapters = []
        chapter_index = 0

        for item_id, _ in book.spine:
            item = book.get_item_with_id(item_id)
            if item and item.get_type() == ITEM_DOCUMENT:
                html_content = item.get_content().decode('utf-8', errors='ignore')
                text = self._extract_text_from_html(html_content)

                if text.strip():
                    # 尝试从 HTML 中提取标题
                    title = self._extract_title_from_html(html_content)
                    if not title:
                        chapter_index += 1
                        title = f"第{chapter_index}章"

                    chapters.append((title, text))

        return chapters

    def _get_content_by_href(self, book: epub.EpubBook, href: str) -> Optional[str]:
        """
        通过 href 获取内容

        Args:
            book: EPUB 书籍对象
            href: 链接地址

        Returns:
            内容文本，如果未找到返回 None
        """
        # 移除锚点
        href = href.split('#')[0]

        for item in book.get_items():
            if item.get_type() == ITEM_DOCUMENT:
                item_name = item.get_name()
                if item_name == href or item_name.endswith('/' + href):
                    html_content = item.get_content().decode('utf-8', errors='ignore')
                    return self._extract_text_from_html(html_content)

        return None

    def _extract_text_from_html(self, html_content: str) -> str:
        """
        从 HTML 内容中提取纯文本

        Args:
            html_content: HTML 内容

        Returns:
            纯文本内容
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove active content and URI/event attributes before extracting text.
        for script in soup(['script', 'style', 'form', 'iframe', 'object', 'embed', 'svg', 'math', 'link', 'meta']):
            script.decompose()
        for tag in soup.find_all(True):
            for attr in list(tag.attrs):
                if attr.lower().startswith('on') or attr.lower() in {'href','src','srcset','xlink:href','style'}:
                    del tag.attrs[attr]

        # 获取文本
        text = soup.get_text()

        # 清理多余空白
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return sanitize_plain_text(text)

    def _extract_title_from_html(self, html_content: str) -> Optional[str]:
        """
        从 HTML 中提取标题

        Args:
            html_content: HTML 内容

        Returns:
            标题文本，如果未找到返回 None
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # 尝试查找标题标签
        for tag in ['h1', 'h2', 'h3', 'title']:
            title_tag = soup.find(tag)
            if title_tag:
                title = title_tag.get_text().strip()
                if title:
                    return title

        return None

    def get_metadata(self, file_path: str) -> dict:
        """
        获取 EPUB 元数据

        Args:
            file_path: 文件路径

        Returns:
            元数据字典

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 无效的 EPUB 文件
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        preflight_epub(file_path)
        try:
            book = epub.read_epub(file_path)
        except Exception as e:
            raise ValueError(f"无法解析 EPUB 文件: {e}")

        metadata = {
            "title": self._get_metadata_value(book, 'title'),
            "creator": self._get_metadata_value(book, 'creator'),
            "language": self._get_metadata_value(book, 'language'),
            "publisher": self._get_metadata_value(book, 'publisher'),
            "identifier": self._get_metadata_value(book, 'identifier'),
            "file_size": os.path.getsize(file_path),
        }

        return metadata

    def _get_metadata_value(self, book: epub.EpubBook, key: str) -> Optional[str]:
        """
        获取元数据值

        Args:
            book: EPUB 书籍对象
            key: 元数据键

        Returns:
            元数据值，如果不存在返回 None
        """
        try:
            values = book.get_metadata('DC', key)
            if values:
                return values[0][0]
        except:
            pass

        return None

    def get_file_stats(self, file_path: str) -> dict:
        """
        获取文件统计信息

        Args:
            file_path: 文件路径

        Returns:
            统计信息字典
        """
        content = self.load(file_path)
        lines = content.splitlines()
        metadata = self.get_metadata(file_path)

        return {
            "file_size": os.path.getsize(file_path),
            "total_lines": len(lines),
            "total_chars": len(content),
            "total_words": len(content.replace("\n", "").replace(" ", "")),
            "title": metadata.get("title"),
            "author": metadata.get("creator"),
        }
