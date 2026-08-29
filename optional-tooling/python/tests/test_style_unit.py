"""
风格分析器单元测试（不需要 LLM）
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from novel_distiller.models.schemas import (
    Chapter,
    NarrativePerspective,
    WritingStyle,
)


def test_imports():
    """测试模块导入"""
    print("测试 1: 模块导入")

    try:
        from novel_distiller.analyzers.style_analyzer import StyleAnalyzer
        print("  OK - StyleAnalyzer 导入成功")

        from novel_distiller.models.schemas import (
            NarrativePerspective,
            RhetoricalDevice,
            VocabularyFeature,
            SentenceFeature,
            NarrativePace,
            WritingStyle,
        )
        print("  OK - 所有数据模型导入成功")

    except Exception as e:
        raise AssertionError("module imports failed") from e


def test_data_models():
    """测试数据模型"""
    print("\n测试 2: 数据模型创建")

    try:
        from novel_distiller.models.schemas import (
            NarrativePerspective,
            RhetoricalDevice,
            VocabularyFeature,
            SentenceFeature,
            NarrativePace,
            WritingStyle,
        )

        # 测试叙事视角枚举
        perspective = NarrativePerspective.FIRST_PERSON
        print(f"  OK - 叙事视角: {perspective.value}")

        # 测试修辞手法
        device = RhetoricalDevice(
            type="比喻",
            frequency=5,
            examples=["像一阵风", "如同星辰"]
        )
        print(f"  OK - 修辞手法: {device.type}, 频率: {device.frequency}")

        # 测试词汇特征
        vocab = VocabularyFeature(
            total_words=1000,
            unique_words=500,
            lexical_diversity=0.5,
            avg_word_length=2.5,
            top_words=[("我", 50), ("他", 30)],
            adjective_ratio=0.15,
            verb_ratio=0.25,
            noun_ratio=0.35,
        )
        print(f"  OK - 词汇特征: 总词数={vocab.total_words}, 多样性={vocab.lexical_diversity}")

        # 测试句式特征
        sentence = SentenceFeature(
            avg_sentence_length=20.5,
            short_sentence_ratio=0.3,
            medium_sentence_ratio=0.5,
            long_sentence_ratio=0.2,
            question_ratio=0.1,
            exclamation_ratio=0.05,
        )
        print(f"  OK - 句式特征: 平均句长={sentence.avg_sentence_length}")

        # 测试叙事节奏
        pace = NarrativePace(
            dialogue_ratio=0.4,
            description_ratio=0.3,
            action_ratio=0.3,
            pace_score=0.55,
        )
        print(f"  OK - 叙事节奏: 对话={pace.dialogue_ratio}, 节奏得分={pace.pace_score}")

        # 测试完整的写作风格
        style = WritingStyle(
            perspective=perspective,
            perspective_confidence=0.85,
            pace=pace,
            rhetoric_devices=[device],
            vocabulary=vocab,
            sentence=sentence,
            style_summary="这是一部采用第一人称叙事的都市重生小说...",
            tone="轻松",
        )
        print(f"  OK - 写作风格: 视角={style.perspective.value}, 基调={style.tone}")

    except Exception as e:
        raise AssertionError("data model construction failed") from e


def test_statistical_methods():
    """测试统计方法（不需要 LLM）"""
    print("\n测试 3: 统计分析方法")

    try:
        from novel_distiller.analyzers.style_analyzer import StyleAnalyzer

        # 创建一个 mock LLM 客户端（不会实际使用）
        class MockLLM:
            pass

        analyzer = StyleAnalyzer(MockLLM())
        print("  OK - 分析器实例化成功")

        # 测试句式分析
        test_text = """
        这是一个测试。这是一个比较长的句子，用来测试句式分析功能是否正常工作。
        这是短句。你知道吗？太棒了！
        """

        sentence_feature = analyzer._analyze_sentence(test_text)
        print(f"  OK - 句式分析: 平均句长={sentence_feature.avg_sentence_length:.1f}")
        print(f"       短句比例={sentence_feature.short_sentence_ratio:.2%}")
        print(f"       疑问句比例={sentence_feature.question_ratio:.2%}")
        print(f"       感叹句比例={sentence_feature.exclamation_ratio:.2%}")

        # 测试词汇分析
        vocab_feature = analyzer._analyze_vocabulary(test_text)
        print(f"  OK - 词汇分析: 总词数={vocab_feature.total_words}")
        print(f"       独特词数={vocab_feature.unique_words}")
        print(f"       词汇多样性={vocab_feature.lexical_diversity:.2%}")

        # 测试节奏分析
        pace = analyzer._analyze_pace(test_text)
        print(f"  OK - 节奏分析: 对话={pace.dialogue_ratio:.2%}")
        print(f"       描写={pace.description_ratio:.2%}")
        print(f"       动作={pace.action_ratio:.2%}")

    except Exception as e:
        raise AssertionError("statistical analysis failed") from e


def test_integration_with_distill_result():
    """测试与蒸馏结果的集成"""
    print("\n测试 4: 与蒸馏结果集成")

    try:
        from novel_distiller.models.schemas import (
            DistillResult,
            NovelMeta,
            WritingStyle,
            NarrativePerspective,
            NarrativePace,
            VocabularyFeature,
            SentenceFeature,
        )

        # 创建一个简单的蒸馏结果
        style = WritingStyle(
            perspective=NarrativePerspective.THIRD_PERSON_LIMITED,
            perspective_confidence=0.9,
            pace=NarrativePace(
                dialogue_ratio=0.4,
                description_ratio=0.35,
                action_ratio=0.25,
                pace_score=0.5,
            ),
            rhetoric_devices=[],
            vocabulary=VocabularyFeature(
                total_words=10000,
                unique_words=3000,
                lexical_diversity=0.3,
                avg_word_length=2.5,
                top_words=[],
                adjective_ratio=0.15,
                verb_ratio=0.25,
                noun_ratio=0.35,
            ),
            sentence=SentenceFeature(
                avg_sentence_length=22.0,
                short_sentence_ratio=0.2,
                medium_sentence_ratio=0.6,
                long_sentence_ratio=0.2,
                question_ratio=0.05,
                exclamation_ratio=0.03,
            ),
            style_summary="测试风格总结",
            tone="中性",
        )

        meta = NovelMeta(
            title="测试小说",
            total_chapters=10,
            total_words=100000,
        )

        result = DistillResult(
            meta=meta,
            chapters=[],
            characters=[],
            plots=[],
            writing_style=style,
        )

        print(f"  OK - 蒸馏结果包含风格分析")
        print(f"       视角: {result.writing_style.perspective.value}")
        print(f"       基调: {result.writing_style.tone}")

    except Exception as e:
        raise AssertionError("DistillResult integration failed") from e


def main():
    """主测试函数"""
    print("=" * 60)
    print("风格分析器单元测试")
    print("=" * 60)
    print()

    tests = [
        test_imports,
        test_data_models,
        test_statistical_methods,
        test_integration_with_distill_result,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"测试异常: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"通过: {passed}/{total}")

    if all(results):
        print("状态: 全部通过")
        return True
    else:
        print("状态: 部分失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
