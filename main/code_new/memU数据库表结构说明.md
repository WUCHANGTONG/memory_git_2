# memU 数据库表结构说明

## 📊 四个表的作用

### 1. `resources` 表
**作用**：存储资源文件信息

**存储内容**：
- `url`: 资源URL或文件路径
- `modality`: 资源类型（"document", "conversation", "image", "audio" 等）
- `local_path`: 本地文件路径
- `caption`: 资源描述/标题
- `embedding`: 向量嵌入（用于相似度搜索）
- `user_id`: 用户ID（通过 scope 字段）

**用户画像存储**：
- 用户画像被转换为 JSON 文件
- 文件路径存储在 `resources.url` 和 `resources.local_path`
- `modality="document"` 表示这是一个文档资源

### 2. `memory_items` 表
**作用**：存储记忆项（从资源中提取的结构化记忆）

**存储内容**：
- `resource_id`: 关联的 `resources.id`
- `memory_type`: 记忆类型（"profile", "event", "knowledge", "behavior", "skill"）
- `summary`: 记忆摘要（LLM 提取的文本摘要）
- `embedding`: 向量嵌入
- `happened_at`: 发生时间
- `extra`: **JSONB 字段**，存储额外的结构化数据（**用户画像的完整 JSON 可能在这里**）
- `user_id`: 用户ID

**用户画像存储**：
- `memory_type="profile"` 表示这是用户画像
- `summary` 包含画像的文本摘要
- `extra` 字段可能包含完整的画像 JSON 数据

### 3. `memory_categories` 表
**作用**：存储记忆分类（用于组织记忆）

**存储内容**：
- `name`: 分类名称
- `description`: 分类描述
- `summary`: 分类摘要
- `embedding`: 向量嵌入
- `user_id`: 用户ID

**用途**：
- memU 会自动将记忆分类（如"健康信息"、"兴趣爱好"等）
- 用于组织和检索相关记忆

### 4. `category_items` 表
**作用**：存储分类和记忆项的关系（多对多关系）

**存储内容**：
- `item_id`: 关联的 `memory_items.id`
- `category_id`: 关联的 `memory_categories.id`
- `user_id`: 用户ID

**用途**：
- 将记忆项关联到分类
- 支持通过分类检索相关记忆

## 🔑 关键理解

### 为什么表结构不会变化？

**memU 使用 JSON/JSONB 存储灵活数据**：

1. **固定表结构**：
   - 表结构是固定的（resources, memory_items, memory_categories, category_items）
   - 这些表的结构不会因为你的画像字段变化而变化

2. **灵活的数据存储**：
   - 用户画像的完整数据存储在：
     - **文件系统**：JSON 文件（通过 `resources.local_path` 引用）
     - **数据库**：`memory_items.extra` 字段（JSONB 类型）
   - JSONB 可以存储任意结构的 JSON 数据

3. **字段变化不影响表结构**：
   ```python
   # 旧版画像结构
   {
     "demographics": {...},
     "health": {...}
   }
   
   # 优化版画像结构
   {
     "identity_language": {...},
     "health_safety": {...},
     "response_style": {...}
   }
   ```
   - 两种结构都可以存储在同一个 `extra` JSONB 字段中
   - 表结构不需要改变

### 清空表的效果

**清空表会删除所有数据**：

```sql
-- 清空所有用户数据
TRUNCATE TABLE category_items CASCADE;
TRUNCATE TABLE memory_categories CASCADE;
TRUNCATE TABLE memory_items CASCADE;
TRUNCATE TABLE resources CASCADE;
```

**效果**：
- ✅ 删除所有用户画像（无论旧版还是优化版）
- ✅ 删除所有对话历史
- ✅ 删除所有记忆分类
- ✅ 删除所有资源文件引用

**注意**：
- 临时文件系统中的 JSON 文件可能还存在（但数据库引用已删除）
- 下次运行时会从零开始，所有新画像都使用优化版结构

## 📋 推荐操作

### 方案1：只清空数据（推荐）
```sql
-- 保留表结构，只清空数据
TRUNCATE TABLE category_items CASCADE;
TRUNCATE TABLE memory_categories CASCADE;
TRUNCATE TABLE memory_items CASCADE;
TRUNCATE TABLE resources CASCADE;
```

**优点**：
- 保留表结构，memU 不需要重新创建表
- 清空所有数据，从零开始
- 保留 `alembic_version` 表，避免版本问题

### 方案2：删除表（完全重置）
```sql
-- 删除表（memU 会在下次启动时重新创建）
DROP TABLE IF EXISTS category_items CASCADE;
DROP TABLE IF EXISTS memory_categories CASCADE;
DROP TABLE IF EXISTS memory_items CASCADE;
DROP TABLE IF EXISTS resources CASCADE;
```

**优点**：
- 完全清空，包括表结构
- memU 会在下次启动时自动创建表

## 🎯 总结

1. **表结构是固定的**：不会因为画像字段变化而变化
2. **数据存储在 JSON/JSONB 中**：字段结构变化不影响表结构
3. **清空表会删除所有数据**：包括旧版和优化版的画像
4. **推荐使用 TRUNCATE**：保留表结构，只清空数据

清空表后，系统会从零开始，所有新画像都使用优化版结构（`identity_language`, `health_safety`, `response_style` 等）。

