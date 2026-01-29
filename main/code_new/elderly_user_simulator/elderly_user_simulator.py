"""
老年人用户模拟器 - 阶段一增强版

用于模拟老年人用户，与助手系统进行对话。
支持 ground_truth_profile（真实画像）和 expressed_profile（已表达画像）管理。
实现基础的噪声模型，模拟真实老人的表达特点。

阶段一功能：
- 管理隐藏真实画像（Ground Truth Profile）
- 跟踪已表达画像（Expressed Profile）
- 应用表达噪声模型（Noise Model）
- 根据 ground_truth_profile 生成用户对话
"""

import os
import json
import random
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

# 导入优化版画像结构
try:
    from profile_schema_optimized import init_optimized_profile, OptimizedUserProfile
    PROFILE_SCHEMA_AVAILABLE = True
except ImportError:
    PROFILE_SCHEMA_AVAILABLE = False
    init_optimized_profile = None
    OptimizedUserProfile = None
    print("[WARN] profile_schema_optimized 模块未找到，将使用字典格式")


class SimulatedUser:
    """
    模拟用户类 - 阶段一增强版
    
    核心功能：
    - 管理 ground_truth_profile（真实画像，不可见，用于评估）
    - 管理 expressed_profile（已表达画像，可见）
    - 应用噪声模型（遗忘、模糊、误导）
    - 根据 ground_truth_profile 生成用户对话
    """
    
    def __init__(
        self,
        ground_truth_profile: Dict[str, Any],
        noise_model: Optional[Dict[str, float]] = None
    ):
        """
        初始化模拟用户
        
        Args:
            ground_truth_profile: 真实用户画像（不可见，用于评估）
            noise_model: 噪声模型参数
        """
        self.ground_truth_profile = ground_truth_profile
        self.expressed_profile = self._init_expressed_profile()
        
        # 默认噪声模型
        self.noise_model = noise_model or {
            "forgetfulness_rate": 0.1,      # 遗忘率：10% 概率忘记某些信息
            "vagueness_rate": 0.15,          # 模糊表达率：15% 概率表达模糊
            "misleading_rate": 0.05,         # 误导率：5% 概率提供错误信息
            "topic_hopping_rate": 0.2         # 话题跳跃率：20% 概率跳话题
        }
    
    def _init_expressed_profile(self) -> Dict[str, Any]:
        """初始化已表达画像（空画像）"""
        if PROFILE_SCHEMA_AVAILABLE:
            return init_optimized_profile()
        else:
            # 如果无法导入，返回空字典结构
            return {
                "identity_language": {},
                "health_safety": {},
                "cognitive_interaction": {},
                "emotional_support": {},
                "lifestyle_social": {},
                "values_preferences": {}
            }
    
    def update_expressed_profile(
        self,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        根据对话历史更新已表达画像
        
        分析对话中已经暴露的画像信息，更新 expressed_profile
        
        Args:
            conversation_history: 对话历史
            
        Returns:
            更新后的 expressed_profile
        """
        # 阶段一：简单实现，后续可以增强
        # 这里暂时返回当前 expressed_profile
        # 后续可以添加对话分析逻辑，自动提取已表达的信息
        return self.expressed_profile
    
    def apply_noise(
        self,
        fact: Dict[str, Any],
        noise_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        应用表达噪声（模糊、否认、跳话题）
        
        Args:
            fact: 要表达的事实
            noise_type: 噪声类型（如果为None，随机选择）
            
        Returns:
            添加噪声后的事实
        """
        if noise_type is None:
            # 随机选择噪声类型
            rand = random.random()
            if rand < self.noise_model["forgetfulness_rate"]:
                noise_type = "forgetfulness"
            elif rand < self.noise_model["forgetfulness_rate"] + self.noise_model["vagueness_rate"]:
                noise_type = "vagueness"
            elif rand < self.noise_model["forgetfulness_rate"] + self.noise_model["vagueness_rate"] + self.noise_model["misleading_rate"]:
                noise_type = "misleading"
            else:
                noise_type = "none"
        
        if noise_type == "forgetfulness":
            # 遗忘：不表达这个事实
            return None
        
        elif noise_type == "vagueness":
            # 模糊：添加模糊词汇
            value = fact.get("value")
            if isinstance(value, str):
                vague_prefixes = ["大概", "可能", "好像", "似乎", "差不多"]
                vague_suffixes = ["左右", "上下", "前后"]
                if random.random() < 0.5:
                    fact["value"] = random.choice(vague_prefixes) + value
                else:
                    fact["value"] = value + random.choice(vague_suffixes)
            return fact
        
        elif noise_type == "misleading":
            # 误导：提供部分错误信息（阶段一简单实现）
            # 后续可以增强为更复杂的误导逻辑
            return fact
        
        else:
            # 无噪声：直接返回
            return fact
    
    def get_profile_summary_for_prompt(self) -> str:
        """
        获取用于提示词的画像摘要（基于 ground_truth_profile）
        
        注意：这个摘要用于指导LLM生成对话，但不直接暴露所有信息
        会根据 expressed_profile 和噪声模型调整
        
        Returns:
            画像摘要文本
        """
        summary_parts = []
        gt = self.ground_truth_profile
        
        # 身份与语言
        identity = gt.get("identity_language", {})
        if identity.get("age", {}).get("value"):
            summary_parts.append(f"年龄：{identity['age']['value']}岁")
        if identity.get("gender", {}).get("value"):
            summary_parts.append(f"性别：{identity['gender']['value']}")
        if identity.get("region", {}).get("value"):
            summary_parts.append(f"地区：{identity['region']['value']}")
        if identity.get("education_level", {}).get("value"):
            summary_parts.append(f"教育程度：{identity['education_level']['value']}")
        
        # 健康与安全
        health = gt.get("health_safety", {})
        if health.get("chronic_conditions", {}).get("value"):
            conditions = health["chronic_conditions"]["value"]
            if isinstance(conditions, list) and len(conditions) > 0:
                summary_parts.append(f"慢性疾病：{', '.join(conditions)}")
        if health.get("mobility_level", {}).get("value"):
            summary_parts.append(f"行动能力：{health['mobility_level']['value']}")
        
        # 生活方式
        lifestyle = gt.get("lifestyle_social", {})
        if lifestyle.get("living_situation", {}).get("value"):
            summary_parts.append(f"居住状况：{lifestyle['living_situation']['value']}")
        if lifestyle.get("core_interests", {}).get("value"):
            interests = lifestyle["core_interests"]["value"]
            if isinstance(interests, list) and len(interests) > 0:
                summary_parts.append(f"兴趣爱好：{', '.join(interests)}")
        
        # 情感支持
        emotional = gt.get("emotional_support", {})
        if emotional.get("loneliness_level", {}).get("value"):
            summary_parts.append(f"孤独感：{emotional['loneliness_level']['value']}")
        
        return "；".join(summary_parts) if summary_parts else "（基本信息）"
    
    def evaluate_extraction_accuracy(
        self,
        extracted_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估画像提取准确性 - 阶段一基础版
        
        对比 extracted_profile vs ground_truth_profile
        
        Args:
            extracted_profile: 助手系统提取的画像
            
        Returns:
            评估结果字典，包含：
            - overall_accuracy: 总体准确率
            - dimension_accuracy: 各维度准确率
            - error_analysis: 错误分析
        """
        gt = self.ground_truth_profile
        extracted = extracted_profile
        
        dimension_accuracy = {}
        total_fields = 0
        correct_fields = 0
        
        # 遍历所有维度
        for dimension_name in ["identity_language", "health_safety", "cognitive_interaction",
                              "emotional_support", "lifestyle_social", "values_preferences"]:
            gt_dim = gt.get(dimension_name, {})
            ext_dim = extracted.get(dimension_name, {})
            
            dim_total = 0
            dim_correct = 0
            
            # 遍历维度内的所有字段
            for field_name in gt_dim.keys():
                gt_field = gt_dim.get(field_name, {})
                ext_field = ext_dim.get(field_name, {})
                
                gt_value = gt_field.get("value")
                ext_value = ext_field.get("value")
                
                if gt_value is not None:
                    dim_total += 1
                    total_fields += 1
                    
                    # 简单匹配：值相同则认为正确
                    if gt_value == ext_value:
                        dim_correct += 1
                        correct_fields += 1
                    # 列表类型：检查交集
                    elif isinstance(gt_value, list) and isinstance(ext_value, list):
                        if set(gt_value) & set(ext_value):
                            dim_correct += 1
                            correct_fields += 1
            
            if dim_total > 0:
                dimension_accuracy[dimension_name] = dim_correct / dim_total
            else:
                dimension_accuracy[dimension_name] = 0.0
        
        overall_accuracy = correct_fields / total_fields if total_fields > 0 else 0.0
        
        return {
            "overall_accuracy": overall_accuracy,
            "dimension_accuracy": dimension_accuracy,
            "total_fields": total_fields,
            "correct_fields": correct_fields,
            "error_analysis": {
                "missing_extractions": [],  # 阶段一简单实现
                "incorrect_extractions": []  # 阶段一简单实现
            }
        }


class SimpleElderlyUserSimulator:
    """
    简单的老年人用户模拟器 - 阶段一增强版
    
    功能：
    - 根据配置文件中的提示词生成用户对话
    - 支持 ground_truth_profile 和 expressed_profile 管理
    - 应用噪声模型模拟真实老人表达特点
    - 与助手系统进行对话
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        ground_truth_profile: Optional[Dict[str, Any]] = None
    ):
        """
        初始化用户模拟器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
            ground_truth_profile: 真实用户画像（如果为None，从配置文件读取）
        """
        self.config = self._load_config(config_path)
        self.llm = None
        self.dashscope_initialized = False
        self.elderly_user_prompt = self.config.get("elderly_user_prompt", "")
        self.llm_config = self.config.get("llm_config", {})
        
        # 初始化 SimulatedUser
        if ground_truth_profile is None:
            # 从配置文件读取 ground_truth_profile
            ground_truth_profile = self.config.get("ground_truth_profile")
            if ground_truth_profile is None:
                # 如果没有配置，使用默认空画像
                if PROFILE_SCHEMA_AVAILABLE:
                    ground_truth_profile = init_optimized_profile()
                else:
                    ground_truth_profile = {}
        
        noise_model = self.config.get("noise_model")
        self.simulated_user = SimulatedUser(
            ground_truth_profile=ground_truth_profile,
            noise_model=noise_model
        )
        
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
        生成用户消息 - 阶段一增强版
        
        根据 ground_truth_profile 和 expressed_profile 生成对话，
        应用噪声模型模拟真实老人表达特点。
        
        Args:
            conversation_history: 对话历史，格式：[{"role": "user", "content": "..."}, ...]
            
        Returns:
            str: 生成的用户消息
        """
        # 更新已表达画像
        self.simulated_user.update_expressed_profile(conversation_history)
        
        # 获取画像摘要（用于提示词）
        profile_summary = self.simulated_user.get_profile_summary_for_prompt()
        
        # 构建对话历史文本
        history_text = ""
        for msg in conversation_history[-10:]:  # 只使用最近10轮
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                history_text += f"用户：{content}\n"
            elif role == "assistant":
                history_text += f"助手：{content}\n"
        
        # 构建完整提示词（整合 ground_truth_profile 信息）
        prompt = f"""{self.elderly_user_prompt}

你的真实画像信息（用于指导对话生成，但不要直接全部说出来，要自然地在对话中体现）：
{profile_summary}

对话历史：
{history_text if history_text else "（这是第一轮对话）"}

请根据以上信息，生成下一轮用户对话。要求：
1. 符合老年人的语言特点
2. 自然、真实、有感情
3. 对话长度适中（1-3句话）
4. 与对话历史连贯
5. 可以自然地体现你的画像信息，但不要一次性全部说出来
6. 可以适当模糊、重复或跳话题（模拟真实老人的表达特点）

只输出对话内容，不要其他说明："""
        
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


