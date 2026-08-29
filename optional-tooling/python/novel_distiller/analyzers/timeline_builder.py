"""
时间线重建器 (Phase 2)
"""

from typing import List, Dict, Optional, Tuple
import re
from ..models.schemas import Chapter, Character, TimelineEvent, TimeReference
from ..utils.llm_client import LLMClient


class TimelineBuilder:
    """时间线重建器"""

    # 常见时间标记模式
    TIME_PATTERNS = {
        'relative': [
            r'(\d+)天(?:后|之后)',
            r'(\d+)天(?:前|之前)',
            r'次日',
            r'第二天',
            r'第三天',
            r'隔日',
            r'当天',
            r'今天',
            r'昨天',
            r'明天',
            r'(\d+)[个]?月(?:后|之后)',
            r'(\d+)[个]?月(?:前|之前)',
            r'(\d+)年(?:后|之后)',
            r'(\d+)年(?:前|之前)',
            r'半[个]?月(?:后|之前|前)',
            r'一周(?:后|之后|前|之前)',
            r'几天[后之]后',
        ],
        'absolute': [
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{1,2}月\d{1,2}日',
            r'[春夏秋冬][天季]',
        ],
        'duration': [
            r'(\d+)天',
            r'(\d+)[个]?小时',
            r'(\d+)分钟',
            r'(\d+)[个]?月',
            r'(\d+)年',
        ]
    }

    def __init__(self, llm_client: LLMClient):
        """
        初始化时间线重建器

        Args:
            llm_client: LLM 客户端
        """
        self.llm = llm_client

    def build_timeline(
        self,
        chapters: List[Chapter],
        characters: List[Character],
        max_chapters: int = 50
    ) -> List[TimelineEvent]:
        """
        构建时间线

        Args:
            chapters: 章节列表
            characters: 人物列表
            max_chapters: 最多分析的章节数

        Returns:
            时间线事件列表
        """
        if not chapters:
            return []

        # 步骤1: 提取关键事件
        events = self._extract_events(chapters[:max_chapters], characters)

        if not events:
            return []

        # 步骤2: 提取时间标记
        for event in events:
            chapter = next((ch for ch in chapters if ch.index == event.chapter), None)
            if chapter:
                event.time_reference = self._extract_time_reference(
                    chapter.content,
                    event.content
                )

        # 步骤3: 建立时间关系
        self._establish_temporal_relations(events)

        # 步骤4: 估算事件时间
        self._estimate_event_times(events)

        return events

    def _extract_events(
        self,
        chapters: List[Chapter],
        characters: List[Character]
    ) -> List[TimelineEvent]:
        """提取关键事件"""
        events = []
        event_id = 1

        # 构建人物名称列表
        character_names = [char.name for char in characters]
        for char in characters:
            character_names.extend(char.aliases)

        for chapter in chapters:
            try:
                system_message = """你是一个小说情节分析专家。
请识别章节中的关键事件。

关键事件标准：
- 推动情节发展的重要事件
- 人物之间的重要互动
- 重大决策或转折
- 战斗、会面、发现、告别等

每章通常有 1-3 个关键事件。"""

                # 限制内容长度
                content_preview = chapter.content[:2500]

                char_info = f"主要人物：{', '.join(character_names[:10])}" if character_names else ""

                prompt = f"""请分析以下章节中的关键事件：

章节：第{chapter.index}章 {chapter.title}
{char_info}

内容：
{content_preview}

请返回 JSON 数组，每个事件包含：
- title: 事件标题（5-15字）
- description: 事件描述（一句话）
- content: 事件内容（原文关键片段，50-200字）
- participants: 参与人物列表（从已知人物中选择）
- importance: 重要程度（high/medium/low）
- event_type: 事件类型（battle/meeting/discovery/decision/general）

每章返回 1-3 个最重要的事件。"""

                response = self.llm.invoke_json(prompt, system_message)

                # 解析响应
                event_list = response if isinstance(response, list) else response.get('events', [])

                for event_data in event_list:
                    if 'title' in event_data and 'description' in event_data:
                        event = TimelineEvent(
                            id=f"EVT{event_id:03d}",
                            title=event_data['title'],
                            description=event_data['description'],
                            chapter=chapter.index,
                            content=event_data.get('content', ''),
                            participants=event_data.get('participants', []),
                            importance=event_data.get('importance', 'medium'),
                            event_type=event_data.get('event_type', 'general')
                        )
                        events.append(event)
                        event_id += 1

            except Exception as e:
                # 出错时跳过本章
                continue

        return events

    def _extract_time_reference(
        self,
        chapter_content: str,
        event_content: str
    ) -> Optional[TimeReference]:
        """提取时间标记"""

        # 在事件内容及其上下文中搜索时间标记
        search_text = event_content

        # 扩展搜索范围：在章节内容中找到事件位置，取前后文
        try:
            event_pos = chapter_content.find(event_content[:50])
            if event_pos > 0:
                # 取事件前后各200字
                start = max(0, event_pos - 200)
                end = min(len(chapter_content), event_pos + len(event_content) + 200)
                search_text = chapter_content[start:end]
        except:
            pass

        # 按优先级搜索时间模式
        for time_type in ['absolute', 'relative', 'duration']:
            for pattern in self.TIME_PATTERNS[time_type]:
                match = re.search(pattern, search_text)
                if match:
                    matched_text = match.group(0)
                    normalized = self._normalize_time_expression(matched_text, time_type)
                    offset = self._calculate_offset_days(matched_text, time_type)

                    return TimeReference(
                        type=time_type,
                        text=matched_text,
                        normalized=normalized,
                        offset_days=offset
                    )

        return None

    def _normalize_time_expression(self, text: str, time_type: str) -> str:
        """标准化时间表达"""

        # 相对时间标准化
        if time_type == 'relative':
            replacements = {
                '次日': '1天后',
                '第二天': '1天后',
                '第三天': '2天后',
                '隔日': '1天后',
                '当天': '0天',
                '今天': '0天',
                '昨天': '1天前',
                '明天': '1天后',
                '半个月后': '15天后',
                '半月后': '15天后',
                '一周后': '7天后',
            }

            for old, new in replacements.items():
                if old in text:
                    return new

            return text

        return text

    def _calculate_offset_days(self, text: str, time_type: str) -> Optional[float]:
        """计算天数偏移"""

        if time_type != 'relative':
            return None

        # 提取数字
        match = re.search(r'(\d+)', text)
        if not match:
            # 特殊处理无数字的情况
            if '次日' in text or '第二天' in text or '隔日' in text or '明天' in text:
                return 1.0
            elif '第三天' in text:
                return 2.0
            elif '当天' in text or '今天' in text:
                return 0.0
            elif '昨天' in text:
                return -1.0
            elif '半月' in text or '半个月' in text:
                return 15.0 if '后' in text else -15.0
            elif '一周' in text:
                return 7.0 if '后' in text else -7.0
            return None

        num = float(match.group(1))

        # 判断方向和单位
        direction = 1.0 if '后' in text else -1.0

        if '年' in text:
            return num * 365 * direction
        elif '月' in text:
            return num * 30 * direction
        elif '天' in text:
            return num * direction
        elif '周' in text:
            return num * 7 * direction
        elif '小时' in text:
            return num / 24 * direction

        return None

    def _establish_temporal_relations(self, events: List[TimelineEvent]):
        """建立事件间的时间关系"""

        if len(events) < 2:
            return

        # 使用 LLM 分析复杂的时间关系
        for i in range(len(events) - 1):
            current = events[i]
            next_event = events[i + 1]

            # 如果都有明确的时间标记，跳过
            if current.time_reference and next_event.time_reference:
                continue

            # 如果跨章节较多，使用 LLM 分析
            if abs(next_event.chapter - current.chapter) > 1:
                self._analyze_temporal_relation(current, next_event)

    def _analyze_temporal_relation(
        self,
        event1: TimelineEvent,
        event2: TimelineEvent
    ):
        """使用 LLM 分析两个事件的时间关系"""

        try:
            system_message = """你是一个时间关系分析专家。
请分析两个事件之间的时间关系。"""

            prompt = f"""请分析以下两个事件的时间关系：

事件1：
- 章节：第{event1.chapter}章
- 标题：{event1.title}
- 描述：{event1.description}
- 时间标记：{event1.time_reference.text if event1.time_reference else '无'}

事件2：
- 章节：第{event2.chapter}章
- 标题：{event2.title}
- 描述：{event2.description}
- 时间标记：{event2.time_reference.text if event2.time_reference else '无'}

问题：事件2 相对于事件1，大约过去了多少天？

请返回 JSON：
{{
  "days": 估算的天数（可以是小数，如 0.5 表示半天）,
  "confidence": 置信度（high/medium/low）,
  "reasoning": 推理过程
}}

如果无法估算，返回 {{"days": null}}"""

            response = self.llm.invoke_json(prompt, system_message)

            days = response.get('days')
            if days is not None and response.get('confidence') in ['high', 'medium']:
                # 如果事件2没有时间标记，添加一个推断的标记
                if not event2.time_reference:
                    event2.time_reference = TimeReference(
                        type='relative',
                        text=f'约{days}天后（推断）',
                        normalized=f'{days}天后',
                        offset_days=float(days)
                    )

        except Exception:
            pass

    def _estimate_event_times(self, events: List[TimelineEvent]):
        """估算事件的绝对时间（故事第N天）"""

        if not events:
            return

        # 第一个事件作为起点（故事第0天）
        events[0].estimated_day = 0.0
        current_day = 0.0

        for i in range(1, len(events)):
            prev_event = events[i - 1]
            current_event = events[i]

            # 如果有明确的时间偏移
            if current_event.time_reference and current_event.time_reference.offset_days is not None:
                if prev_event.estimated_day is not None:
                    current_event.estimated_day = prev_event.estimated_day + current_event.time_reference.offset_days
                    current_day = current_event.estimated_day
            else:
                # 根据章节间隔估算
                chapter_gap = current_event.chapter - prev_event.chapter

                if chapter_gap == 0:
                    # 同一章，估计同一天
                    current_event.estimated_day = current_day
                elif chapter_gap == 1:
                    # 相邻章节，估计相隔 0.5-1 天
                    estimated_gap = 1.0
                    current_day += estimated_gap
                    current_event.estimated_day = current_day
                else:
                    # 跨越多章，按比例估算
                    estimated_gap = chapter_gap * 1.5
                    current_day += estimated_gap
                    current_event.estimated_day = current_day

    def get_timeline_summary(self, events: List[TimelineEvent]) -> Dict:
        """
        获取时间线统计摘要

        Args:
            events: 事件列表

        Returns:
            统计信息字典
        """
        if not events:
            return {
                "total_events": 0,
                "span_days": 0,
                "events_per_day": 0,
                "event_types": {},
                "chapters_covered": 0
            }

        # 统计事件类型
        type_counts = {}
        for event in events:
            type_counts[event.event_type] = type_counts.get(event.event_type, 0) + 1

        # 计算时间跨度
        estimated_days = [e.estimated_day for e in events if e.estimated_day is not None]
        span_days = max(estimated_days) - min(estimated_days) if estimated_days else 0

        # 统计覆盖的章节
        chapters = set(e.chapter for e in events)

        return {
            "total_events": len(events),
            "span_days": span_days,
            "events_per_day": len(events) / max(span_days, 1),
            "event_types": type_counts,
            "chapters_covered": len(chapters),
            "time_markers": len([e for e in events if e.time_reference is not None])
        }

    def export_timeline_text(self, events: List[TimelineEvent]) -> str:
        """
        导出时间线为文本格式

        Args:
            events: 事件列表

        Returns:
            格式化的时间线文本
        """
        if not events:
            return "时间线为空"

        lines = ["=" * 60, "时间线", "=" * 60, ""]

        for event in events:
            # 时间信息
            time_info = ""
            if event.estimated_day is not None:
                time_info = f"[第{event.estimated_day:.1f}天]"

            # 时间标记
            time_marker = ""
            if event.time_reference:
                time_marker = f" ({event.time_reference.text})"

            # 事件信息
            lines.append(f"{time_info} 第{event.chapter}章{time_marker}")
            lines.append(f"  {event.title}")
            lines.append(f"  {event.description}")

            if event.participants:
                lines.append(f"  参与：{', '.join(event.participants[:5])}")

            lines.append("")

        return "\n".join(lines)
