"""
老年人用户模拟器 - 简化版

用于模拟老年人用户，与助手系统进行对话。
读取配置文件中的提示词，使用LLM生成用户对话。
"""

import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# 尝试导入 DashScope SDK
try:
    import dashscope
    from dashscope import Generation
    DASHSCOPE_SDK_AVAILABLE = True
except ImportError:
    DASHSCOPE_SDK_AVAILABLE = False
    dashscope = None
    Generation = None
    print("[WARN] dashscope SDK 未安装，请安装: pip install dashscope")

# 尝试导入 langchain
try:
    from langchain_community.chat_models import ChatTongyi
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatTongyi = None
    ChatPromptTemplate = None

# 加载环境变量
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# 从环境变量读取API Key
api_key = os.getenv("DASHSCOPE_API_KEY", "")


class SimpleElderlyUserSimulator:
    """
    简单的老年人用户模拟器
    
    功能：
    - 根据配置文件中的提示词生成用户对话
    - 与助手系统进行对话
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化用户模拟器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.config = self._load_config(config_path)
        self.llm = None
        self.dashscope_initialized = False
        self.elderly_user_prompt = self.config.get("elderly_user_prompt", "")
        self.llm_config = self.config.get("llm_config", {})
        self._init_llm()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        if config_path is None:
            config_path = Path(__file__).parent / "elderly_user_simulator_config.json"
        else:
            config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _init_llm(self):
        """初始化LLM"""
        if not api_key:
            raise ValueError("未设置 DASHSCOPE_API_KEY，请在 .env 文件中配置")
        
        # 优先使用 langchain
        if LANGCHAIN_AVAILABLE:
            try:
                self.llm = ChatTongyi(
                    dashscope_api_key=api_key,
                    model_name=self.llm_config.get("model", "qwen-turbo"),
                    temperature=self.llm_config.get("temperature", 0.7)
                )
                return
            except Exception as e:
                print(f"[WARN] langchain 初始化失败: {e}，尝试使用 DashScope SDK")
        
        # 使用 DashScope SDK
        if DASHSCOPE_SDK_AVAILABLE:
            dashscope.api_key = api_key
            self.dashscope_initialized = True
    
    def generate_user_message(
        self,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        生成用户消息
        
        Args:
            conversation_history: 对话历史，格式：[{"role": "user", "content": "..."}, ...]
            
        Returns:
            str: 生成的用户消息
        """
        # 构建对话历史文本
        history_text = ""
        for msg in conversation_history[-10:]:  # 只使用最近10轮
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                history_text += f"用户：{content}\n"
            elif role == "assistant":
                history_text += f"助手：{content}\n"
        
        # 构建完整提示词
        prompt = f"""{self.elderly_user_prompt}

对话历史：
{history_text if history_text else "（这是第一轮对话）"}

请生成下一轮用户对话（只输出对话内容，不要其他说明）："""
        
        # 调用LLM生成消息
        return self._call_llm(prompt)
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM生成消息"""
        # 优先使用 langchain
        if LANGCHAIN_AVAILABLE and self.llm:
            try:
                messages = [("human", prompt)]
                template = ChatPromptTemplate.from_messages(messages)
                response = self.llm.invoke(template.format_messages())
                
                if hasattr(response, 'content'):
                    return response.content.strip()
                elif isinstance(response, str):
                    return response.strip()
                else:
                    return str(response).strip()
            except Exception as e:
                print(f"[WARN] langchain 调用失败: {e}，尝试使用 DashScope SDK")
        
        # 使用 DashScope SDK
        if DASHSCOPE_SDK_AVAILABLE and self.dashscope_initialized:
            try:
                response = Generation.call(
                    model=self.llm_config.get("model", "qwen-turbo"),
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.llm_config.get("temperature", 0.7)
                )
                
                if response.status_code == 200:
                    return response.output.choices[0].message.content.strip()
                else:
                    raise ValueError(f"DashScope API 调用失败: {response.message}")
            except Exception as e:
                raise ValueError(f"LLM 调用失败: {e}")
        
        raise ValueError("LLM 未初始化，请检查 API Key 配置")


