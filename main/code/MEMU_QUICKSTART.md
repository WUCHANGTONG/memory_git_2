# MemU 快速开始指南

## 🚀 5 分钟快速部署

### 步骤 1：配置环境变量

确保在 `memory/.env` 文件中设置了 DashScope API Key：

```bash
DASHSCOPE_API_KEY=sk-your-actual-api-key-here
```

### 步骤 2：安装 MemU

```bash
# 进入 memU-main 目录
cd memU-main

# 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell

# 安装 memU
pip install -e .
```

### 步骤 3：测试配置

```bash
# 运行 DashScope 测试脚本
python test_dashscope.py
```

**预期输出**：
```
✅ API Key 已加载
✅ MemoryService 初始化成功
✅ 记忆提取成功
✅ 检索成功
```

---

## 📝 基本使用示例

### 示例 1：处理对话并提取记忆

```python
import asyncio
from memu.app import MemoryService
import os
from dotenv import load_dotenv

load_dotenv("../memory/.env")  # 加载环境变量

async def main():
    # 初始化服务
    service = MemoryService(
        llm_profiles={
            "default": {
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": os.getenv("DASHSCOPE_API_KEY"),
                "chat_model": "qwen-max",
                "client_backend": "http"
            }
        },
        database_config={
            "metadata_store": {"provider": "inmemory"},
        },
    )
    
    # 处理对话文件
    result = await service.memorize(
        resource_url="path/to/conversation.json",
        modality="conversation",
        user={"user_id": "user_123"}
    )
    
    print(f"提取了 {len(result['items'])} 个记忆条目")
    print(f"生成了 {len(result['categories'])} 个类别")

asyncio.run(main())
```

### 示例 2：检索记忆

```python
# 检索相关记忆
queries = [
    {"role": "user", "content": {"text": "用户的偏好是什么？"}}
]

result = await service.retrieve(
    queries=queries,
    where={"user_id": "user_123"}
)

# 查看检索结果
for item in result['items']:
    print(f"[{item['memory_type']}] {item['summary']}")
```

---

## 🔧 常用配置

### 模型选择

```python
# 最强性能（推荐用于复杂任务）
"chat_model": "qwen-max"

# 平衡性能和速度
"chat_model": "qwen-plus"

# 最快速度（适合简单任务）
"chat_model": "qwen-turbo"
```

### 检索方法

```python
# RAG 检索（快速，基于向量相似度）
service.retrieve_config.method = "rag"

# LLM 检索（深度理解，但较慢）
service.retrieve_config.method = "llm"
```

---

## 📚 下一步

- 📖 查看完整部署计划：`MEMU_DEPLOYMENT_PLAN.md`
- 🔍 探索示例代码：`memU-main/examples/`
- 📝 阅读 MemU 文档：`memU-main/README_zh.md`

---

## ❓ 常见问题

**Q: 需要数据库吗？**  
A: 不需要。使用 `inmemory` 存储模式即可开始，无需数据库。

**Q: 支持哪些模型？**  
A: 支持 DashScope（通义千问）的所有模型，包括 qwen-max、qwen-plus、qwen-turbo 等。

**Q: 如何迁移到生产环境？**  
A: 将 `inmemory` 改为 PostgreSQL + pgvector，参考 `MEMU_DEPLOYMENT_PLAN.md`。

