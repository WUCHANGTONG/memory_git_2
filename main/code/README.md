# 用户画像提取系统

## 功能说明

这是一个专注于从老年人对话中提取和更新用户画像的系统。系统会分析对话内容，持续完善用户画像信息。

## 配置步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

**方法一：使用 .env 文件（推荐）**

1. 将 `env_example.txt` 复制到项目根目录（`memory` 目录），重命名为 `.env`
2. 编辑 `.env` 文件，将 `your-api-key-here` 替换为您的阿里云 DashScope API Key

```bash
# Windows PowerShell（从 memory_git 目录运行）
Copy-Item memory\code\env_example.txt memory\.env

# Linux/Mac（从 memory_git 目录运行）
cp memory/code/env_example.txt memory/.env
```

然后在 `.env` 文件中设置：
```
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

### 3. 运行测试

```bash
cd code
python agent.py
```

## 使用说明

运行 `agent.py` 后：

- 输入对话内容（模拟老年人）：系统会自动提取画像信息
- 输入 `show`：查看当前用户画像
- 输入 `exit`：退出程序并显示最终画像

### 示例对话

```
你（模拟老人）: 我今年68岁了，住在北京
🔄 正在提取画像信息...
📌 更新后的用户画像：
{
  "demographics": {
    "age": {"value": 68, "confidence": 0.9},
    "city_level": {"value": "北京", "confidence": 0.9},
    ...
  }
}
✅ 画像已更新
```

## 文件说明

- `agent.py`: 主程序，对话循环和画像更新
- `profile_extractor.py`: 画像提取器，使用LLM提取用户画像
- `profile_schema.py`: 用户画像结构定义
- `requirements.txt`: Python依赖包列表
- `env_example.txt`: 环境变量配置示例文件

## 注意事项

1. 确保已正确配置 `DASHSCOPE_API_KEY`
2. `.env` 文件应放在项目根目录（`memory` 目录），不是 `code` 目录
3. 数据文件存储在 `code/data/` 目录下（自动创建）
4. 如果遇到导入错误，请检查 langchain 版本和 ChatTongyi 的导入路径
5. 项目已从 `memory/` 移动到 `memory_git/memory/`，路径已自动适配

