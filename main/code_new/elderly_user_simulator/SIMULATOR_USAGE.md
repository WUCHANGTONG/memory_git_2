# 用户模拟器使用说明（阶段一增强版）

## 📋 功能说明

本版本实现了两种交互模式，并新增了阶段一增强功能：
1. **真实用户模式**：用户从终端输入，与助手对话（已实现）
2. **模拟用户模式**：模拟老年人用户自动生成对话，与助手对话（已实现）

### 阶段一新增功能
- ✅ **Ground Truth Profile 管理**：真实用户画像（不可见，用于评估）
- ✅ **Expressed Profile 管理**：已通过对话显露的部分画像
- ✅ **噪声模型**：模拟真实老人的表达特点（遗忘、模糊、误导、话题跳跃）
- ✅ **画像提取准确性评估**：对比提取画像与真实画像的准确性

## 🔧 配置方法

### 1. 环境变量配置

在 `.env` 文件中添加：

```env
# 交互模式：real_user（真实用户）或 simulated_user（模拟用户）
INTERACTION_MODE=simulated_user

# 可选：指定配置文件路径（如果不指定，使用默认路径）
ELDERLY_USER_CONFIG=main/code_new/elderly_user_simulator/elderly_user_simulator_config.json
```

### 2. 用户模拟器配置文件

配置文件：`elderly_user_simulator/elderly_user_simulator_config.json`

**基础配置**：
```json
{
  "elderly_user_prompt": "你是一个68岁的老年女性，来自石家庄...",
  "llm_config": {
    "model": "qwen-turbo",
    "temperature": 0.7
  }
}
```

**完整配置（阶段一增强版）**：
```json
{
  "elderly_user_prompt": "你是一个68岁的老年女性，来自石家庄...",
  "llm_config": {
    "model": "qwen-turbo",
    "temperature": 0.7
  },
  "ground_truth_profile": {
    "identity_language": {
      "age": {"value": 68, "confidence": 1.0},
      "gender": {"value": "女", "confidence": 1.0},
      "region": {"value": "石家庄", "confidence": 1.0}
    },
    "health_safety": {
      "chronic_conditions": {"value": ["高血压"], "confidence": 1.0}
    },
    "lifestyle_social": {
      "living_situation": {"value": "独居", "confidence": 1.0}
    }
  },
  "noise_model": {
    "forgetfulness_rate": 0.1,
    "vagueness_rate": 0.15,
    "misleading_rate": 0.05,
    "topic_hopping_rate": 0.2
  },
  "conversation_config": {
    "countdown_enabled": true,
    "countdown_seconds": 5,
    "auto_continue": true,
    "max_turns": null
  }
}
```

**配置说明**：
- `elderly_user_prompt`：模拟老年人的提示词描述，用于指导LLM生成符合老年人特点的对话
- `llm_config`：LLM配置
  - `model`：使用的模型名称（默认：qwen-turbo）
  - `temperature`：生成温度（默认：0.7）
- `ground_truth_profile`（可选）：真实用户画像，用于评估画像提取准确性
  - 如果未配置，将使用默认空画像
  - 支持优化版画像结构（OptimizedUserProfile）
- `noise_model`（可选）：噪声模型参数
  - `forgetfulness_rate`：遗忘率（默认：0.1）
  - `vagueness_rate`：模糊表达率（默认：0.15）
  - `misleading_rate`：误导率（默认：0.05）
  - `topic_hopping_rate`：话题跳跃率（默认：0.2）
- `conversation_config`（可选，阶段二新增）：对话配置
  - `countdown_enabled`：是否启用倒计时（默认：true）
  - `countdown_seconds`：倒计时秒数（默认：5）
  - `auto_continue`：倒计时结束后是否自动继续（默认：true）
  - `max_turns`：最大对话轮数（null表示无限制，默认：null）

## 🚀 使用方法

### 模式1：真实用户模式（默认）

```bash
# 在 .env 文件中设置（或不设置，默认就是真实用户模式）
INTERACTION_MODE=real_user

# 运行程序
python main/code_new/agent.py
```

**使用流程**：
1. 输入用户ID（或使用默认）
2. 直接输入对话内容
3. 系统提取画像并生成个性化回答
4. 输入 `exit` 退出

### 模式2：模拟用户模式

```bash
# 在 .env 文件中设置
INTERACTION_MODE=simulated_user

# 运行程序
python main/code_new/agent.py
```

**使用流程**：
1. 输入用户ID（或使用默认）
2. 按回车键开始对话
3. 系统自动生成用户消息和助手回复
4. 每轮对话后有倒计时（默认5秒），可以：
   - 提前输入 `y` 继续对话
   - 提前输入 `n` 或 `exit` 退出
   - 等待倒计时结束自动继续（默认行为）

## 📝 示例

### 模拟用户模式示例

```
============================================================
用户画像记忆系统
============================================================

[INFO] 正在初始化 memU 存储层...
[OK] memU 存储层初始化成功

请输入用户ID（直接回车使用默认 'default_user'）: test_user
[INFO] 当前用户ID: test_user

[INFO] 正在加载历史画像...
[INFO] 新用户，已初始化空画像（优化版）

[INFO] 正在初始化 Memory...
[OK] Memory 初始化成功

[INFO] 正在初始化个性化回答生成器...
[OK] 个性化回答生成器初始化成功

[INFO] 正在初始化用户模拟器...
[OK] 用户模拟器初始化成功

============================================================
对话系统已启动
============================================================

模式：模拟用户模式
  - 模拟老年人用户将自动生成对话
  - 系统会提取并更新用户画像
  - 系统会根据用户画像生成个性化回答
  - 每轮对话后会询问是否继续

------------------------------------------------------------

按回车键开始对话...

开始对话...

--- 第 1 轮对话 ---

[INFO] 正在生成用户消息...
用户: 你好，我最近有点失眠，睡不好觉

[INFO] 正在提取画像信息...
[OK] 画像提取完成

[INFO] 正在生成个性化回答...
助手: 您好！我理解您最近睡眠不好的困扰。对于您来说，保持良好的睡眠质量非常重要...

------------------------------------------------------------
是否继续对话？(y/n，或输入 'exit' 退出): [5秒后自动继续] y

--- 第 2 轮对话 ---

[INFO] 正在生成用户消息...
用户: 我今年68岁了，平时一个人住

[INFO] 正在处理用户消息...
[OK] 画像提取完成
助手: 我了解您的情况。作为一位68岁的独居老人...

------------------------------------------------------------
是否继续对话？(y/n，或输入 'exit' 退出): [5秒后自动继续] 时间到，自动继续...

[INFO] 正在保存数据...
[OK] 数据已保存

对话已结束，再见！
```

## ⚙️ 自定义配置

### 修改模拟用户提示词

编辑 `elderly_user_simulator/elderly_user_simulator_config.json` 文件中的 `elderly_user_prompt` 字段：

```json
{
  "elderly_user_prompt": "你是一个70岁的老年男性，来自北京，退休教师。你的语言特点：\n- 说话比较正式，但也很亲切\n- 喜欢分享生活经验\n- 关注健康、教育、社会话题\n\n请根据对话历史，生成下一轮用户对话。要求：\n1. 符合老年人的语言特点\n2. 自然、真实、有感情\n3. 对话长度适中（1-3句话）\n4. 与对话历史连贯"
}
```

### 修改LLM配置

```json
{
  "llm_config": {
    "model": "qwen-plus",
    "temperature": 0.8
  }
}
```

### 配置 Ground Truth Profile

Ground Truth Profile 是真实用户画像，用于评估画像提取的准确性。配置示例：

```json
{
  "ground_truth_profile": {
    "identity_language": {
      "age": {"value": 72, "confidence": 1.0},
      "gender": {"value": "男", "confidence": 1.0},
      "region": {"value": "北京", "confidence": 1.0},
      "education_level": {"value": "大学", "confidence": 1.0}
    },
    "health_safety": {
      "chronic_conditions": {"value": ["糖尿病", "高血压"], "confidence": 1.0},
      "mobility_level": {"value": "正常", "confidence": 1.0}
    },
    "lifestyle_social": {
      "living_situation": {"value": "与配偶同住", "confidence": 1.0},
      "core_interests": {"value": ["书法", "太极拳"], "confidence": 1.0}
    },
    "emotional_support": {
      "loneliness_level": {"value": "低", "confidence": 1.0}
    }
  }
}
```

### 调整噪声模型

噪声模型控制模拟用户的表达特点，可以调整参数：

```json
{
  "noise_model": {
    "forgetfulness_rate": 0.15,    // 增加遗忘率
    "vagueness_rate": 0.2,          // 增加模糊表达率
    "misleading_rate": 0.05,        // 保持误导率
    "topic_hopping_rate": 0.25      // 增加话题跳跃率
  }
}
```

## 🔬 评估功能（阶段一新增）

### 评估画像提取准确性

在对话过程中，可以评估助手系统提取的画像与真实画像的匹配度：

```python
from elderly_user_simulator.elderly_user_simulator import SimpleElderlyUserSimulator

# 初始化模拟器
simulator = SimpleElderlyUserSimulator()

# 假设助手系统提取了画像
extracted_profile = {...}  # 从助手系统获取

# 评估准确性
evaluation = simulator.simulated_user.evaluate_extraction_accuracy(
    extracted_profile
)

# 查看结果
print(f"总体准确率: {evaluation['overall_accuracy']:.2%}")
print(f"各维度准确率:")
for dim, acc in evaluation['dimension_accuracy'].items():
    print(f"  {dim}: {acc:.2%}")
```

**评估指标**：
- `overall_accuracy`：总体准确率（所有字段的匹配度）
- `dimension_accuracy`：各维度准确率（identity_language, health_safety 等）
- `total_fields`：总字段数
- `correct_fields`：正确字段数

## ⚠️ 注意事项

1. **API Key**：确保 `.env` 文件中配置了 `DASHSCOPE_API_KEY`
2. **依赖**：需要安装 `dashscope` 或 `langchain` 和 `langchain-community`
3. **配置文件**：配置文件必须是有效的JSON格式
4. **模式切换**：修改 `.env` 文件后需要重启程序

## 🔄 后续扩展

根据 `ELDERLY_USER_SIMULATOR_PLAN.md` 文档，后续阶段将实现：

### 阶段二（✅ 已完成）
- ✅ 与助手系统集成
- ✅ 对话循环逻辑
- ✅ 对话历史管理
- ✅ 对话质量控制
- ✅ **倒计时功能（5秒倒计时，结束后默认继续）**

### 阶段三（计划中）
- 画像配置系统
- 画像模板库
- 画像配置生成器

### 阶段四（计划中）
- 语言风格模拟
- 语言风格映射器（用户侧 ↔ 助手侧）
- 风格对齐验证

### 阶段五（计划中）
- 信息释放节奏控制器
- 场景模板系统
- 轨迹生成器

### 阶段六（计划中）
- 模式切换优化
- 配置管理系统

### 阶段七（计划中）
- 完整的评估系统
- 数据导出功能
- 评估报告生成

## 📚 相关文档

- `ELDERLY_USER_SIMULATOR_PLAN.md`：完整实现计划
- `STAGE_1_COMPLETE.md`：阶段一完成报告
- `profile_schema_optimized.py`：优化版画像结构定义

---

**创建时间**: 2026-01-28  
**最后更新**: 2026-01-28（阶段二完成版）  
**版本**: v2.0（阶段二完成版）


