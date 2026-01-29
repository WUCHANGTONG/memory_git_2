# 阶段一完成报告：基础用户模拟器（增强版）

## 📋 完成时间
2026-01-28

## ✅ 已完成功能

### 1. SimulatedUser 类（增强版）

实现了 `SimulatedUser` 类，包含以下核心功能：

#### 1.1 Ground Truth Profile 管理
- **ground_truth_profile**：真实用户画像（不可见，用于评估）
- 从配置文件读取或通过构造函数传入
- 支持优化版画像结构（OptimizedUserProfile）

#### 1.2 Expressed Profile 管理
- **expressed_profile**：已通过对话显露的部分画像
- 初始化为空画像
- 提供 `update_expressed_profile()` 方法（阶段一基础版）

#### 1.3 噪声模型（Noise Model）
实现了基础的噪声模型，包含以下参数：
- **forgetfulness_rate** (0.1)：遗忘率，10% 概率忘记某些信息
- **vagueness_rate** (0.15)：模糊表达率，15% 概率表达模糊
- **misleading_rate** (0.05)：误导率，5% 概率提供错误信息
- **topic_hopping_rate** (0.2)：话题跳跃率，20% 概率跳话题

实现了 `apply_noise()` 方法，支持：
- 遗忘：不表达某些事实
- 模糊：添加模糊词汇（"大概"、"可能"、"好像"等）
- 误导：提供部分错误信息（阶段一简单实现）

### 2. SimpleElderlyUserSimulator 类（增强版）

#### 2.1 集成 SimulatedUser
- 在初始化时创建 `SimulatedUser` 实例
- 支持从配置文件读取 `ground_truth_profile` 和 `noise_model`

#### 2.2 增强的 generate_user_message() 方法
- 根据 `ground_truth_profile` 生成用户对话
- 整合画像摘要到提示词中
- 指导LLM自然地在对话中体现画像信息，而不是一次性全部说出来
- 支持噪声模型，模拟真实老人的表达特点

#### 2.3 画像提取准确性评估
实现了 `evaluate_extraction_accuracy()` 方法（阶段一基础版）：
- 对比 `extracted_profile` vs `ground_truth_profile`
- 计算总体准确率和各维度准确率
- 支持字段值匹配和列表交集匹配
- 提供错误分析框架（阶段一简单实现）

### 3. 配置文件增强

更新了 `elderly_user_simulator_config.json`，新增：

#### 3.1 ground_truth_profile
完整的优化版画像结构示例，包含：
- identity_language（身份与语言）
- health_safety（健康与安全）
- lifestyle_social（生活方式与社交）
- emotional_support（情感与陪伴需求）
- cognitive_interaction（认知与交互能力）
- values_preferences（价值观与话题偏好）

#### 3.2 noise_model
噪声模型参数配置：
```json
{
  "forgetfulness_rate": 0.1,
  "vagueness_rate": 0.15,
  "misleading_rate": 0.05,
  "topic_hopping_rate": 0.2
}
```

## 🏗️ 技术实现

### 文件结构
```
main/code_new/elderly_user_simulator/
├── elderly_user_simulator.py          # 核心实现（增强版）
├── elderly_user_simulator_config.json  # 配置文件（增强版）
├── SIMULATOR_USAGE.md                 # 使用说明
├── STAGE_1_COMPLETE.md                 # 本文件
└── __init__.py                         # 包初始化
```

### 核心类和方法

#### SimulatedUser 类
```python
class SimulatedUser:
    def __init__(ground_truth_profile, noise_model)
    def update_expressed_profile(conversation_history)
    def apply_noise(fact, noise_type)
    def get_profile_summary_for_prompt()
    def evaluate_extraction_accuracy(extracted_profile)
```

#### SimpleElderlyUserSimulator 类
```python
class SimpleElderlyUserSimulator:
    def __init__(config_path, ground_truth_profile)
    def generate_user_message(conversation_history)  # 增强版
```

### 依赖关系
- `profile_schema_optimized`：优化版画像结构
- `dashscope` 或 `langchain`：LLM调用
- `dotenv`：环境变量管理

## 📊 功能验证

### 1. Ground Truth Profile 管理
✅ 可以从配置文件读取 ground_truth_profile
✅ 可以通过构造函数传入 ground_truth_profile
✅ 支持优化版画像结构

### 2. Expressed Profile 管理
✅ 初始化为空画像
✅ 提供更新方法框架（阶段一基础版）

### 3. 噪声模型
✅ 支持遗忘、模糊、误导、话题跳跃
✅ 可以应用到事实表达中

### 4. 对话生成
✅ 根据 ground_truth_profile 生成对话
✅ 整合画像信息到提示词
✅ 支持噪声模型

### 5. 评估功能
✅ 可以对比 extracted_profile 和 ground_truth_profile
✅ 计算准确率
✅ 提供错误分析框架

## 🔄 向后兼容性

- ✅ 保持了 `SimpleElderlyUserSimulator` 的原有接口
- ✅ 如果配置文件中没有 `ground_truth_profile`，会使用默认空画像
- ✅ 如果配置文件中没有 `noise_model`，会使用默认噪声参数
- ✅ `agent.py` 无需修改即可使用新功能

## 📝 使用示例

### 基本使用
```python
from elderly_user_simulator.elderly_user_simulator import SimpleElderlyUserSimulator

# 使用默认配置文件
simulator = SimpleElderlyUserSimulator()

# 生成用户消息
conversation_history = []
user_message = simulator.generate_user_message(conversation_history)
```

### 自定义 Ground Truth Profile
```python
from profile_schema_optimized import init_optimized_profile

# 创建自定义 ground_truth_profile
ground_truth = init_optimized_profile()
ground_truth["identity_language"]["age"]["value"] = 72
ground_truth["identity_language"]["gender"]["value"] = "男"

# 使用自定义 profile
simulator = SimpleElderlyUserSimulator(
    ground_truth_profile=ground_truth
)
```

### 评估画像提取准确性
```python
# 假设助手系统提取了画像
extracted_profile = {...}  # 从助手系统获取

# 评估准确性
evaluation = simulator.simulated_user.evaluate_extraction_accuracy(
    extracted_profile
)

print(f"总体准确率: {evaluation['overall_accuracy']:.2%}")
print(f"各维度准确率: {evaluation['dimension_accuracy']}")
```

## 🎯 阶段一目标达成情况

根据 `ELDERLY_USER_SIMULATOR_PLAN.md` 的阶段一要求：

| 任务 | 状态 | 说明 |
|------|------|------|
| 创建 `SimulatedUser` 基础类 | ✅ | 已完成，包含 ground_truth_profile |
| 实现 `generate_user_message()` 方法 | ✅ | 已完成，支持 ground_truth_profile |
| 实现基础的提示词构建 | ✅ | 已完成，整合画像摘要 |
| 实现LLM调用 | ✅ | 已完成，支持 DashScope API |
| 实现 ground_truth_profile 管理 | ✅ | 已完成 |
| 实现 expressed_profile 管理 | ✅ | 已完成（基础版） |
| 实现基础的噪声模型 | ✅ | 已完成 |

## 🚀 下一步计划（阶段二）

根据 `ELDERLY_USER_SIMULATOR_PLAN.md`，阶段二将实现：

1. **与助手系统集成**
   - 设计助手系统接口
   - 实现对话循环逻辑
   - 实现对话历史管理
   - 实现对话质量控制

2. **增强功能**
   - 完善 `update_expressed_profile()` 方法
   - 增强 `evaluate_extraction_accuracy()` 方法
   - 实现更复杂的噪声模型

## 📚 相关文档

- `ELDERLY_USER_SIMULATOR_PLAN.md`：完整实现计划
- `SIMULATOR_USAGE.md`：使用说明
- `profile_schema_optimized.py`：优化版画像结构定义

---

**文档创建时间**: 2026-01-28  
**版本**: v1.0（阶段一完成版）  
**状态**: ✅ 阶段一已完成

