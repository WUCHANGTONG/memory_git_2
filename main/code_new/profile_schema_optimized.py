"""
用户画像结构定义模块 - 生成控制型优化版

设计理念：
1. 双层架构：生成控制核心层 + 解释学习层
2. 面向LLM生成：每个字段都是直接的"控制旋钮"
3. 减少冗余：合并语义重叠的字段
4. 统一接口：提供标准化的生成控制参数

核心原则：
- 生成控制层：直接注入Prompt，影响回答生成
- 解释学习层：用于画像更新和效果评估，不直接给LLM
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from datetime import datetime


class FieldValue(BaseModel):
    """画像字段值结构"""
    value: Optional[Union[str, int, float, List[str]]] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    last_updated: Optional[str] = None


# ==================== 生成控制核心层 ====================

class IdentityLanguage(BaseModel):
    """身份与语言 - 影响称呼、语言风格、解释深度"""
    age: FieldValue = Field(default_factory=FieldValue)  # 年龄
    gender: FieldValue = Field(default_factory=FieldValue)  # 性别
    region: FieldValue = Field(default_factory=FieldValue)  # 地区
    education_level: FieldValue = Field(default_factory=FieldValue)  # 教育程度
    explanation_depth_preference: FieldValue = Field(default_factory=FieldValue)  # 解释深度偏好


class HealthSafety(BaseModel):
    """健康与风险控制 - 影响建议强度、安全提示、保守程度"""
    chronic_conditions: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 慢性疾病
    mobility_level: FieldValue = Field(default_factory=FieldValue)  # 行动能力
    daily_energy_level: FieldValue = Field(default_factory=FieldValue)  # 日常精力水平
    risk_sensitivity_level: FieldValue = Field(default_factory=FieldValue)  # 风险敏感度


class CognitiveInteraction(BaseModel):
    """认知与交互能力 - 影响句长、步骤拆分、重复确认"""
    attention_span: FieldValue = Field(default_factory=FieldValue)  # 注意力持续时间
    processing_speed: FieldValue = Field(default_factory=FieldValue)  # 信息处理速度
    digital_literacy: FieldValue = Field(default_factory=FieldValue)  # 数字技能水平
    instruction_following_ability: FieldValue = Field(default_factory=FieldValue)  # 指令理解能力


class EmotionalSupport(BaseModel):
    """情感与陪伴需求 - 影响语气选择、陪伴模式"""
    baseline_mood: FieldValue = Field(default_factory=FieldValue)  # 基础情绪状态
    loneliness_level: FieldValue = Field(default_factory=FieldValue)  # 孤独感程度
    emotional_support_need: FieldValue = Field(default_factory=FieldValue)  # 情感支持需求强度
    preferred_conversation_mode: FieldValue = Field(default_factory=FieldValue)  # 偏好对话模式


class LifestyleSocial(BaseModel):
    """生活方式与社交环境 - 影响举例、推荐、社交导向"""
    living_situation: FieldValue = Field(default_factory=FieldValue)  # 居住状况
    social_support_level: FieldValue = Field(default_factory=FieldValue)  # 社交支持水平
    independence_level: FieldValue = Field(default_factory=FieldValue)  # 独立性水平
    core_interests: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 核心兴趣


class ValuesPreferences(BaseModel):
    """价值观与话题偏好 - 影响话题选择、价值对齐、避免踩雷"""
    topic_preferences: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 话题偏好
    taboo_topics: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 敏感话题
    value_orientation: FieldValue = Field(default_factory=FieldValue)  # 价值观导向
    motivational_factors: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 激励因素


class ResponseStyleController(BaseModel):
    """生成风格控制器 - 直接控制LLM生成参数的核心层"""
    formality_level: FieldValue = Field(default_factory=FieldValue)  # 正式程度 (casual/formal/warm)
    verbosity_level: FieldValue = Field(default_factory=FieldValue)  # 详细程度 (brief/moderate/detailed)
    emotional_tone: FieldValue = Field(default_factory=FieldValue)  # 情感语调 (neutral/caring/encouraging)
    directive_strength: FieldValue = Field(default_factory=FieldValue)  # 指导强度 (suggestive/moderate/directive)
    information_density: FieldValue = Field(default_factory=FieldValue)  # 信息密度 (low/medium/high)
    risk_cautiousness: FieldValue = Field(default_factory=FieldValue)  # 风险谨慎度 (relaxed/cautious/very_cautious)


# ==================== 解释学习层 ====================

class InteractionHistory(BaseModel):
    """交互历史 - 用于画像更新和效果评估，不直接给LLM"""
    successful_interaction_patterns: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))
    failed_interaction_patterns: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))
    preference_evolution_trend: FieldValue = Field(default_factory=FieldValue)
    response_satisfaction_score: FieldValue = Field(default_factory=FieldValue)
    last_interaction_feedback: FieldValue = Field(default_factory=FieldValue)


# ==================== 主画像类 ====================

class OptimizedUserProfile(BaseModel):
    """优化的用户画像 - 生成控制型"""
    
    # 生成控制核心层（直接用于LLM生成）
    identity_language: IdentityLanguage = Field(default_factory=IdentityLanguage)
    health_safety: HealthSafety = Field(default_factory=HealthSafety)
    cognitive_interaction: CognitiveInteraction = Field(default_factory=CognitiveInteraction)
    emotional_support: EmotionalSupport = Field(default_factory=EmotionalSupport)
    lifestyle_social: LifestyleSocial = Field(default_factory=LifestyleSocial)
    values_preferences: ValuesPreferences = Field(default_factory=ValuesPreferences)
    response_style: ResponseStyleController = Field(default_factory=ResponseStyleController)
    
    # 解释学习层（后台使用）
    interaction_history: InteractionHistory = Field(default_factory=InteractionHistory)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return self.model_dump(mode='json')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizedUserProfile':
        """从字典创建"""
        return cls.model_validate(data)

    def get_generation_control_params(self) -> Dict[str, Any]:
        """获取LLM生成控制参数 - 这是最重要的接口"""
        return {
            # 语言风格控制
            "formality_level": self.response_style.formality_level.value or "warm",
            "verbosity_level": self.response_style.verbosity_level.value or "moderate", 
            "emotional_tone": self.response_style.emotional_tone.value or "caring",
            
            # 内容控制
            "information_density": self.response_style.information_density.value or "medium",
            "explanation_depth": self.identity_language.explanation_depth_preference.value or "moderate",
            "directive_strength": self.response_style.directive_strength.value or "suggestive",
            
            # 安全控制
            "risk_cautiousness": self.response_style.risk_cautiousness.value or "cautious",
            "health_awareness": bool(self.health_safety.chronic_conditions.value),
            
            # 认知适配
            "attention_span": self.cognitive_interaction.attention_span.value or "normal",
            "processing_speed": self.cognitive_interaction.processing_speed.value or "normal",
            
            # 情感支持
            "emotional_support_need": self.emotional_support.emotional_support_need.value or "moderate",
            "loneliness_level": self.emotional_support.loneliness_level.value or "low",
            
            # 个性化内容
            "core_interests": self.lifestyle_social.core_interests.value or [],
            "taboo_topics": self.values_preferences.taboo_topics.value or [],
            "motivational_factors": self.values_preferences.motivational_factors.value or []
        }

    def get_prompt_injection_string(self) -> str:
        """生成直接注入Prompt的控制字符串"""
        params = self.get_generation_control_params()
        
        # 构建控制指令
        control_instructions = []
        
        # 语言风格
        if params["formality_level"] == "warm":
            control_instructions.append("使用温暖亲切的语调")
        elif params["formality_level"] == "formal":
            control_instructions.append("使用正式礼貌的语言")
        
        # 详细程度
        if params["verbosity_level"] == "brief":
            control_instructions.append("回答简洁明了")
        elif params["verbosity_level"] == "detailed":
            control_instructions.append("提供详细解释")
        
        # 认知适配
        if params["attention_span"] == "short":
            control_instructions.append("分段呈现信息，避免长段落")
        
        # 情感支持
        if params["emotional_support_need"] == "high":
            control_instructions.append("优先提供情感关怀和支持")
        
        # 安全控制
        if params["risk_cautiousness"] == "very_cautious":
            control_instructions.append("对健康和安全建议要格外谨慎")
        
        # 个性化内容
        if params["core_interests"]:
            control_instructions.append(f"结合用户兴趣（{', '.join(params['core_interests'][:3])}）举例")
        
        if params["taboo_topics"]:
            control_instructions.append(f"避免涉及敏感话题：{', '.join(params['taboo_topics'])}")
        
        return "生成控制参数：" + "；".join(control_instructions) + "。"


def init_optimized_profile() -> Dict[str, Any]:
    """初始化优化的用户画像"""
    profile = OptimizedUserProfile()
    return profile.to_dict()


# ==================== 从旧版本迁移 ====================

def migrate_from_v1_to_optimized(v1_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    从V1画像迁移到优化版本
    
    自动检测并迁移所有可映射的字段，保留置信度信息
    """
    optimized = init_optimized_profile()
    
    # 映射V1字段到优化版本
    if "demographics" in v1_profile:
        v1_demo = v1_profile["demographics"]
        opt_identity = optimized["identity_language"]
        
        if "age" in v1_demo and v1_demo["age"].get("value") is not None:
            opt_identity["age"] = v1_demo["age"]
        if "gender" in v1_demo and v1_demo["gender"].get("value") is not None:
            opt_identity["gender"] = v1_demo["gender"]
        if "city_level" in v1_demo and v1_demo["city_level"].get("value") is not None:
            opt_identity["region"] = v1_demo["city_level"]
        if "education" in v1_demo and v1_demo["education"].get("value") is not None:
            opt_identity["education_level"] = v1_demo["education"]
    
    if "health" in v1_profile:
        v1_health = v1_profile["health"]
        opt_health = optimized["health_safety"]
        
        if "chronic_conditions" in v1_health and v1_health["chronic_conditions"].get("value") is not None:
            opt_health["chronic_conditions"] = v1_health["chronic_conditions"]
        if "mobility" in v1_health and v1_health["mobility"].get("value") is not None:
            opt_health["mobility_level"] = v1_health["mobility"]
        # 尝试从其他字段推导
        if "sleep_quality" in v1_health and v1_health["sleep_quality"].get("value") is not None:
            sleep_quality = v1_health["sleep_quality"]["value"]
            if sleep_quality in ["差", "不好", "失眠"]:
                opt_health["daily_energy_level"] = {"value": "低", "confidence": v1_health["sleep_quality"].get("confidence", 0.6)}
    
    if "cognitive" in v1_profile:
        v1_cog = v1_profile["cognitive"]
        opt_cog = optimized["cognitive_interaction"]
        
        if "digital_literacy" in v1_cog and v1_cog["digital_literacy"].get("value") is not None:
            opt_cog["digital_literacy"] = v1_cog["digital_literacy"]
        if "memory_status" in v1_cog and v1_cog["memory_status"].get("value") is not None:
            # 从记忆状况推导注意力
            memory = v1_cog["memory_status"]["value"]
            if memory in ["健忘", "记性不好", "记忆差"]:
                opt_cog["attention_span"] = {"value": "short", "confidence": v1_cog["memory_status"].get("confidence", 0.6)}
        if "expression_fluency" in v1_cog and v1_cog["expression_fluency"].get("value") is not None:
            fluency = v1_cog["expression_fluency"]["value"]
            if fluency in ["不流畅", "困难"]:
                opt_cog["processing_speed"] = {"value": "slow", "confidence": v1_cog["expression_fluency"].get("confidence", 0.6)}
    
    if "emotional" in v1_profile:
        v1_emo = v1_profile["emotional"]
        opt_emo = optimized["emotional_support"]
        
        if "baseline_mood" in v1_emo and v1_emo["baseline_mood"].get("value") is not None:
            opt_emo["baseline_mood"] = v1_emo["baseline_mood"]
        if "loneliness_level" in v1_emo and v1_emo["loneliness_level"].get("value") is not None:
            opt_emo["loneliness_level"] = v1_emo["loneliness_level"]
            # 从孤独感推导情感支持需求
            loneliness = v1_emo["loneliness_level"]["value"]
            if loneliness in ["高", "很高", "严重"]:
                opt_emo["emotional_support_need"] = {"value": "高", "confidence": v1_emo["loneliness_level"].get("confidence", 0.7)}
        if "anxiety_level" in v1_emo and v1_emo["anxiety_level"].get("value") is not None:
            anxiety = v1_emo["anxiety_level"]["value"]
            if anxiety in ["高", "很高", "严重"]:
                opt_health = optimized["health_safety"]
                opt_health["risk_sensitivity_level"] = {"value": "高", "confidence": v1_emo["anxiety_level"].get("confidence", 0.6)}
    
    if "lifestyle" in v1_profile:
        v1_life = v1_profile["lifestyle"]
        opt_life = optimized["lifestyle_social"]
        
        if "living_arrangement" in v1_life and v1_life["living_arrangement"].get("value") is not None:
            opt_life["living_situation"] = v1_life["living_arrangement"]
            # 从居住安排推导社交支持
            living = v1_life["living_arrangement"]["value"]
            if "独居" in living or "一个人" in living:
                opt_life["social_support_level"] = {"value": "低", "confidence": v1_life["living_arrangement"].get("confidence", 0.7)}
        if "hobbies" in v1_life and v1_life["hobbies"].get("value") is not None:
            opt_life["core_interests"] = v1_life["hobbies"]
    
    if "preferences" in v1_profile:
        v1_pref = v1_profile["preferences"]
        opt_style = optimized["response_style"]
        
        if "communication_style" in v1_pref and v1_pref["communication_style"].get("value") is not None:
            # 映射到新的控制参数
            comm_style = v1_pref["communication_style"]["value"]
            conf = v1_pref["communication_style"].get("confidence", 0.7)
            if "温和" in comm_style or "亲切" in comm_style:
                opt_style["formality_level"] = {"value": "warm", "confidence": conf}
                opt_style["emotional_tone"] = {"value": "caring", "confidence": conf}
            elif "正式" in comm_style:
                opt_style["formality_level"] = {"value": "formal", "confidence": conf}
            elif "简洁" in comm_style or "直接" in comm_style:
                opt_style["verbosity_level"] = {"value": "brief", "confidence": conf}
    
    # 自动推导 response_style 的其他字段
    opt_style = optimized["response_style"]
    opt_identity = optimized["identity_language"]
    opt_cog = optimized["cognitive_interaction"]
    opt_emo = optimized["emotional_support"]
    opt_health = optimized["health_safety"]
    
    # 从年龄推导正式程度
    if opt_identity["age"].get("value") is not None:
        age = opt_identity["age"]["value"]
        if isinstance(age, int) and age >= 70:
            if opt_style["formality_level"].get("value") is None:
                opt_style["formality_level"] = {"value": "warm", "confidence": 0.7}
    
    # 从注意力推导详细程度
    if opt_cog["attention_span"].get("value") == "short":
        if opt_style["verbosity_level"].get("value") is None:
            opt_style["verbosity_level"] = {"value": "brief", "confidence": 0.7}
    
    # 从孤独感推导情感语调
    if opt_emo["loneliness_level"].get("value") in ["高", "很高"]:
        if opt_style["emotional_tone"].get("value") is None:
            opt_style["emotional_tone"] = {"value": "caring", "confidence": 0.7}
    
    # 从慢性病推导风险谨慎度
    if opt_health["chronic_conditions"].get("value") and len(opt_health["chronic_conditions"]["value"]) > 0:
        if opt_style["risk_cautiousness"].get("value") is None:
            opt_style["risk_cautiousness"] = {"value": "cautious", "confidence": 0.7}
    
    return optimized


# ==================== 生成控制辅助类 ====================

class GenerationController:
    """生成控制器 - 将画像转换为LLM控制参数"""
    
    @staticmethod
    def build_system_prompt(profile: OptimizedUserProfile) -> str:
        """根据画像构建系统提示词"""
        control_params = profile.get_generation_control_params()
        
        base_prompt = "你是一个专为老年用户设计的AI助手。"
        
        # 添加控制指令
        control_prompt = profile.get_prompt_injection_string()
        
        return f"{base_prompt}\n\n{control_prompt}"
    
    @staticmethod
    def adapt_response_style(response: str, profile: OptimizedUserProfile) -> str:
        """根据画像调整回答风格"""
        params = profile.get_generation_control_params()
        
        # 这里可以实现后处理逻辑
        # 例如：根据attention_span调整段落长度
        if params["attention_span"] == "short":
            response = GenerationController._break_into_short_paragraphs(response)
        
        # 根据verbosity_level调整详细程度
        if params["verbosity_level"] == "brief":
            response = GenerationController._make_concise(response)
        
        return response
    
    @staticmethod
    def _break_into_short_paragraphs(text: str) -> str:
        """将长段落拆分为短段落"""
        # 简单实现：在句号后添加换行
        import re
        return re.sub(r'。(?!\n)', '。\n\n', text)
    
    @staticmethod
    def _make_concise(text: str) -> str:
        """使文本更简洁"""
        # 简单实现：移除一些修饰词
        concise_text = text.replace("非常", "").replace("特别", "").replace("尤其", "")
        return concise_text


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""
    # 1. 创建画像
    profile = OptimizedUserProfile()
    
    # 2. 设置一些控制参数
    profile.response_style.formality_level.value = "warm"
    profile.response_style.verbosity_level.value = "moderate"
    profile.cognitive_interaction.attention_span.value = "short"
    profile.emotional_support.emotional_support_need.value = "high"
    
    # 3. 获取生成控制参数
    control_params = profile.get_generation_control_params()
    print("生成控制参数:", control_params)
    
    # 4. 构建系统提示词
    system_prompt = GenerationController.build_system_prompt(profile)
    print("系统提示词:", system_prompt)
    
    # 5. 获取直接注入的控制字符串
    control_string = profile.get_prompt_injection_string()
    print("控制字符串:", control_string)


if __name__ == "__main__":
    example_usage()