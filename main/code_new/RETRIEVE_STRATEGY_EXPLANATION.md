# memU Retrieve 查询策略原理分析

## 问题背景

在使用 `retrieve()` 查询用户画像时，发现 `items` 为空，只能查到 `resources` 层的文件。需要分析：
1. retrieve 查询策略的工作原理
2. 为什么只能查到资源层文件
3. 是查询策略的原因，还是保存时的问题

## 一、memU 的三层存储架构

memU 采用**三层渐进式存储架构**：

```
Resources (资源层)
    ↓ 提取
Items (记忆项层)
    ↓ 分类
Categories (类别层)
```

### 1. Resources（资源层）
- **存储内容**：原始文件（JSON、TXT、图片等）
- **特点**：完整保存原始数据，包含所有信息
- **用途**：作为数据源，供后续提取和处理

### 2. Items（记忆项层）
- **存储内容**：从 resources 中提取的**结构化记忆项**
- **特点**：通过 LLM 从原始文档中提取的语义化记忆片段
- **格式**：每条 item 是一个独立的、自包含的记忆描述（如："用户喜欢Python编程"）
- **用途**：用于语义搜索和记忆检索

### 3. Categories（类别层）
- **存储内容**：对 items 的**语义分类和摘要**
- **特点**：将相关的 items 组织到不同类别中，并生成类别摘要
- **用途**：提供更高层次的记忆组织

## 二、memorize（保存）流程

当调用 `memorize()` 保存用户画像时，memU 会执行以下流程：

```python
# 1. 资源摄取 (ingest_resource)
#    读取文件内容，保存到 resources 表

# 2. 预处理 (preprocess_multimodal)  
#    如果是多模态内容，进行预处理

# 3. 提取记忆项 (extract_items)
#    使用 LLM 从文档中提取结构化记忆项
#    这是关键步骤！会调用 LLM 分析文档内容

# 4. 分类和持久化 (categorize_items)
#    将提取的 items 分配到 categories
#    创建 items 和 relations

# 5. 更新类别摘要 (persist_index)
#    更新 categories 的摘要信息
```

### 关键点：extract_items 步骤

在 `_memorize_extract_items` 中，memU 会：
1. 读取文档内容（JSON 文本）
2. 调用 LLM，使用特定的 prompt 提取记忆项
3. 期望 LLM 返回 JSON 格式的记忆项列表

**问题可能出现在这里**：
- 如果文档是**纯 JSON 格式的画像数据**（如我们的 profile JSON），LLM 可能：
  - 无法正确理解 JSON 结构
  - 提取的记忆项格式不符合预期
  - 或者根本没有提取到有效的记忆项

## 三、retrieve（查询）流程

`retrieve()` 采用**分层渐进式检索策略**：

### 检索流程（RAG 方法）

```
1. 查询意图路由 (route_intention)
   ↓
2. 检索 Categories（如果启用）
   - 使用向量相似度搜索
   - 如果找到足够信息，可能提前停止
   ↓
3. 充分性检查 (sufficiency_check)
   - LLM 判断当前结果是否足够
   - 如果足够，停止检索
   ↓
4. 检索 Items（如果启用且上一步继续）
   - 在相关 categories 中搜索 items
   - 使用向量相似度搜索
   ↓
5. 充分性检查
   ↓
6. 检索 Resources（如果启用且上一步继续）
   - 搜索原始资源文件
   - 使用向量相似度搜索
```

### 关键配置

```python
retrieve_config = {
    "method": "rag",  # 或 "llm"
    "category": {
        "enabled": True,  # 默认启用
        "top_k": 5
    },
    "item": {
        "enabled": True,  # 默认启用
        "top_k": 5
    },
    "resource": {
        "enabled": True,  # 默认启用
        "top_k": 5
    },
    "sufficiency_check": True  # 充分性检查
}
```

### 为什么 items 可能为空？

**原因 1：保存时没有成功提取 items**
- 如果 `memorize()` 时 LLM 无法从 JSON 文档中提取有效的记忆项
- 那么数据库中就没有 items 记录
- `retrieve()` 自然找不到 items

**原因 2：语义搜索不匹配**
- 即使有 items，但查询 "用户 {user_id} 的画像信息" 与 items 的语义不匹配
- 向量相似度搜索找不到相关 items
- 但 resources 的 caption 或 embedding 可能匹配

**原因 3：充分性检查提前停止**
- 如果在 categories 层就认为信息足够，可能不会继续检索 items
- 但这种情况应该会有 categories，不会只有 resources

**原因 4：查询策略的分层特性**
- retrieve 是**语义搜索**，不是精确匹配
- 如果 items 的 embedding 与查询不相似，就找不到
- 但 resources 可能因为文件名、路径等元数据被找到

## 四、当前代码的问题分析

### 保存阶段（save_profile）

```python
result = await service.memorize(
    resource_url=str(temp_file),
    modality="document",
    user={"user_id": user_id}
)
```

**可能的问题**：
1. JSON 格式的画像数据可能无法被 LLM 正确解析为记忆项
2. 提取的 items 可能为空或格式不正确
3. 需要检查 `result.get("items")` 是否为空

### 查询阶段（load_profile）

```python
result = await service.retrieve(
    queries=[{"role": "user", "content": {"text": f"用户 {user_id} 的画像信息"}}],
    where={"user_id": user_id}
)
```

**可能的问题**：
1. 查询文本 "用户 {user_id} 的画像信息" 可能不够具体
2. 如果 items 为空，retrieve 会跳过 items 层，直接到 resources 层
3. resources 可能因为文件路径包含 "profile" 而被找到

## 五、解决方案

### 方案 1：检查保存时是否生成了 items

在 `save_profile` 中添加检查：

```python
result = await service.memorize(...)
items_count = len(result.get("items", []))
if items_count == 0:
    print(f"[WARN] 画像保存时未提取到 items，可能无法被语义搜索找到")
```

### 方案 2：直接查询 resources（当前已实现）

如果 items 为空，直接通过 database 查询 resources：

```python
# 如果 retrieve 没有返回 resources，直接查询 database
store = service._get_database()
where_filters = {"user_id": user_id}
all_resources = store.resource_repo.list_resources(where_filters)
```

### 方案 3：改进查询策略

1. **使用更具体的查询**：
   ```python
   queries = [{"role": "user", "content": {"text": "用户画像 profile"}}]
   ```

2. **禁用充分性检查**（如果需要完整结果）：
   ```python
   retrieve_config={"method": "rag", "sufficiency_check": False}
   ```

3. **强制检索所有层**：
   ```python
   retrieve_config={
       "method": "rag",
       "category": {"enabled": True},
       "item": {"enabled": True},
       "resource": {"enabled": True}
   }
   ```

### 方案 4：改进保存策略

如果 JSON 格式无法被正确提取，可以考虑：

1. **使用 conversation modality**：
   ```python
   # 将画像转换为对话格式
   conversation = [{"role": "user", "content": json.dumps(profile)}]
   # 然后使用 conversation modality
   ```

2. **手动创建 memory items**：
   ```python
   # 使用 create_memory_item 直接创建 items
   await service.create_memory_item(
       memory_type="profile",
       memory_content=json.dumps(profile),
       memory_categories=["User Profile"]
   )
   ```

## 六、结论

**为什么只能查到 resources？**

**主要原因**：保存时可能没有成功提取 items，或者提取的 items 与查询语义不匹配。

**具体原因**：
1. ✅ **保存阶段**：JSON 格式的画像数据可能无法被 LLM 正确提取为记忆项
2. ✅ **查询阶段**：即使有 items，语义搜索也可能找不到（向量不匹配）
3. ✅ **查询策略**：retrieve 的分层策略会跳过空的 items 层，直接到 resources 层

**解决方向**：
- 检查保存时是否生成了 items（添加调试信息）
- 如果 items 为空，使用直接查询 resources 的备选方案（已实现）
- 考虑改进保存策略，确保 items 被正确提取

## 七、验证方法

1. **检查保存结果**：
   ```python
   result = await service.memorize(...)
   print(f"items: {len(result.get('items', []))}")
   print(f"resources: {len(result.get('resources', []))}")
   ```

2. **检查数据库中的 items**：
   ```python
   store = service._get_database()
   items = store.memory_item_repo.list_items({"user_id": user_id})
   print(f"数据库中的 items 数量: {len(items)}")
   ```

3. **检查 retrieve 的中间结果**：
   查看调试信息中的 `category_hits`、`item_hits`、`resource_hits`

