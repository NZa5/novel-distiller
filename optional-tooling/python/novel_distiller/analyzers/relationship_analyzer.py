"""
人物关系分析器 (Phase 2)
"""

from typing import List, Dict
from ..models.schemas import Character, Chapter, CharacterRelation
from ..utils.llm_client import LLMClient


class RelationshipAnalyzer:
    """人物关系分析器"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化分析器
        
        Args:
            llm_client: LLM 客户端
        """
        self.llm = llm_client
    
    def extract_relationships(
        self,
        characters: List[Character],
        chapters: List[Chapter],
        max_chapters: int = 30
    ) -> List[CharacterRelation]:
        """
        提取人物关系
        
        Args:
            characters: 人物列表
            chapters: 章节列表
            max_chapters: 最多分析的章节数
        
        Returns:
            人物关系列表
        """
        if not characters or len(characters) < 2:
            return []
        
        # 构建人物名称映射（包含别名）
        character_names = self._build_character_map(characters)
        
        # 分析章节中的人物互动
        relations_dict: Dict[tuple, CharacterRelation] = {}
        
        for chapter in chapters[:max_chapters]:
            # 找出本章出现的人物
            chapter_characters = self._find_characters_in_chapter(
                chapter, character_names
            )
            
            if len(chapter_characters) < 2:
                continue
            
            # 使用 LLM 分析人物关系
            chapter_relations = self._analyze_chapter_relations(
                chapter, chapter_characters
            )
            
            # 合并关系
            for relation in chapter_relations:
                key = (relation.source, relation.target)
                
                if key in relations_dict:
                    # 更新已有关系
                    existing = relations_dict[key]
                    existing.chapters.append(chapter.index)
                    existing.chapters = sorted(list(set(existing.chapters)))
                    # 增加关系强度
                    existing.strength = min(1.0, existing.strength + 0.1)
                else:
                    # 新增关系
                    relation.chapters = [chapter.index]
                    relations_dict[key] = relation
        
        return list(relations_dict.values())
    
    def _build_character_map(self, characters: List[Character]) -> Dict[str, Character]:
        """构建人物名称映射"""
        char_map = {}
        for char in characters:
            char_map[char.name] = char
            for alias in char.aliases:
                char_map[alias] = char
        return char_map
    
    def _find_characters_in_chapter(
        self,
        chapter: Chapter,
        character_map: Dict[str, Character]
    ) -> List[str]:
        """找出章节中出现的人物"""
        found = []
        content = chapter.content
        
        for name in character_map.keys():
            if name in content:
                # 使用主名称
                main_name = character_map[name].name
                if main_name not in found:
                    found.append(main_name)
        
        return found
    
    def _analyze_chapter_relations(
        self,
        chapter: Chapter,
        characters: List[str]
    ) -> List[CharacterRelation]:
        """分析章节中的人物关系"""
        
        if len(characters) < 2:
            return []
        
        try:
            system_message = """你是一个小说人物关系分析专家。
请分析文本中人物之间的关系。

关系类型包括：亲属、朋友、敌对、师徒、恋人、同事、陌生人等。

只分析有明确互动的人物，不要推测。"""
            
            # 限制内容长度
            content_preview = chapter.content[:2000]
            
            prompt = f"""请分析以下章节中这些人物之间的关系：

人物列表：{', '.join(characters)}

章节内容：
{chapter.title}
{content_preview}

请返回 JSON 数组，每个关系包含：
- source: 人物A的名字
- target: 人物B的名字
- relation_type: 关系类型（从上述类型中选择）
- description: 关系描述（一句话）
- strength: 关系强度 0-1

只返回在这个章节中有互动的人物关系。"""
            
            response = self.llm.invoke_json(prompt, system_message)
            
            # 解析响应
            relations = []
            relation_list = response if isinstance(response, list) else response.get('relations', [])
            
            for rel_data in relation_list:
                if 'source' in rel_data and 'target' in rel_data:
                    relation = CharacterRelation(
                        source=rel_data['source'],
                        target=rel_data['target'],
                        relation_type=rel_data.get('relation_type', '未知'),
                        description=rel_data.get('description', ''),
                        strength=float(rel_data.get('strength', 0.5)),
                        chapters=[]
                    )
                    relations.append(relation)
            
            return relations
        
        except Exception as e:
            # 出错时返回空列表
            return []
    
    def build_relationship_summary(
        self,
        relations: List[CharacterRelation]
    ) -> Dict:
        """
        构建关系统计摘要
        
        Args:
            relations: 关系列表
        
        Returns:
            统计信息字典
        """
        if not relations:
            return {
                "total_relations": 0,
                "relation_types": {},
                "most_connected": []
            }
        
        # 统计关系类型
        type_counts = {}
        for rel in relations:
            type_counts[rel.relation_type] = type_counts.get(rel.relation_type, 0) + 1
        
        # 统计每个人物的关系数
        char_counts = {}
        for rel in relations:
            char_counts[rel.source] = char_counts.get(rel.source, 0) + 1
            char_counts[rel.target] = char_counts.get(rel.target, 0) + 1
        
        # 找出关系最多的人物
        most_connected = sorted(
            char_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_relations": len(relations),
            "relation_types": type_counts,
            "most_connected": [
                {"name": name, "count": count}
                for name, count in most_connected
            ]
        }
