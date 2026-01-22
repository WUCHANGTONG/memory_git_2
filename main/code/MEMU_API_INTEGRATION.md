# memU Cloud API 集成文档

## 📚 参考资源

- **GitHub 仓库**: https://github.com/NevaMind-AI/memU
- **memU Cloud**: https://memu.pro
- **API 文档**: 参考 SERVICE_API.md（在 GitHub 仓库中）

## 🔑 核心 API 接口

根据 memU GitHub 仓库和文档，memU 提供两种使用方式：

### 方式1: memU Cloud API（云端服务）

#### 1. Python SDK 安装

```bash
pip install memu-py
```

**注意**: 包名是 `memu-py`，不是 `memu`

#### 2. 客户端初始化

```python
from memu import MemuClient

memu_client = MemuClient(
    base_url="https://api.memu.so",  # memU Cloud API 地址
    api_key="YOUR_MEMU_API_KEY"
)
```

### 方式2: memU Service（自托管或本地使用）

#### 1. Python SDK 安装

```bash
pip install memu
```

**注意**: 包名是 `memu`（不是 `memu-py`）

#### 2. Service 初始化

```python
from memu import Service

# 需要配置 LLM provider（如 OpenAI）
service = Service(
    api_key="YOUR_MEMU_API_KEY",  # memU API Key
    # 可能需要其他配置参数
)
```
```

### 3. 核心 API 方法

#### 方式1: memU Cloud API（异步任务模式）

##### 3.1 `memorize_conversation()` - 存储记忆（异步）

**功能**: 提交记忆提取任务，异步处理对话内容

**参数**:
- `conversation`: 对话消息列表
- `user_id`: 用户ID（用于隔离）
- `user_name`: 用户名（可选）
- `agent_id`: Agent ID（可选）
- `agent_name`: Agent 名称（可选）
- `session_date`: 会话日期（可选）

**返回**: `task_id`（任务ID）

**注意**: 这是异步任务，需要轮询任务状态

```python
# 示例
task_id = await memu_client.memorize_conversation(
    conversation=[
        {"role": "user", "content": "我是石家庄人，今年68岁了"},
        {"role": "assistant", "content": "您好！很高兴认识您"}
    ],
    user_id="user_001",
    user_name="测试用户"
)
```

##### 3.2 `get_task_status(task_id)` - 查询任务状态

**功能**: 查询记忆提取任务的状态

**参数**:
- `task_id`: 任务ID

**返回**: 任务状态（"PENDING", "DONE", "FAILED" 等）

```python
# 示例
status = await memu_client.get_task_status(task_id)
```

##### 3.3 `retrieve_related_memory_items()` - 检索记忆

**功能**: 检索相关的记忆项

**参数**:
- `query`: 查询内容
- `user_id`: 用户ID（用于过滤）
- `where`: 过滤条件（可选）
- `top_k`: 返回数量限制（可选）

**返回**: 相关记忆项、资源、分类等

```python
# 示例
result = await memu_client.retrieve_related_memory_items(
    query="用户的偏好和习惯",
    user_id="user_001",
    where={"user_id": "user_001"},
    top_k=10
)
```

#### 方式2: memU Service（同步模式）

##### 3.1 `memorize()` - 提取和存储记忆（同步）

**功能**: 处理输入资源并提取结构化记忆

**参数**:
- `resource_url`: 文件路径或 URL（可选）
- `resource_content`: 直接传入内容（可选）
- `modality`: 模态类型（"conversation" | "document" | "image" | "video" | "audio"）
- `user`: 用户信息字典（如 `{"user_id": "123"}`）

**返回**: 包含 resource、items、categories 的字典

```python
# 示例
result = await service.memorize(
    resource_content=json.dumps(conversation_data),
    modality="conversation",
    user={"user_id": "user_001"}
)

# 返回：
# {
#     "resource": {...},      # 存储的资源元数据
#     "items": [...],         # 提取的记忆项
#     "categories": [...]     # 更新的类别摘要
# }
```

##### 3.2 `retrieve()` - 查询记忆（同步）

**功能**: 检索相关记忆

**参数**:
- `queries`: 查询列表（格式：`[{"role": "user", "content": {"text": "..."}}]`）
- `where`: 过滤条件（如 `{"user_id": "123"}`）
- `method`: 检索方法（"rag" 快速检索 或 "llm" 深度检索）

**返回**: 包含 categories、items、resources 的字典

```python
# 示例
result = await service.retrieve(
    queries=[
        {"role": "user", "content": {"text": "用户画像信息"}}
    ],
    where={"user_id": "user_001"},
    method="rag"  # 或 "llm"
)

# 返回：
# {
#     "categories": [...],     # 相关类别（RAG 方式包含相似度分数）
#     "items": [...],          # 相关记忆项
#     "resources": [...],      # 相关原始资源
#     "next_step_query": "..." # 重写的查询（如果适用）
# }
```

### 4. 异步任务处理流程

memU 的 `memorize` 是异步任务模式：

1. **提交任务**: 调用 `memorize_conversation()` 获得 `task_id`
2. **轮询状态**: 使用 `get_task_status()` 查询任务状态
3. **等待完成**: 当状态为 "DONE" 时，任务完成
4. **检索记忆**: 使用 `retrieve_related_memory_items()` 获取提取的记忆

## 🔄 集成策略

### 方案1: 完全异步集成（推荐）

- 提交记忆任务后立即返回，不等待完成
- 后台轮询任务状态
- 任务完成后更新本地缓存

**优点**: 不阻塞主流程
**缺点**: 需要处理异步逻辑和任务状态管理

### 方案2: 同步等待（简单）

- 提交任务后轮询直到完成
- 完成后立即检索记忆
- 更新本地缓存

**优点**: 逻辑简单
**缺点**: 可能阻塞主流程

### 方案3: 仅使用本地缓存（当前实现）

- 不使用 memU API，仅使用本地缓存
- 后续可以逐步迁移到 memU

**优点**: 简单可靠，无外部依赖
**缺点**: 缺少 memU 的智能记忆提取能力

## 📝 集成实现建议

### 1. 在 `memory_store.py` 中添加 memU 支持

```python
class MemoryStore:
    def __init__(self, base_path: str = "code/data", use_memu: bool = False):
        # ... 现有代码 ...
        
        # memU 客户端（可选）
        self.memu_client = None
        self.use_memu = use_memu
        
        if use_memu:
            try:
                from memu import MemuClient
                api_key = os.getenv("MEMU_API_KEY", "")
                if api_key:
                    self.memu_client = MemuClient(
                        base_url="https://api.memu.so",
                        api_key=api_key
                    )
            except ImportError:
                print("⚠️  memu-py 未安装，将仅使用本地缓存")
                self.use_memu = False
    
    async def save_profile_to_memu(self, user_id: str, profile: Dict[str, Any]):
        """保存画像到 memU（异步）"""
        if not self.memu_client:
            return None
        
        # 将画像转换为对话格式
        profile_text = json.dumps(profile, ensure_ascii=False)
        conversation = [
            {"role": "user", "content": f"用户画像信息：{profile_text}"}
        ]
        
        try:
            task_id = await self.memu_client.memorize_conversation(
                conversation=conversation,
                user_id=user_id
            )
            return task_id
        except Exception as e:
            print(f"⚠️  memU API 保存失败: {e}")
            return None
    
    async def load_profile_from_memu(self, user_id: str) -> Dict[str, Any]:
        """从 memU 加载画像（异步）"""
        if not self.memu_client:
            return {}
        
        try:
            result = await self.memu_client.retrieve_related_memory_items(
                query="用户画像信息",
                user_id=user_id,
                where={"user_id": user_id}
            )
            # 解析 result 并转换为画像格式
            # ... 解析逻辑 ...
            return {}
        except Exception as e:
            print(f"⚠️  memU API 加载失败: {e}")
            return {}
```

### 2. 处理异步调用

由于 memU API 是异步的，需要：

- **选项A**: 使用 `asyncio.run()` 包装异步调用（同步函数中）
- **选项B**: 将相关方法改为 `async def`（需要修改调用方）
- **选项C**: 使用后台任务队列（复杂但更优雅）

### 3. Fallback 机制

```python
def save_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
    # 1. 先保存到本地缓存（确保数据不丢失）
    local_success = self._save_profile_local(user_id, profile)
    
    # 2. 尝试保存到 memU（如果启用）
    if self.use_memu and self.memu_client:
        try:
            # 异步提交任务（不等待完成）
            asyncio.create_task(self.save_profile_to_memu(user_id, profile))
        except Exception as e:
            print(f"⚠️  memU 提交失败，已保存到本地缓存: {e}")
    
    return local_success
```

## ⚠️ 注意事项

1. **异步任务**: `memorize` 是异步的，需要处理任务状态轮询
2. **API Key**: 需要从环境变量 `MEMU_API_KEY` 读取
3. **错误处理**: API 调用失败时，必须 fallback 到本地缓存
4. **用户隔离**: 使用 `user_id` 参数确保多用户数据隔离
5. **数据格式**: 需要将画像转换为 memU 可接受的格式（对话或文档）

## 🚀 下一步行动

### 步骤1: 确认使用方式

根据你的需求选择：

- **memU Cloud API** (`memu-py`): 如果使用云端服务，需要 API Key
- **memU Service** (`memu`): 如果自托管或本地使用

### 步骤2: 安装和测试

```bash
# 方式1: Cloud API
pip install memu-py

# 方式2: Service
pip install memu
```

创建测试脚本验证 API 连接：

```python
# test_memu_connection.py
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# 测试 Cloud API
async def test_cloud_api():
    try:
        from memu import MemuClient
        client = MemuClient(
            base_url="https://api.memu.so",
            api_key=os.getenv("MEMU_API_KEY", "")
        )
        print("✅ memU Cloud API 客户端初始化成功")
        return True
    except Exception as e:
        print(f"❌ memU Cloud API 初始化失败: {e}")
        return False

# 测试 Service
async def test_service():
    try:
        from memu import Service
        service = Service(api_key=os.getenv("MEMU_API_KEY", ""))
        print("✅ memU Service 初始化成功")
        return True
    except Exception as e:
        print(f"❌ memU Service 初始化失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_cloud_api())
    # asyncio.run(test_service())
```

### 步骤3: 逐步集成

1. 先实现 `save_profile_to_memu`
2. 再实现 `load_profile_from_memu`
3. 测试验证 fallback 机制

### 步骤4: 查阅官方文档

- **GitHub**: https://github.com/NevaMind-AI/memU
- **文档**: 查看仓库中的 `SERVICE_API.md` 或 `docs/` 目录
- **示例**: 查看 `examples/` 目录中的示例代码

## 📌 当前状态

- ✅ 本地缓存功能已完成并测试通过
- ⏳ memU API 集成待实现
- 📝 需要确认准确的 API 接口和参数格式

---

**建议**: 先查阅 memU 官方文档或示例代码，确认准确的 API 接口后再开始集成。

