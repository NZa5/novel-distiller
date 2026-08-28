"""
情节提取器
"""

import json
from typing import List
from ..models.schemas import Plot, PlotType, Chapter
from ..utils.llm_client import LLMClient


class PlotExtractor:
    """情节提取器"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化提取器
        
        Args:
            llm_client: LLM 客户端
        """
        self.llm = llm_client
    
    def extract(self, chapters: List[Chapter], max_chapters: int = 50) -> List[Plot]:
        """
        提取情节
        
        Args:
            chapters: 章节列表
            max_chapters: 最多分析的章节数
        
        Returns:
            情节列表
        """
        # 选择要分析的章节
        chapters_to_analyze = chapters[:max_chapters]
        
        system_message = """你是一个专业的小说分析专家，擅长识别和提取小说的情节线。
你的任务是分析章节，提取主要情节线，包括：
1. 主线（main）：贯穿全文的核心情节
2. 支线（sub）：独立但与主线相关的情节
3. 伏笔（foreshadowing）：埋下的线索，可能在后续章节中揭示

对于每条情节线，请提取：
- type: 类型（main/sub/foreshadowing）
- title: 情节标题（简短描述，10-20字）
- chapters: 涉及的章节序号列表
- description: 详细描述（100-200字）
- key_events: 关键事件列表（每个事件 20-50字）"""
        
        # 准备章节摘要
        chapters_summary = []
        for ch in chapters_to_analyze:
            # 生成章节摘要
            summary = self._summarize_chapter(ch)
            chapters_summary.append(f"第{ch.index}章 {ch.title}: {summary}")
        
        prompt = f"""请分析以下章节，提取主要情节线：

{chr(10).join(chapters_summary)}

请以 JSON 数组格式返回结果，每条情节线包含：type, title, chapters, description, key_events

示例格式：
[
  {{
    "type": "main",
    "title": "获得系统，踏上修炼之路",
    "chapters": [1, 2, 3, 5, 8],
    "description": "主角张三意外获得修炼系统，开始在系统的帮助下修炼，逐渐提升实力。期间遇到挑战和机遇，结识了好友李四。",
    "key_events": [
      "第1章：张三在野外遇险，意外激活系统",
      "第2章：完成系统新手任务，获得第一个功法",
      "第3章：在学院测试中展露实力",
      "第5章：结识李四，成为好友"
    ]
  }},
  {{
    "type": "sub",
    "title": "学院比武大会",
    "chapters": [10, 11, 12],
    "description": "学院举办比武大会，张三参加并取得优异成绩，引起关注。",
    "key_events": [
      "第10章：报名参加比武大会",
      "第11章：连胜数场，进入决赛",
      "第12章：决赛获胜，获得奖励"
    ]
  }}
]"""
        
        try:
            response = self.llm.invoke_json(prompt, system_message)
            
            # 解析 JSON 并转换为 Plot 对象
            plots = []
            plot_list = response if isinstance(response, list) else response.get("plots", [])
            
            for plot_data in plot_list:
                try:
                    plots.append(
                        Plot(
                            type=PlotType(plot_data.get("type", "main")),
                            title=plot_data.get("title", ""),
                            chapters=plot_data.get("chapters", []),
                            description=plot_data.get("description", ""),
                            key_events=plot_data.get("key_events", []),
                        )
                    )
                except (KeyError, ValueError) as e:
                    print(f"警告：跳过无效的情节数据: {e}")
                    continue
            
            return plots
        
        except Exception as e:
            print(f"情节提取失败: {e}")
            return []
    
    def _summarize_chapter(self, chapter: Chapter) -> str:
        """
        生成章节摘要（简化版，不调用 LLM）
        
        Args:
            chapter: 章节
        
        Returns:
            摘要文本
        """
        # 简单提取前 300 字作为摘要
        content = chapter.content.replace("\n", " ").strip()
        if len(content) > 300:
            return content[:300] + "..."
        return content
    
    def extract_main_plot(self, chapters: List[Chapter]) -> List[Plot]:
        """提取主线情节"""
        all_plots = self.extract(chapters)
        return [p for p in all_plots if p.type == PlotType.MAIN]
    
    def extract_sub_plots(self, chapters: List[Chapter]) -> List[Plot]:
        """提取支线情节"""
        all_plots = self.extract(chapters)
        return [p for p in all_plots if p.type == PlotType.SUB]
