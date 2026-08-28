"""
EPUB Loader 单元测试（模拟测试）

注意：由于缺少真实 EPUB 文件，这里只测试代码结构和基本逻辑
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_import():
    """测试导入"""
    try:
        from novel_distiller.loaders.epub_loader import EpubLoader
        print("✓ EpubLoader 导入成功")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_class_structure():
    """测试类结构"""
    from novel_distiller.loaders.epub_loader import EpubLoader

    # 检查类是否可以实例化
    loader = EpubLoader()
    print("✓ EpubLoader 实例化成功")

    # 检查方法是否存在
    methods = [
        'load',
        'load_with_chapters',
        'get_metadata',
        'get_file_stats',
        '_extract_text_from_html',
        '_extract_title_from_html',
        '_extract_from_toc',
        '_extract_from_spine',
        '_get_content_by_href',
        '_get_metadata_value',
    ]

    for method_name in methods:
        if hasattr(loader, method_name):
            print(f"✓ 方法 {method_name} 存在")
        else:
            print(f"✗ 方法 {method_name} 不存在")
            return False

    return True


def test_html_extraction():
    """测试 HTML 文本提取功能"""
    from novel_distiller.loaders.epub_loader import EpubLoader

    loader = EpubLoader()

    # 测试用例 1: 基本 HTML
    html1 = """
    <html>
        <head><title>第一章</title></head>
        <body>
            <h1>第一章 开始</h1>
            <p>这是第一段内容。</p>
            <p>这是第二段内容。</p>
        </body>
    </html>
    """
    text1 = loader._extract_text_from_html(html1)
    assert "第一章 开始" in text1
    assert "第一段内容" in text1
    print("✓ HTML 文本提取测试通过")

    # 测试用例 2: 带脚本和样式的 HTML
    html2 = """
    <html>
        <head>
            <style>body { color: red; }</style>
        </head>
        <body>
            <script>console.log('test');</script>
            <p>正文内容</p>
        </body>
    </html>
    """
    text2 = loader._extract_text_from_html(html2)
    assert "console.log" not in text2
    assert "color: red" not in text2
    assert "正文内容" in text2
    print("✓ HTML 脚本和样式过滤测试通过")

    return True


def test_title_extraction():
    """测试标题提取功能"""
    from novel_distiller.loaders.epub_loader import EpubLoader

    loader = EpubLoader()

    # 测试用例 1: h1 标题
    html1 = "<html><body><h1>第一章 标题</h1><p>内容</p></body></html>"
    title1 = loader._extract_title_from_html(html1)
    assert title1 == "第一章 标题"
    print("✓ H1 标题提取测试通过")

    # 测试用例 2: h2 标题
    html2 = "<html><body><h2>第二章</h2><p>内容</p></body></html>"
    title2 = loader._extract_title_from_html(html2)
    assert title2 == "第二章"
    print("✓ H2 标题提取测试通过")

    # 测试用例 3: 无标题
    html3 = "<html><body><p>纯内容</p></body></html>"
    title3 = loader._extract_title_from_html(html3)
    assert title3 is None
    print("✓ 无标题情况测试通过")

    return True


def test_error_handling():
    """测试错误处理"""
    from novel_distiller.loaders.epub_loader import EpubLoader

    loader = EpubLoader()

    # 测试文件不存在
    try:
        loader.load("nonexistent_file.epub")
        print("✗ 应该抛出 FileNotFoundError")
        return False
    except FileNotFoundError:
        print("✓ FileNotFoundError 正确抛出")

    return True


def test_integration_with_chapter_splitter():
    """测试与 ChapterSplitter 的集成"""
    try:
        from novel_distiller.loaders.epub_loader import EpubLoader
        from novel_distiller.loaders.chapter_splitter import ChapterSplitter

        print("✓ EpubLoader 和 ChapterSplitter 可以同时导入")

        # 测试它们可以一起使用
        loader = EpubLoader()
        splitter = ChapterSplitter()

        print("✓ 两个类可以同时实例化")

        return True
    except Exception as e:
        print(f"✗ 集成测试失败: {e}")
        return False


def test_package_import():
    """测试从包级别导入"""
    try:
        from novel_distiller.loaders import EpubLoader, ChapterSplitter
        print("✓ 可以从 novel_distiller.loaders 导入 EpubLoader")
        return True
    except ImportError as e:
        print(f"✗ 包级别导入失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("EPUB Loader 测试套件")
    print("=" * 60)
    print()

    tests = [
        ("导入测试", test_import),
        ("类结构测试", test_class_structure),
        ("HTML 提取测试", test_html_extraction),
        ("标题提取测试", test_title_extraction),
        ("错误处理测试", test_error_handling),
        ("ChapterSplitter 集成测试", test_integration_with_chapter_splitter),
        ("包导入测试", test_package_import),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n[测试] {test_name}")
        print("-" * 60)
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} 通过\n")
            else:
                failed += 1
                print(f"✗ {test_name} 失败\n")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} 异常: {e}\n")

    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
