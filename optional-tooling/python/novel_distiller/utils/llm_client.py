"""
LLM 客户端封装
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 加载环境变量
load_dotenv()


class LLMClient:
    """LLM 客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ):
        """
        初始化 LLM 客户端
        
        Args:
            api_key: API Key（默认从环境变量读取）
            base_url: API 基础 URL
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError("API Key 未设置，请在 .env 文件中配置 OPENAI_API_KEY")
        
        # 初始化 ChatOpenAI
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
    
    def invoke(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        调用 LLM
        
        Args:
            prompt: 用户提示词
            system_message: 系统消息
            **kwargs: 其他参数
        
        Returns:
            LLM 响应文本
        """
        messages = []
        
        if system_message:
            messages.append(SystemMessage(content=system_message))
        
        messages.append(HumanMessage(content=prompt))
        
        response = self.llm.invoke(messages, **kwargs)
        return response.content
    
    def invoke_json(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用 LLM 并返回 JSON
        
        Args:
            prompt: 用户提示词
            system_message: 系统消息
            **kwargs: 其他参数
        
        Returns:
            解析后的 JSON 对象
        """
        import json
        
        # 添加 JSON 格式要求
        json_prompt = f"{prompt}\n\n请以 JSON 格式返回结果，不要包含任何其他文本。"
        
        response = self.invoke(json_prompt, system_message, **kwargs)
        
        # 尝试提取 JSON
        try:
            # 查找 JSON 代码块
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            raise ValueError(f"无法解析 JSON 响应: {e}\n响应内容: {response}")
