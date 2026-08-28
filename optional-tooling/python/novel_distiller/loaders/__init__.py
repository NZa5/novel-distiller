"""
Loaders package
"""

from .txt_loader import TxtLoader
from .epub_loader import EpubLoader
from .chapter_splitter import ChapterSplitter

__all__ = ["TxtLoader", "EpubLoader", "ChapterSplitter"]
