"""
LLM 客户端封装
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any, Iterable
from urllib.parse import urlparse
from ipaddress import ip_address
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage


@dataclass(frozen=True)
class RemotePolicy:
    allow_remote: bool = False
    allowed_hosts: frozenset[str] = frozenset({"api.openai.com"})


def validate_endpoint(endpoint: str, policy: RemotePolicy):
    parsed = urlparse(endpoint)
    host = (parsed.hostname or "").lower()
    if not policy.allow_remote:
        raise ValueError("ND-REMOTE-DISALLOWED")
    if parsed.scheme != "https" or parsed.username or parsed.password or not host:
        raise ValueError("ND-REMOTE-ENDPOINT")
    if host not in {h.lower() for h in policy.allowed_hosts}:
        raise ValueError("ND-REMOTE-HOST")
    try:
        addr = ip_address(host)
    except ValueError:
        addr = None
    if addr is not None and (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved):
        raise ValueError("ND-REMOTE-ENDPOINT")
    return parsed


class LLMClient:
    """LLM 客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        policy: Optional[RemotePolicy] = None,
        allow_remote: bool = False,
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
        self.policy = policy or RemotePolicy(allow_remote=allow_remote)
        validate_endpoint(self.base_url, self.policy)

        self.temperature = temperature
        self.max_tokens = max_tokens
        if not self.api_key:
            raise ValueError("ND-CREDENTIAL-MISSING")
        
        # 初始化 ChatOpenAI
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
    
    def invoke_messages(self, messages: Iterable[BaseMessage], **kwargs) -> str:
        response = self.llm.invoke(list(messages), **kwargs)
        return response.content

    def invoke(self, prompt: str, system_message: Optional[str] = None, **kwargs) -> str:
        messages = ([SystemMessage(content=system_message)] if system_message else []) + [HumanMessage(content=prompt)]
        return self.invoke_messages(messages, **kwargs)

    def invoke_json_messages(self, messages: Iterable[BaseMessage], **kwargs) -> Dict[str, Any]:
        import json
        try:
            response = self.invoke_messages(messages, **kwargs)
            text = response.split("```json", 1)[1].split("```", 1)[0].strip() if "```json" in response else response.strip()
            return json.loads(text)
        except (json.JSONDecodeError, IndexError, TypeError):
            raise ValueError("ND-MODEL-JSON: invalid provider response") from None

    def invoke_json(self, prompt: str, system_message: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        json_prompt = f"{prompt}\n\n请以 JSON 格式返回结果，不要包含任何其他文本。"
        return self.invoke_json_messages(([SystemMessage(content=system_message)] if system_message else []) + [HumanMessage(content=json_prompt)], **kwargs)
