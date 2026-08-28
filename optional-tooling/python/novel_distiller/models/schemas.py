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


class CharacterRelation(BaseModel):
    """人物关系（Phase 2）"""
    source: str = Field(description="人物A")
    target: str = Field(description="人物B")
    relation_type: str = Field(description="关系类型（亲属/朋友/敌对/师徒/恋人/同事等）")
    description: str = Field(description="关系描述")
    chapters: List[int] = Field(default_factory=list, description="关系出现的章节")
    strength: float = Field(default=0.5, description="关系强度 0-1")


class Foreshadowing(BaseModel):
    """伏笔信息（Phase 2）"""
    id: str = Field(description="伏笔ID")
    title: str = Field(description="伏笔标题")
    planted_chapter: int = Field(description="埋设章节")
    planted_content: str = Field(description="埋设内容")
    revealed_chapter: Optional[int] = Field(None, description="回收章节")
    revealed_content: Optional[str] = Field(None, description="回收内容")
    status: str = Field(default="planted", description="状态: planted/revealed/abandoned")
    importance: str = Field(default="medium", description="重要程度: high/medium/low")
    description: str = Field(default="", description="伏笔描述")


class TimeReference(BaseModel):
    """时间引用（Phase 2）"""
    type: str = Field(description="类型: absolute(绝对时间)/relative(相对时间)/duration(时长)")
    text: str = Field(description="原文表述")
    normalized: Optional[str] = Field(None, description="标准化表述")
    offset_days: Optional[float] = Field(None, description="相对天数偏移")


class TimelineEvent(BaseModel):
    """时间线事件（Phase 2）"""
    id: str = Field(description="事件ID")
    title: str = Field(description="事件标题")
    description: str = Field(description="事件描述")
    chapter: int = Field(description="所在章节")
    content: str = Field(description="事件内容（原文引用）")
    time_reference: Optional[TimeReference] = Field(None, description="时间标记")
    estimated_day: Optional[float] = Field(None, description="估计的故事天数")
    participants: List[str] = Field(default_factory=list, description="参与人物")
    importance: str = Field(default="medium", description="重要程度: high/medium/low")
    event_type: str = Field(default="general", description="事件类型: battle/meeting/discovery/decision/general")


class NarrativePerspective(str, Enum):
    """叙事视角"""
    FIRST_PERSON = "first_person"  # 第一人称
    THIRD_PERSON_LIMITED = "third_person_limited"  # 第三人称限知
    THIRD_PERSON_OMNISCIENT = "third_person_omniscient"  # 第三人称全知
    MIXED = "mixed"  # 混合视角


class RhetoricalDevice(BaseModel):
    """修辞手法"""
    type: str = Field(description="修辞类型（比喻/拟人/排比/夸张等）")
    frequency: int = Field(description="出现频率")
    examples: List[str] = Field(default_factory=list, description="示例")


class VocabularyFeature(BaseModel):
    """词汇特征"""
    total_words: int = Field(description="总词数")
    unique_words: int = Field(description="独特词数")
    lexical_diversity: float = Field(description="词汇多样性（unique/total）")
    avg_word_length: float = Field(description="平均词长")
    top_words: List[tuple] = Field(default_factory=list, description="高频词（词，频次）")
    adjective_ratio: float = Field(description="形容词比例")
    verb_ratio: float = Field(description="动词比例")
    noun_ratio: float = Field(description="名词比例")


class SentenceFeature(BaseModel):
    """句式特征"""
    avg_sentence_length: float = Field(description="平均句长（字数）")
    short_sentence_ratio: float = Field(description="短句比例（<10字）")
    medium_sentence_ratio: float = Field(description="中句比例（10-30字）")
    long_sentence_ratio: float = Field(description="长句比例（>30字）")
    question_ratio: float = Field(description="疑问句比例")
    exclamation_ratio: float = Field(description="感叹句比例")


class NarrativePace(BaseModel):
    """叙事节奏"""
    dialogue_ratio: float = Field(description="对话比例")
    description_ratio: float = Field(description="描写比例")
    action_ratio: float = Field(description="动作比例")
    pace_score: float = Field(description="节奏得分（0-1，越高越快）")


class WritingStyle(BaseModel):
    """写作风格分析"""
    perspective: NarrativePerspective = Field(description="叙事视角")
    perspective_confidence: float = Field(description="视角判断置信度")
    pace: NarrativePace = Field(description="叙事节奏")
    rhetoric_devices: List[RhetoricalDevice] = Field(default_factory=list, description="修辞手法")
    vocabulary: VocabularyFeature = Field(description="词汇特征")
    sentence: SentenceFeature = Field(description="句式特征")
    style_summary: str = Field(description="风格总结")
    tone: str = Field(description="整体基调（轻松/严肃/幽默/悲伤等）")


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
    relations: List[CharacterRelation] = Field(default_factory=list, description="人物关系（Phase 2）")
    foreshadows: List[Foreshadowing] = Field(default_factory=list, description="伏笔列表（Phase 2）")
    timeline: List[TimelineEvent] = Field(default_factory=list, description="时间线事件（Phase 2）")
    writing_style: Optional[WritingStyle] = Field(None, description="写作风格（Phase 2）")
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
