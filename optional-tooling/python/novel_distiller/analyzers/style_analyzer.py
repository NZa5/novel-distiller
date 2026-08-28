"""
风格分析器
"""

import re
from collections import Counter
from typing import List, Dict, Tuple
import jieba
import jieba.posseg as pseg
from ..models.schemas import (
    Chapter,
    WritingStyle,
    NarrativePerspective,
    NarrativePace,
    RhetoricalDevice,
    VocabularyFeature,
    SentenceFeature,
)
from ..utils.llm_client import LLMClient


class StyleAnalyzer:
    """风格分析器"""

    def __init__(self, llm_client: LLMClient):
        """
        初始化分析器

        Args:
            llm_client: LLM 客户端
        """
        self.llm = llm_client
        # 初始化 jieba（可以在这里添加自定义词典）
        jieba.initialize()

    def analyze(
        self,
        chapters: List[Chapter],
        sample_size: int = 10
    ) -> WritingStyle:
        """
        分析写作风格

        Args:
            chapters: 章节列表
            sample_size: 采样章节数（用于统计分析）

        Returns:
            写作风格分析结果
        """
        # 选择采样章节（前、中、后各取一些）
        sampled_chapters = self._sample_chapters(chapters, sample_size)

        # 合并采样文本
        sampled_text = "\n".join([ch.content for ch in sampled_chapters])

        # 1. 分析叙事视角（LLM）
        perspective, perspective_confidence = self._analyze_perspective(sampled_chapters)

        # 2. 分析叙事节奏（统计 + LLM）
        pace = self._analyze_pace(sampled_text)

        # 3. 分析修辞手法（LLM）
        rhetoric_devices = self._analyze_rhetoric(sampled_chapters[:3])

        # 4. 分析词汇特征（统计）
        vocabulary = self._analyze_vocabulary(sampled_text)

        # 5. 分析句式特征（统计）
        sentence = self._analyze_sentence(sampled_text)

        # 6. 生成风格总结和基调（LLM）
        style_summary, tone = self._generate_summary(
            sampled_chapters[:3],
            perspective,
            pace,
            vocabulary,
            sentence
        )

        return WritingStyle(
            perspective=perspective,
            perspective_confidence=perspective_confidence,
            pace=pace,
            rhetoric_devices=rhetoric_devices,
            vocabulary=vocabulary,
            sentence=sentence,
            style_summary=style_summary,
            tone=tone,
        )

    def _sample_chapters(
        self,
        chapters: List[Chapter],
        sample_size: int
    ) -> List[Chapter]:
        """
        采样章节（前、中、后均匀采样）

        Args:
            chapters: 章节列表
            sample_size: 采样数量

        Returns:
            采样的章节列表
        """
        if sample_size <= 0 or not chapters:
            return []
        if len(chapters) <= sample_size:
            return chapters

        # 均匀覆盖全文，且避免 sample_size<3 时 ``-0:`` 返回全部章节。
        indices = ([round(i * (len(chapters) - 1) / (sample_size - 1))
                    for i in range(sample_size)]
                   if sample_size > 1 else [0])
        return [chapters[i] for i in dict.fromkeys(indices)]

    def _analyze_perspective(
        self,
        chapters: List[Chapter]
    ) -> Tuple[NarrativePerspective, float]:
        """
        分析叙事视角

        Args:
            chapters: 章节列表

        Returns:
            (视角类型, 置信度)
        """
        # 统计第一人称标志词
        first_person_markers = ["我", "我们", "咱", "俺"]
        third_person_markers = ["他", "她", "它", "他们", "她们"]

        first_count = 0
        third_count = 0

        for ch in chapters[:3]:
            for marker in first_person_markers:
                first_count += ch.content.count(marker)
            for marker in third_person_markers:
                third_count += ch.content.count(marker)

        total = first_count + third_count
        if total == 0:
            return NarrativePerspective.THIRD_PERSON_LIMITED, 0.5

        first_ratio = first_count / total

        # 使用 LLM 确认
        try:
            system_message = """你是一个叙事学专家，擅长分析小说的叙事视角。
请判断以下文本采用的叙事视角：
1. first_person: 第一人称（"我"作为叙述者）
2. third_person_limited: 第三人称限知（通过某个角色视角叙述）
3. third_person_omniscient: 第三人称全知（上帝视角，知晓所有人想法）
4. mixed: 混合视角（多个视角切换）"""

            content_sample = "\n\n".join([
                f"第{ch.index}章片段:\n{ch.content[:500]}"
                for ch in chapters[:3]
            ])

            prompt = f"""请分析以下小说片段的叙事视角：

{content_sample}

请以 JSON 格式返回：
{{
  "perspective": "视角类型（first_person/third_person_limited/third_person_omniscient/mixed）",
  "confidence": 置信度（0-1之间的小数）,
  "reasoning": "判断理由"
}}"""

            response = self.llm.invoke_json(prompt, system_message)

            perspective_str = response.get("perspective", "third_person_limited")
            confidence = float(response.get("confidence", 0.7))

            # 结合统计结果调整置信度
            if perspective_str == "first_person" and first_ratio < 0.3:
                confidence *= 0.7
            elif perspective_str.startswith("third_person") and first_ratio > 0.5:
                confidence *= 0.7

            return NarrativePerspective(perspective_str), confidence

        except Exception as e:
            print(f"视角分析失败，使用统计结果: {e}")

            # 回退到统计判断
            if first_ratio > 0.6:
                return NarrativePerspective.FIRST_PERSON, 0.8
            elif first_ratio > 0.3:
                return NarrativePerspective.MIXED, 0.6
            else:
                return NarrativePerspective.THIRD_PERSON_LIMITED, 0.7

    def _analyze_pace(self, text: str) -> NarrativePace:
        """
        分析叙事节奏

        Args:
            text: 文本内容

        Returns:
            叙事节奏分析结果
        """
        # 检测对话（引号内容）
        dialogue_pattern = r'[「『""]([^」』""]+)[」』""]'
        dialogues = re.findall(dialogue_pattern, text)
        dialogue_chars = sum(len(d) for d in dialogues)

        # 检测动作词（使用词性标注）
        words = pseg.cut(text)
        verb_chars = 0
        total_chars = len(text)

        for word, flag in words:
            if flag.startswith('v'):  # 动词
                verb_chars += len(word)

        # 计算比例
        dialogue_ratio = dialogue_chars / total_chars if total_chars > 0 else 0
        action_ratio = verb_chars / total_chars if total_chars > 0 else 0
        description_ratio = max(0, 1 - dialogue_ratio - action_ratio)

        # 归一化
        total_ratio = dialogue_ratio + action_ratio + description_ratio
        if total_ratio > 0:
            dialogue_ratio /= total_ratio
            action_ratio /= total_ratio
            description_ratio /= total_ratio

        # 计算节奏得分（对话和动作越多，节奏越快）
        pace_score = dialogue_ratio * 0.6 + action_ratio * 0.4

        return NarrativePace(
            dialogue_ratio=round(dialogue_ratio, 3),
            description_ratio=round(description_ratio, 3),
            action_ratio=round(action_ratio, 3),
            pace_score=round(pace_score, 3),
        )

    def _analyze_rhetoric(
        self,
        chapters: List[Chapter]
    ) -> List[RhetoricalDevice]:
        """
        分析修辞手法

        Args:
            chapters: 章节列表

        Returns:
            修辞手法列表
        """
        try:
            system_message = """你是一个修辞学专家，擅长识别文学作品中的修辞手法。
常见修辞手法包括：比喻、拟人、排比、夸张、对偶、反问、设问、借代、双关、反复等。"""

            content_sample = "\n\n".join([
                f"第{ch.index}章片段:\n{ch.content[:800]}"
                for ch in chapters
            ])

            prompt = f"""请分析以下小说片段中使用的修辞手法：

{content_sample}

请识别出现频率较高的修辞手法（至少3种），并给出示例。

以 JSON 数组格式返回：
[
  {{
    "type": "修辞类型（如：比喻）",
    "frequency": 估计出现次数（整数）,
    "examples": ["示例1", "示例2"]
  }}
]"""

            response = self.llm.invoke_json(prompt, system_message)

            devices = []
            device_list = response if isinstance(response, list) else response.get("devices", [])

            for device_data in device_list:
                try:
                    devices.append(
                        RhetoricalDevice(
                            type=device_data["type"],
                            frequency=int(device_data.get("frequency", 1)),
                            examples=device_data.get("examples", [])[:3],  # 最多保留3个示例
                        )
                    )
                except (KeyError, ValueError) as e:
                    print(f"警告：跳过无效的修辞数据: {e}")
                    continue

            return devices

        except Exception as e:
            print(f"修辞分析失败: {e}")
            return []

    def _analyze_vocabulary(self, text: str) -> VocabularyFeature:
        """
        分析词汇特征

        Args:
            text: 文本内容

        Returns:
            词汇特征分析结果
        """
        # 分词
        words = list(jieba.cut(text))
        words = [w.strip() for w in words if w.strip() and len(w.strip()) > 1]

        # 词性标注
        words_pos = pseg.cut(text)

        # 统计各词性数量
        pos_counter = Counter()
        for word, flag in words_pos:
            if word.strip() and len(word.strip()) > 1:
                pos_counter[flag[0]] += 1  # 取词性首字母

        total_pos = sum(pos_counter.values())

        adjective_ratio = pos_counter.get('a', 0) / total_pos if total_pos > 0 else 0
        verb_ratio = pos_counter.get('v', 0) / total_pos if total_pos > 0 else 0
        noun_ratio = pos_counter.get('n', 0) / total_pos if total_pos > 0 else 0

        # 基本统计
        total_words = len(words)
        unique_words = len(set(words))
        lexical_diversity = unique_words / total_words if total_words > 0 else 0

        avg_word_length = sum(len(w) for w in words) / total_words if total_words > 0 else 0

        # 高频词（排除停用词）
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
                     '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
                     '你', '会', '着', '没有', '看', '好', '自己', '这', '那'}

        filtered_words = [w for w in words if w not in stopwords]
        word_counter = Counter(filtered_words)
        top_words = word_counter.most_common(10)

        return VocabularyFeature(
            total_words=total_words,
            unique_words=unique_words,
            lexical_diversity=round(lexical_diversity, 4),
            avg_word_length=round(avg_word_length, 2),
            top_words=top_words,
            adjective_ratio=round(adjective_ratio, 4),
            verb_ratio=round(verb_ratio, 4),
            noun_ratio=round(noun_ratio, 4),
        )

    def _analyze_sentence(self, text: str) -> SentenceFeature:
        """
        分析句式特征

        Args:
            text: 文本内容

        Returns:
            句式特征分析结果
        """
        # 分句（按句号、问号、感叹号）
        sentences = re.split(r'[。！？!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return SentenceFeature(
                avg_sentence_length=0,
                short_sentence_ratio=0,
                medium_sentence_ratio=0,
                long_sentence_ratio=0,
                question_ratio=0,
                exclamation_ratio=0,
            )

        # 句长统计
        sentence_lengths = [len(s) for s in sentences]
        avg_length = sum(sentence_lengths) / len(sentence_lengths)

        short_count = sum(1 for l in sentence_lengths if l < 10)
        medium_count = sum(1 for l in sentence_lengths if 10 <= l <= 30)
        long_count = sum(1 for l in sentence_lengths if l > 30)

        total = len(sentences)
        short_ratio = short_count / total
        medium_ratio = medium_count / total
        long_ratio = long_count / total

        # 标点统计
        question_count = text.count('？') + text.count('?')
        exclamation_count = text.count('！') + text.count('!')
        total_punctuation = text.count('。') + question_count + exclamation_count

        question_ratio = question_count / total_punctuation if total_punctuation > 0 else 0
        exclamation_ratio = exclamation_count / total_punctuation if total_punctuation > 0 else 0

        return SentenceFeature(
            avg_sentence_length=round(avg_length, 2),
            short_sentence_ratio=round(short_ratio, 3),
            medium_sentence_ratio=round(medium_ratio, 3),
            long_sentence_ratio=round(long_ratio, 3),
            question_ratio=round(question_ratio, 3),
            exclamation_ratio=round(exclamation_ratio, 3),
        )

    def _generate_summary(
        self,
        chapters: List[Chapter],
        perspective: NarrativePerspective,
        pace: NarrativePace,
        vocabulary: VocabularyFeature,
        sentence: SentenceFeature,
    ) -> Tuple[str, str]:
        """
        生成风格总结和基调

        Args:
            chapters: 章节列表
            perspective: 叙事视角
            pace: 叙事节奏
            vocabulary: 词汇特征
            sentence: 句式特征

        Returns:
            (风格总结, 基调)
        """
        perspective_map = {
            NarrativePerspective.FIRST_PERSON: "第一人称",
            NarrativePerspective.THIRD_PERSON_LIMITED: "第三人称限知",
            NarrativePerspective.THIRD_PERSON_OMNISCIENT: "第三人称全知",
            NarrativePerspective.MIXED: "混合视角",
        }

        try:
            system_message = """你是一个文学评论家，擅长分析小说的写作风格。
请根据提供的文本片段和统计数据，总结作者的写作风格特点和作品的整体基调。"""

            content_sample = "\n\n".join([
                f"第{ch.index}章片段:\n{ch.content[:600]}"
                for ch in chapters
            ])

            perspective_map = {
                NarrativePerspective.FIRST_PERSON: "第一人称",
                NarrativePerspective.THIRD_PERSON_LIMITED: "第三人称限知",
                NarrativePerspective.THIRD_PERSON_OMNISCIENT: "第三人称全知",
                NarrativePerspective.MIXED: "混合视角",
            }

            prompt = f"""请分析以下小说的写作风格：

文本片段：
{content_sample}

统计数据：
- 叙事视角：{perspective_map.get(perspective, "未知")}
- 对话比例：{pace.dialogue_ratio:.1%}
- 描写比例：{pace.description_ratio:.1%}
- 动作比例：{pace.action_ratio:.1%}
- 节奏得分：{pace.pace_score:.2f}（0-1，越高越快）
- 词汇多样性：{vocabulary.lexical_diversity:.2%}
- 平均句长：{sentence.avg_sentence_length:.1f}字
- 短句比例：{sentence.short_sentence_ratio:.1%}

请以 JSON 格式返回：
{{
  "style_summary": "风格总结（150-200字，描述语言特点、叙事节奏、表达方式等）",
  "tone": "整体基调（轻松/严肃/幽默/悲伤/热血/冷峻/温馨等，1-2个词）"
}}"""

            response = self.llm.invoke_json(prompt, system_message)

            return (
                response.get("style_summary", ""),
                response.get("tone", "中性"),
            )

        except Exception as e:
            print(f"风格总结生成失败: {e}")

            # 回退到简单总结
            pace_desc = "快节奏" if pace.pace_score > 0.6 else "慢节奏" if pace.pace_score < 0.4 else "中等节奏"

            summary = f"采用{perspective_map.get(perspective, '未知')}叙事，{pace_desc}，" \
                     f"对话占比{pace.dialogue_ratio:.0%}，描写占比{pace.description_ratio:.0%}。" \
                     f"词汇多样性为{vocabulary.lexical_diversity:.1%}，平均句长{sentence.avg_sentence_length:.0f}字。"

            return summary, "中性"
