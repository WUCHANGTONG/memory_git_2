# memU API 接口参考文档

## 📚 文档来源

- **GitHub 仓库**: https://github.com/NevaMind-AI/memU
- **memU Cloud**: https://memu.pro
- **Python SDK**: `memu-py` (PyPI: https://pypi.org/project/memu-py/)

## 🔑 核心概念

memU 是一个长期记忆系统，支持：
- **多模态输入**: 对话、文档、图片、视频、音频
- **三层结构**: Resource（原始资源）→ Item（记忆项）→ Category（类别摘要）
- **两种检索方式**: RAG（向量检索）和 LLM（语义检索）

## 📦 SDK 安装与初始化

### 安装

```bash
pip install memu-py
```

### 客户端初始化

```python
from memu import MemuClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MemuClient(
    base_url="https://api.memu.so",  # memU Cloud API 地址
    api_key=os.getenv("MEMU_API_KEY", "")  # 从环境变量读取
)
```

## 🛠️ 核心 API 方法

### 1. `memorize_conversation()` - 存储记忆（异步）

**功能**: 提交对话内容，异步提取结构化记忆

**方法签名**:
```python
async def memorize_conversation(
    conversation: Union[str, List[Dict[str, str]]],  # 对话内容
    user_id: str,                                    # 用户ID（必需）
    user_name: Optional[str] = None,                 # 用户名（可选）
    agent_id: Optional[str] = None,                  # Agent ID（可选）
    agent_name: Optional[str] = None,               # Agent 名称（可选）
    session_date: Optional[str] = None               # 会话日期 ISO 8601（可选）
) -> Dict[str, Any]
```

**参数说明**:
- `conversation`: 
  - 字符串格式: `"User: ...\nAssistant: ..."`
  - 或消息列表: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`
- `user_id`: 用户唯一标识，用于数据隔离
- `user_name`: 用户显示名称（可选）
- `agent_id`: Agent 标识（可选）
- `agent_name`: Agent 显示名称（可选）
- `session_date`: ISO 8601 格式日期字符串（可选）

**返回值**:
```python
{
    "task_id": "xxx",      # 任务ID，用于查询状态
    "status": "PENDING",   # 任务状态
    # 其他元数据...
}
```

**使用示例**:
```python
# 方式1: 使用消息列表
result = await client.memorize_conversation(
    conversation=[
        {"role": "user", "content": "我是石家庄人，今年68岁了"},
        {"role": "assistant", "content": "您好！很高兴认识您"}
    ],
    user_id="user_001",
    user_name="测试用户"
)
task_id = result["task_id"]

# 方式2: 使用字符串格式
result = await client.memorize_conversation(
    conversation="User: 我是石家庄人\nAssistant: 您好！",
    user_id="user_001"
)
```

**REST API**: `POST /api/v3/memory/memorize` 或 `/api/v1/memory/memorize`

---

### 2. `get_task_status()` - 查询任务状态

**功能**: 查询记忆提取任务的处理状态

**方法签名**:
```python
async def get_task_status(
    task_id: str  # 任务ID
) -> Dict[str, Any]
```

**返回值**:
```python
{
    "status": "PENDING" | "COMPLETE" | "FAILED",  # 任务状态
    "result": {...},  # 任务完成时的结果（包含 items, categories 等）
    "error": "...",   # 失败时的错误信息
    # 其他状态信息...
}
```

**使用示例**:
```python
status = await client.get_task_status(task_id)
if status["status"] == "COMPLETE":
    items = status["result"].get("items", [])
    categories = status["result"].get("categories", [])
```

**REST API**: `GET /api/v3/memory/memorize/status/{task_id}`

---

### 3. `retrieve_related_memory_items()` - 检索记忆项

**功能**: 基于查询检索相关的记忆项

**方法签名**:
```python
async def retrieve_related_memory_items(
    query: str,                          # 查询内容
    user_id: Optional[str] = None,       # 用户ID（用于过滤）
    where: Optional[Dict[str, Any]] = None,  # 过滤条件
    top_k: Optional[int] = None,         # 返回数量限制
    method: Optional[str] = "rag"        # 检索方法: "rag" 或 "llm"
) -> Dict[str, Any]
```

**参数说明**:
- `query`: 查询文本，如 "用户的偏好和习惯"
- `user_id`: 用户ID，用于过滤该用户的记忆
- `where`: 额外的过滤条件，如 `{"user_id": "123", "agent_id": "456"}`
- `top_k`: 返回结果数量限制
- `method`: 
  - `"rag"`: 基于向量嵌入的快速检索（默认）
  - `"llm"`: 基于 LLM 的深度语义检索

**返回值**:
```python
{
    "items": [           # 相关记忆项列表
        {
            "id": "...",
            "content": "...",
            "created_at": "...",
            "category": "...",
            # 其他字段...
        }
    ],
    "categories": [...],  # 相关类别
    "resources": [...],   # 相关原始资源
    "scores": [...],      # 相似度分数（RAG 方法）
    # 其他信息...
}
```

**使用示例**:
```python
# RAG 检索（快速）
result = await client.retrieve_related_memory_items(
    query="用户的偏好和习惯",
    user_id="user_001",
    where={"user_id": "user_001"},
    top_k=10,
    method="rag"
)

# LLM 检索（深度语义）
result = await client.retrieve_related_memory_items(
    query="用户画像信息",
    user_id="user_001",
    method="llm"
)
```

**REST API**: `POST /api/v3/memory/retrieve/related-memory-items` 或 `/api/v1/memory/retrieve/related-memory-items`

---

### 4. `retrieve_default_categories()` - 获取默认类别

**功能**: 获取用户的所有记忆类别摘要

**方法签名**:
```python
async def retrieve_default_categories(
    user_id: Optional[str] = None,      # 用户ID
    include_items: bool = False,          # 是否包含记忆项
    where: Optional[Dict[str, Any]] = None  # 过滤条件
) -> Dict[str, Any]
```

**返回值**:
```python
{
    "categories": [
        {
            "name": "preferences",      # 类别名称
            "summary": "...",            # 类别摘要
            "items": [...],              # 记忆项（如果 include_items=True）
            # 其他字段...
        }
    ]
}
```

**使用示例**:
```python
result = await client.retrieve_default_categories(
    user_id="user_001",
    include_items=True  # 包含记忆项详情
)
```

**REST API**: `POST /api/v3/memory/retrieve/default-categories` 或 `/api/v1/memory/retrieve/default-categories`

---

### 5. `delete_memories()` - 删除记忆

**功能**: 删除指定的记忆项或类别

**方法签名**:
```python
async def delete_memories(
    where: Dict[str, Any],  # 过滤条件，如 {"user_id": "123"}
    memory_ids: Optional[List[str]] = None,  # 要删除的记忆ID列表
    category_names: Optional[List[str]] = None  # 要删除的类别名称列表
) -> Dict[str, Any]
```

**使用示例**:
```python
# 删除用户的所有记忆
await client.delete_memories(where={"user_id": "user_001"})

# 删除特定记忆项
await client.delete_memories(
    where={"user_id": "user_001"},
    memory_ids=["item_1", "item_2"]
)
```

**REST API**: `DELETE /api/v3/memory/delete` 或 `/api/v1/memory/delete`

---

## 🔄 异步任务处理流程

memU Cloud API 的 `memorize_conversation()` 是异步任务模式：

### 完整流程

```python
import asyncio
from memu import MemuClient

async def memorize_and_wait(client: MemuClient, conversation, user_id):
    # 1. 提交任务
    result = await client.memorize_conversation(
        conversation=conversation,
        user_id=user_id
    )
    task_id = result["task_id"]
    
    # 2. 轮询任务状态
    while True:
        status = await client.get_task_status(task_id)
        
        if status["status"] == "COMPLETE":
            # 任务完成，获取结果
            items = status["result"].get("items", [])
            categories = status["result"].get("categories", [])
            return items, categories
        elif status["status"] == "FAILED":
            # 任务失败
            raise Exception(f"任务失败: {status.get('error', '未知错误')}")
        else:
            # 任务进行中，等待后重试
            await asyncio.sleep(1)  # 等待1秒后重试

# 使用
client = MemuClient(api_key="...", base_url="https://api.memu.so")
items, categories = await memorize_and_wait(
    client,
    conversation=[{"role": "user", "content": "..."}],
    user_id="user_001"
)
```

### 简化流程（不等待完成）

```python
# 提交任务后立即返回，不等待完成
result = await client.memorize_conversation(...)
task_id = result["task_id"]
# 保存 task_id，后续可以查询状态
```

---

## 📊 数据模型

### MemoryItem（记忆项）

```python
{
    "id": "item_123",
    "content": "用户喜欢喝咖啡",
    "created_at": "2026-01-22T10:00:00Z",
    "category": "preferences",
    "resource_id": "resource_456",
    # 其他字段...
}
```

### Category（类别）

```python
{
    "name": "preferences",
    "summary": "用户偏好：喜欢喝咖啡，不喜欢甜食",
    "user_id": "user_001",
    "items": [...],  # 该类别下的记忆项
    # 其他字段...
}
```

### Resource（资源）

```python
{
    "id": "resource_456",
    "type": "conversation",
    "content": "...",  # 原始内容
    "created_at": "2026-01-22T10:00:00Z",
    "user_id": "user_001",
    # 其他字段...
}
```

---

## 🔐 认证

所有 API 请求都需要通过 HTTP Header 进行认证：

```
Authorization: Bearer YOUR_MEMU_API_KEY
```

SDK 会自动处理认证，只需在初始化时提供 `api_key`。

---

## ⚠️ 注意事项

1. **异步任务**: `memorize_conversation()` 是异步的，需要轮询任务状态
2. **用户隔离**: 使用 `user_id` 参数确保多用户数据隔离
3. **错误处理**: API 调用可能失败，需要处理异常和 fallback
4. **版本差异**: Cloud API 可能使用 `/api/v3/` 或 `/api/v1/` 路径
5. **数据格式**: 对话内容可以是字符串或消息列表格式

---

## 📝 集成建议

### 1. 保存用户画像到 memU

```python
async def save_profile_to_memu(client, user_id, profile):
    # 将画像转换为对话格式
    profile_text = json.dumps(profile, ensure_ascii=False)
    conversation = [
        {"role": "user", "content": f"用户画像信息：{profile_text}"}
    ]
    
    # 提交任务
    result = await client.memorize_conversation(
        conversation=conversation,
        user_id=user_id,
        user_name=f"User_{user_id}"
    )
    return result["task_id"]
```

### 2. 从 memU 加载用户画像

```python
async def load_profile_from_memu(client, user_id):
    # 检索用户画像相关的记忆
    result = await client.retrieve_related_memory_items(
        query="用户画像信息",
        user_id=user_id,
        where={"user_id": user_id},
        method="llm"  # 使用 LLM 方法获得更好的语义理解
    )
    
    # 从 result["items"] 中提取画像信息
    # 需要解析 items 的 content 字段，提取画像数据
    # ...
    return profile
```

### 3. Fallback 机制

```python
def save_profile(self, user_id, profile):
    # 1. 先保存到本地缓存（确保数据不丢失）
    local_success = self._save_profile_local(user_id, profile)
    
    # 2. 尝试保存到 memU（如果启用）
    if self.use_memu and self.memu_client:
        try:
            # 异步提交任务（不等待完成）
            asyncio.create_task(
                self.save_profile_to_memu(user_id, profile)
            )
        except Exception as e:
            print(f"memU 提交失败，已保存到本地缓存: {e}")
    
    return local_success
```

---

## 📌 参考资源

- **GitHub 仓库**: https://github.com/NevaMind-AI/memU
- **memU Cloud**: https://memu.pro
- **API 文档**: 查看 GitHub 仓库中的 `SERVICE_API.md` 或 `docs/` 目录
- **示例代码**: 查看 GitHub 仓库中的 `examples/` 目录

---

**最后更新**: 2026-01-22  
**基于**: memU GitHub 仓库和官方文档

