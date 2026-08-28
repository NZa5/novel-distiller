"""
Markdown 导出器
"""

import os
from pathlib import Path
from ..models.schemas import DistillResult, CharacterRole, PlotType


class MarkdownExporter:
    """Markdown 导出器"""
    
    def export(self, result: DistillResult, output_path: str):
        """
        导出蒸馏结果为 Markdown 报告
        
        Args:
            result: 蒸馏结果
            output_path: 输出文件路径
        """
        # 创建输出目录
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 生成 Markdown 内容
        md_content = self._generate_markdown(result)
        
        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        return output_path
    
    def _generate_markdown(self, result: DistillResult) -> str:
        """生成 Markdown 内容"""
        
        lines = []
        
        # 标题
        lines.append(f"# 《{result.meta.title}》蒸馏报告\n")
        
        # 基本信息
        lines.append("## 📖 基本信息\n")
        lines.append(f"- **标题**: {result.meta.title}")
        if result.meta.author:
            lines.append(f"- **作者**: {result.meta.author}")
        if result.meta.genre:
            lines.append(f"- **类型**: {result.meta.genre}")
        lines.append(f"- **总章节**: {result.meta.total_chapters}章")
        lines.append(f"- **总字数**: {result.meta.total_words:,}字")
        lines.append(f"- **蒸馏时间**: {result.meta.distill_date.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 人物信息
        lines.append("## 👥 主要人物\n")
        
        # 按角色类型分组
        role_names = {
            CharacterRole.PROTAGONIST: "主角",
            CharacterRole.MAJOR: "主要配角",
            CharacterRole.MINOR: "次要配角",
            CharacterRole.VILLAIN: "反派",
            CharacterRole.SUPPORTING: "其他",
        }
        
        for role, role_name in role_names.items():
            chars = [ch for ch in result.characters if ch.role == role]
            if chars:
                lines.append(f"### {role_name}\n")
                for ch in chars:
                    lines.append(f"#### {ch.name}")
                    if ch.aliases:
                        lines.append(f"- **别名**: {', '.join(ch.aliases)}")
                    lines.append(f"- **简介**: {ch.description}")
                    lines.append(f"- **首次出现**: 第{ch.first_appearance}章")
                    if ch.key_traits:
                        lines.append(f"- **关键特征**: {', '.join(ch.key_traits)}")
                    lines.append("")
        
        # 人物关系 (Phase 2)
        if result.relations:
            lines.append("## 🔗 人物关系\n")
            
            # 按关系类型分组
            relation_types = {}
            for rel in result.relations:
                rel_type = rel.relation_type
                if rel_type not in relation_types:
                    relation_types[rel_type] = []
                relation_types[rel_type].append(rel)
            
            for rel_type, rels in relation_types.items():
                lines.append(f"### {rel_type}\n")
                for rel in rels:
                    lines.append(f"- **{rel.source} ↔ {rel.target}**: {rel.description}")
                    lines.append(f"  - 出现章节: {', '.join(f'第{ch}章' for ch in rel.chapters[:5])}{'...' if len(rel.chapters) > 5 else ''}")
                    lines.append(f"  - 关系强度: {'★' * int(rel.strength * 5)}")
                lines.append("")
        
        # 情节脉络
        lines.append("## 📊 情节脉络\n")
        
        plot_type_names = {
            PlotType.MAIN: "主线",
            PlotType.SUB: "支线",
            PlotType.FORESHADOWING: "伏笔",
        }
        
        for plot_type, type_name in plot_type_names.items():
            plots = [p for p in result.plots if p.type == plot_type]
            if plots:
                lines.append(f"### {type_name}\n")
                for i, plot in enumerate(plots, 1):
                    lines.append(f"#### {i}. {plot.title}")
                    lines.append(f"**涉及章节**: {', '.join(f'第{ch}章' for ch in plot.chapters)}")
                    lines.append(f"\n{plot.description}\n")
                    
                    if plot.key_events:
                        lines.append("**关键事件**:")
                        for event in plot.key_events:
                            lines.append(f"- {event}")
                    lines.append("")
        
        # 章节列表
        lines.append("## 📚 章节列表\n")
        lines.append("| 序号 | 标题 | 字数 |")
        lines.append("|------|------|------|")
        for ch in result.chapters:
            lines.append(f"| {ch.index} | {ch.title} | {ch.word_count:,} |")
        lines.append("")
        
        # 统计信息
        lines.append("## 📈 统计信息\n")
        word_counts = [ch.word_count for ch in result.chapters]
        lines.append(f"- **平均章节长度**: {sum(word_counts) // len(word_counts):,}字")
        lines.append(f"- **最长章节**: 第{max(result.chapters, key=lambda x: x.word_count).index}章 ({max(word_counts):,}字)")
        lines.append(f"- **最短章节**: 第{min(result.chapters, key=lambda x: x.word_count).index}章 ({min(word_counts):,}字)")
        lines.append(f"- **主要人物数**: {len([c for c in result.characters if c.role in [CharacterRole.PROTAGONIST, CharacterRole.MAJOR]])}人")
        lines.append(f"- **情节线数**: {len(result.plots)}条")
        lines.append("")
        
        # 质量评估
        if result.quality_metrics:
            lines.append("## ✅ 质量评估\n")
            lines.append(f"- **完整性**: {result.quality_metrics.completeness * 100:.1f}%")
            lines.append(f"- **一致性**: {result.quality_metrics.consistency * 100:.1f}%")
            lines.append(f"- **覆盖度**: {result.quality_metrics.coverage * 100:.1f}%")
            if result.quality_metrics.notes:
                lines.append("\n**备注**:")
                for note in result.quality_metrics.notes:
                    lines.append(f"- {note}")
            lines.append("")
        
        # 页脚
        lines.append("---")
        lines.append("\n*本报告由 Novel Distiller 自动生成*")
        
        return "\n".join(lines)
