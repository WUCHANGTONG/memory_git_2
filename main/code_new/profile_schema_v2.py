"""
用户画像结构定义模块 V2.0 - 面向个性化回答生成优化版

优化设计：7+1维度架构
- 保留并优化原有维度
- 新增Communication和Social Context维度
- 增加Interaction History动态维度
- 所有维度都直接服务于个性化回答生成

使用 Pydantic 2.x 进行数据验证和结构定义。
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from datetime import datetime


class FieldValue(BaseModel):
    """画像字段值结构"""
    value: Optional[Union[str, int, float, List[str]]] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    last_updated: Optional[str] = None  # 最后更新时间
    source: Optional[str] = None  # 信息来源


class Demographics(BaseModel):
    """人口统计信息 - 影响称呼方式、话题选择、文化背景"""
    age: FieldValue = Field(default_factory=FieldValue)
    gender: FieldValue = Field(default_factory=FieldValue)
    location: FieldValue = Field(default_factory=FieldValue)  # 地理位置
    education: FieldValue = Field(default_factory=FieldValue)
    occupation: FieldValue = Field(default_factory=FieldValue)  # 职业背景
    family_structure: FieldValue = Field(default_factory=FieldValue)  # 家庭结构


class Health(BaseModel):
    """健康状况 - 影响关怀重点、建议类型、敏感话题处理"""
    chronic_conditions: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))
    mobility_level: FieldValue = Field(default_factory=FieldValue)  # 行动能力
    sensory_abilities: FieldValue = Field(default_factory=FieldValue)  # 视听能力
    medication_routine: FieldValue = Field(default_factory=FieldValue)  # 用药习惯
    health_concerns: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 健康担忧
    energy_patterns: FieldValue = Field(default_factory=FieldValue)  # 精力模式
    pain_levels: FieldValue = Field(default_factory=FieldValue)  # 疼痛状况


class Cognitive(BaseModel):
    """认知能力 - 影响信息呈现方式、解释复杂度、重复频率"""
    memory_capacity: FieldValue = Field(default_factory=FieldValue)  # 记忆能力
    attention_span: FieldValue = Field(default_factory=FieldValue)  # 注意力持续时间
    digital_literacy: FieldValue = Field(default_factory=FieldValue)  # 数字技能
    learning_preference: FieldValue = Field(default_factory=FieldValue)  # 学习偏好
    confusion_triggers: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 混淆触发因素
    comprehension_level: FieldValue = Field(default_factory=FieldValue)  # 理解能力


class Emotional(BaseModel):
    """情感状态 - 影响语气选择、情感支持、话题敏感度"""
    baseline_mood: FieldValue = Field(default_factory=FieldValue)  # 基础情绪
    emotional_triggers: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 情感触发因素
    stress_indicators: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 压力表现
    comfort_sources: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 安慰来源
    emotional_needs: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 情感需求
    mood_patterns: FieldValue = Field(default_factory=FieldValue)  # 情绪模式
    coping_mechanisms: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 应对机制
    social_emotional_state: FieldValue = Field(default_factory=FieldValue)  # 社交情感状态


class Communication(BaseModel):
    """沟通特征 - 直接影响回答的语言风格、节奏、表达方式"""
    language_style: FieldValue = Field(default_factory=FieldValue)  # 语言风格偏好
    conversation_pace: FieldValue = Field(default_factory=FieldValue)  # 对话节奏
    information_density: FieldValue = Field(default_factory=FieldValue)  # 信息密度偏好
    repetition_tolerance: FieldValue = Field(default_factory=FieldValue)  # 重复容忍度
    question_asking_pattern: FieldValue = Field(default_factory=FieldValue)  # 提问习惯
    topic_transition_style: FieldValue = Field(default_factory=FieldValue)  # 话题转换方式
    feedback_preference: FieldValue = Field(default_factory=FieldValue)  # 反馈偏好
    cultural_communication_traits: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 文化沟通特征


class InterestsValues(BaseModel):
    """兴趣价值观 - 影响话题选择、例子引用、价值观对齐"""
    core_interests: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 核心兴趣
    topic_preferences: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 话题偏好
    value_system: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 价值观体系
    life_priorities: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 生活重点
    cultural_values: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 文化价值观
    taboo_topics: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 敏感话题
    nostalgic_elements: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 怀旧元素


class SocialContext(BaseModel):
    """社交环境 - 影响关系定位、社交话题、情感支持方式"""
    living_situation: FieldValue = Field(default_factory=FieldValue)  # 居住状况
    primary_relationships: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 主要关系
    social_support_network: FieldValue = Field(default_factory=FieldValue)  # 社交支持网络
    loneliness_patterns: FieldValue = Field(default_factory=FieldValue)  # 孤独感模式
    social_interaction_frequency: FieldValue = Field(default_factory=FieldValue)  # 社交频率
    relationship_concerns: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 关系担忧
    social_role_identity: FieldValue = Field(default_factory=FieldValue)  # 社会角色认同


class InteractionHistory(BaseModel):
    """交互历史 - 记录对话模式、偏好变化、个性化效果"""
    conversation_patterns: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 对话模式
    successful_interactions: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 成功交互
    failed_interactions: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 失败交互
    preference_evolution: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 偏好变化
    response_satisfaction: FieldValue = Field(default_factory=FieldValue)  # 回答满意度
    engagement_triggers: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))  # 参与触发因素
    personalization_effectiveness: FieldValue = Field(default_factory=FieldValue)  # 个性化效果


class UserProfileV2(BaseModel):
    """完整的用户画像 V2.0 - 面向个性化回答生成"""
    demographics: Demographics = Field(default_factory=Demographics)
    health: Health = Field(default_factory=Health)
    cognitive: Cognitive = Field(default_factory=Cognitive)
    emotional: Emotional = Field(default_factory=Emotional)
    communication: Communication = Field(default_factory=Communication)  # 新增
    interests_values: InterestsValues = Field(default_factory=InterestsValues)  # 重命名
    social_context: SocialContext = Field(default_factory=SocialContext)  # 新增
    interaction_history: InteractionHistory = Field(default_factory=InteractionHistory)  # 新增

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return self.model_dump(mode='json')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfileV2':
        """从字典创建"""
        return cls.model_validate(data)

    def get_personalization_context(self) -> Dict[str, Any]:
        """获取个性化回答生成的关键上下文"""
        return {
            "language_style": self.communication.language_style.value,
            "conversation_pace": self.communication.conversation_pace.value,
            "emotional_needs": self.emotional.emotional_needs.value,
            "comfort_sources": self.emotional.comfort_sources.value,
            "core_interests": self.interests_values.core_interests.value,
            "taboo_topics": self.interests_values.taboo_topics.value,
            "cognitive_level": {
                "attention_span": self.cognitive.attention_span.value,
                "comprehension_level": self.cognitive.comprehension_level.value
            },
            "social_needs": {
                "loneliness_patterns": self.social_context.loneliness_patterns.value,
                "social_role_identity": self.social_context.social_role_identity.value
            }
        }


def init_profile_v2() -> Dict[str, Any]:
    """
    初始化空用户画像结构 V2.0
    
    Returns:
        Dict: 包含7+1个维度的用户画像字典
    """
    profile = UserProfileV2()
    return profile.to_dict()


# 向后兼容性支持
def migrate_from_v1(v1_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    从V1画像结构迁移到V2
    
    Args:
        v1_profile: V1版本的画像字典
        
    Returns:
        Dict: V2版本的画像字典
    """
    v2_profile = init_profile_v2()
    
    # 映射V1字段到V2
    if "demographics" in v1_profile:
        v1_demo = v1_profile["demographics"]
        v2_demo = v2_profile["demographics"]
        
        # 直接映射的字段
        for field in ["age", "gender", "education"]:
            if field in v1_demo:
                v2_demo[field] = v1_demo[field]
        
        # 字段重命名映射
        if "city_level" in v1_demo:
            v2_demo["location"] = v1_demo["city_level"]
        if "marital_status" in v1_demo:
            v2_demo["family_structure"] = v1_demo["marital_status"]
    
    if "health" in v1_profile:
        v1_health = v1_profile["health"]
        v2_health = v2_profile["health"]
        
        # 直接映射
        if "chronic_conditions" in v1_health:
            v2_health["chronic_conditions"] = v1_health["chronic_conditions"]
        if "mobility" in v1_health:
            v2_health["mobility_level"] = v1_health["mobility"]
        if "medication_adherence" in v1_health:
            v2_health["medication_routine"] = v1_health["medication_adherence"]
    
    if "cognitive" in v1_profile:
        v1_cog = v1_profile["cognitive"]
        v2_cog = v2_profile["cognitive"]
        
        if "memory_status" in v1_cog:
            v2_cog["memory_capacity"] = v1_cog["memory_status"]
        if "digital_literacy" in v1_cog:
            v2_cog["digital_literacy"] = v1_cog["digital_literacy"]
        if "expression_fluency" in v1_cog:
            v2_cog["comprehension_level"] = v1_cog["expression_fluency"]
    
    if "emotional" in v1_profile:
        v1_emo = v1_profile["emotional"]
        v2_emo = v2_profile["emotional"]
        
        if "baseline_mood" in v1_emo:
            v2_emo["baseline_mood"] = v1_emo["baseline_mood"]
        if "loneliness_level" in v1_emo:
            v2_profile["social_context"]["loneliness_patterns"] = v1_emo["loneliness_level"]
        if "anxiety_level" in v1_emo:
            v2_emo["stress_indicators"] = {"value": [v1_emo["anxiety_level"]["value"]], 
                                         "confidence": v1_emo["anxiety_level"]["confidence"]}
    
    if "lifestyle" in v1_profile:
        v1_life = v1_profile["lifestyle"]
        
        if "living_arrangement" in v1_life:
            v2_profile["social_context"]["living_situation"] = v1_life["living_arrangement"]
        if "hobbies" in v1_life:
            v2_profile["interests_values"]["core_interests"] = v1_life["hobbies"]
    
    if "preferences" in v1_profile:
        v1_pref = v1_profile["preferences"]
        v2_comm = v2_profile["communication"]
        
        if "communication_style" in v1_pref:
            v2_comm["language_style"] = v1_pref["communication_style"]
        if "service_channel_preference" in v1_pref:
            v2_comm["feedback_preference"] = v1_pref["service_channel_preference"]
    
    return v2_profile


# 个性化回答生成辅助函数
class PersonalizationHelper:
    """个性化回答生成辅助类"""
    
    @staticmethod
    def get_language_style_prompt(profile: Dict[str, Any]) -> str:
        """根据用户画像生成语言风格提示"""
        comm = profile.get("communication", {})
        style = comm.get("language_style", {}).get("value", "温和")
        pace = comm.get("conversation_pace", {}).get("value", "正常")
        
        style_prompts = {
            "温和亲切": "使用温暖、关怀的语调，多用情感词汇",
            "正式礼貌": "使用正式、尊敬的语言，避免过于随意的表达",
            "简洁直接": "语言简洁明了，直接回答问题，避免冗长",
            "详细耐心": "提供详细解释，耐心引导，不怕重复"
        }
        
        pace_prompts = {
            "缓慢": "分段呈现信息，给用户充分的理解时间",
            "正常": "保持正常的信息呈现节奏",
            "快速": "可以提供更多信息，用户理解能力较强"
        }
        
        return f"{style_prompts.get(style, '')}。{pace_prompts.get(pace, '')}"
    
    @staticmethod
    def get_content_personalization_prompt(profile: Dict[str, Any]) -> str:
        """根据用户画像生成内容个性化提示"""
        interests = profile.get("interests_values", {}).get("core_interests", {}).get("value", [])
        taboo = profile.get("interests_values", {}).get("taboo_topics", {}).get("value", [])
        
        prompt = ""
        if interests:
            prompt += f"结合用户的兴趣爱好（{', '.join(interests)}）来举例说明。"
        if taboo:
            prompt += f"避免涉及敏感话题：{', '.join(taboo)}。"
        
        return prompt
    
    @staticmethod
    def get_emotional_support_prompt(profile: Dict[str, Any]) -> str:
        """根据用户画像生成情感支持提示"""
        comfort = profile.get("emotional", {}).get("comfort_sources", {}).get("value", [])
        needs = profile.get("emotional", {}).get("emotional_needs", {}).get("value", [])
        
        prompt = ""
        if comfort:
            prompt += f"在需要安慰时，可以引用：{', '.join(comfort)}。"
        if needs:
            prompt += f"关注用户的情感需求：{', '.join(needs)}。"
        
        return prompt