"""
Analyzers package
"""

from .character_extractor import CharacterExtractor
from .plot_extractor import PlotExtractor
from .structure_analyzer import StructureAnalyzer
from .relationship_analyzer import RelationshipAnalyzer
from .foreshadowing_detector import ForeshadowingDetector

__all__ = [
    "CharacterExtractor",
    "PlotExtractor",
    "StructureAnalyzer",
    "RelationshipAnalyzer",
    "ForeshadowingDetector",
]
