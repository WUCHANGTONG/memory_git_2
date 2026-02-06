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
    from langchain_core.prompts import ChatPromptTemplate
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
- identity_language.* （身份与语言控制，影响称呼和语言风格）
- response_style.* （生成风格控制器，直接影响回答风格）
- emotional_support.* （情感与陪伴控制，影响语气和陪伴模式）
- cognitive_interaction.* （认知与交互控制，影响信息呈现方式）

**二级控制字段** - 次优先提取：
- health_safety.* （健康与风险控制，影响建议强度和安全提示）
- lifestyle_social.* （生活方式与社交控制，影响举例和推荐）

**三级背景字段** - 基础信息：
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

▼▼▼ 以下为各字段详细定义（含判断依据与枚举边界） ▼▼▼

1. identity_language（身份与语言控制） — 一级背景字段
— age（年龄）
定义：用户的实际年龄，用于称呼方式和内容适配。
判断依据：
明确表达：“我今年78了”“快80的人了”
间接线索：“退休30年了”（需结合常识推算，置信度≤0.6）
枚举值说明：
整数（如 78）：仅当用户直接说出具体数字时使用（confidence ≥0.9）
若为模糊表述（如“年纪大了”），不填值，保持 null
用途：→ 决定称呼（“李大爷”“王奶奶”）、避免年轻化用语
— gender（性别）
定义：用户的生理性别，影响语言风格和举例。
判断依据：
自称：“我是男的”“老太婆一个”
称呼线索：子女称“爸/妈”，社区称“张爷爷/李奶奶”
声音/头像（若多模态可用，但纯文本中不可依赖）
枚举值说明：
"男" / "女"：需有明确自称或第三方可靠指代（confidence ≥0.9）
无明确信息 → 保持 null（confidence = 0.0）
用途：→ 选择性别适配的关怀用语（如“老爷子保重” vs “老太太多歇歇”）
— region（地区）
定义：用户常住地，用于本地化内容（天气、政策、方言）。
判断依据：
直接提及：“我在杭州”“住在北京朝阳”
本地事件：“我们小区昨天发了重阳节慰问品”
方言词汇：“侬好”“咋整”“得劲”
枚举值说明：
字符串格式，尽可能详细（如 "浙江省杭州市"优先于"南方"）
用途：→ 推送本地服务、使用地域相关比喻（如“像咱们胡同里那棵老槐树一样稳”）
— education_level（教育程度）
定义：用户最高学历，控制解释复杂度。
判断依据：
明确说明：“我是高中毕业”“上过师范”
职业线索：“以前是语文老师” → 通常 ≥ 高中
语言特征：能使用成语、引经据典 → 可能较高；频繁说“我不懂这些词” → 可能较低
枚举值说明：
"小学" / "初中" / "高中" / "大学" / "其他"
默认：若无信息，不填（避免刻板印象）
用途：→ 控制术语使用（如用“血糖高”而非“糖尿病”）
— explanation_depth_preference（解释深度偏好）
定义：用户希望获得的信息详略程度。
判断依据：
明确要求：“讲细点，我想弄明白” → 详细；“说重点就行” → 简单
行为反馈：“上次你说得太快，我没记住” → 倾向详细
枚举值说明：
"简单"：用户多次要求简化、跳过细节
"适中"：无明确偏好，默认值（confidence = 0.5）
"详细"：主动追问步骤、原理
用途：→ 控制回答长度与细节层级（一级影响 verbosity_level）

health_safety（健康与风险控制） — 二级控制字段
— chronic_conditions（慢性疾病）
定义：用户已确诊的长期健康问题。
判断依据：
直接陈述：“我有高血压”“糖尿病十几年了”
行为线索：“每天吃降压药”“血糖要测三次”
枚举值说明：
列表格式，标准化病名（如 ["高血压", "关节炎"]）
仅当用户明确提及疾病名称或典型治疗行为时记录（confidence ≥0.9）
模糊说法如“身子不好”不计入
用途：→ 触发健康提醒、避免剧烈活动建议
— mobility_level（行动能力）
定义：用户日常活动的身体限制程度。
判断依据：
明确描述：“腿脚还行”“走不了远路”“坐轮椅”
行为线索：“买菜得坐公交”“上下楼喘”
枚举值说明：
"良好"：能独立外出、爬楼梯
"一般"：短距离可走，长距离需辅助
"受限"：需拐杖/轮椅，或基本不出门
默认：若无信息，不填（confidence = 0.0）
用途：→ 推荐适合的活动（如“室内太极” vs “公园散步”）

cognitive_interaction（认知与交互控制） — 一级控制字段
— attention_span（注意力持续时间）
定义：用户能专注理解一段信息的时长。
判断依据：
"短"：说“别啰嗦”“记不住那么多”“一次说一件事”；频繁打断或转移话题
"正常"：能听完一段话并回应，偶尔要求重复
"长"：主动追问细节、复述确认、处理多步骤指令
枚举值说明：
默认假设为 "短"（老年群体常见，confidence = 0.6）
有明确证据才升级为 "正常" 或 "长"
用途：→ 控制段落长度、是否分步说明（直接影响 information_density）
— digital_literacy（数字技能水平）
定义：用户使用智能设备的能力。
判断依据：
"基础"：会接视频电话、用微信语音；常说“孩子帮我弄的”“我不敢点”
"中等"：会扫码、支付、看健康码；能独立操作常用APP
"熟练"：主动设置功能、提技术问题（如“怎么连蓝牙？”）
枚举值说明：
用户说“不太会弄新玩意儿” → "基础"（confidence = 0.8）
无信息 → 不填（避免高估）
用途：→ 决定是否使用技术术语、是否提供图文指引

emotional_support（情感与陪伴控制） — 一级控制字段
— baseline_mood（基础情绪状态）
定义：用户常态下的情绪倾向。
判断依据：
"乐观"：常用“还好”“挺好的”“没事”；主动分享趣事
"中性"：陈述事实，无明显情绪词（如“今天量了血压”）
"悲观"：频繁抱怨“没意思”“不中用了”“拖累孩子”
枚举值说明：
默认值："中性"（confidence = 0.5）
单次负面情绪不等于 "悲观"，需多次或强烈表达
用途：→ 选择语气（鼓励/关怀/中性）
— loneliness_level（孤独感程度）
定义：用户主观感受到的社交缺失程度。
判断依据：
"低"：提到“老伴有伴”“子女常来”“社区活动多”
"中"：偶尔说“一个人吃饭”“没人说话”
"高"：反复说“没人管我”“连个说话的人都没有”
枚举值说明：
独居 ≠ 孤独（可能社交活跃），需结合情感表达
默认：若无信息，不填
用途：→ 控制陪伴强度（是否主动开启闲聊）
— preferred_conversation_mode（偏好对话模式）
定义：用户希望机器人以何种角色互动。
判断依据：
"陪伴型"：主动闲聊、问“你怎么样？”、分享生活故事
"工具型"：只问功能（“怎么设闹钟？”“提醒吃药”），说完即结束
"混合"：既有任务请求，又有情感表达（如“今天头晕…你能陪我说会儿吗？”）
枚举值说明：
默认："混合"（confidence = 0.6）
明确拒绝闲聊（“别扯别的，就说正事”）→ "工具型"
用途：→ 决定是否插入关怀语、是否延伸话题

lifestyle_social（生活方式与社交控制） — 二级控制字段
— living_situation（居住状况）
定义：用户当前主要居住安排。
判断依据：
"独居"：说“就我一个人”“老伴走了”
"与配偶"：提到“我们俩”“老头子在看电视”
"与子女"：说“跟儿子住”“闺女让我搬来”
"其他"：养老院、亲戚家等
枚举值说明：
需明确提及，否则不填
用途：→ 推荐内容（如独居用户推安全设备）
— social_support_level（社交支持水平）
定义：用户可获得的现实社会帮助程度。
判断依据：
"高"：子女常联系、有邻居互助、参加社区活动
"中"：偶尔有人探望，但不频繁
"低"：说“孩子们忙”“不想麻烦别人”
枚举值说明：
与 living_situation 联动判断（如独居但子女每天打电话 → "中"）
用途：→ 是否建议“联系家人”或“参加社区活动”
— independence_level（独立性水平）
定义：用户自主完成日常事务的能力与意愿。
判断依据：
"高"：说“我自己能行”“不用他们管”
"中"：接受部分帮助，但保留决策（“药我自己买，你提醒就行”）
"低"：常说“得叫孩子来”“我不敢弄”
枚举值说明：
行为比语言更可靠（如主动操作设备 → 高独立性）
用途：→ 控制建议方式（指导性 vs 建议性）
— core_interests（核心兴趣）
定义：用户长期关注或喜爱的活动/话题。
判断依据：
主动提及：“我喜欢种菜”“每天打太极”
反复讨论同一主题
枚举值说明：
列表格式，标准化兴趣（如 ["种菜", "京剧", "养生"]）
临时兴趣（“今天看了个电影”）不计入
用途：→ 个性化举例、推荐相关内容

values_preferences（价值观与话题控制） — 三级背景字段
— topic_preferences（话题偏好）
定义：用户愿意深入讨论的主题。
判断依据：
主动开启话题：“最近血压怎么样？”“孙子考大学了”
对某类话题回应积极、追问细节
枚举值说明：
列表格式（如 ["健康", "家庭", "养生"]）
默认：若无信息，不填
用途：→ 优先选择这些话题开启对话
— taboo_topics（敏感话题）
定义：用户明确表示不愿讨论的内容。
判断依据：
直接拒绝：“别说这个”“提钱伤感情”
情绪回避：一提某事就沉默、转移话题
枚举值说明：
仅当用户明确表达时记录（如 ["金钱", "丧葬"]）
无信息 → 空列表（confidence = 0.0）
用途：→ 严格避免相关话题

**interaction_history (交互历史 - 学习层，不直接给LLM)**
> ⚠️ 仅允许在用户明确反馈时更新以下两项：
- last_interaction_feedback: 最近交互反馈（字符串，如“说话慢点儿”）
- response_satisfaction_score: 满意度（0.0–1.0，仅当用户给出评分如“打8分”时计算）
> 其余字段（如 successful_interaction_patterns）禁止模型自行推断！

==================================================
【置信度评分规范】
==================================================
- **0.9–1.0**：用户明确直接表达（如“我有高血压”）
- **0.7–0.8**：多次提及或语义非常清晰
- **0.5–0.6**：合理推断（如根据职业推教育）
- **0.0**：无信息或无法推断
- **response_style 推导字段**：confidence = 0.6–0.7（基于其他字段逻辑推导）

==================================================
【语言与表达容错规则】
==================================================
- “老伴” → 配偶；“娃” → 子女；“身子不行了” → mobility_level="受限"
- “还行” → 一般；“挺好” → 良好
- 结合上下文消歧代词（如“他”是否指子女）

==================================================
【few-shot 示例：对话 → 字段更新】
==================================================

▶ 示例1：
对话：「我今年78了，耳朵有点背，你说话慢点儿啊。我有高血压，每天吃药。」
→ 更新：
  identity_language.age = 78 (conf=1.0)
  health_safety.chronic_conditions = ["高血压"] (conf=1.0)
  cognitive_interaction.attention_span = "短" (conf=0.7, 因“耳朵背”常伴随注意力下降)
  interaction_history.last_interaction_feedback = "你说话慢点儿啊" (conf=1.0)

▶ 示例2：
对话：「我自己住，孩子们都在外地。不过社区挺热闹，我每天去活动室打太极。」
→ 更新：
  lifestyle_social.living_situation = "独居" (conf=1.0)
  lifestyle_social.social_support_level = "中" (conf=0.8, 社区支持)
  lifestyle_social.core_interests = ["太极"] (conf=1.0)

▶ 示例3：
对话：「别扯别的，就说怎么设闹钟！上次你说得太快，我都没记住。」
→ 更新：
  emotional_support.preferred_conversation_mode = "工具型" (conf=1.0)
  cognitive_interaction.attention_span = "短" (conf=1.0)
  response_style.verbosity_level = "简洁" (conf=0.7, 推导)

==================================================
【字段更新规则】
==================================================
1. 只更新对话中出现新信息或比原画像更明确的信息。
2. 不得删除原有字段，只能覆盖 value 和 confidence。
3. 列表字段（如 core_interests）应合并新增项，去重。
4. 模糊信息必须规范化为既定枚举值（如“走不动” → mobility_level="受限"）。

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

