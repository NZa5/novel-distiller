"""
JSON 导出器
"""

import json
import os
from pathlib import Path
from ..models.schemas import DistillResult


class JsonExporter:
    """JSON 导出器"""
    
    def export(self, result: DistillResult, output_dir: str):
        """
        导出蒸馏结果为 JSON 文件
        
        Args:
            result: 蒸馏结果
            output_dir: 输出目录
        """
        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 导出元数据
        meta_path = os.path.join(output_dir, "novel_meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(result.meta.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        
        # 导出章节列表（不包含完整内容）
        chapters_summary = [
            {
                "index": ch.index,
                "title": ch.title,
                "word_count": ch.word_count,
                "summary": ch.summary,
                "start_line": ch.start_line,
                "end_line": ch.end_line,
            }
            for ch in result.chapters
        ]
        chapters_path = os.path.join(output_dir, "chapters.json")
        with open(chapters_path, "w", encoding="utf-8") as f:
            json.dump(chapters_summary, f, ensure_ascii=False, indent=2)
        
        # 导出人物
        characters_path = os.path.join(output_dir, "characters.json")
        with open(characters_path, "w", encoding="utf-8") as f:
            json.dump(
                [ch.model_dump() for ch in result.characters],
                f,
                ensure_ascii=False,
                indent=2
            )
        
        # 导出情节
        plots_path = os.path.join(output_dir, "plots.json")
        with open(plots_path, "w", encoding="utf-8") as f:
            json.dump(
                [p.model_dump() for p in result.plots],
                f,
                ensure_ascii=False,
                indent=2
            )
        
        # 导出人物关系 (Phase 2)
        relations_path = None
        if result.relations:
            relations_path = os.path.join(output_dir, "relations.json")
            with open(relations_path, "w", encoding="utf-8") as f:
                json.dump(
                    [r.model_dump() for r in result.relations],
                    f,
                    ensure_ascii=False,
                    indent=2
                )
        
        # 导出伏笔 (Phase 2)
        foreshadows_path = None
        if result.foreshadows:
            foreshadows_path = os.path.join(output_dir, "foreshadows.json")
            with open(foreshadows_path, "w", encoding="utf-8") as f:
                json.dump(
                    [f.model_dump() for f in result.foreshadows],
                    f,
                    ensure_ascii=False,
                    indent=2
                )
        
        # 导出质量评估
        if result.quality_metrics:
            quality_path = os.path.join(output_dir, "quality_metrics.json")
            with open(quality_path, "w", encoding="utf-8") as f:
                json.dump(
                    result.quality_metrics.model_dump(),
                    f,
                    ensure_ascii=False,
                    indent=2
                )
        
        # 导出完整结果
        full_path = os.path.join(output_dir, "full_result.json")
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(
                result.model_dump(),
                f,
                ensure_ascii=False,
                indent=2,
                default=str
            )
        
        return {
            "meta": meta_path,
            "chapters": chapters_path,
            "characters": characters_path,
            "plots": plots_path,
            "relations": relations_path,  # Phase 2
            "foreshadows": foreshadows_path,  # Phase 2
            "quality": quality_path if result.quality_metrics else None,
            "full": full_path,
        }
