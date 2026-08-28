"""
Novel Distiller - 小说蒸馏工具

从小说中提取和分析核心信息的 AI Skill
"""

__version__ = "0.3.0"
__author__ = "Novel Distiller Team"

from .distiller import NovelDistiller
from .models.schemas import (
    NovelMeta,
    Chapter,
    Character,
    Plot,
    DistillResult,
)

__all__ = [
    "NovelDistiller",
    "NovelMeta",
    "Chapter",
    "Character",
    "Plot",
    "DistillResult",
]
