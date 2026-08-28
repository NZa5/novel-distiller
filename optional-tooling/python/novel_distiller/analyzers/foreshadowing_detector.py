"""
伏笔检测器 (Phase 2)
"""

from typing import List, Optional, Dict
from ..models.schemas import Chapter
from ..utils.llm_client import LLMClient
from pydantic import BaseModel, Field


class Foreshadowing(BaseModel):
    """伏笔信息"""
    id: str = Field(description="伏笔ID")
    title: str = Field(description="伏笔标题")
    planted_chapter: int = Field(description="埋设章节")
    planted_content: str = Field(description="埋设内容")
    revealed_chapter: Optional[int] = Field(None, description="回收章节")
    revealed_content: Optional[str] = Field(None, description="回收内容")
    status: str = Field(default="planted", description="状态: planted/revealed/abandoned")
    importance: str = Field(default="medium", description="重要程度: high/medium/low")
    description: str = Field(default="", description="伏笔描述")


class ForeshadowingDetector:
    """伏笔检测器"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化检测器
        
        Args:
            llm_client: LLM 客户端
        """
        self.llm = llm_client
    
    def detect(
        self,
        chapters: List[Chapter],
        max_chapters: int = 50
    ) -> List[Foreshadowing]:
        """
        检测伏笔的埋设和回收
        
        Args:
            chapters: 章节列表
            max_chapters: 最多分析的章节数
        
        Returns:
            伏笔列表
        """
        if not chapters:
            return []
        
        # 第一遍：识别潜在伏笔
        planted_foreshadows = self._detect_planted(chapters[:max_chapters])
        
        if not planted_foreshadows:
            return []
        
        # 第二遍：寻找伏笔回收
        self._detect_revealed(planted_foreshadows, chapters)
        
        return planted_foreshadows
    
    def _detect_planted(self, chapters: List[Chapter]) -> List[Foreshadowing]:
        """检测伏笔埋设"""
        foreshadows = []
        foreshadow_id = 1
        
        for chapter in chapters:
            try:
                system_message = """你是一个小说伏笔识别专家。
伏笔是指：作者在前文中对后续情节的暗示、预告、埋设，为后文做铺垫。

典型伏笔特征：
- 神秘的物品、人物、事件
- 未解的谜团
- 含糊的暗示
- 特殊的描写或强调
- 留白和悬念

请识别章节中的伏笔，只返回明显的伏笔，不要过度解读。"""
                
                content_preview = chapter.content[:2000]
                
                prompt = f"""请分析以下章节中的伏笔：

章节：{chapter.title}
内容：
{content_preview}

请返回 JSON 数组，每个伏笔包含：
- title: 伏笔标题（简短）
- content: 伏笔的具体内容（原文引用）
- importance: 重要程度（high/medium/low）
- description: 伏笔描述（为什么这是伏笔）

只返回明显的伏笔，一般每章0-2个。"""
                
                response = self.llm.invoke_json(prompt, system_message)
                
                # 解析响应
                fs_list = response if isinstance(response, list) else response.get('foreshadows', [])
                
                for fs_data in fs_list:
                    if 'title' in fs_data and 'content' in fs_data:
                        foreshadow = Foreshadowing(
                            id=f"FS{foreshadow_id:03d}",
                            title=fs_data['title'],
                            planted_chapter=chapter.index,
                            planted_content=fs_data['content'],
                            importance=fs_data.get('importance', 'medium'),
                            description=fs_data.get('description', ''),
                            status='planted'
                        )
                        foreshadows.append(foreshadow)
                        foreshadow_id += 1
            
            except Exception:
                # 出错时跳过本章
                continue
        
        return foreshadows
    
    def _detect_revealed(
        self,
        foreshadows: List[Foreshadowing],
        chapters: List[Chapter]
    ):
        """检测伏笔回收"""
        
        for foreshadow in foreshadows:
            # 从埋设章节之后开始搜索
            start_idx = foreshadow.planted_chapter
            search_chapters = [ch for ch in chapters if ch.index > start_idx]
            
            if not search_chapters:
                continue
            
            # 限制搜索范围（后续30章内）
            search_chapters = search_chapters[:30]
            
            # 使用 LLM 寻找回收
            revealed = self._find_revelation(foreshadow, search_chapters)
            
            if revealed:
                foreshadow.revealed_chapter = revealed['chapter']
                foreshadow.revealed_content = revealed['content']
                foreshadow.status = 'revealed'
    
    def _find_revelation(
        self,
        foreshadow: Foreshadowing,
        chapters: List[Chapter]
    ) -> Optional[Dict]:
        """寻找伏笔回收"""
        
        try:
            system_message = """你是一个小说伏笔回收识别专家。
请判断给定的伏笔是否在后续章节中被回收（揭示、呼应、解答）。"""
            
            # 构建搜索内容（每章取前500字）
            chapter_summaries = []
            for ch in chapters[:10]:  # 最多检查10章
                summary = f"第{ch.index}章 {ch.title}: {ch.content[:500]}"
                chapter_summaries.append(summary)
            
            chapters_text = "\n\n".join(chapter_summaries)
            
            prompt = f"""伏笔信息：
标题：{foreshadow.title}
内容：{foreshadow.planted_content}
描述：{foreshadow.description}

后续章节：
{chapters_text}

问题：这个伏笔是否在后续章节中被回收？

如果被回收，返回 JSON：
{{
  "revealed": true,
  "chapter": 章节序号,
  "content": "回收的具体内容（原文引用）"
}}

如果未回收，返回：
{{
  "revealed": false
}}"""
            
            response = self.llm.invoke_json(prompt, system_message)
            
            if response.get('revealed'):
                return {
                    'chapter': response['chapter'],
                    'content': response.get('content', '')
                }
            
            return None
        
        except Exception:
            return None
    
    def get_statistics(self, foreshadows: List[Foreshadowing]) -> Dict:
        """获取伏笔统计信息"""
        
        if not foreshadows:
            return {
                "total": 0,
                "revealed": 0,
                "planted": 0,
                "abandoned": 0,
                "reveal_rate": 0.0
            }
        
        revealed_count = len([f for f in foreshadows if f.status == 'revealed'])
        planted_count = len([f for f in foreshadows if f.status == 'planted'])
        abandoned_count = len([f for f in foreshadows if f.status == 'abandoned'])
        
        return {
            "total": len(foreshadows),
            "revealed": revealed_count,
            "planted": planted_count,
            "abandoned": abandoned_count,
            "reveal_rate": revealed_count / len(foreshadows) if foreshadows else 0.0,
            "avg_span": self._calculate_avg_span(foreshadows)
        }
    
    def _calculate_avg_span(self, foreshadows: List[Foreshadowing]) -> float:
        """计算平均回收跨度"""
        spans = []
        for f in foreshadows:
            if f.revealed_chapter:
                span = f.revealed_chapter - f.planted_chapter
                spans.append(span)
        
        return sum(spans) / len(spans) if spans else 0.0
