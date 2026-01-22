"""
用户画像结构定义模块

定义用户画像的6个维度结构：
- demographics: 人口统计信息
- health: 健康状况
- cognitive: 认知能力
- emotional: 情感状态
- lifestyle: 生活方式
- preferences: 偏好设置

使用 Pydantic 2.x 进行数据验证和结构定义。
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field


class FieldValue(BaseModel):
    """画像字段值结构"""
    value: Optional[Union[str, int, float, List[str]]] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Demographics(BaseModel):
    """人口统计信息"""
    age: FieldValue = Field(default_factory=lambda: FieldValue())
    gender: FieldValue = Field(default_factory=lambda: FieldValue())
    city_level: FieldValue = Field(default_factory=lambda: FieldValue())
    education: FieldValue = Field(default_factory=lambda: FieldValue())
    marital_status: FieldValue = Field(default_factory=lambda: FieldValue())


class Health(BaseModel):
    """健康状况"""
    chronic_conditions: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))
    mobility: FieldValue = Field(default_factory=lambda: FieldValue())
    sleep_quality: FieldValue = Field(default_factory=lambda: FieldValue())
    medication_adherence: FieldValue = Field(default_factory=lambda: FieldValue())


class Cognitive(BaseModel):
    """认知能力"""
    memory_status: FieldValue = Field(default_factory=lambda: FieldValue())
    digital_literacy: FieldValue = Field(default_factory=lambda: FieldValue())
    expression_fluency: FieldValue = Field(default_factory=lambda: FieldValue())


class Emotional(BaseModel):
    """情感状态"""
    baseline_mood: FieldValue = Field(default_factory=lambda: FieldValue())
    loneliness_level: FieldValue = Field(default_factory=lambda: FieldValue())
    anxiety_level: FieldValue = Field(default_factory=lambda: FieldValue())


class Lifestyle(BaseModel):
    """生活方式"""
    living_arrangement: FieldValue = Field(default_factory=lambda: FieldValue())
    daily_routine: FieldValue = Field(default_factory=lambda: FieldValue())
    hobbies: FieldValue = Field(default_factory=lambda: FieldValue(value=[]))


class Preferences(BaseModel):
    """偏好设置"""
    communication_style: FieldValue = Field(default_factory=lambda: FieldValue())
    service_channel_preference: FieldValue = Field(default_factory=lambda: FieldValue())
    privacy_sensitivity: FieldValue = Field(default_factory=lambda: FieldValue())


class UserProfile(BaseModel):
    """完整的用户画像"""
    demographics: Demographics = Field(default_factory=Demographics)
    health: Health = Field(default_factory=Health)
    cognitive: Cognitive = Field(default_factory=Cognitive)
    emotional: Emotional = Field(default_factory=Emotional)
    lifestyle: Lifestyle = Field(default_factory=Lifestyle)
    preferences: Preferences = Field(default_factory=Preferences)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容旧代码）"""
        return self.model_dump(mode='json')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """从字典创建（兼容旧代码）"""
        return cls.model_validate(data)


def init_profile() -> Dict[str, Any]:
    """
    初始化空用户画像结构（返回字典格式，兼容旧代码）
    
    Returns:
        Dict: 包含6个维度的用户画像字典，所有字段初始值为None，confidence为0.0
        
    结构说明：
        {
            "demographics": {
                "age": {"value": None, "confidence": 0.0},
                "gender": {"value": None, "confidence": 0.0},
                ...
            },
            "health": {...},
            "cognitive": {...},
            "emotional": {...},
            "lifestyle": {...},
            "preferences": {...}
        }
    """
    profile = UserProfile()
    return profile.to_dict()

