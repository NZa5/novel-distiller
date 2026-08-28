"""
结构分析器
"""

from typing import Optional
from ..models.schemas import NovelMeta, Chapter
from ..utils.llm_client import LLMClient
from typing import List


class StructureAnalyzer:
    """结构分析器"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化分析器
        
        Args:
            llm_client: LLM 客户端
        """
        self.llm = llm_client
    
    def analyze_meta(
        self,
        chapters: List[Chapter],
        file_path: str = ""
    ) -> NovelMeta:
        """
        分析小说元数据
        
        Args:
            chapters: 章节列表
            file_path: 文件路径（用于提取标题）
        
        Returns:
            小说元数据
        """
        # 计算总字数
        total_words = sum(ch.word_count for ch in chapters)
        
        # 尝试从前几章提取标题和作者
        title, author = self._extract_title_author(chapters[:3])
        
        # 如果未提取到标题，使用文件名
        if not title:
            import os
            title = os.path.splitext(os.path.basename(file_path))[0] if file_path else "未知标题"
        
        # 尝试识别类型
        genre = self._detect_genre(chapters[:10])
        
        return NovelMeta(
            title=title,
            author=author,
            total_chapters=len(chapters),
            total_words=total_words,
            genre=genre,
        )
    
    def _extract_title_author(self, chapters: List[Chapter]) -> tuple[str, Optional[str]]:
        """
        从前几章提取标题和作者
        
        Args:
            chapters: 前几章内容
        
        Returns:
            (标题, 作者)
        """
        if not chapters:
            return "未知标题", None
        
        # 简单实现：从第一章提取
        first_chapter = chapters[0]
        
        # 如果第一章标题不是"第一章"这种格式，可能就是书名
        if not any(keyword in first_chapter.title for keyword in ["第", "章", "Chapter"]):
            return first_chapter.title, None
        
        # 尝试使用 LLM 提取
        try:
            system_message = "你是一个小说分析专家，擅长从文本中提取书名和作者信息。"
            
            content_preview = first_chapter.content[:500]
            prompt = f"""请从以下文本中提取小说的标题和作者（如果有）。

文本：
{first_chapter.title}
{content_preview}

请以 JSON 格式返回：
{{
  "title": "书名",
  "author": "作者名（如果找不到则为 null）"
}}"""
            
            response = self.llm.invoke_json(prompt, system_message)
            return response.get("title", "未知标题"), response.get("author")
        
        except Exception:
            return "未知标题", None
    
    def _detect_genre(self, chapters: List[Chapter]) -> Optional[str]:
        """
        检测小说类型
        
        Args:
            chapters: 前几章内容
        
        Returns:
            类型（玄幻/都市/历史等）
        """
        if not chapters:
            return None
        
        try:
            system_message = """你是一个小说类型识别专家。请根据文本内容判断小说类型。
常见类型包括：玄幻、修真、都市、历史、科幻、悬疑、武侠、言情、军事等。"""
            
            # 组合前几章内容
            content_samples = []
            for ch in chapters[:5]:
                preview = ch.content[:300]
                content_samples.append(f"{ch.title}: {preview}")
            
            prompt = f"""请分析以下章节内容，判断这本小说的类型：

{chr(10).join(content_samples)}

请只返回类型名称（如"玄幻"、"都市"等），不要其他解释。"""
            
            response = self.llm.invoke(prompt, system_message)
            return response.strip()
        
        except Exception:
            return None
    
    def analyze_narrative_structure(self, chapters: List[Chapter]) -> dict:
        """
        分析叙事结构
        
        Args:
            chapters: 章节列表
        
        Returns:
            结构分析结果
        """
        return {
            "total_chapters": len(chapters),
            "avg_chapter_length": sum(ch.word_count for ch in chapters) // len(chapters) if chapters else 0,
            "longest_chapter": max(chapters, key=lambda x: x.word_count).index if chapters else None,
            "shortest_chapter": min(chapters, key=lambda x: x.word_count).index if chapters else None,
        }
