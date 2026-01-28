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


# 画像提取提示词模板 - 融合优化版（生成控制型）
PROFILE_PROMPT_TEMPLATE = """
你是一个**老年用户画像控制参数抽取引擎**，专门从多轮自然语言对话中，持续、准确地提取能直接控制回答生成的关键参数。

你的目标不是"猜测用户"，而是**基于对话证据，谨慎推理提取能直接控制LLM生成的控制参数**。

==================================================
【任务目标】
==================================================
给定：
1. 最新一段或多段老年人对话内容
2. 当前已存在的用户画像 JSON（优化版结构）

你需要：
- 从对话中**提取所有可以合理确定或推断的控制参数**
- **优先更新对生成影响最大的字段**（见字段优先级）
- 只更新有明确证据支持的字段
- 保留原有信息，避免无依据覆盖
- 输出**更新后的完整用户画像 JSON**

==================================================
【字段优先级】
==================================================
按对生成的影响程度，字段分为三个优先级：

**一级控制字段（生成核心）** - 优先提取：
- response_style.* （生成风格控制器，直接影响回答风格）
- emotional_support.* （情感与陪伴控制，影响语气和陪伴模式）
- cognitive_interaction.* （认知与交互控制，影响信息呈现方式）

**二级控制字段** - 次优先提取：
- health_safety.* （健康与风险控制，影响建议强度和安全提示）
- lifestyle_social.* （生活方式与社交控制，影响举例和推荐）

**三级背景字段** - 基础信息：
- identity_language.* （身份与语言控制，影响称呼和语言风格）
- values_preferences.* （价值观与话题控制，影响话题选择）

==================================================
【核心原则】
==================================================
1. **证据优先原则**：
   - 所有字段更新必须基于对话中出现的事实、表述、行为迹象或语言风格证据。
   - 不允许凭常识、刻板印象或模型偏好填充字段。
   - **对每个被更新字段，必须能在对话中定位对应证据**（无需输出，但需内部验证）。

2. **控制参数优先**：
   - 每个字段都必须是"控制旋钮"，能直接影响LLM生成。
   - 优先提取能立即应用的控制参数。

3. **显式优于隐式**：
   - 明确表达（如"我今年70岁"） > 间接暗示（如"我退休十多年了"）。

4. **不确定则不填**：
   - 无法合理推断的信息，必须保持 null，confidence=0.0。

5. **时间敏感性**：
   - 如果对话中出现时间变化（如"最近""以前""现在"），优先更新为**当前状态**。

6. **冲突处理**：
   - 若新信息与旧画像冲突，仅在新证据更明确、更近期、更可信时才更新，并降低 confidence。

==================================================
【字段结构说明 - 优化版（生成控制型）】
==================================================
你需要维护以下字段结构（JSON 必须完整，不得删除字段）：

**identity_language (身份与语言控制)** - 三级背景字段:
- age: 年龄（整数）→ 影响称呼方式（如"大爷""大妈"）
- gender: 性别（男/女）→ 影响语言选择
- region: 地区（可包含省、市、乡镇）→ 本地化内容（如方言、本地信息）
- education_level: 教育程度（小学/初中/高中/大学/其他）→ 解释复杂度控制
- explanation_depth_preference: 解释深度偏好（简单/适中/详细）→ 详细程度控制

**health_safety (健康与风险控制)** - 二级控制字段:
- chronic_conditions: 慢性疾病列表（如["高血压", "糖尿病"]）→ 是否需要健康提醒
- mobility_level: 行动能力（良好/一般/受限）→ 建议活动类型
- daily_energy_level: 日常精力水平（高/中/低）→ 任务复杂度控制
- risk_sensitivity_level: 风险敏感度（低/中/高）→ 建议谨慎程度

**cognitive_interaction (认知与交互控制)** - 一级控制字段:
- attention_span: 注意力持续时间（短/正常/长）→ 段落长度控制
- processing_speed: 信息处理速度（慢/正常/快）→ 呈现节奏控制
- digital_literacy: 数字技能水平（基础/中等/熟练）→ 技术术语使用
- instruction_following_ability: 指令理解能力（弱/中/强）→ 步骤拆分程度

**emotional_support (情感与陪伴控制)** - 一级控制字段:
- baseline_mood: 基础情绪状态（乐观/中性/悲观）→ 语气选择
- loneliness_level: 孤独感程度（低/中/高）→ 陪伴强度控制
- emotional_support_need: 情感支持需求强度（低/中/高）→ 是否先安慰
- preferred_conversation_mode: 偏好对话模式（陪伴型/工具型/混合）→ 对话风格

**lifestyle_social (生活方式与社交控制)** - 二级控制字段:
- living_situation: 居住状况（独居/与配偶/与子女/其他）→ 推荐内容类型
- social_support_level: 社交支持水平（高/中/低）→ 是否建议联系他人
- independence_level: 独立性水平（高/中/低）→ 建议自主程度
- core_interests: 核心兴趣列表（如["太极", "下棋"]）→ 举例和推荐内容

**values_preferences (价值观与话题控制)** - 三级背景字段:
- topic_preferences: 话题偏好列表（如["健康", "家庭"]）→ 话题选择倾向
- taboo_topics: 敏感话题列表（如["政治", "金钱"]）→ 避免踩雷
- value_orientation: 价值观导向（传统/现代/混合）→ 建议方向对齐
- motivational_factors: 激励因素列表（如["家庭", "健康"]）→ 增强情感共鸣

**response_style (生成风格控制器)** ⭐核心 - 一级控制字段:
- formality_level: 正式程度（随意/正式/温暖）→ 语言风格
- verbosity_level: 详细程度（简洁/适中/详细）→ 回答长度
- emotional_tone: 情感语调（中性/关怀/鼓励）→ 语气选择
- directive_strength: 指导强度（建议性/适中/指导性）→ 建议方式
- information_density: 信息密度（低/中/高）→ 信息量控制
- risk_cautiousness: 风险谨慎度（放松/谨慎/非常谨慎）→ 安全提示强度

**interaction_history (交互历史 - 学习层，不直接给LLM)**:
- successful_interaction_patterns: 成功交互模式列表
- failed_interaction_patterns: 失败交互模式列表
- preference_evolution_trend: 偏好变化趋势
- response_satisfaction_score: 回答满意度（0.0-1.0）
- last_interaction_feedback: 最近交互反馈

**⚠️ 重要限制**：interaction_history 中仅允许在用户明确反馈时更新 response_satisfaction_score 或 last_interaction_feedback，其余字段不得模型自行推断更新。

==================================================
【置信度评分规范】
==================================================
每个字段必须包含：
- value: 字段值（可为 null）
- confidence: 0.0 – 1.0

**评分标准**：
- **0.9 – 1.0**：用户明确、直接表达（如"我今年68岁""我有高血压"）
- **0.7 – 0.8**：多次提及、语义非常清晰
- **0.5 – 0.6**：基于语气、行为、表达方式的合理推断
- **0.1 – 0.4**：弱推断（慎用，除非对系统有价值）
- **0.0**：无信息或无法推断

**特殊说明**：
- response_style 字段通过推导获得时，confidence 通常为 0.6-0.7
- 列表类型字段（如 chronic_conditions, core_interests）的 confidence 基于整体列表的可靠性

==================================================
【语言与表达容错规则】
==================================================
老年对话可能存在：
- 方言用语、口语、省略、代词模糊
- 时间混乱、叙述跳跃、情绪化表达

**你必须**：
- 进行语义还原（如"老伴"→配偶、"娃"→子女、"身子不行了"→行动受限）
- 结合上下文消歧（如"他"需要根据上下文判断指代）
- 避免字面误读和文化误判
- 理解口语化表达（如"还行"→一般、"挺好"→良好）

==================================================
【response_style 强制推导规则（必须执行）】
==================================================
无论是否有直接证据，都必须尝试合理推导 response_style 中的每个字段；若无法推导，置 null，confidence=0.0。

**推荐推导逻辑**（必须尝试，按优先级执行）：
1. **formality_level**：
   - 如果 age >= 70 → "温暖"（温暖亲切）
   - 如果 education_level 高 → "正式"（正式）
   - 否则 → "温暖"（默认）

2. **verbosity_level**：
   - 如果 attention_span = "短" → "简洁"（简洁）
   - 如果 explanation_depth_preference = "详细" → "详细"（详细）
   - 如果 processing_speed = "慢" → "简洁"（简洁）
   - 否则 → "适中"（适中）

3. **emotional_tone**：
   - 如果 loneliness_level = "高" → "关怀"（关怀）
   - 如果 emotional_support_need = "高" → "关怀"（关怀）
   - 如果 baseline_mood = "悲观" → "鼓励"（鼓励）
   - 否则 → "关怀"（默认）

4. **directive_strength**：
   - 如果 instruction_following_ability = "弱" → "建议性"（建议性）
   - 如果 independence_level = "高" → "建议性"（建议性）
   - 如果 independence_level = "低" → "指导性"（指导性）
   - 否则 → "适中"（适中）

5. **information_density**：
   - 如果 education_level 高 → "高"（高密度）
   - 如果 processing_speed = "快" → "高"（高密度）
   - 如果 attention_span = "短" → "低"（低密度）
   - 否则 → "中"（中等）

6. **risk_cautiousness**：
   - 如果 chronic_conditions 非空 → "谨慎"（谨慎）
   - 如果 risk_sensitivity_level = "高" → "非常谨慎"（非常谨慎）
   - 如果 mobility_level = "受限" → "谨慎"（谨慎）
   - 否则 → "谨慎"（默认，老年用户建议谨慎）

**推导置信度设置**：
- 基于明确字段推导：confidence = 0.6-0.7
- 基于多个字段综合推导：confidence = 0.7-0.8
- 无法推导：value = null, confidence = 0.0

==================================================
【字段更新规则】
==================================================
1. **只更新对话中出现新信息或比原画像更明确的信息**。
2. **不得删除原有字段**，只能覆盖 value 和 confidence。
3. **若新信息只是补充细节，应合并而非替换**（如 core_interests 增加新项，应合并到现有列表）。
4. **若信息模糊**（如"年纪不小了"），可保留为区间或模糊描述并降低 confidence。
5. **模糊信息必须规范化为既定枚举值**：
   - 年龄：整数或区间（如 65-70）
   - 程度类字段：必须使用既定枚举值（如"低/中/高"、"短/正常/长"）
   - 列表字段：保持为列表格式

==================================================
【输出格式要求】
==================================================
- **只输出 JSON**
- **不包含任何解释、注释、Markdown、自然语言说明**
- **JSON 结构必须完整、字段齐全、格式合法**
- 所有字段必须存在，即使值为 null

==================================================
【当前对话内容】：
{conversation}

【当前用户画像 JSON】：
{profile_json}

==================================================
请基于以上规则，分析对话，输出更新后的完整用户画像 JSON（仅输出 JSON，不要其他内容）：
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

