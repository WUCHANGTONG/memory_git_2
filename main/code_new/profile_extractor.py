"""
用户画像提取模块

使用LLM从对话内容中提取和更新用户画像信息。
主要功能：
- 从对话中提取用户画像维度信息
- 合并新旧画像，保留高置信度信息
- 处理JSON解析错误

使用 DashScope API (通义千问) 进行画像提取。
"""

from typing import Dict, Any, Optional
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv

# 尝试导入 langchain，如果不存在则使用直接 HTTP 调用
try:
    from langchain_community.chat_models import ChatTongyi
    from langchain.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("警告: langchain 未安装，将使用 DashScope SDK 直接调用")

# 尝试导入 DashScope SDK
try:
    import dashscope
    from dashscope import Generation
    DASHSCOPE_SDK_AVAILABLE = True
except ImportError:
    DASHSCOPE_SDK_AVAILABLE = False
    if not LANGCHAIN_AVAILABLE:
        print("警告: dashscope SDK 未安装，请安装: pip install dashscope")

# 加载 .env 文件（从项目根目录查找）
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# 从环境变量读取API Key
api_key = os.getenv("DASHSCOPE_API_KEY", "")


def check_api_key() -> Dict[str, Any]:
    """
    检查API Key是否配置，返回诊断信息
    
    Returns:
        Dict: 包含以下字段的诊断信息
            - status: "missing" 或 "configured"
            - message: 状态消息
            - suggestions: 配置建议列表（仅当status为missing时）
            - key_preview: API Key前8位预览（仅当status为configured时）
    """
    if not api_key:
        return {
            "status": "missing",
            "message": "未设置 DASHSCOPE_API_KEY",
            "suggestions": [
                f"在项目根目录创建 .env 文件（路径: {env_path}）",
                "在 .env 文件中添加：DASHSCOPE_API_KEY=your-api-key",
                "或者设置环境变量：$env:DASHSCOPE_API_KEY='your-api-key' (Windows PowerShell)"
            ]
        }
    else:
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        return {
            "status": "configured",
            "message": f"已读取 API Key: {masked_key}",
            "key_preview": api_key[:8] + "..." if len(api_key) > 8 else "***"
        }


# 延迟初始化LLM
llm = None
dashscope_initialized = False


def init_llm():
    """
    初始化LLM（延迟初始化），支持两种方式：
    1. 使用 langchain (如果已安装)
    2. 使用 DashScope SDK 直接调用
    
    Returns:
        LLM实例或None
        
    Raises:
        ValueError: 当API Key未设置或LLM初始化失败时
    """
    global llm, dashscope_initialized
    
    if not api_key:
        raise ValueError("未设置 DASHSCOPE_API_KEY，请先配置API Key")
    
    # 优先使用 langchain
    if LANGCHAIN_AVAILABLE and llm is None:
        try:
            llm = ChatTongyi(
                dashscope_api_key=api_key,
                model_name="qwen-turbo",
                temperature=0
            )
            return llm
        except Exception as e:
            print(f"警告: langchain 初始化失败: {e}，尝试使用 DashScope SDK")
    
    # 使用 DashScope SDK
    if DASHSCOPE_SDK_AVAILABLE and not dashscope_initialized:
        dashscope.api_key = api_key
        dashscope_initialized = True
        return None
    
    if not DASHSCOPE_SDK_AVAILABLE:
        raise ValueError("请安装 dashscope: pip install dashscope")
    
    return None


# 画像提取提示词模板
PROFILE_PROMPT_TEMPLATE = """
你是一个专业的用户画像抽取器，专门用于分析老年人对话内容，从对话中提取用户信息。

## 任务说明
从给定的对话内容中提取用户信息，更新用户画像。**必须仔细分析对话，提取所有能推断出的信息**。

## 字段提取指南
请根据对话内容，识别并提取以下信息：

**人口统计信息 (demographics)**:
- age: 年龄（如"我68岁"、"今年70了"）
- gender: 性别（如"我是男的"、"老太太"）
- city_level: 城市/地区（如"我是石家庄人"、"住在北京"、"上海人"）
- education: 教育程度（如"小学毕业"、"上过大学"）
- marital_status: 婚姻状况（如"老伴"、"单身"、"离婚"）

**健康状况 (health)**:
- chronic_conditions: 慢性疾病列表（如"高血压"、"糖尿病"）
- mobility: 行动能力（如"走不动"、"腿脚不好"）
- sleep_quality: 睡眠质量（如"睡不好"、"失眠"）
- medication_adherence: 用药情况（如"每天吃药"、"忘记吃药"）

**认知能力 (cognitive)**:
- memory_status: 记忆状况（如"记性不好"、"健忘"）
- digital_literacy: 数字设备使用能力（如"不会用手机"、"会用微信"）
- expression_fluency: 表达流畅度（从对话中判断）

**情感状态 (emotional)**:
- baseline_mood: 基础情绪（如"心情好"、"不开心"）
- loneliness_level: 孤独感（如"一个人"、"没人陪"）
- anxiety_level: 焦虑程度（如"担心"、"焦虑"）

**生活方式 (lifestyle)**:
- living_arrangement: 居住安排（如"和儿子住"、"独居"）
- daily_routine: 日常作息（如"早起"、"晚上散步"）
- hobbies: 兴趣爱好列表（如"下棋"、"打麻将"、"跳广场舞"）

**偏好设置 (preferences)**:
- communication_style: 沟通风格（从对话中判断）
- service_channel_preference: 服务渠道偏好
- privacy_sensitivity: 隐私敏感度

## 重要规则
1. **必须从对话中提取信息**：仔细分析对话，提取所有能推断出的信息
2. **置信度设置**：
   - 明确提到的信息（如"我是石家庄人"）confidence设为0.8-1.0
   - 间接推断的信息（如从语气判断）confidence设为0.5-0.7
   - 无法推断的信息保持null，confidence为0.0
3. **只更新有信息的字段**：如果对话中没有相关信息，保持原有值不变
4. **不要删除字段**：保持JSON结构完整
5. **输出格式**：只输出JSON，不要有任何解释性文字、markdown标记

## 提取示例
示例1 - 对话："你好，我是石家庄人，今年68岁了"
应提取：
- demographics.city_level: value="石家庄", confidence=0.9
- demographics.age: value=68, confidence=0.9

示例2 - 对话："我有点高血压，每天都要吃药"
应提取：
- health.chronic_conditions: value=["高血压"], confidence=0.9
- health.medication_adherence: value="每天服药", confidence=0.9

## 当前对话内容：
{conversation}

当前用户画像：
{profile_json}

请仔细分析对话，提取所有能推断出的信息，输出更新后的完整用户画像JSON（只输出JSON，不要其他内容）：
"""


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    从文本中提取JSON，处理可能的markdown代码块或其他格式
    
    Args:
        text: 包含JSON的文本内容
        
    Returns:
        Dict: 解析后的JSON字典
        
    Raises:
        ValueError: 当无法从文本中提取有效JSON时
    """
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 尝试提取代码块中的JSON
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 尝试提取第一个完整的JSON对象
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"无法从响应中提取有效的JSON: {text[:200]}")


def merge_profile(old_profile: Dict[str, Any], new_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并新旧画像，保留旧画像的结构，只更新有值的字段
    
    合并策略：
    - 对于包含value和confidence的字段：只有当新值置信度更高或旧值为None时才更新
    - 对于列表类型：合并去重
    - 对于嵌套字典：递归合并
    
    Args:
        old_profile: 旧的用户画像字典
        new_profile: 新提取的用户画像字典
        
    Returns:
        Dict: 合并后的用户画像字典（深拷贝，不修改原字典）
    """
    merged = json.loads(json.dumps(old_profile))  # 深拷贝
    
    def merge_dict(old_dict: dict, new_dict: dict):
        for key, value in new_dict.items():
            if key in old_dict:
                if isinstance(value, dict) and isinstance(old_dict[key], dict):
                    # 如果都有value和confidence字段，进行合并
                    if "value" in value and "confidence" in value:
                        # 只有当新值的置信度更高或旧值为None时才更新
                        old_conf = old_dict[key].get("confidence", 0.0)
                        new_conf = value.get("confidence", 0.0)
                        if new_conf > old_conf or old_dict[key].get("value") is None:
                            old_dict[key] = value
                    else:
                        # 递归合并嵌套字典
                        merge_dict(old_dict[key], value)
                elif isinstance(value, list) and isinstance(old_dict[key], list):
                    # 对于列表类型，合并去重
                    old_dict[key] = list(set(old_dict[key] + value))
                else:
                    old_dict[key] = value
    
    merge_dict(merged, new_profile)
    return merged


def _call_llm_with_langchain(conversation: str, profile_json: str) -> str:
    """使用 langchain 调用 LLM"""
    global llm
    if llm is None:
        init_llm()
    
    if LANGCHAIN_AVAILABLE:
        prompt = ChatPromptTemplate.from_template(PROFILE_PROMPT_TEMPLATE)
        messages = prompt.format_messages(
            conversation=conversation,
            profile_json=profile_json
        )
        response = llm.invoke(messages)
        if hasattr(response, 'content'):
            return response.content
        return str(response)
    else:
        raise ValueError("langchain 未安装")


def _call_llm_with_dashscope(conversation: str, profile_json: str) -> str:
    """使用 DashScope SDK 直接调用 LLM"""
    if not DASHSCOPE_SDK_AVAILABLE:
        raise ValueError("dashscope SDK 未安装")
    
    init_llm()  # 确保已初始化
    
    prompt = PROFILE_PROMPT_TEMPLATE.format(
        conversation=conversation,
        profile_json=profile_json
    )
    
    response = Generation.call(
        model='qwen-turbo',
        prompt=prompt,
        temperature=0
    )
    
    if response.status_code == 200:
        return response.output.text
    else:
        raise ValueError(f"DashScope API 调用失败: {response.message}")


def update_profile(conversation: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    从对话内容中提取用户画像信息并更新现有画像
    
    流程：
    1. 使用LLM从对话中提取画像信息
    2. 解析LLM返回的JSON
    3. 合并新旧画像（保留高置信度信息）
    4. 返回更新后的画像
    
    Args:
        conversation: 对话内容字符串，格式如 "用户：xxx"
        profile: 当前用户画像字典，必须符合profile_schema定义的结构
    
    Returns:
        Dict: 更新后的用户画像字典
        
    注意：
        - 如果提取失败或发生错误，返回原画像（不中断流程）
        - 错误信息会打印到控制台
    """
    try:
        # 确保LLM已初始化
        init_llm()
        
        # 格式化profile为JSON字符串
        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
        
        # 调用LLM（优先使用 langchain，否则使用 DashScope SDK）
        try:
            if LANGCHAIN_AVAILABLE:
                response_text = _call_llm_with_langchain(conversation, profile_json)
            else:
                response_text = _call_llm_with_dashscope(conversation, profile_json)
        except Exception as e:
            # 如果一种方式失败，尝试另一种
            if LANGCHAIN_AVAILABLE and DASHSCOPE_SDK_AVAILABLE:
                try:
                    response_text = _call_llm_with_dashscope(conversation, profile_json)
                except Exception as e2:
                    raise ValueError(f"所有LLM调用方式都失败: {e}, {e2}")
            else:
                raise
        
        # 提取JSON
        new_profile = extract_json_from_text(response_text)
        
        # 合并新旧画像
        updated_profile = merge_profile(profile, new_profile)
        
        return updated_profile
        
    except ValueError as e:
        # API Key相关错误
        error_msg = str(e)
        key_info = check_api_key()
        print(f"\n[ERROR] API配置错误: {error_msg}")
        print(f"\n当前状态: {key_info['message']}")
        print("\n请检查以下几点：")
        print("1. 确认 .env 文件位于项目根目录（main目录）")
        print("2. 确认 .env 文件中包含：DASHSCOPE_API_KEY=your-actual-api-key")
        print("3. 确认API Key格式正确（阿里云DashScope的API Key通常以 sk- 开头）")
        print("4. 确认API Key有效且未过期")
        if key_info['status'] == 'configured':
            print(f"   当前API Key前8位: {key_info['key_preview']}")
        return profile
    except Exception as e:
        error_str = str(e)
        # 检查是否是API Key错误
        if "401" in error_str or "InvalidApiKey" in error_str or "Invalid API-key" in error_str:
            key_info = check_api_key()
            print(f"\n[ERROR] API Key无效错误 (401 Unauthorized)")
            print(f"错误详情: {error_str}")
            print(f"\n当前状态: {key_info['message']}")
            print("\n请按以下步骤排查：")
            print("1. 检查 .env 文件中的 API Key 是否正确复制（注意不要有多余空格）")
            print("2. 登录阿里云DashScope控制台确认API Key是否有效")
            print("   - 访问: https://dashscope.console.aliyun.com/")
            print("   - 检查API Key是否被禁用或删除")
            print("3. 确认API Key格式正确（通常以 sk- 开头）")
            print("4. 确认API Key有调用通义千问模型的权限")
            print("5. 检查账户余额是否充足")
            if key_info['status'] == 'configured':
                print(f"\n当前使用的API Key前8位: {key_info['key_preview']}")
        else:
            print(f"[ERROR] 画像更新失败: {error_str}")
            print(f"对话内容: {conversation[:100]}...")
        # 发生错误时返回原画像，不中断流程
        return profile

