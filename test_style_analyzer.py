"""
风格分析器测试脚本
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from novel_distiller.models.schemas import Chapter
from novel_distiller.analyzers.style_analyzer import StyleAnalyzer
from novel_distiller.utils.llm_client import LLMClient

# 加载环境变量
load_dotenv()


def test_style_analyzer():
    """测试风格分析器"""

    # 创建测试章节数据
    test_chapters = [
        Chapter(
            index=1,
            title="第一章 重生",
            content="""
            "我竟然重生了？"张凡睁开眼睛，看着熟悉的天花板，心中涌起难以置信的情绪。

            这是他十年前的卧室。墙上的海报，桌上的书本，一切都是那么熟悉。他记得，就在刚才，
            自己还在医院的病床上，因为绝症而走到了生命的尽头。

            "这次，我一定要改变命运！"他暗暗发誓。回想起前世的种种遗憾，张凡握紧了拳头。
            那些错过的机会，那些没有珍惜的人，这一次，他绝不会再让悲剧重演。

            窗外，清晨的阳光透过窗帘洒进房间，金色的光芒让一切都显得那么美好。张凡深吸一口气，
            感受着青春的活力在身体里涌动。这种感觉，已经十年没有体验过了。

            "小凡，起床了！"母亲熟悉的声音从楼下传来，温柔而慈祥。

            张凡的眼眶湿润了。前世，母亲五年前就因为一场意外离开了人世。而现在，她还活着，
            还在楼下为自己准备早餐。这种失而复得的幸福，让他几乎落泪。
            """,
            word_count=300,
            start_line=1,
            end_line=20,
        ),
        Chapter(
            index=2,
            title="第二章 改变",
            content="""
            早餐桌上，父亲正在看报纸，母亲端来热气腾腾的豆浆和油条。一切都像是梦境一般美好。

            "今天有什么打算吗？"父亲放下报纸，关切地问道。

            张凡想了想，说："我想去图书馆看书。"

            前世的他，高中时代浪费了太多时间在游戏上，最终只考上了一所普通的二本院校。
            而这一次，他要牢牢把握住每一分每一秒，考上理想的大学，为将来的人生铺平道路。

            "好孩子，知道上进了。"母亲欣慰地笑了，"多吃点，别饿着。"

            张凡狼吞虎咽地吃完早餐，背起书包就往外走。路上，他回想着前世的记忆。
            如果他没记错，今天下午，小区附近会发生一场车祸，一个小女孩会被撞伤。
            这次，他一定要阻止这场悲剧。

            阳光很好，风也很温柔。张凡走在熟悉的街道上，心中充满了希望。重生，
            不仅是命运的恩赐，更是一次改写人生的机会。他要让这一世，活得精彩，活得无悔。
            """,
            word_count=280,
            start_line=21,
            end_line=40,
        ),
        Chapter(
            index=3,
            title="第三章 机遇",
            content="""
            图书馆里很安静，只有翻书的声音偶尔响起。张凡找了个靠窗的位置坐下，开始翻阅数学教材。

            作为一个经历过高考的人，他深知基础的重要性。那些曾经困扰自己的难题，现在看来都变得
            简单了许多。不是因为题目变简单了，而是经历和阅历让他的思维更加成熟。

            正当他专心致志地做题时，一个女孩走到他旁边，小声问："同学，这里有人坐吗？"

            张凡抬起头，看到一张清秀的脸庞。他认出来了，这是班上的文艺委员林雨薇。前世，
            她考上了北大，而自己则因为成绩不佳，最终与她失去了联系。

            "没人，你坐吧。"他笑着说。

            林雨薇点点头，坐下后也拿出了书本。两个人安静地学习着，偶尔会交流几句题目。
            张凡发现，林雨薇对数学有着很深的理解，她的解题思路往往能给自己带来启发。

            时光在指尖流逝，不知不觉已经到了中午。张凡看了看表，该去小区门口了。
            那场车祸，他必须要阻止。
            """,
            word_count=280,
            start_line=41,
            end_line=60,
        ),
    ]

    print("=" * 60)
    print("风格分析器测试")
    print("=" * 60)

    try:
        # 初始化 LLM 客户端
        print("\n1. 初始化 LLM 客户端...")
        llm_client = LLMClient()
        print("   ✓ LLM 客户端初始化成功")

        # 初始化风格分析器
        print("\n2. 初始化风格分析器...")
        analyzer = StyleAnalyzer(llm_client)
        print("   ✓ 风格分析器初始化成功")

        # 执行分析
        print("\n3. 执行风格分析...")
        print("   (这可能需要几秒钟...)")
        style = analyzer.analyze(test_chapters, sample_size=3)
        print("   ✓ 风格分析完成")

        # 输出结果
        print("\n" + "=" * 60)
        print("分析结果")
        print("=" * 60)

        print(f"\n【叙事视角】")
        print(f"  类型: {style.perspective.value}")
        print(f"  置信度: {style.perspective_confidence:.2%}")

        print(f"\n【叙事节奏】")
        print(f"  对话比例: {style.pace.dialogue_ratio:.2%}")
        print(f"  描写比例: {style.pace.description_ratio:.2%}")
        print(f"  动作比例: {style.pace.action_ratio:.2%}")
        print(f"  节奏得分: {style.pace.pace_score:.2f} (0-1，越高越快)")

        print(f"\n【修辞手法】")
        if style.rhetoric_devices:
            for device in style.rhetoric_devices:
                print(f"  - {device.type}: 出现 {device.frequency} 次")
                if device.examples:
                    print(f"    示例: {device.examples[0][:50]}...")
        else:
            print("  未检测到明显的修辞手法")

        print(f"\n【词汇特征】")
        print(f"  总词数: {style.vocabulary.total_words}")
        print(f"  独特词数: {style.vocabulary.unique_words}")
        print(f"  词汇多样性: {style.vocabulary.lexical_diversity:.2%}")
        print(f"  平均词长: {style.vocabulary.avg_word_length:.2f} 字")
        print(f"  形容词比例: {style.vocabulary.adjective_ratio:.2%}")
        print(f"  动词比例: {style.vocabulary.verb_ratio:.2%}")
        print(f"  名词比例: {style.vocabulary.noun_ratio:.2%}")
        if style.vocabulary.top_words:
            print(f"  高频词 (前5):")
            for word, count in style.vocabulary.top_words[:5]:
                print(f"    - {word}: {count} 次")

        print(f"\n【句式特征】")
        print(f"  平均句长: {style.sentence.avg_sentence_length:.1f} 字")
        print(f"  短句比例 (<10字): {style.sentence.short_sentence_ratio:.2%}")
        print(f"  中句比例 (10-30字): {style.sentence.medium_sentence_ratio:.2%}")
        print(f"  长句比例 (>30字): {style.sentence.long_sentence_ratio:.2%}")
        print(f"  疑问句比例: {style.sentence.question_ratio:.2%}")
        print(f"  感叹句比例: {style.sentence.exclamation_ratio:.2%}")

        print(f"\n【整体风格】")
        print(f"  基调: {style.tone}")
        print(f"  总结: {style.style_summary}")

        print("\n" + "=" * 60)
        print("✓ 测试成功完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = test_style_analyzer()
    sys.exit(0 if success else 1)
