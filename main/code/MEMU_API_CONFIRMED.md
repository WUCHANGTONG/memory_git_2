# memU API 接口确认总结

## ✅ 确认时间
2026-01-22

## 📋 已确认的 API 接口

### 1. 客户端初始化 ✅

**包名**: `memu-py`

**初始化方式**:
```python
from memu import MemuClient

client = MemuClient(
    base_url="https://api.memu.so",
    api_key="YOUR_MEMU_API_KEY"
)
```

**状态**: ✅ 已验证（测试脚本通过）

---

### 2. `memorize_conversation()` - 存储记忆 ✅

**功能**: 提交对话内容，异步提取结构化记忆

**关键参数**:
- `conversation`: 字符串或消息列表 `[{"role": "user", "content": "..."}]`
- `user_id`: 用户ID（必需，用于数据隔离）
- `user_name`, `agent_id`, `agent_name`, `session_date`: 可选

**返回值**: 
- `task_id`: 任务ID（用于查询状态）
- `status`: 任务状态（"PENDING"）

**特点**: 
- ✅ 异步任务模式
- ✅ 支持字符串和结构化消息两种格式
- ✅ 需要轮询任务状态

**REST API**: `POST /api/v3/memory/memorize` 或 `/api/v1/memory/memorize`

---

### 3. `get_task_status()` - 查询任务状态 ✅

**功能**: 查询记忆提取任务的处理状态

**参数**:
- `task_id`: 任务ID

**返回值**:
- `status`: "PENDING" | "COMPLETE" | "FAILED"
- `result`: 任务完成时的结果（包含 items, categories）
- `error`: 失败时的错误信息

**REST API**: `GET /api/v3/memory/memorize/status/{task_id}`

---

### 4. `retrieve_related_memory_items()` - 检索记忆项 ✅

**功能**: 基于查询检索相关的记忆项

**关键参数**:
- `query`: 查询文本
- `user_id`: 用户ID（用于过滤）
- `where`: 过滤条件（如 `{"user_id": "123"}`）
- `top_k`: 返回数量限制
- `method`: "rag"（快速）或 "llm"（深度语义）

**返回值**:
- `items`: 相关记忆项列表
- `categories`: 相关类别
- `resources`: 相关原始资源
- `scores`: 相似度分数（RAG 方法）

**REST API**: `POST /api/v3/memory/retrieve/related-memory-items`

---

### 5. `retrieve_default_categories()` - 获取默认类别 ✅

**功能**: 获取用户的所有记忆类别摘要

**参数**:
- `user_id`: 用户ID
- `include_items`: 是否包含记忆项详情
- `where`: 过滤条件

**返回值**:
- `categories`: 类别列表（包含 name, summary, items 等）

**REST API**: `POST /api/v3/memory/retrieve/default-categories`

---

### 6. `delete_memories()` - 删除记忆 ✅

**功能**: 删除指定的记忆项或类别

**参数**:
- `where`: 过滤条件
- `memory_ids`: 要删除的记忆ID列表（可选）
- `category_names`: 要删除的类别名称列表（可选）

**REST API**: `DELETE /api/v3/memory/delete`

---

## 🔄 异步任务处理流程

### 完整流程（等待完成）

1. 调用 `memorize_conversation()` 获得 `task_id`
2. 轮询 `get_task_status(task_id)` 直到状态为 "COMPLETE"
3. 从 `status["result"]` 中提取 items 和 categories

### 简化流程（不等待）

1. 调用 `memorize_conversation()` 获得 `task_id`
2. 保存 `task_id`，后续可以查询状态
3. 立即返回，不阻塞主流程

---

## 📊 数据模型

### MemoryItem（记忆项）
- `id`: 记忆项ID
- `content`: 记忆内容
- `created_at`: 创建时间
- `category`: 所属类别
- `resource_id`: 关联的资源ID

### Category（类别）
- `name`: 类别名称
- `summary`: 类别摘要
- `user_id`: 用户ID
- `items`: 该类别下的记忆项列表

### Resource（资源）
- `id`: 资源ID
- `type`: 资源类型（conversation, document 等）
- `content`: 原始内容
- `created_at`: 创建时间
- `user_id`: 用户ID

---

## 🎯 集成方案确认

### 方案1: 完全异步（推荐）

**流程**:
1. 保存到本地缓存（立即）
2. 异步提交到 memU（不等待完成）
3. 后台轮询任务状态（可选）

**优点**: 不阻塞主流程
**缺点**: 需要处理异步逻辑

### 方案2: 同步等待（简单）

**流程**:
1. 保存到本地缓存
2. 提交到 memU 并等待完成
3. 更新本地缓存（可选）

**优点**: 逻辑简单
**缺点**: 可能阻塞主流程

### 方案3: 仅本地缓存（当前）

**流程**:
1. 仅保存到本地缓存

**优点**: 简单可靠
**缺点**: 缺少 memU 的智能记忆提取能力

---

## ✅ 已确认的信息

- [x] SDK 包名: `memu-py`
- [x] 客户端类: `MemuClient`
- [x] Base URL: `https://api.memu.so`
- [x] 认证方式: API Key（通过环境变量或参数）
- [x] 异步任务模式: `memorize_conversation()` 返回 `task_id`
- [x] 用户隔离: 通过 `user_id` 参数
- [x] 对话格式: 支持字符串和消息列表两种格式
- [x] 检索方法: RAG（快速）和 LLM（深度语义）

---

## ⚠️ 待确认的信息

- [ ] 准确的参数名称和类型（需要查看实际 SDK 源码）
- [ ] 返回值的完整结构（需要实际测试）
- [ ] 错误处理的具体异常类型
- [ ] 任务状态轮询的最佳间隔时间
- [ ] 画像数据如何映射到 memU 的记忆结构

---

## 📝 下一步行动

1. **查看 SDK 源码**: 确认准确的参数名称和类型
2. **编写测试代码**: 实际调用 API 验证返回值结构
3. **设计数据映射**: 确定如何将用户画像映射到 memU 的记忆结构
4. **实现集成代码**: 在 `memory_store.py` 中添加 memU 支持
5. **测试验证**: 确保 fallback 机制正常工作

---

## 📚 参考文档

- **API 参考文档**: `MEMU_API_REFERENCE.md`（已创建）
- **集成文档**: `MEMU_API_INTEGRATION.md`（已创建）
- **测试结果**: `MEMU_CONNECTION_TEST_RESULTS.md`（已创建）

---

**状态**: ✅ API 接口已基本确认，可以开始集成  
**建议**: 先编写简单的测试代码验证 API 调用，再开始正式集成

