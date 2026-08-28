"""
小说蒸馏器 - 核心模块
"""

import os
from typing import Optional
from pathlib import Path

from .models.schemas import DistillResult, QualityMetrics
from .loaders import TxtLoader, EpubLoader, ChapterSplitter
from .analyzers import CharacterExtractor, PlotExtractor, StructureAnalyzer, StyleAnalyzer, TimelineBuilder
from .analyzers.relationship_analyzer import RelationshipAnalyzer
from .analyzers.foreshadowing_detector import ForeshadowingDetector
from .exporters import JsonExporter, MarkdownExporter
from .visualizers import RelationshipVisualizer
from .utils import LLMClient


class NovelDistiller:
    """小说蒸馏器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        初始化蒸馏器

        Args:
            api_key: OpenAI API Key
            base_url: API 基础 URL
            model: 模型名称
        """
        # 初始化 LLM 客户端
        self.llm = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

        # 初始化各个组件
        self.txt_loader = TxtLoader()
        self.epub_loader = EpubLoader()
        self.chapter_splitter = ChapterSplitter()
        self.character_extractor = CharacterExtractor(self.llm)
        self.plot_extractor = PlotExtractor(self.llm)
        self.structure_analyzer = StructureAnalyzer(self.llm)
        self.relationship_analyzer = RelationshipAnalyzer(self.llm)  # Phase 2
        self.foreshadowing_detector = ForeshadowingDetector(self.llm)  # Phase 2
        self.style_analyzer = StyleAnalyzer(self.llm)  # Phase 2
        self.timeline_builder = TimelineBuilder(self.llm)  # Phase 2
        self.relationship_visualizer = RelationshipVisualizer()  # Phase 2
        self.json_exporter = JsonExporter()
        self.markdown_exporter = MarkdownExporter()

    def distill_novel(
        self,
        file_path: str,
        output_dir: str = "output",
        verbose: bool = False,
        extract_characters: bool = True,
        extract_plots: bool = True,
        extract_relationships: bool = True,  # Phase 2
        detect_foreshadowing: bool = True,  # Phase 2
        analyze_style: bool = False,
        build_timeline: bool = False,
    ) -> DistillResult:
        """
        蒸馏小说

        Args:
            file_path: 小说文件路径
            output_dir: 输出目录
            verbose: 是否显示详细信息
            extract_characters: 是否提取人物
            extract_plots: 是否提取情节
            extract_relationships: 是否提取人物关系 (Phase 2)
            detect_foreshadowing: 是否检测伏笔 (Phase 2)

        Returns:
            蒸馏结果
        """
        if verbose:
            print(f"📖 开始蒸馏小说: {file_path}")

        # 1. 加载文件
        if verbose:
            print("⏳ 加载文件...")
        if Path(file_path).suffix.lower() == ".epub":
            content = self.epub_loader.load(file_path)
        else:
            content = self.txt_loader.load(file_path)

        # 2. 分割章节
        if verbose:
            print("⏳ 分割章节...")
        chapters = self.chapter_splitter.split(content)
        if verbose:
            print(f"✅ 检测到 {len(chapters)} 个章节")

        # 3. 分析元数据
        if verbose:
            print("⏳ 分析小说元数据...")
        meta = self.structure_analyzer.analyze_meta(chapters, file_path)
        if verbose:
            print(f"✅ 标题: {meta.title}")
            if meta.author:
                print(f"   作者: {meta.author}")
            if meta.genre:
                print(f"   类型: {meta.genre}")
            print(f"   字数: {meta.total_words:,}字")

        # 4. 提取人物
        characters = []
        if extract_characters:
            if verbose:
                print("⏳ 提取人物信息...")
            characters = self.character_extractor.extract(chapters)
            if verbose:
                print(f"✅ 提取到 {len(characters)} 个人物")

        # 5. 提取情节
        plots = []
        if extract_plots:
            if verbose:
                print("⏳ 提取情节线...")
            plots = self.plot_extractor.extract(chapters)
            if verbose:
                print(f"✅ 提取到 {len(plots)} 条情节线")

        # 6. 提取人物关系 (Phase 2)
        relations = []
        if extract_relationships and characters:
            if verbose:
                print("⏳ 分析人物关系...")
            relations = self.relationship_analyzer.extract_relationships(
                characters, chapters
            )
            if verbose:
                print(f"✅ 提取到 {len(relations)} 对人物关系")

        # 6.5 检测伏笔 (Phase 2)
        foreshadows = []
        if detect_foreshadowing:
            if verbose:
                print("⏳ 检测伏笔...")
            foreshadows = self.foreshadowing_detector.detect(chapters)
            if verbose:
                revealed = len([f for f in foreshadows if f.status == 'revealed'])
                print(f"✅ 检测到 {len(foreshadows)} 个伏笔（已回收 {revealed} 个）")

        # 7. 质量评估
        if verbose:
            print("⏳ 评估蒸馏质量...")
        quality_metrics = self._evaluate_quality(chapters, characters, plots)

        # 7.5 Phase 2 分析（默认关闭，避免改变既有调用的 LLM 成本）
        writing_style = self.style_analyzer.analyze(chapters) if analyze_style else None
        timeline = (self.timeline_builder.build_timeline(chapters, characters)
                    if build_timeline else [])

        # 8. 构建结果
        result = DistillResult(
            meta=meta,
            chapters=chapters,
            characters=characters,
            plots=plots,
            relations=relations,  # Phase 2
            foreshadows=foreshadows,  # Phase 2
            timeline=timeline,
            writing_style=writing_style,
            quality_metrics=quality_metrics,
        )

        # 9. 导出结果
        if verbose:
            print(f"⏳ 导出结果到 {output_dir}...")

        # 导出 JSON
        json_files = self.json_exporter.export(result, output_dir)

        # 导出 Markdown
        md_path = os.path.join(output_dir, "report.md")
        self.markdown_exporter.export(result, md_path)

        # 导出关系图谱 (Phase 2)
        if relations:
            graph_path = os.path.join(output_dir, "relationship_graph.png")
            self.relationship_visualizer.visualize(
                relations, characters, graph_path
            )
            self.relationship_visualizer.export_graph_data(
                relations, characters, output_dir
            )

        if verbose:
            print("✅ 蒸馏完成！")
            print(f"\n📂 输出文件:")
            print(f"   - JSON: {json_files['full']}")
            print(f"   - Markdown: {md_path}")
            print(f"\n{result.summary}")

        return result

    def _evaluate_quality(
        self,
        chapters,
        characters,
        plots
    ) -> QualityMetrics:
        """
        评估蒸馏质量

        Args:
            chapters: 章节列表
            characters: 人物列表
            plots: 情节列表

        Returns:
            质量评估结果
        """
        notes = []

        # 完整性：是否提取了足够的人物和情节
        completeness = 0.0
        if characters:
            completeness += 0.5
            notes.append(f"提取了 {len(characters)} 个人物")
        else:
            notes.append("警告：未提取到人物信息")

        if plots:
            completeness += 0.5
            notes.append(f"提取了 {len(plots)} 条情节线")
        else:
            notes.append("警告：未提取到情节信息")

        # 一致性：暂时设为高分（后续可添加一致性检查）
        consistency = 0.95

        # 覆盖度：根据提取的情节涉及的章节数计算
        coverage = 0.0
        if plots and chapters:
            covered_chapters = set()
            for plot in plots:
                covered_chapters.update(plot.chapters)
            coverage = len(covered_chapters) / len(chapters)
            notes.append(f"覆盖了 {len(covered_chapters)}/{len(chapters)} 个章节")

        return QualityMetrics(
            completeness=completeness,
            consistency=consistency,
            coverage=coverage,
            notes=notes,
        )

    def batch_distill(
        self,
        file_paths: list[str],
        output_base_dir: str = "output",
        verbose: bool = False,
    ) -> dict[str, DistillResult]:
        """
        批量蒸馏多本小说

        Args:
            file_paths: 文件路径列表
            output_base_dir: 输出基础目录
            verbose: 是否显示详细信息

        Returns:
            文件路径到蒸馏结果的映射
        """
        results = {}

        for i, file_path in enumerate(file_paths, 1):
            if verbose:
                print(f"\n{'='*60}")
                print(f"处理 {i}/{len(file_paths)}: {file_path}")
                print(f"{'='*60}")

            # 为每本小说创建独立输出目录
            file_name = Path(file_path).stem
            output_dir = os.path.join(output_base_dir, file_name)

            try:
                result = self.distill_novel(
                    file_path=file_path,
                    output_dir=output_dir,
                    verbose=verbose,
                )
                results[file_path] = result
            except Exception as e:
                if verbose:
                    print(f"❌ 蒸馏失败: {e}")
                results[file_path] = None

        return results
