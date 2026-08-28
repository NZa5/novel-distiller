"""
命令行工具
"""

import argparse
import sys
from pathlib import Path

from novel_distiller import NovelDistiller


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Novel Distiller - 小说蒸馏工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 蒸馏单本小说
  python -m novel_distiller distill novel.txt
  
  # 指定输出目录
  python -m novel_distiller distill novel.txt --output output/
  
  # 详细模式
  python -m novel_distiller distill novel.txt --verbose
  
  # 只提取人物
  python -m novel_distiller distill novel.txt --no-plots
  
  # 只提取情节
  python -m novel_distiller distill novel.txt --no-characters
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # distill 命令
    distill_parser = subparsers.add_parser("distill", help="蒸馏小说")
    distill_parser.add_argument("file", help="小说文件路径")
    distill_parser.add_argument(
        "-o", "--output",
        default="output",
        help="输出目录（默认: output）"
    )
    distill_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细信息"
    )
    distill_parser.add_argument(
        "--no-characters",
        action="store_true",
        help="不提取人物信息"
    )
    distill_parser.add_argument(
        "--no-plots",
        action="store_true",
        help="不提取情节信息"
    )
    distill_parser.add_argument(
        "--api-key",
        help="OpenAI API Key（覆盖环境变量）"
    )
    distill_parser.add_argument(
        "--base-url",
        help="API 基础 URL（覆盖环境变量）"
    )
    distill_parser.add_argument(
        "--model",
        help="模型名称（覆盖环境变量）"
    )
    
    # batch 命令
    batch_parser = subparsers.add_parser("batch", help="批量蒸馏")
    batch_parser.add_argument("files", nargs="+", help="小说文件路径列表")
    batch_parser.add_argument(
        "-o", "--output",
        default="output",
        help="输出基础目录（默认: output）"
    )
    batch_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细信息"
    )
    
    # version 命令
    version_parser = subparsers.add_parser("version", help="显示版本信息")
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 执行命令
    if args.command == "version":
        from novel_distiller import __version__
        print(f"Novel Distiller v{__version__}")
        sys.exit(0)
    
    elif args.command == "distill":
        # 检查文件是否存在
        if not Path(args.file).exists():
            print(f"❌ 错误：文件不存在: {args.file}")
            sys.exit(1)
        
        try:
            # 初始化蒸馏器
            distiller = NovelDistiller(
                api_key=args.api_key,
                base_url=args.base_url,
                model=args.model,
            )
            
            # 蒸馏小说
            result = distiller.distill_novel(
                file_path=args.file,
                output_dir=args.output,
                verbose=args.verbose,
                extract_characters=not args.no_characters,
                extract_plots=not args.no_plots,
            )
            
            if not args.verbose:
                print(result.summary)
                print(f"\n✅ 结果已导出到: {args.output}")
        
        except Exception as e:
            print(f"❌ 蒸馏失败: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    elif args.command == "batch":
        # 检查文件
        invalid_files = [f for f in args.files if not Path(f).exists()]
        if invalid_files:
            print(f"❌ 错误：以下文件不存在:")
            for f in invalid_files:
                print(f"  - {f}")
            sys.exit(1)
        
        try:
            # 初始化蒸馏器
            distiller = NovelDistiller()
            
            # 批量蒸馏
            results = distiller.batch_distill(
                file_paths=args.files,
                output_base_dir=args.output,
                verbose=args.verbose,
            )
            
            # 显示汇总
            success_count = sum(1 for r in results.values() if r is not None)
            print(f"\n{'='*60}")
            print(f"批量蒸馏完成: {success_count}/{len(args.files)} 成功")
            print(f"{'='*60}")
        
        except Exception as e:
            print(f"❌ 批量蒸馏失败: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
