# 用户画像提取系统

## 功能说明

这是一个专注于从老年人对话中提取和更新用户画像的系统。系统会分析对话内容，持续完善用户画像信息。

## 特性

- ✅ 使用 Pydantic 2.x 进行数据验证
- ✅ 支持两种 LLM 调用方式（langchain 或 DashScope SDK）
- ✅ 自动合并新旧画像，保留高置信度信息
- ✅ 完善的错误处理和提示

## 配置步骤

### 1. 安装依赖

```bash
# 安装必需依赖
pip install python-dotenv

# 选择一种 LLM 调用方式（推荐 langchain）
pip install langchain langchain-community

# 或者直接使用 DashScope SDK
pip install dashscope
```

### 2. 配置 API Key

**方法一：使用 .env 文件（推荐）**

在项目根目录（`main/`）创建 `.env` 文件：

```env
DASHSCOPE_API_KEY=sk-your-actual-api-key-here
```

**方法二：设置环境变量**

Windows PowerShell:
```powershell
$env:DASHSCOPE_API_KEY="sk-your-api-key-here"
```

Linux/Mac:
```bash
export DASHSCOPE_API_KEY="sk-your-api-key-here"
```

## 使用示例

### 基本使用

```python
from profile_schema import init_profile
from profile_extractor import update_profile, check_api_key

# 检查 API Key 配置
key_info = check_api_key()
print(key_info['message'])

# 初始化空画像
profile = init_profile()

# 从对话中提取画像
conversation = "你好，我是石家庄人，今年68岁了"
profile = update_profile(conversation, profile)

# 查看更新后的画像
import json
print(json.dumps(profile, ensure_ascii=False, indent=2))
```

### 运行测试

```bash
cd code_new
python test_profile_extraction.py
```

## 用户画像结构

系统提取6个维度的用户画像：

1. **demographics（人口统计）**: 年龄、性别、城市、教育、婚姻状况
2. **health（健康状况）**: 慢性疾病、行动能力、睡眠质量、用药情况
3. **cognitive（认知能力）**: 记忆状况、数字设备使用能力、表达流畅度
4. **emotional（情感状态）**: 基础情绪、孤独感、焦虑程度
5. **lifestyle（生活方式）**: 居住安排、日常作息、兴趣爱好
6. **preferences（偏好设置）**: 沟通风格、服务渠道偏好、隐私敏感度

## 文件说明

- `profile_schema.py`: 用户画像结构定义（使用 Pydantic 2.x）
- `profile_extractor.py`: 画像提取逻辑（支持 langchain 和 DashScope SDK）
- `requirements.txt`: Python依赖包列表
- `test_profile_extraction.py`: 测试脚本

## 注意事项

1. 确保已正确配置 `DASHSCOPE_API_KEY`
2. `.env` 文件应放在项目根目录（`main/`），不是 `code_new/` 目录
3. 代码会自动选择可用的 LLM 调用方式（优先使用 langchain）
4. 如果遇到导入错误，请检查依赖是否正确安装

## 与旧版本的区别

- ✅ 使用 Pydantic 2.x（而不是 1.x）
- ✅ 支持两种 LLM 调用方式（自动选择）
- ✅ 更好的错误处理和提示
- ✅ 代码结构更清晰

