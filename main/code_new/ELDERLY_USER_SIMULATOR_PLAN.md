# 老年人用户模拟器实现计划（修订版）

## 📋 项目背景

### 目标
实现一个模拟老年人用户的大模型，用于与已构建的助手系统（`agent.py`）进行自动对话，生成"用户轨迹（trajectory）"数据，用于测试画像提取功能。

### 核心需求
1. **双模型架构**：
   - **助手模型**：已存在（`agent.py`），提供个性化回答
   - **用户模拟模型**：需要构建，模拟老年人用户，生成用户对话

2. **两种交互模式**：
   - **模式1：真实用户模式**（已实现）
     - 真实用户从终端输入
     - 与助手模型交互
     - 提取画像并生成个性化回答
   
   - **模式2：模拟用户模式**（待实现）
     - 模拟老年人模型自动生成用户对话
     - 与助手模型进行多轮对话
     - 生成完整的用户轨迹数据

3. **数据单元**：
   - 生成的是"用户轨迹（trajectory）"，不是单个句子
   - 轨迹是一系列相关的对话轮次（3-10轮）
   - 每个轨迹应该体现一个完整的用户画像维度或场景

4. **配置切换**：
   - 通过配置可以切换两种模式
   - 模式1：真实用户输入（当前实现）
   - 模式2：模拟用户自动对话（待实现）

## 🎯 设计目标

### 功能目标
1. **模拟老年人用户对话**：
   - 根据画像配置生成符合老年人特点的对话
   - 模拟真实的老年人语言特点（口语化、方言、表达习惯等）
   - 体现老年人的认知特点（记忆模糊、话题跳跃、情绪化表达等）

2. **与助手系统集成**：
   - 能够调用助手系统的对话接口
   - 接收助手回复并生成下一轮用户对话
   - 记录完整的对话轨迹

3. **轨迹生成**：
   - 生成多轮对话轨迹（3-10轮）
   - 每个轨迹围绕一个主题或场景
   - 轨迹内容自然、连贯、真实

4. **画像维度覆盖**：
   - 能够根据配置生成体现不同画像维度的对话
   - 覆盖优化版画像schema的所有维度
   - 每个轨迹重点体现某些画像维度

### 技术目标
1. **可控性**：能够控制生成对话的画像维度
2. **真实性**：生成的对话符合老年人特点
3. **可配置**：通过配置切换真实用户/模拟用户模式
4. **可扩展性**：易于添加新的场景和画像配置

## 🏗️ 架构设计

### 整体架构

```
系统架构
├── agent.py (助手系统 - 已存在)
│   ├── chat_loop() - 对话循环
│   ├── 画像提取功能
│   └── 个性化回答功能
│
├── elderly_user_simulator/ (用户模拟器 - 待构建)
│   ├── elderly_user_simulator.py      # 用户模拟器实现
│   ├── elderly_user_simulator_config.json  # 用户模拟器配置
│   └── SIMULATOR_USAGE.md             # 用户模拟器使用说明
│   ├── ElderlyUserSimulator - 用户模拟器类
│   ├── ProfileConfigurator - 画像配置器
│   ├── LanguageStyleGenerator - 语言风格生成器
│   └── TrajectoryGenerator - 轨迹生成器
│
└── 配置系统
    ├── 模式切换（真实用户 / 模拟用户）
    └── 画像配置（指定要体现的画像维度）
```

### 核心组件

#### 1. SimulatedUser（用户模拟器 - 增强版）

**职责**：
- 根据画像配置生成用户对话
- 模拟老年人的语言和认知特点
- 与助手系统进行对话
- **管理隐藏真实画像（Ground Truth Profile）**
- **跟踪已表达画像（Expressed Profile）**
- **应用表达噪声模型（Noise Model）**

**核心数据结构**：
```python
class SimulatedUser:
    ground_truth_profile: Dict[str, Any]   # 真正的用户画像（不可见，用于评估）
    expressed_profile: Dict[str, Any]       # 已通过对话显露的部分（可见）
    noise_model: Dict[str, float]           # 表达噪声参数（遗忘、模糊、误导）
    disclosure_controller: DisclosureController  # 信息释放节奏控制器
    language_style_generator: LanguageStyleGenerator  # 语言风格生成器
```

**核心方法**：
- `generate_user_message(conversation_history, profile_config)` - 生成用户消息
- `simulate_conversation(profile_config, scenario, max_turns)` - 模拟完整对话
- `_build_user_prompt(...)` - 构建用户提示词
- `update_expressed_profile(conversation_history)` - 更新已表达画像
- `evaluate_extraction_accuracy(extracted_profile)` - 评估提取准确性

#### 2. ProfileConfigurator（画像配置器）

**职责**：
- 生成画像配置（指定要体现的画像维度）
- 管理画像模板
- 确保画像配置的合理性

**配置方式**：
- 完整画像配置：指定所有维度的值
- 部分画像配置：只指定部分维度
- 画像模板：使用预设的画像模板

#### 3. LanguageStyleGenerator（语言风格生成器 - 增强版）

**职责**：
- 根据画像配置生成语言风格提示词
- 模拟老年人的语言特点
- 控制表达的个性化程度
- **与助手侧的 ResponseStyleController 做一一映射**

**核心映射关系**：
```python
class LanguageStyleMapper:
    """用户侧语言特征 ↔ 助手侧控制参数映射"""
    
    MAPPING = {
        # 表达模糊 → 助手需要更详细、需要澄清
        "expression_vagueness": {
            "user_side": "表达模糊、不具体",
            "assistant_side": {
                "verbosity_level": "详细",
                "information_density": "中",
                "directive_strength": "建议性"  # 需要澄清，不能太直接
            }
        },
        
        # 句子短、跳跃 → 助手需要简洁、分段
        "short_attention_span": {
            "user_side": "句子短、话题跳跃",
            "assistant_side": {
                "verbosity_level": "简洁",
                "attention_span": "短",
                "information_density": "低"
            }
        },
        
        # 情绪化表达 → 助手需要关怀、共情
        "emotional_expression": {
            "user_side": "情绪化、情感丰富",
            "assistant_side": {
                "emotional_tone": "关怀",
                "formality_level": "温暖",
                "directive_strength": "建议性"  # 情绪化时不能太指导性
            }
        },
        
        # 抗拒建议 → 助手需要更温和、建议性
        "resistance_to_advice": {
            "user_side": "抗拒建议、坚持己见",
            "assistant_side": {
                "directive_strength": "建议性",  # 不能太强
                "emotional_tone": "关怀",
                "formality_level": "温暖"
            }
        },
        
        # 技术困惑 → 助手需要详细步骤、低密度
        "technical_confusion": {
            "user_side": "技术问题困惑、理解困难",
            "assistant_side": {
                "verbosity_level": "详细",
                "information_density": "低",  # 低密度，分步骤
                "directive_strength": "指导性",  # 需要明确指导
                "explanation_depth": "详细"
            }
        }
    }
```

**语言特点**：
- 口语化程度
- 方言特色
- 表达习惯（重复、强调、感叹）
- 认知特点（记忆模糊、话题跳跃）
- **与助手侧 ResponseStyle 的映射关系**

**核心方法**：
- `generate_language_style(profile_config)` - 生成语言风格提示词
- `map_to_assistant_style(user_language_features)` - 映射到助手侧控制参数
- `validate_style_alignment(user_style, assistant_style)` - 验证风格对齐

#### 4. DisclosureController（信息释放节奏控制器）

**职责**：
- 控制每轮对话最多暴露的画像事实数量
- 控制画像维度的暴露优先级
- 控制表达噪声注入（模糊、否认、跳话题）
- 模拟真实老人的表达特点（慢慢说、绕着说、偶尔不说清楚）

**核心参数**：
```python
class DisclosureController:
    max_new_facts_per_turn: int = 1  # 每轮最多暴露几个新画像事实
    priority_order: List[str] = [
        "emotional_support",    # 优先暴露：情感与支持
        "health_safety",         # 其次：健康与安全
        "identity_language",     # 再次：身份与语言
        "values_preferences",     # 最后：价值观与偏好
        "lifestyle_social",      # 生活方式与社交
        "cognitive_interaction"  # 认知与交互
    ]
    noise_injection_rate: float = 0.15  # 模糊、否认、跳话题的概率
    disclosure_strategy: str = "gradual"  # 释放策略：gradual（渐进）/ burst（爆发）
```

**核心方法**：
- `select_facts_to_disclose(ground_truth, expressed, turn)` - 选择本轮要暴露的事实
- `apply_noise(fact, noise_model)` - 应用表达噪声
- `should_disclose_dimension(dimension, priority_order)` - 判断是否应该暴露该维度

#### 5. TrajectoryGenerator（轨迹生成器）

**职责**：
- 管理场景模板
- 生成完整的用户轨迹
- 控制轨迹长度和内容
- **与信息释放节奏控制器协同工作**

**场景类型**：
- 健康咨询场景
- 日常聊天场景
- 技术支持场景
- 情感倾诉场景
- 兴趣爱好场景
- 身份介绍场景

## 📐 实现方案

### 阶段1：基础用户模拟器（2-3天）

**目标**：实现基本的用户模拟器，能够生成用户对话

**任务**：
1. 创建 `elderly_user_simulator/elderly_user_simulator.py` 模块
2. 实现 `SimulatedUser` 基础类（包含 ground_truth_profile）
3. 实现 `generate_user_message()` 方法
4. 实现基础的提示词构建
5. 实现LLM调用（使用DashScope API）
6. **实现 ground_truth_profile 和 expressed_profile 管理**
7. **实现基础的噪声模型**

**输出**：
- 能够根据简单配置生成用户对话
- 能够模拟基本的老年人语言特点
- **能够管理隐藏真实画像和已表达画像**

### 阶段2：与助手系统集成（2-3天）

**目标**：实现用户模拟器与助手系统的对话集成

**任务**：
1. 设计助手系统接口（如何调用agent.py的对话功能）
2. 实现对话循环逻辑：
   - 用户模拟器生成消息
   - 调用助手系统获取回复
   - 用户模拟器根据回复生成下一轮消息
3. 实现对话历史管理
4. 实现对话质量控制（检测异常、重试等）

**助手系统接口设计**：
- **方案1**：直接调用agent.py的函数（推荐）
  - 提取 `chat_loop` 中的核心逻辑
  - 创建可复用的对话处理函数
  - 用户模拟器调用该函数

- **方案2**：通过API调用（如果助手系统有API）
  - 需要助手系统提供API接口
  - 用户模拟器通过HTTP调用

- **方案3**：模拟助手回复（用于快速测试）
  - 使用简单的规则或LLM生成助手回复
  - 不依赖真实助手系统

**输出**：
- 能够与助手系统进行完整对话
- 能够记录对话历史
- 能够生成多轮对话轨迹

### 阶段3：画像配置系统（2-3天）

**目标**：实现灵活的画像配置系统

**任务**：
1. 实现 `ProfileConfigurator` 类
2. 设计画像配置格式
3. 实现画像模板库：
   - 预设画像模板（如"独居老人"、"慢性病患者"等）
   - 画像维度组合模板
4. 实现画像配置生成器：
   - 完整画像配置
   - 部分画像配置
   - 随机画像配置
5. 实现画像配置验证

**输出**：
- 画像配置系统
- 画像模板库（10-20个模板）
- 画像配置生成器

### 阶段4：语言风格模拟和映射（3-4天）

**目标**：实现真实的老年人语言特点模拟，并与助手侧 ResponseStyle 建立映射

**任务**：
1. 分析老年人语言特点
2. 设计语言风格提示词模板
3. 实现 `LanguageStyleGenerator` 类
4. **实现 `LanguageStyleMapper` 类（用户侧 ↔ 助手侧映射）**
5. 根据画像配置调整语言风格：
   - 根据地区调整方言特色
   - 根据教育程度调整语言复杂度
   - 根据认知能力调整表达清晰度
6. 实现语言特点注入（口语化、重复、感叹等）
7. **建立用户侧语言特征与助手侧控制参数的映射表**
8. **实现风格对齐验证功能**

**输出**：
- 语言风格生成器
- **语言风格映射器（用户侧 ↔ 助手侧）**
- 语言特点库
- 方言特色库（可选）
- **风格对齐验证工具**

### 阶段5：信息释放节奏控制和轨迹生成（3-4天）

**目标**：实现信息释放节奏控制器和场景模板系统

**任务**：
1. 实现 `DisclosureController` 类：
   - 控制每轮最多暴露的画像事实数量
   - 实现画像维度暴露优先级
   - 实现表达噪声注入（模糊、否认、跳话题）
   - 实现释放策略（渐进式/爆发式）
2. 设计场景模板结构
3. 开发6类场景模板：
   - 健康咨询场景（3-5个模板）
   - 日常聊天场景（3-5个模板）
   - 技术支持场景（2-3个模板）
   - 情感倾诉场景（2-3个模板）
   - 兴趣爱好场景（2-3个模板）
   - 身份介绍场景（2-3个模板）
4. 实现 `TrajectoryGenerator` 类
5. 实现轨迹生成逻辑：
   - 选择场景
   - **与 DisclosureController 协同工作**
   - **控制每轮信息释放量**
   - 生成对话轨迹
   - 控制轨迹长度
6. 建立场景与画像维度的映射关系

**输出**：
- **信息释放节奏控制器**
- 场景模板库（15-25个模板）
- 轨迹生成器（集成信息释放控制）
- 场景选择接口

### 阶段6：模式切换和配置系统（1-2天）

**目标**：实现真实用户/模拟用户模式切换

**任务**：
1. 修改 `agent.py` 支持模式切换：
   - 添加配置项：`INTERACTION_MODE`（`real_user` / `simulated_user`）
   - 修改 `chat_loop` 支持两种模式
   - 模式1：真实用户输入（当前实现）
   - 模式2：调用用户模拟器自动生成对话
2. 实现配置管理：
   - 环境变量配置
   - 配置文件支持
3. 实现模式切换逻辑
4. 测试两种模式的切换

**配置设计**：
```env
# .env 文件
INTERACTION_MODE=real_user        # 真实用户模式
# 或
INTERACTION_MODE=simulated_user   # 模拟用户模式

# 模拟用户模式配置
SIMULATED_USER_PROFILE=elderly_template_001  # 画像模板
SIMULATED_USER_SCENARIO=health_consultation  # 场景类型
SIMULATED_USER_MAX_TURNS=5                   # 最大对话轮数
```

**输出**：
- 支持模式切换的agent.py
- 配置管理系统
- 两种模式都能正常工作

### 阶段7：评估系统和数据输出（2-3天）

**目标**：实现评估系统和轨迹数据的输出验证

**任务**：
1. **实现画像提取准确性评估**：
   - 对比 extracted_profile vs ground_truth_profile
   - 计算各维度的准确率、召回率
   - 测量收敛速度（每轮对话后画像的改进）
   - 检测错误提取（误提取、漏提取）
2. **实现风格对齐评估**：
   - 验证用户侧语言特征是否触发助手侧相应控制参数
   - 测量风格匹配度
   - 检测风格不匹配的情况
3. 设计轨迹数据格式（包含 ground_truth_profile）
4. 实现轨迹格式化器
5. 实现数据验证器：
   - 验证轨迹完整性
   - 验证画像覆盖度
   - 验证语言真实性
   - **验证评估指标**
6. 实现数据导出功能（JSON格式，包含评估结果）
7. 实现轨迹数据集管理
8. **生成评估报告**

**输出**：
- **画像提取准确性评估系统**
- **风格对齐评估系统**
- 轨迹数据格式规范（包含 ground_truth）
- 数据验证工具
- 数据导出功能（包含评估结果）
- 轨迹数据集
- **评估报告生成器**

## 🔧 技术实现细节

### 用户模拟器核心实现

#### 1. ElderlyUserSimulator 类结构

```python
class ElderlyUserSimulator:
    """老年人用户模拟器"""
    
    def __init__(self, llm_config=None):
        """初始化用户模拟器"""
        self.llm = None  # LLM实例
        self.profile_configurator = ProfileConfigurator()
        self.language_style_generator = LanguageStyleGenerator()
        self._init_llm(llm_config)
    
    def generate_user_message(
        self, 
        conversation_history: List[Dict],
        profile_config: Dict,
        scenario: str = None
    ) -> str:
        """生成用户消息"""
        # 1. 构建语言风格提示词
        language_style = self.language_style_generator.generate(profile_config)
        
        # 2. 构建用户提示词
        prompt = self._build_user_prompt(
            conversation_history=conversation_history,
            profile_config=profile_config,
            language_style=language_style,
            scenario=scenario
        )
        
        # 3. 调用LLM生成消息
        message = self._call_llm(prompt)
        
        return message
    
    def simulate_conversation(
        self,
        profile_config: Dict,
        scenario: str,
        max_turns: int = 5,
        assistant_callback: Callable = None
    ) -> List[Dict]:
        """模拟完整对话"""
        trajectory = []
        conversation_history = []
        
        for turn in range(max_turns):
            # 1. 生成用户消息
            user_message = self.generate_user_message(
                conversation_history=conversation_history,
                profile_config=profile_config,
                scenario=scenario
            )
            
            # 2. 记录用户消息
            trajectory.append({
                "turn": turn + 1,
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            conversation_history.append({"role": "user", "content": user_message})
            
            # 3. 调用助手系统获取回复
            if assistant_callback:
                assistant_response = assistant_callback(user_message)
            else:
                assistant_response = self._mock_assistant_response(user_message)
            
            # 4. 记录助手回复
            trajectory.append({
                "turn": turn + 1,
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.now().isoformat()
            })
            conversation_history.append({"role": "assistant", "content": assistant_response})
        
        return trajectory
```

#### 2. 助手系统接口设计

**方案1：直接调用agent.py的函数（推荐）**

修改 `agent.py`，提取核心对话处理逻辑：

```python
# agent.py 中新增函数
async def process_user_message(
    user_id: str,
    user_input: str,
    profile: Dict[str, Any],
    memory_manager: ChatMemoryManager,
    memu_store: MemUStore,
    responder: Optional[Any] = None,
    enable_personalized_response: bool = True
) -> Dict[str, Any]:
    """
    处理用户消息（可被用户模拟器调用）
    
    Returns:
        {
            "assistant_response": str,  # 助手回复
            "updated_profile": Dict,     # 更新后的画像
            "extraction_success": bool   # 画像提取是否成功
        }
    """
    # 1. 保存用户消息
    await memory_manager.add_message(user_id, "user", user_input)
    
    # 2. 提取画像
    updated_profile = update_profile(user_input, profile)
    
    # 3. 保存画像
    await memu_store.save_profile(user_id, updated_profile)
    
    # 4. 生成个性化回答（如果启用）
    assistant_response = ""
    if enable_personalized_response and responder:
        assistant_response = await responder.generate_response(
            user_id, user_input, updated_profile
        )
        await memory_manager.add_message(user_id, "assistant", assistant_response)
    
    return {
        "assistant_response": assistant_response,
        "updated_profile": updated_profile,
        "extraction_success": True
    }
```

用户模拟器调用：

```python
# elderly_user_simulator.py
from agent import process_user_message

async def simulate_with_assistant(
    user_id: str,
    profile_config: Dict,
    scenario: str,
    max_turns: int = 5,
    memory_manager: ChatMemoryManager = None,
    memu_store: MemUStore = None,
    responder: Optional[Any] = None
):
    """与真实助手系统对话"""
    trajectory = []
    conversation_history = []
    current_profile = init_optimized_profile()
    
    for turn in range(max_turns):
        # 1. 生成用户消息
        user_message = self.generate_user_message(
            conversation_history=conversation_history,
            profile_config=profile_config,
            scenario=scenario
        )
        
        # 2. 调用助手系统
        result = await process_user_message(
            user_id=user_id,
            user_input=user_message,
            profile=current_profile,
            memory_manager=memory_manager,
            memu_store=memu_store,
            responder=responder,
            enable_personalized_response=True
        )
        
        # 3. 记录对话
        trajectory.append({
            "turn": turn + 1,
            "role": "user",
            "content": user_message
        })
        trajectory.append({
            "turn": turn + 1,
            "role": "assistant",
            "content": result["assistant_response"]
        })
        
        # 4. 更新对话历史和画像
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": result["assistant_response"]})
        current_profile = result["updated_profile"]
    
    return trajectory
```

#### 3. 模式切换实现

修改 `agent.py` 的 `chat_loop` 函数：

```python
# agent.py
async def chat_loop(
    user_id: str,
    profile: Dict[str, Any],
    memory_manager: ChatMemoryManager,
    memu_store: MemUStore,
    responder: Optional[Any] = None,
    enable_personalized_response: bool = True,
    interaction_mode: str = "real_user",  # 新增参数
    user_simulator: Optional[Any] = None,  # 新增参数
    simulator_config: Optional[Dict] = None  # 新增参数
):
    """对话循环主函数"""
    
    if interaction_mode == "simulated_user":
        # 模拟用户模式
        if not user_simulator:
            raise ValueError("模拟用户模式需要提供 user_simulator")
        
        # 生成轨迹
        trajectory = await user_simulator.simulate_conversation(
            profile_config=simulator_config.get("profile_config", {}),
            scenario=simulator_config.get("scenario", "daily_chat"),
            max_turns=simulator_config.get("max_turns", 5),
            assistant_callback=lambda msg: asyncio.run(
                process_user_message(
                    user_id, msg, profile, memory_manager, 
                    memu_store, responder, enable_personalized_response
                )
            )["assistant_response"]
        )
        
        # 保存轨迹
        await save_trajectory(user_id, trajectory)
        
    else:
        # 真实用户模式（当前实现）
        while True:
            user_input = input("你: ").strip()
            # ... 现有逻辑 ...
```

### 提示词设计

**用户模拟器提示词模板**：

```
你是一个{age}岁的{gender}，来自{region}，{education_level}文化程度。

你的语言特点：
- 使用口语化表达，如"还行"、"挺好"、"不太行"等
- {dialect_features}
- 表达习惯：{expression_habits}
- 认知特点：{cognitive_features}

当前场景：{scenario_description}

对话历史：
{conversation_history}

你的画像特征：
{profile_summary}

请根据以上信息，生成下一轮用户对话。要求：
1. 符合老年人的语言特点
2. 体现画像维度：{profile_dimensions}
3. 与对话历史连贯
4. 自然、真实、有感情
5. 对话长度适中（1-3句话）
```

## 📊 场景模板设计

### 场景分类和模板

#### 1. 健康咨询场景
**目标画像维度**：health_safety, emotional_support

**场景模板**：
- 失眠问题咨询
- 慢性病管理咨询
- 日常健康问题咨询

#### 2. 日常聊天场景
**目标画像维度**：lifestyle_social, values_preferences

**场景模板**：
- 天气聊天
- 日常生活分享
- 家庭话题

#### 3. 技术支持场景
**目标画像维度**：cognitive_interaction, identity_language

**场景模板**：
- 手机使用问题
- 微信操作问题
- 网购问题

#### 4. 情感倾诉场景
**目标画像维度**：emotional_support, lifestyle_social

**场景模板**：
- 孤独感表达
- 家庭关系困扰
- 生活压力倾诉

#### 5. 兴趣爱好场景
**目标画像维度**：values_preferences, lifestyle_social

**场景模板**：
- 兴趣爱好分享
- 活动参与咨询
- 学习新技能

#### 6. 身份介绍场景
**目标画像维度**：identity_language, lifestyle_social

**场景模板**：
- 自我介绍
- 家庭情况介绍
- 居住情况介绍

## 📈 实施计划

### 开发顺序

1. **阶段1：基础用户模拟器**（2-3天）
   - 实现基本的用户对话生成
   - 验证可行性

2. **阶段2：与助手系统集成**（2-3天）
   - 实现对话集成
   - 测试完整对话流程

3. **阶段3：画像配置系统**（2-3天）
   - 实现画像配置
   - 开发画像模板

4. **阶段4：语言风格模拟**（2-3天）
   - 实现语言风格生成
   - 测试语言真实性

5. **阶段5：场景模板和轨迹生成**（2-3天）
   - 开发场景模板
   - 实现轨迹生成

6. **阶段6：模式切换**（1-2天）
   - 实现模式切换
   - 测试两种模式

7. **阶段7：数据输出和验证**（1-2天）
   - 实现数据导出
   - 实现数据验证

**总计**：16-25天（增加了评估系统开发时间）

### 里程碑

- **M1：基础用户模拟器完成** - 能够生成用户对话
- **M2：助手系统集成完成** - 能够与助手对话
- **M3：画像配置完成** - 能够控制画像维度
- **M4：语言风格完成** - 对话语言真实自然
- **M5：场景模板完成** - 能够选择场景生成轨迹
- **M6：模式切换完成** - 能够切换两种模式
- **M7：评估系统完成** - 能够评估画像提取准确性和风格对齐
- **M8：数据输出完成** - 能够导出验证数据集和评估报告

## 🧪 测试策略

### 单元测试

1. **用户模拟器测试**：
   - 测试对话生成功能
   - 测试语言风格
   - 测试画像配置
   - **测试 ground_truth_profile 管理**
   - **测试 expressed_profile 更新**

2. **画像配置器测试**：
   - 测试画像配置生成
   - 测试画像模板

3. **信息释放控制器测试**：
   - 测试事实选择逻辑
   - 测试噪声注入
   - 测试优先级控制

4. **语言风格映射器测试**：
   - 测试用户侧到助手侧的映射
   - 测试风格对齐验证

### 集成测试

1. **对话集成测试**：
   - 测试与助手系统的完整对话
   - 测试对话质量控制
   - **测试信息释放节奏**

2. **模式切换测试**：
   - 测试两种模式的切换
   - 测试配置管理

3. **评估系统测试**：
   - 测试画像提取准确性评估
   - 测试风格对齐评估
   - 测试收敛速度测量

### 验证测试

1. **轨迹质量验证**：
   - 验证轨迹连贯性
   - 验证语言真实性
   - 验证画像覆盖度
   - **验证信息释放节奏合理性**

2. **评估准确性验证**：
   - 验证 ground_truth 与 extracted 的对比准确性
   - 验证风格映射的准确性
   - 验证评估指标的合理性

## 📝 配置规范

### 环境变量配置

```env
# .env 文件

# 交互模式：real_user（真实用户）或 simulated_user（模拟用户）
INTERACTION_MODE=real_user

# 模拟用户模式配置（仅在 INTERACTION_MODE=simulated_user 时生效）
SIMULATED_USER_PROFILE=elderly_template_001
SIMULATED_USER_SCENARIO=health_consultation
SIMULATED_USER_MAX_TURNS=5
SIMULATED_USER_AUTO_START=true  # 是否自动开始对话
```

### 画像模板配置

```json
{
  "elderly_template_001": {
    "name": "独居老人",
    "identity_language": {
      "age": {"value": 72, "confidence": 1.0},
      "gender": {"value": "女", "confidence": 1.0},
      "region": {"value": "石家庄", "confidence": 1.0}
    },
    "lifestyle_social": {
      "living_situation": {"value": "独居", "confidence": 1.0}
    }
  }
}
```

## ⚠️ 注意事项

1. **助手系统接口**：
   - 需要提取agent.py的核心逻辑
   - 确保接口设计合理
   - 避免循环依赖

2. **模式切换**：
   - 确保两种模式都能正常工作
   - 配置管理要清晰
   - 错误处理要完善

3. **数据真实性**：
   - 确保生成的对话真实自然
   - 注意语言特点的准确性
   - 避免过于机械化

4. **成本控制**：
   - 大量轨迹生成会产生API调用成本
   - 考虑使用缓存机制
   - 考虑批量生成优化

## 🎯 成功标准

1. **功能完整性**：
   - ✅ 能够生成用户对话
   - ✅ 能够与助手系统对话
   - ✅ 能够生成用户轨迹
   - ✅ 能够切换两种模式
   - ✅ **能够管理 ground truth profile**
   - ✅ **能够控制信息释放节奏**
   - ✅ **能够映射用户侧语言到助手侧控制参数**

2. **数据质量**：
   - ✅ 对话语言真实自然
   - ✅ 轨迹连贯流畅
   - ✅ 画像覆盖完整
   - ✅ **信息释放节奏合理（模拟真实老人）**

3. **评估能力**（从"测试工具"升级为"评价系统"）：
   - ✅ **能够评估画像提取准确性**
   - ✅ **能够测量收敛速度**
   - ✅ **能够检测错误提取**
   - ✅ **能够验证风格对齐**
   - ✅ **能够生成评估报告**

4. **可用性**：
   - ✅ 易于配置和使用
   - ✅ 文档完整清晰
   - ✅ 便于扩展和维护
   - ✅ **评估结果清晰易懂**

## 🔬 研究级增强功能

### 增强点1：隐藏真实画像（Ground Truth Profile）层

**设计理念**：
- 系统需要知道"真实答案"才能评估画像提取的准确性
- 这是从"测试工具"升级为"评价系统"的关键

**实现结构**：
```python
class SimulatedUser:
    """用户模拟器 - 增强版"""
    
    def __init__(self, ground_truth_profile: Dict[str, Any]):
        self.ground_truth_profile = ground_truth_profile  # 真正的用户画像（不可见）
        self.expressed_profile = init_optimized_profile()  # 已通过对话显露的部分
        self.noise_model = {
            "forgetfulness_rate": 0.1,      # 遗忘率
            "vagueness_rate": 0.15,         # 模糊表达率
            "misleading_rate": 0.05,        # 误导率
            "topic_hopping_rate": 0.2       # 话题跳跃率
        }
    
    def update_expressed_profile(self, conversation_history: List[Dict]):
        """根据对话历史更新已表达画像"""
        # 分析对话中已经暴露的画像信息
        # 更新 expressed_profile
        pass
    
    def evaluate_extraction_accuracy(
        self, 
        extracted_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估画像提取准确性
        
        Returns:
            {
                "overall_accuracy": float,      # 总体准确率
                "dimension_accuracy": Dict,      # 各维度准确率
                "convergence_speed": float,     # 收敛速度
                "error_analysis": Dict          # 错误分析
            }
        """
        # 对比 extracted_profile vs ground_truth_profile
        # 计算准确率、召回率、F1分数
        # 测量收敛速度
        # 分析错误类型
        pass
```

**评估指标**：
- **准确率（Accuracy）**：提取的画像与真实画像的匹配度
- **召回率（Recall）**：真实画像中被提取出的比例
- **收敛速度（Convergence Speed）**：需要多少轮对话才能达到高准确率
- **错误分析（Error Analysis）**：误提取、漏提取、置信度错误等

### 增强点2：信息释放节奏控制器

**设计理念**：
- 真实老人不会一次性说出所有信息
- 需要模拟"慢慢说、绕着说、偶尔不说清楚"的特点
- 控制信息释放的节奏和优先级

**实现结构**：
```python
class DisclosureController:
    """信息释放节奏控制器"""
    
    def __init__(self):
        self.max_new_facts_per_turn = 1  # 每轮最多暴露几个新画像事实
        self.priority_order = [
            "emotional_support",    # 优先暴露：情感需求
            "health_safety",        # 其次：健康问题
            "identity_language",    # 再次：身份信息
            "values_preferences",   # 最后：价值观
            "lifestyle_social",
            "cognitive_interaction"
        ]
        self.noise_injection_rate = 0.15  # 模糊、否认、跳话题的概率
        self.disclosure_strategy = "gradual"  # 渐进式释放
    
    def select_facts_to_disclose(
        self,
        ground_truth: Dict[str, Any],
        expressed: Dict[str, Any],
        turn: int
    ) -> List[Dict[str, Any]]:
        """
        选择本轮要暴露的画像事实
        
        Args:
            ground_truth: 真实画像
            expressed: 已表达画像
            turn: 当前轮次
            
        Returns:
            要暴露的事实列表（最多 max_new_facts_per_turn 个）
        """
        # 1. 找出未表达的事实
        # 2. 按优先级排序
        # 3. 选择前 max_new_facts_per_turn 个
        # 4. 应用噪声模型
        pass
    
    def apply_noise(
        self,
        fact: Dict[str, Any],
        noise_model: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        应用表达噪声（模糊、否认、跳话题）
        
        Returns:
            添加噪声后的事实
        """
        # 根据 noise_model 添加：
        # - 模糊表达（"大概"、"可能"、"好像"）
        # - 否认（"不是"、"没有"）
        # - 话题跳跃
        pass
```

**释放策略**：
- **渐进式（Gradual）**：每轮少量释放，逐步积累
- **爆发式（Burst）**：某些轮次集中释放多个事实
- **优先级控制**：按维度优先级决定释放顺序

### 增强点3：语言风格映射器

**设计理念**：
- 用户侧的语言特征应该触发助手侧相应的控制参数
- 这是验证"系统是否自动调节生成风格来匹配用户"的关键

**实现结构**：
```python
class LanguageStyleMapper:
    """用户侧语言特征 ↔ 助手侧控制参数映射"""
    
    MAPPING = {
        "expression_vagueness": {
            "user_side": "表达模糊、不具体",
            "assistant_side": {
                "verbosity_level": "详细",
                "information_density": "中",
                "directive_strength": "建议性"
            },
            "validation": "助手是否主动澄清模糊点"
        },
        
        "short_attention_span": {
            "user_side": "句子短、话题跳跃",
            "assistant_side": {
                "verbosity_level": "简洁",
                "attention_span": "短",
                "information_density": "低"
            },
            "validation": "助手回答是否分段、简洁"
        },
        
        "emotional_expression": {
            "user_side": "情绪化、情感丰富",
            "assistant_side": {
                "emotional_tone": "关怀",
                "formality_level": "温暖",
                "directive_strength": "建议性"
            },
            "validation": "助手是否使用关怀语调"
        },
        
        "resistance_to_advice": {
            "user_side": "抗拒建议、坚持己见",
            "assistant_side": {
                "directive_strength": "建议性",
                "emotional_tone": "关怀",
                "formality_level": "温暖"
            },
            "validation": "助手是否降低指导强度"
        },
        
        "technical_confusion": {
            "user_side": "技术问题困惑、理解困难",
            "assistant_side": {
                "verbosity_level": "详细",
                "information_density": "低",
                "directive_strength": "指导性",
                "explanation_depth": "详细"
            },
            "validation": "助手是否提供详细步骤、低密度信息"
        }
    }
    
    def map_to_assistant_style(
        self,
        user_language_features: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        将用户侧语言特征映射到助手侧控制参数
        
        Args:
            user_language_features: {
                "expression_vagueness": 0.8,
                "short_attention_span": 0.6,
                ...
            }
            
        Returns:
            助手侧控制参数建议
        """
        # 根据用户侧特征，查找映射表
        # 生成助手侧控制参数建议
        pass
    
    def validate_style_alignment(
        self,
        user_style: Dict[str, Any],
        assistant_style: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证风格对齐
        
        Returns:
            {
                "alignment_score": float,  # 对齐分数
                "matched_features": List,   # 匹配的特征
                "mismatched_features": List # 不匹配的特征
            }
        """
        # 对比用户侧特征和助手侧控制参数
        # 计算对齐分数
        # 识别匹配和不匹配的特征
        pass
```

**验证假设**：
- "如果用户侧语言发生某种变化，系统是否自动调节生成风格来匹配？"
- 这是系统中最科学、最智能的部分
- 可以通过评估系统验证这个假设

---

**文档创建时间**: 2026-01-28  
**最后更新**: 2026-01-28（增加研究级增强功能）  
**状态**: 📋 计划阶段，待实施  
**版本**: v2.0（研究级增强版）
