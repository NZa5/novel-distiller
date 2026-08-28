"""
数据模型定义
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class CharacterRole(str, Enum):
    """人物角色类型"""
    PROTAGONIST = "protagonist"  # 主角
    MAJOR = "major"  # 主要配角
    MINOR = "minor"  # 次要配角
    VILLAIN = "villain"  # 反派
    SUPPORTING = "supporting"  # 路人/龙套


class PlotType(str, Enum):
    """情节类型"""
    MAIN = "main"  # 主线
    SUB = "sub"  # 支线
    FORESHADOWING = "foreshadowing"  # 伏笔


class NovelMeta(BaseModel):
    """小说元数据"""
    title: str = Field(description="小说标题")
    author: Optional[str] = Field(None, description="作者")
    total_chapters: int = Field(description="总章节数")
    total_words: int = Field(description="总字数")
    distill_date: datetime = Field(default_factory=datetime.now, description="蒸馏时间")
    genre: Optional[str] = Field(None, description="类型（玄幻/都市/历史等）")


class Chapter(BaseModel):
    """章节信息"""
    index: int = Field(description="章节序号")
    title: str = Field(description="章节标题")
    content: str = Field(description="章节内容")
    word_count: int = Field(description="字数")
    summary: Optional[str] = Field(None, description="章节摘要")
    start_line: int = Field(description="起始行号")
    end_line: int = Field(description="结束行号")


class Character(BaseModel):
    """人物信息"""
    name: str = Field(description="人物姓名")
    aliases: List[str] = Field(default_factory=list, description="别名列表")
    role: CharacterRole = Field(description="角色类型")
    description: str = Field(description="人物简介")
    first_appearance: int = Field(description="首次出现章节")
    key_traits: List[str] = Field(default_factory=list, description="关键特征")


class Plot(BaseModel):
    """情节信息"""
    type: PlotType = Field(description="情节类型")
    title: str = Field(description="情节标题")
    chapters: List[int] = Field(description="涉及章节列表")
    description: str = Field(description="情节描述")
    key_events: List[str] = Field(default_factory=list, description="关键事件")


class QualityMetrics(BaseModel):
    """质量评估指标"""
    completeness: float = Field(description="完整性得分 (0-1)")
    consistency: float = Field(description="一致性得分 (0-1)")
    coverage: float = Field(description="覆盖度得分 (0-1)")
    notes: List[str] = Field(default_factory=list, description="评估备注")


class DistillResult(BaseModel):
    """蒸馏结果"""
    meta: NovelMeta = Field(description="小说元数据")
    chapters: List[Chapter] = Field(description="章节列表")
    characters: List[Character] = Field(description="人物列表")
    plots: List[Plot] = Field(description="情节列表")
    quality_metrics: Optional[QualityMetrics] = Field(None, description="质量评估")
    
    @property
    def summary(self) -> str:
        """生成摘要"""
        return f"""
《{self.meta.title}》蒸馏报告

基本信息：
- 总章节：{self.meta.total_chapters}章
- 总字数：{self.meta.total_words:,}字
- 主要人物：{len([c for c in self.characters if c.role in [CharacterRole.PROTAGONIST, CharacterRole.MAJOR]])}人
- 情节线：{len(self.plots)}条

蒸馏时间：{self.meta.distill_date.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
    
    def get_protagonist(self) -> Optional[Character]:
        """获取主角"""
        protagonists = [c for c in self.characters if c.role == CharacterRole.PROTAGONIST]
        return protagonists[0] if protagonists else None
    
    def get_main_plots(self) -> List[Plot]:
        """获取主线情节"""
        return [p for p in self.plots if p.type == PlotType.MAIN]
