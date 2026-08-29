"""
基础使用示例
"""

from novel_distiller import NovelDistiller

# 示例小说文本
SAMPLE_NOVEL = """第一章 开端

张三是一个普通的高中生，每天过着平凡的生活。

这天放学后，他走在回家的路上，突然看到天空出现了奇怪的光芒。

"那是什么？"张三好奇地抬头看去。

第二章 系统降临

光芒越来越亮，最后化作一道流光，直接冲进了张三的身体。

【叮！修炼系统已绑定宿主】

一个机械的声音在张三脑海中响起。

"什么情况？"张三惊讶地站在原地。

【恭喜宿主获得新手大礼包，请查收】

张三按照系统的提示，打开了新手大礼包，获得了基础功法《入门心法》。

第三章 初试身手

第二天，张三来到学校，发现自己的体质似乎变强了。

体育课上，他轻松地完成了以前做不到的动作。

"张三，你最近有练什么吗？"班长李四好奇地问道。

"额，就是跑跑步而已。"张三含糊地回答。

李四是张三的好朋友，两人从小学就认识了。

第四章 危机出现

放学后，张三和李四一起回家。

路过小巷时，突然冲出几个混混。

"小子，把钱交出来！"为首的混混凶狠地说道。

李四害怕地躲在张三身后。

张三深吸一口气，运转体内的真气，准备应对。

第五章 化解危机

张三感觉到体内力量涌动，他快速出手，几招就制服了混混们。

"厉害啊张三！"李四惊讶地说。

混混们灰溜溜地逃走了。

从这天起，张三决定要好好修炼，变得更强。

【任务完成！获得奖励：100修炼点】

系统的提示让张三更加有动力了。
"""


def basic_example():
    """基础使用示例"""
    print("=" * 60)
    print("Novel Distiller 基础使用示例")
    print("=" * 60)
    
    # 创建测试文件
    import os
    os.makedirs("examples/data", exist_ok=True)
    
    test_file = "examples/data/sample_novel.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(SAMPLE_NOVEL)
    
    print(f"\n✅ 已创建示例小说: {test_file}\n")
    
    # 初始化蒸馏器
    try:
        distiller = NovelDistiller()
        
        # 蒸馏小说
        print("开始蒸馏...\n")
        result = distiller.distill_novel(
            file_path=test_file,
            output_dir="examples/output",
            verbose=True,
        )
        
        # 显示结果
        print("\n" + "=" * 60)
        print("蒸馏结果预览")
        print("=" * 60)
        
        print("\n📖 基本信息:")
        print(f"  标题: {result.meta.title}")
        print(f"  章节: {result.meta.total_chapters}章")
        print(f"  字数: {result.meta.total_words}字")
        
        print("\n👥 人物信息:")
        for char in result.characters[:3]:  # 只显示前3个
            print(f"  - {char.name} ({char.role.value}): {char.description[:50]}...")
        
        print("\n📊 情节信息:")
        for plot in result.plots[:2]:  # 只显示前2条
            print(f"  - {plot.title}: {plot.description[:50]}...")
        
        print("\n✅ 完整报告已导出到: examples/output/")
    
    except ValueError as e:
        print(f"\n⚠️  需要配置 API Key 才能运行示例")
        print(f"   请复制 .env.example 为 .env 并填入你的 API Key")
        print(f"\n   错误信息: {e}")
    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")


if __name__ == "__main__":
    basic_example()
