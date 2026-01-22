# memU API 问题根本原因分析

## 📅 分析时间
2026-01-22

## 🎯 核心问题（一句话总结）

**MemuClient 初始化时缺少项目上下文绑定（project_slug/project_id），导致后端无法识别请求属于哪个 Memory 项目，即使 API Key 是正确的 Memory Key。**

## 🔍 问题详细分析

### 1. 错误信息解读

**错误信息**：
```
API key does not come from a Memory project
```

**错误码**：`400 BAD_REQUEST`

**真实含义**：
- ❌ **不是**：API Key 本身错误或不是 Memory Key
- ✅ **实际是**：API Key 是正确的，但请求缺少项目上下文，后端无法判断这个 Key 属于哪个 Memory 项目

### 2. 当前代码的问题点

#### 问题1️⃣：客户端初始化缺少项目参数（最致命）

**当前代码**：
```python
client = MemuClient(
    base_url="https://api.memu.so",
    api_key=api_key
)
```

**问题**：
- 没有传入 `project_slug`、`project_id` 或 `workspace_id`
- 后端收到请求时，无法确定这个 API Key 属于哪个 Memory 项目
- 即使 API Key 是正确的 Memory Key，也无法通过验证

**memU 系统架构理解**：
- memU Cloud 支持多个项目/工作空间
- 同一个账户可能有多个 Memory 项目
- API Key 可能关联到多个项目，需要通过项目标识来明确上下文

#### 问题2️⃣：agent_id 使用测试值

**当前代码**：
```python
agent_id="test_agent_001",
agent_name="测试Agent"
```

**问题**：
- 使用了不存在的测试 agent_id
- memU 的 Memory 功能是绑定到具体 Agent 的
- 如果 agent_id 不存在于指定的项目中，请求可能被拒绝

**memU 系统理解**：
- Memory 不是全局的，而是绑定到具体的 Agent
- 每个 Memory 项目可能有多个 Agent
- agent_id 必须在项目中真实存在

#### 问题3️⃣：所有接口都需要项目上下文

**影响范围**：
- `memorize_conversation()` - 存储记忆
- `retrieve_related_memory_items()` - 检索记忆项
- `retrieve_default_categories()` - 获取默认类别
- `get_task_status()` - 查询任务状态

**原因**：
- 所有这些操作都需要知道在哪个项目/Agent 的上下文中执行
- 缺少项目上下文会导致所有接口都返回相同的错误

### 3. SDK 参数支持分析

**MemuClient.__init__ 签名**：
```python
(self, base_url: str = None, api_key: str = None, timeout: float = 30.0, max_retries: int = 3, **kwargs)
```

**关键发现**：
- ⚠️ **SDK 不支持直接传入 `project_slug`**
- ❌ `**kwargs` 会被传递给 `httpx.Client`，而 `httpx.Client` 不接受 `project_slug` 参数
- ❌ 尝试传入 `project_slug` 会报错：`TypeError: Client.__init__() got an unexpected keyword argument 'project_slug'`

**SDK 源码分析**：
```python
# SDK 的 __init__ 方法
def __init__(self, base_url, api_key, timeout=30.0, max_retries=3, **kwargs):
    # ...
    client_kwargs = {
        "timeout": self.timeout,
        "headers": {...},
        **kwargs,  # 所有 kwargs 都传给 httpx.Client
    }
    self._client = httpx.Client(**client_kwargs)  # 这里会失败
```

**SDK 使用的 endpoint**：
- 当前 SDK 使用：`api/v2/memory/memorize`
- 可能需要：`api/v3/memory/{project_slug}/memorize` 或类似格式

**问题**：
1. SDK 版本（0.2.2）可能不支持项目上下文
2. 项目上下文可能需要通过其他方式传递（请求头、URL 路径、请求体）
3. 需要检查 SDK 是否有其他方式设置项目上下文

### 4. 项目标识信息

**从控制台获取的信息**：
- Project Slug: `872227535-org-proj-26012201`
- 这个 slug 需要在初始化时传入

**可能的解决方案**：

由于 SDK 不支持直接传入 `project_slug`，可能需要：

1. **通过请求头传递**：
```python
# 需要修改 SDK 或使用自定义请求
headers = {
    "Authorization": f"Bearer {api_key}",
    "X-Project-Slug": "872227535-org-proj-26012201"  # 或其他 header 名
}
```

2. **通过 URL 路径传递**：
```python
# SDK 当前使用: api/v2/memory/memorize
# 可能需要: api/v3/memory/{project_slug}/memorize
# 这需要修改 SDK 的 endpoint 构建逻辑
```

3. **通过请求体传递**：
```python
# 在 MemorizeRequest 中添加 project_slug 字段
# 需要检查 MemorizeRequest 模型是否支持
```

4. **升级或修改 SDK**：
- 当前 SDK 版本：0.2.2
- 可能需要更新到支持项目上下文的版本
- 或需要修改 SDK 源码

### 5. agent_id 的真实性要求

**当前问题**：
- 使用 `agent_id="test_agent_001"` 这样的测试值
- 这个 agent 在项目中不存在

**正确做法**：
1. 在 memU 控制台查看当前 Memory 项目中已有的 agent_id
2. 或创建一个新的 agent，使用真实的 agent_id
3. 使用控制台中真实存在的 agent_id

**为什么重要**：
- Memory 功能是 Agent 级别的
- 每个 Agent 有自己独立的记忆空间
- 不存在的 agent_id 会导致请求失败

## 📊 问题根源总结

### 技术层面

1. **架构设计**：
   - memU 采用多项目/多 Agent 架构
   - 每个请求都需要明确的项目上下文
   - API Key 可能关联多个项目，需要项目标识来区分

2. **SDK 实现**：
   - SDK 可能支持项目参数，但文档不明确
   - 需要通过 `**kwargs` 传递，或检查源码确认参数名

3. **API 设计**：
   - 后端需要项目上下文来验证请求
   - 缺少上下文时返回误导性的错误信息

### 使用层面

1. **配置不完整**：
   - 只配置了 API Key，缺少项目标识
   - 缺少真实的 agent_id

2. **理解偏差**：
   - 误以为 API Key 错误，实际是缺少项目上下文
   - 误以为可以随意使用 agent_id

## 🎯 解决方案方向

### 必须做的修改

1. **添加项目标识**：
   - 在 MemuClient 初始化时传入 `project_slug`
   - 从环境变量读取：`MEMU_PROJECT_SLUG`

2. **使用真实 agent_id**：
   - 从控制台获取真实的 agent_id
   - 或创建新的 agent 并使用其 ID

3. **更新所有测试**：
   - 所有 API 调用都需要项目上下文
   - 确保所有测试使用相同的项目配置

### 需要验证的点

1. ✅ **SDK 不支持直接传入 `project_slug`**（已验证）
2. ❓ **项目上下文如何传递？**（请求头、URL 路径、请求体？）
3. ❓ **如何获取真实的 agent_id？**（需要从控制台获取）
4. ❓ **SDK 版本是否与 API 版本匹配？**（当前 0.2.2，API 可能需要 v3）
5. ❓ **MemorizeRequest 模型是否支持 project_slug 字段？**
6. ❓ **是否需要修改 SDK 源码或使用自定义请求？**

## 📝 下一步行动

1. **检查 MemorizeRequest 模型**：
   - 查看 `MemorizeRequest` 是否支持 `project_slug` 字段
   - 如果支持，可以在请求体中传递

2. **检查 API 文档**：
   - 确认 memU Cloud API v3 如何传递项目上下文
   - 是请求头、URL 路径还是请求体？

3. **获取真实配置**：
   - 从控制台获取真实的 agent_id
   - 确认 project_slug 的正确格式：`872227535-org-proj-26012201`

4. **可能的解决方案**：
   - 方案A：修改 SDK 源码，添加项目上下文支持
   - 方案B：使用自定义 HTTP 请求，绕过 SDK
   - 方案C：升级 SDK 到支持项目上下文的版本
   - 方案D：在请求体中添加 project_slug（如果模型支持）

5. **测试验证**：
   - 先测试单一接口（memorize_conversation）
   - 使用真实的 agent_id
   - 验证项目上下文传递方式

## 🔗 相关文档

- `MEMU_STORAGE_TEST_RESULTS.md` - 之前的测试结果
- `MEMU_AUTH_HEADER_TEST.md` - Authorization header 测试结果

