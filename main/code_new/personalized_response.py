"""
个性化回答生成模块

根据用户画像和对话历史，生成个性化回答。
使用优化版画像schema的生成控制接口，实现基于画像的个性化回答生成。
"""

import os
from typing import Dict, Any, Optional, TYPE_CHECKING
from pathlib import Path
from dotenv import load_dotenv

# 尝试导入 langchain
try:
    from langchain_community.chat_models import ChatTongyi
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatTongyi = None
    ChatPromptTemplate = None
    print("[WARN] langchain 未安装，将使用 DashScope SDK 直接调用")

# 尝试导入 DashScope SDK
try:
    import dashscope
    from dashscope import Generation
    DASHSCOPE_SDK_AVAILABLE = True
except ImportError:
    DASHSCOPE_SDK_AVAILABLE = False
    dashscope = None
    Generation = None
    if not LANGCHAIN_AVAILABLE:
        print("[WARN] dashscope SDK 未安装，请安装: pip install dashscope")

# 导入优化版画像schema
try:
    from profile_schema_optimized import (
        OptimizedUserProfile,
        GenerationController
    )
    SCHEMA_AVAILABLE = True
except ImportError:
    SCHEMA_AVAILABLE = False
    OptimizedUserProfile = None
    GenerationController = None
    print("[WARN] profile_schema_optimized 未安装，个性化回答功能可能受限")

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# 从环境变量读取API Key
api_key = os.getenv("DASHSCOPE_API_KEY", "")


class PersonalizedResponder:
    """
    个性化回答生成器
    
    功能：
    - 根据用户画像生成个性化回答
    - 使用优化版schema的生成控制接口
    - 支持从memU检索相关记忆
    - 支持对话历史上下文
    """
    
    def __init__(self, memu_store=None, memory_manager=None):
        """
        初始化个性化回答生成器
        
        Args:
            memu_store: memU存储层实例（可选，用于记忆检索）
            memory_manager: Memory管理器实例（可选，用于获取对话历史）
        """
        self.memu_store = memu_store
        self.memory_manager = memory_manager
        self.llm = None
        self.dashscope_initialized = False
        self._init_llm()
    
    def _init_llm(self):
        """初始化LLM（延迟初始化）"""
        if not api_key:
            print("[WARN] 未设置 DASHSCOPE_API_KEY，个性化回答功能可能不可用")
            return
        
        # 优先使用 langchain
        if LANGCHAIN_AVAILABLE and self.llm is None:
            try:
                self.llm = ChatTongyi(
                    dashscope_api_key=api_key,
                    model_name="qwen-turbo",
                    temperature=0.7  # 个性化回答需要一定的创造性
                )
                return
            except Exception as e:
                print(f"[WARN] langchain 初始化失败: {e}，尝试使用 DashScope SDK")
        
        # 使用 DashScope SDK
        if DASHSCOPE_SDK_AVAILABLE and not self.dashscope_initialized:
            dashscope.api_key = api_key
            self.dashscope_initialized = True
    
    async def generate_response(
        self, 
        user_id: str, 
        user_input: str, 
        profile: Dict[str, Any]
    ) -> str:
        """
        根据用户画像和对话历史生成个性化回答
        
        Args:
            user_id: 用户ID
            user_input: 用户输入内容
            profile: 用户画像字典（优化版结构）
            
        Returns:
            str: 个性化回答
            
        Raises:
            ValueError: 当LLM未初始化或API Key未设置时
        """
        if not SCHEMA_AVAILABLE:
            raise ValueError("profile_schema_optimized 未安装，无法生成个性化回答")
        
        # 将字典转换为 OptimizedUserProfile 对象
        try:
            profile_obj = OptimizedUserProfile.from_dict(profile)
        except Exception as e:
            print(f"[WARN] 画像格式转换失败: {e}，使用默认配置")
            profile_obj = OptimizedUserProfile()
        
        # 1. 获取生成控制参数
        control_params = profile_obj.get_generation_control_params()
        
        # 2. 构建系统提示词（包含画像控制参数）
        system_prompt = GenerationController.build_system_prompt(profile_obj)
        
        # 3. 获取对话历史上下文
        conversation_context = ""
        if self.memory_manager:
            try:
                conversation_context = self.memory_manager.get_conversation_context(
                    user_id, 
                    limit=10
                )
            except Exception as e:
                print(f"[WARN] 获取对话历史失败: {e}")
        
        # 4. 从memU检索相关记忆（可选）
        memory_context = ""
        if self.memu_store:
            try:
                memory_result = await self.memu_store.get_user_memory(user_id, user_input)
                if memory_result and isinstance(memory_result, dict):
                    # 提取记忆内容
                    # memU 返回的结果可能包含 resources 或 items
                    if "resources" in memory_result and memory_result["resources"]:
                        # 提取第一个资源的内容
                        first_resource = memory_result["resources"][0]
                        if isinstance(first_resource, dict):
                            if "content" in first_resource:
                                memory_context = first_resource["content"]
                            elif "text" in first_resource:
                                memory_context = first_resource["text"]
                            elif "metadata" in first_resource and "content" in first_resource["metadata"]:
                                memory_context = first_resource["metadata"]["content"]
                    elif "items" in memory_result and memory_result["items"]:
                        # 提取第一个 item 的内容
                        first_item = memory_result["items"][0]
                        if isinstance(first_item, dict):
                            if "content" in first_item:
                                memory_context = first_item["content"]
                            elif "text" in first_item:
                                memory_context = first_item["text"]
            except Exception as e:
                print(f"[WARN] 检索记忆失败: {e}")
        
        # 5. 构建用户提示词（不包含系统提示词）
        user_prompt = self._build_user_prompt(
            user_input=user_input,
            conversation_context=conversation_context,
            memory_context=memory_context,
            control_params=control_params
        )
        
        # 6. 调用LLM生成回答
        response = self._call_llm(user_prompt, system_prompt)
        
        # 7. 后处理优化（根据画像调整回答风格）
        final_response = GenerationController.adapt_response_style(
            response, 
            profile_obj
        )
        
        return final_response
    
    def _build_user_prompt(
        self,
        user_input: str,
        conversation_context: str = "",
        memory_context: str = "",
        control_params: Dict[str, Any] = None
    ) -> str:
        """
        构建用户提示词（不包含系统提示词）
        
        Args:
            user_input: 用户输入
            conversation_context: 对话历史上下文
            memory_context: 相关记忆上下文
            control_params: 生成控制参数
            
        Returns:
            str: 用户提示词
        """
        prompt_parts = []
        
        # 添加相关记忆（如果有）
        if memory_context:
            prompt_parts.append(f"## 相关记忆\n{memory_context}")
        
        # 添加对话历史（如果有）
        if conversation_context:
            prompt_parts.append(f"## 对话历史\n{conversation_context}")
        
        # 添加用户当前问题
        prompt_parts.append(f"## 当前问题\n用户：{user_input}")
        
        # 添加回答要求
        prompt_parts.append("\n## 回答要求")
        prompt_parts.append("1. 根据用户画像信息，提供个性化的回答")
        prompt_parts.append("2. 考虑用户的年龄、健康状况、生活方式等特征")
        prompt_parts.append("3. 使用适合老年人的语言风格（简单、亲切、耐心）")
        prompt_parts.append("4. 如果用户画像中有相关信息，要充分利用")
        prompt_parts.append("5. 回答要具体、实用、有帮助")
        
        # 添加个性化控制要求（基于控制参数）
        if control_params:
            # 语言风格控制
            formality = control_params.get("formality_level", "")
            if formality == "温暖":
                prompt_parts.append("6. 使用温暖亲切的语调，多用情感词汇表达关心")
            elif formality == "正式":
                prompt_parts.append("6. 使用正式礼貌的语言，保持尊敬的态度")
            elif formality == "随意":
                prompt_parts.append("6. 使用轻松随意的语言，像朋友聊天一样")
            
            # 详细程度控制
            verbosity = control_params.get("verbosity_level", "")
            if verbosity == "简洁":
                prompt_parts.append("7. 回答要简洁明了，避免冗长的解释")
            elif verbosity == "详细":
                prompt_parts.append("7. 提供详细完整的解释，不需要担心篇幅")
            elif verbosity == "适中":
                prompt_parts.append("7. 回答适度详细，保持适中的篇幅")
            
            # 认知适配控制
            attention = control_params.get("attention_span", "")
            if attention == "短":
                prompt_parts.append("8. 使用短段落，每段控制在2-3句话以内，避免长篇大论")
            elif attention == "长":
                prompt_parts.append("8. 可以使用较长的段落，提供完整的说明")
            
            # 安全风险控制
            risk = control_params.get("risk_cautiousness", "")
            if risk == "非常谨慎":
                prompt_parts.append("9. 对于健康和安全建议要格外谨慎，强调潜在风险")
            elif risk == "谨慎":
                prompt_parts.append("9. 对健康和安全相关建议保持适度谨慎")
            
            # 情感支持控制
            loneliness = control_params.get("loneliness_level", "")
            if loneliness in ["高", "很高"]:
                prompt_parts.append("10. 关注用户的情感状态，多给予陪伴和关怀")
            
            # 核心兴趣
            if control_params.get("core_interests"):
                interests = ", ".join(control_params["core_interests"][:3])
                prompt_parts.append(f"11. 可以结合用户的兴趣（{interests}）举例说明，增强共鸣")
            
            # 敏感话题
            if control_params.get("taboo_topics"):
                taboos = ", ".join(control_params["taboo_topics"])
                prompt_parts.append(f"12. 严格避免涉及敏感话题：{taboos}")
        else:
            prompt_parts.append("6. 根据生成控制参数调整回答风格")
        
        prompt_parts.append("\n请生成个性化回答：")
        
        return "\n".join(prompt_parts)
    
    def _call_llm(self, user_prompt: str, system_prompt: str = "") -> str:
        """
        调用LLM生成回答
        
        Args:
            user_prompt: 用户提示词
            system_prompt: 系统提示词
            
        Returns:
            str: LLM生成的回答
            
        Raises:
            ValueError: 当LLM未初始化时
        """
        # 优先使用 langchain
        if LANGCHAIN_AVAILABLE and self.llm:
            try:
                # 构建消息列表
                messages = []
                if system_prompt:
                    messages.append(("system", system_prompt))
                messages.append(("human", user_prompt))
                
                # 使用 ChatPromptTemplate
                template = ChatPromptTemplate.from_messages(messages)
                formatted_messages = template.format_messages()
                
                # 调用 LLM
                response = self.llm.invoke(formatted_messages)
                
                # 提取回答内容
                if hasattr(response, 'content'):
                    return response.content
                elif isinstance(response, str):
                    return response
                else:
                    return str(response)
            except Exception as e:
                print(f"[WARN] langchain 调用失败: {e}，尝试使用 DashScope SDK")
        
        # 使用 DashScope SDK
        if DASHSCOPE_SDK_AVAILABLE and self.dashscope_initialized:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": user_prompt})
                
                response = Generation.call(
                    model="qwen-turbo",
                    messages=messages,
                    temperature=0.7
                )
                
                if response.status_code == 200:
                    return response.output.choices[0].message.content
                else:
                    raise ValueError(f"DashScope API 调用失败: {response.message}")
            except Exception as e:
                raise ValueError(f"LLM 调用失败: {e}")
        
        raise ValueError("LLM 未初始化，请检查 API Key 配置")

