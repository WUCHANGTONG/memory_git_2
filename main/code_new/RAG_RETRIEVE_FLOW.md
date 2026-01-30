# RAG 检索流程详解

## 概述

RAG (Retrieval-Augmented Generation) 检索方式使用**向量嵌入（embedding）和余弦相似度**来进行快速、可扩展的记忆检索。

## 完整流程

```
retrieve(queries, where={"user_id": "3"})
    ↓
【初始化阶段】
提取查询: "用户 3 的画像信息"
规范化 where: {"user_id": "3"}
选择 workflow: "retrieve_rag"  ← 关键：使用 RAG 工作流
构建初始 state
    ↓
【Workflow 执行】
    ↓
Step 1: route_intention (路由意图判断)
  - 使用 LLM 判断是否需要检索
  - 重写查询（解决代词指代等）
  - 输出: needs_retrieval, rewritten_query, active_query
    ↓
Step 2: route_category (Tier 1 - 类别检索) 🔑 向量检索
  - 从数据库加载所有类别（应用 where 过滤）
  - 将查询转换为向量: embed("用户 3 的画像信息")
  - 将类别摘要转换为向量: embed(category.summary)
  - 使用余弦相似度计算: cosine_similarity(query_vec, category_vec)
  - 返回 top_k 个最相关的类别（带相似度分数）
  - 输出: category_hits [(category_id, score), ...], query_vector
    ↓
Step 3: sufficiency_after_category (类别充分性检查)
  - 使用 LLM 判断类别信息是否足够
  - 如果足够 → proceed_to_items = False，提前结束
  - 如果不够 → 重写查询，proceed_to_items = True，继续
  - 如果需要继续，重新计算 query_vector（基于重写后的查询）
    ↓
Step 4: recall_items (Tier 2 - 记忆项检索) 🔑 向量检索
  - 从数据库加载所有 items（应用 where 过滤）
  - 使用已有的 query_vector（或重新计算）
  - 调用 vector_search_items(query_vec, top_k, where)
    - 在数据库中执行: SELECT item_id, 1 - cosine_distance(embedding, query_vec) AS score
    - 按距离排序，返回 top_k
  - 返回 top_k 个最相关的 items（带相似度分数）
  - 输出: item_hits [(item_id, score), ...]
    ↓
Step 5: sufficiency_after_items (记忆项充分性检查)
  - 使用 LLM 判断 items 信息是否足够
  - 如果足够 → proceed_to_resources = False，提前结束
  - 如果不够 → 重写查询，proceed_to_resources = True，继续
  - 如果需要继续，重新计算 query_vector（基于重写后的查询）
    ↓
Step 6: recall_resources (Tier 3 - 资源检索) 🔑 向量检索
  - 从数据库加载所有资源（应用 where 过滤）
  - 构建资源描述语料库（resource caption corpus）
  - 使用已有的 query_vector（或重新计算）
  - 对每个资源描述计算向量并执行余弦相似度搜索
  - 返回 top_k 个最相关的资源（带相似度分数）
  - 输出: resource_hits [(resource_id, score), ...]
    ↓
Step 7: build_context (构建最终响应)
  - 从 state 中提取 category_hits, item_hits, resource_hits
  - 通过 materialize_hits 转换为完整对象（包含所有字段）
  - 构建最终响应，包含:
    - needs_retrieval
    - original_query
    - rewritten_query
    - next_step_query
    - categories: [完整类别对象列表]
    - items: [完整记忆项对象列表]
    - resources: [完整资源对象列表]
    ↓
返回 response
```

## 关键步骤详解

### Step 2: route_category (RAG 方式)

```python
# 1. 获取查询向量
qvec = await embed_client.embed(["用户 3 的画像信息"])[0]

# 2. 获取所有类别（已应用 where 过滤）
category_pool = store.memory_category_repo.list_categories(where_filters)

# 3. 对每个类别的 summary 进行向量化
summary_texts = [cat.summary for cat in category_pool.values() if cat.summary]
summary_embeddings = await embed_client.embed(summary_texts)

# 4. 计算余弦相似度并排序
corpus = [(category_id, embedding) for ...]
hits = cosine_topk(qvec, corpus, k=top_k)  # 返回 [(category_id, score), ...]
```

**关键点**：
- 使用 embedding 模型将文本转换为向量
- 使用余弦相似度计算相似性（值越大越相似）
- 返回结果包含相似度分数

### Step 4: recall_items (RAG 方式)

```python
# 1. 使用已有的 query_vector（或重新计算）
qvec = state.get("query_vector")

# 2. 在数据库中执行向量搜索
item_hits = store.memory_item_repo.vector_search_items(
    qvec,                    # 查询向量
    top_k,                   # 返回数量
    where=where_filters       # 过滤条件
)

# 数据库查询（PostgreSQL 示例）:
# SELECT item_id, (1 - cosine_distance(embedding, query_vec)) AS score
# FROM memory_items
# WHERE embedding IS NOT NULL AND user_id = '3'
# ORDER BY cosine_distance(embedding, query_vec)
# LIMIT top_k
```

**关键点**：
- 直接在数据库层面执行向量搜索（如果支持）
- 使用预存储的 item.embedding 向量
- 返回结果包含相似度分数

### Step 6: recall_resources (RAG 方式)

```python
# 1. 构建资源描述语料库
corpus = self._resource_caption_corpus(store, resources=resource_pool)
# corpus = [(resource_id, caption_text), ...]

# 2. 对语料库进行向量化（如果尚未向量化）
# 3. 执行余弦相似度搜索
resource_hits = cosine_topk(qvec, corpus, k=top_k)
```

## RAG vs LLM 对比

### 核心区别

| 方面 | RAG 方式 | LLM 方式 |
|------|---------|---------|
| **Tier 1 (类别)** | 向量相似度搜索 | LLM 分析查询与类别相关性 |
| **Tier 2 (记忆项)** | 向量相似度搜索（所有 items） | LLM 分析（仅相关类别的 items） |
| **Tier 3 (资源)** | 向量相似度搜索 | LLM 分析查询与资源相关性 |
| **速度** | ⚡ 快速（纯向量计算） | 🐢 较慢（需要多次 LLM 调用） |
| **成本** | 💰 低（仅 embedding API） | 💰💰 高（多次 LLM API 调用） |
| **语义理解** | 中等（基于向量相似度） | 深度（LLM 理解上下文和细微差别） |
| **返回结果** | 包含相似度分数 | 按 LLM 推理排序（无分数） |
| **查询重写** | 仅在 sufficiency_check 时 | 在每个层级自动优化 |

### 详细对比

#### 1. route_category 步骤

**RAG 方式**：
```python
# 使用向量检索
qvec = await embed_client.embed([query])[0]
hits = await _rank_categories_by_summary(qvec, top_k, ...)
# 返回: [(category_id, similarity_score), ...]
```

**LLM 方式**：
```python
# 使用 LLM 分析
hits = await _llm_rank_categories(query, top_k, ...)
# LLM 分析所有类别，返回最相关的类别列表
# 返回: [category_object, ...] (无分数)
```

#### 2. recall_items 步骤

**RAG 方式**：
```python
# 对所有 items 进行向量搜索
item_hits = store.memory_item_repo.vector_search_items(
    qvec, top_k, where=where_filters
)
# 返回: [(item_id, similarity_score), ...]
```

**LLM 方式**：
```python
# 仅对相关类别的 items 进行 LLM 分析
category_ids = [cat["id"] for cat in category_hits]
item_hits = await _llm_rank_items(
    query, top_k, category_ids, ...
)
# 返回: [item_object, ...] (无分数)
```

#### 3. recall_resources 步骤

**RAG 方式**：
```python
# 向量搜索资源描述
resource_hits = cosine_topk(qvec, resource_corpus, k=top_k)
# 返回: [(resource_id, similarity_score), ...]
```

**LLM 方式**：
```python
# LLM 分析资源相关性
resource_hits = await _llm_rank_resources(
    query, top_k, category_hits, item_hits, ...
)
# 返回: [resource_object, ...] (无分数)
```

## RAG 方式的优势

1. **性能优势**：
   - 向量计算速度快，适合大规模数据
   - 可以充分利用数据库的向量索引（如 PostgreSQL 的 pgvector）

2. **成本优势**：
   - 只需要 embedding API 调用（比 LLM API 便宜）
   - 向量可以预先计算和缓存

3. **可扩展性**：
   - 支持百万级别的记忆项检索
   - 向量搜索可以并行化

4. **结果可解释性**：
   - 返回相似度分数，可以用于阈值过滤
   - 可以调整 top_k 来控制返回数量

## RAG 方式的局限性

1. **语义理解深度**：
   - 基于向量相似度，可能无法理解复杂的语义关系
   - 对于需要深度推理的查询，可能不如 LLM 方式准确

2. **上下文感知**：
   - 虽然支持查询重写，但主要依赖向量相似度
   - 对于需要复杂上下文理解的场景，LLM 方式可能更合适

## 实际执行示例

假设查询："用户 3 的画像信息"

### RAG 方式执行流程：

1. **route_intention**: 
   - LLM 判断：需要检索 ✓
   - 重写查询："用户 3 的画像信息"（无需重写）

2. **route_category**:
   - 查询向量化: `[0.1, 0.2, ..., 0.9]` (1536维)
   - 类别摘要向量化: 
     - "用户偏好": `[0.15, 0.18, ..., 0.85]`
     - "个人信息": `[0.12, 0.22, ..., 0.88]`
   - 余弦相似度计算:
     - "个人信息": 0.92 (最高)
     - "用户偏好": 0.78
   - 返回: `[("cat_001", 0.92), ("cat_002", 0.78)]`

3. **sufficiency_after_category**:
   - LLM 判断：类别信息不够，需要继续检索
   - 重写查询："用户 3 的画像信息，包括其基本信息、偏好设置等"

4. **recall_items**:
   - 查询向量化（基于重写后的查询）
   - 数据库向量搜索:
     ```sql
     SELECT item_id, 1 - cosine_distance(embedding, query_vec) AS score
     FROM memory_items
     WHERE user_id = '3' AND embedding IS NOT NULL
     ORDER BY cosine_distance(embedding, query_vec)
     LIMIT 5
     ```
   - 返回: `[("item_001", 0.89), ("item_002", 0.85), ...]`

5. **sufficiency_after_items**:
   - LLM 判断：信息足够，可以结束

6. **build_context**:
   - 将 item_ids 转换为完整的 item 对象
   - 构建最终响应

## 流程图对比

### RAG 方式流程图

```
查询: "用户 3 的画像信息"
    ↓
[route_intention] LLM 判断是否需要检索
    ↓
[route_category] 🔑 向量检索
  - embed(query) → query_vec
  - embed(category.summary) → category_vecs
  - cosine_similarity(query_vec, category_vecs)
  - 返回 top_k 类别 + 分数
    ↓
[sufficiency_after_category] LLM 判断是否足够
    ↓ (如果不够)
[recall_items] 🔑 向量检索
  - 使用 query_vec
  - vector_search_items(query_vec, top_k, where)
  - 数据库向量搜索（所有 items）
  - 返回 top_k items + 分数
    ↓
[sufficiency_after_items] LLM 判断是否足够
    ↓ (如果不够)
[recall_resources] 🔑 向量检索
  - 使用 query_vec
  - cosine_topk(query_vec, resource_corpus, k)
  - 返回 top_k 资源 + 分数
    ↓
[build_context] 构建最终响应
```

### LLM 方式流程图

```
查询: "用户 3 的画像信息"
    ↓
[route_intention] LLM 判断是否需要检索
    ↓
[route_category] 🔑 LLM 分析
  - LLM 分析查询与所有类别的相关性
  - 返回最相关的类别列表（无分数）
    ↓
[sufficiency_after_category] LLM 判断是否足够
    ↓ (如果不够)
[recall_items] 🔑 LLM 分析
  - 仅从相关类别的 items 中搜索
  - LLM 分析查询与 items 的相关性
  - 返回最相关的 items 列表（无分数）
    ↓
[sufficiency_after_items] LLM 判断是否足够
    ↓ (如果不够)
[recall_resources] 🔑 LLM 分析
  - LLM 分析查询与资源的相关性
  - 考虑已找到的 categories 和 items
  - 返回最相关的资源列表（无分数）
    ↓
[build_context] 构建最终响应
```

## 关键代码位置

### RAG 方式关键实现

1. **类别检索** (`_rag_route_category`):
   ```python
   # 文件: memU-main/src/memu/app/retrieve.py:260
   qvec = await embed_client.embed([state["active_query"]])[0]
   hits, summary_lookup = await self._rank_categories_by_summary(
       qvec, top_k, ctx, store, embed_client=embed_client, categories=category_pool
   )
   ```

2. **记忆项检索** (`_rag_recall_items`):
   ```python
   # 文件: memU-main/src/memu/app/retrieve.py:324
   state["item_hits"] = store.memory_item_repo.vector_search_items(
       qvec, self.retrieve_config.item.top_k, where=where_filters
   )
   ```

3. **资源检索** (`_rag_recall_resources`):
   ```python
   # 文件: memU-main/src/memu/app/retrieve.py:376
   state["resource_hits"] = cosine_topk(
       qvec, corpus, k=self.retrieve_config.resource.top_k
   )
   ```

### LLM 方式关键实现

1. **类别检索** (`_llm_route_category`):
   ```python
   # 文件: memU-main/src/memu/app/retrieve.py:546
   hits = await self._llm_rank_categories(
       state["active_query"], top_k, ctx, store,
       llm_client=llm_client, categories=category_pool
   )
   ```

2. **记忆项检索** (`_llm_recall_items`):
   ```python
   # 文件: memU-main/src/memu/app/retrieve.py:591
   state["item_hits"] = await self._llm_rank_items(
       state["active_query"], top_k, category_ids, ...
   )
   ```

3. **资源检索** (`_llm_recall_resources`):
   ```python
   # 文件: memU-main/src/memu/app/retrieve.py:644
   state["resource_hits"] = await self._llm_rank_resources(
       state["active_query"], top_k, category_hits, item_hits, ...
   )
   ```

## 总结

RAG 检索方式通过向量嵌入和余弦相似度实现了快速、可扩展的记忆检索。它特别适合：
- 大规模记忆库
- 需要快速响应的场景
- 成本敏感的应用
- 需要相似度分数的场景

与 LLM 方式相比，RAG 方式在速度和成本上有明显优势，但在深度语义理解方面可能略逊一筹。选择哪种方式取决于具体的应用场景和需求。

### 选择建议

**使用 RAG 方式，如果：**
- ✅ 需要快速响应（毫秒级）
- ✅ 记忆库规模大（> 10万条）
- ✅ 成本敏感
- ✅ 需要相似度分数进行阈值过滤
- ✅ 查询相对直接，不需要复杂推理

**使用 LLM 方式，如果：**
- ✅ 需要深度语义理解
- ✅ 查询复杂，需要上下文推理
- ✅ 记忆库规模较小（< 1万条）
- ✅ 对准确性要求高于速度
- ✅ 需要跨层级的智能关联分析

