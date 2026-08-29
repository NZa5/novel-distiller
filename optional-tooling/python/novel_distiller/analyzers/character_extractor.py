"""
人物提取器
"""

import json
from typing import List
from ..models.schemas import Character, CharacterRole, Chapter
from ..utils.llm_client import LLMClient


class CharacterExtractor:
    """人物提取器"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化提取器
        
        Args:
            llm_client: LLM 客户端
        """
        self.llm = llm_client
    
    def extract(self, chapters: List[Chapter], max_chapters: int = 30) -> List[Character]:
        """
        提取人物
        
        Args:
            chapters: 章节列表
            max_chapters: 最多分析的章节数（避免 Token 过多）
        
        Returns:
            人物列表
        """
        # 选择要分析的章节（前期章节通常包含主要人物介绍）
        chapters_to_analyze = chapters[:max_chapters]
        
        # 构建提示词
        system_message = """你是一个专业的小说分析专家，擅长识别和提取小说中的人物信息。
你的任务是从给定的章节中提取所有重要人物，包括：
1. 主角（protagonist）：故事的核心人物
2. 主要配角（major）：对情节有重要影响的角色
3. 次要配角（minor）：有名字但作用较小的角色
4. 反派（villain）：与主角对立的角色
5. 路人/龙套（supporting）：一笔带过的角色

对于每个人物，请提取：
- name: 人物姓名（使用最常见的称呼）
- aliases: 别名列表（如小名、称号等）
- role: 角色类型（protagonist/major/minor/villain/supporting）
- description: 简短的人物描述（50-100字）
- first_appearance: 首次出现的章节序号
- key_traits: 关键特征列表（如性格、能力、身份等）"""
        
        # 准备章节内容摘要
        chapters_summary = []
        for ch in chapters_to_analyze:
            # 限制每章内容长度
            content_preview = ch.content[:1000] + "..." if len(ch.content) > 1000 else ch.content
            chapters_summary.append(f"第{ch.index}章 {ch.title}\n{content_preview}")
        
        prompt = f"""请分析以下章节，提取所有重要人物：

{chr(10).join(chapters_summary)}

请以 JSON 数组格式返回结果，每个人物包含：name, aliases, role, description, first_appearance, key_traits

示例格式：
[
  {{
    "name": "张三",
    "aliases": ["阿三", "三哥"],
    "role": "protagonist",
    "description": "主角，普通青年，因机缘巧合获得系统",
    "first_appearance": 1,
    "key_traits": ["谨慎", "善良", "有责任心"]
  }},
  {{
    "name": "李四",
    "aliases": ["四爷"],
    "role": "major",
    "description": "主角的好友，江湖老手",
    "first_appearance": 3,
    "key_traits": ["豪爽", "讲义气", "武功高强"]
  }}
]"""
        
        try:
            response = self.llm.invoke_json(prompt, system_message)
            
            # 解析 JSON 并转换为 Character 对象
            characters = []
            character_list = response if isinstance(response, list) else response.get("characters", [])
            
            for char_data in character_list:
                try:
                    characters.append(
                        Character(
                            name=char_data["name"],
                            aliases=char_data.get("aliases", []),
                            role=CharacterRole(char_data.get("role", "supporting")),
                            description=char_data.get("description", ""),
                            first_appearance=char_data.get("first_appearance", 1),
                            key_traits=char_data.get("key_traits", []),
                        )
                    )
                except (KeyError, ValueError) as e:
                    print(f"警告：跳过无效的人物数据: {e}")
                    continue
            
            return characters
        
        except Exception as e:
            print(f"人物提取失败: {e}")
            return []
    
    def extract_by_role(self, chapters: List[Chapter], role: CharacterRole) -> List[Character]:
        """
        按角色类型提取人物
        
        Args:
            chapters: 章节列表
            role: 角色类型
        
        Returns:
            指定类型的人物列表
        """
        all_characters = self.extract(chapters)
        return [ch for ch in all_characters if ch.role == role]
    
    def get_protagonist(self, chapters: List[Chapter]) -> List[Character]:
        """提取主角"""
        return self.extract_by_role(chapters, CharacterRole.PROTAGONIST)
    
    def get_major_characters(self, chapters: List[Chapter]) -> List[Character]:
        """提取主要配角"""
        return self.extract_by_role(chapters, CharacterRole.MAJOR)
