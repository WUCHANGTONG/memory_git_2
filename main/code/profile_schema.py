"""
用户画像结构定义模块

定义用户画像的6个维度结构：
- demographics: 人口统计信息
- health: 健康状况
- cognitive: 认知能力
- emotional: 情感状态
- lifestyle: 生活方式
- preferences: 偏好设置
"""

from typing import Dict, Any, Optional, List, Union


def init_profile() -> Dict[str, Dict[str, Dict[str, Union[None, float, List]]]]:
    """
    初始化空用户画像结构
    
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
    return {
        "demographics": {
            "age": {"value": None, "confidence": 0.0},
            "gender": {"value": None, "confidence": 0.0},
            "city_level": {"value": None, "confidence": 0.0},
            "education": {"value": None, "confidence": 0.0},
            "marital_status": {"value": None, "confidence": 0.0}
        },
        "health": {
            "chronic_conditions": {"value": [], "confidence": 0.0},
            "mobility": {"value": None, "confidence": 0.0},
            "sleep_quality": {"value": None, "confidence": 0.0},
            "medication_adherence": {"value": None, "confidence": 0.0}
        },
        "cognitive": {
            "memory_status": {"value": None, "confidence": 0.0},
            "digital_literacy": {"value": None, "confidence": 0.0},
            "expression_fluency": {"value": None, "confidence": 0.0}
        },
        "emotional": {
            "baseline_mood": {"value": None, "confidence": 0.0},
            "loneliness_level": {"value": None, "confidence": 0.0},
            "anxiety_level": {"value": None, "confidence": 0.0}
        },
        "lifestyle": {
            "living_arrangement": {"value": None, "confidence": 0.0},
            "daily_routine": {"value": None, "confidence": 0.0},
            "hobbies": {"value": [], "confidence": 0.0}
        },
        "preferences": {
            "communication_style": {"value": None, "confidence": 0.0},
            "service_channel_preference": {"value": None, "confidence": 0.0},
            "privacy_sensitivity": {"value": None, "confidence": 0.0}
        }
    }
