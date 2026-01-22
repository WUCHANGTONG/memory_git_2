# 阶段1实现计划：集成 memU Cloud API

## 📋 目标

使用 memU Cloud API（通过 API Key）实现：
- ✅ 用户画像持久化存储（多用户支持）
- ✅ 对话历史存储（为阶段2做准备）
- ✅ 程序重启后画像恢复
- ✅ 本地缓存作为 fallback（网络异常时）

---

## 🛠️ 技术栈

- **memU SDK**: `memu` (Python SDK，通过 `pip install memu` 安装)
- **存储方式**: memU Cloud API + 本地 JSON 缓存
- **API Key**: 从 `.env` 文件读取 `MEMU_API_KEY`
- **核心 API**: 
  - `memorize()` - 提取和存储记忆（支持 conversation 模态）
  - `retrieve()` - 查询记忆（支持 RAG 和 LLM 两种方式）

---

## 📦 依赖安装

### 1. 更新 requirements.txt

```txt
# 添加 memU SDK
memu>=1.0.0
```

**注意**：根据 [memU GitHub](https://github.com/NevaMind-AI/memU)，SDK 包名是 `memu`，不是 `memu-py`

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

在项目根目录的 `.env` 文件中添加：
```env
MEMU_API_KEY=your-memu-api-key-here
```

---

## 📁 文件结构

```
code/
├── memory_store.py          # 新建：memU存储层封装
├── profile_schema.py        # 已有：画像结构定义
├── profile_extractor.py     # 已有：画像提取逻辑
├── agent.py                 # 已有：主程序（阶段3会修改）
├── data/                    # 新建：本地缓存目录
│   ├── profiles/           # 本地画像缓存
│   │   └── {user_id}.json
│   └── conversations/      # 本地对话缓存（可选）
│       └── {user_id}.json
└── requirements.txt         # 更新：添加memu-py
```

---

## 🔧 实现细节

### 1. memory_store.py 接口设计

```python
"""
memU Cloud API 存储层封装

使用 memU Cloud API 存储用户画像和对话历史。
同时维护本地 JSON 缓存作为 fallback。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# memU SDK 导入
# 根据 memU GitHub 文档，使用 Service 类
try:
    from memu import Service
    MEMU_AVAILABLE = True
except ImportError:
    print("⚠️  警告：memU SDK 未安装，请运行: pip install memu")
    Service = None
    MEMU_AVAILABLE = False


class MemoryStore:
    """
    memU Cloud API 存储层
    
    功能：
    - 用户画像存储和加载（通过 memU API）
    - 对话历史存储（为阶段2做准备）
    - 本地缓存 fallback
    """
    
    def __init__(self, api_key: Optional[str] = None, base_path: str = "code/data"):
        """
        初始化 MemoryStore
        
        Args:
            api_key: memU API Key，如果为None则从环境变量读取
            base_path: 本地缓存基础路径
        """
        # 加载环境变量
        load_dotenv()
        self.api_key = api_key or os.getenv("MEMU_API_KEY", "")
        
        if not self.api_key:
            print("⚠️  警告：未设置 MEMU_API_KEY")
        
        # 初始化 memU Service
        # 根据 memU 文档，Service 需要配置 LLM provider（如 OpenAI）
        self.memu_service = None
        if MEMU_AVAILABLE and self.api_key:
            try:
                # memU Service 初始化需要配置
                # 参考：https://github.com/NevaMind-AI/memU
                # 需要提供 LLM provider 配置（如 OpenAI API Key）
                openai_api_key = os.getenv("OPENAI_API_KEY", "")
                if not openai_api_key:
                    print("⚠️  警告：memU 需要 OPENAI_API_KEY 配置")
                    print("   请在 .env 中添加: OPENAI_API_KEY=your-openai-key")
                else:
                    # 初始化 memU Service
                    # 注意：实际初始化方式需要查阅 memU SDK 文档
                    # 这里使用占位符，实际实现时需要根据文档调整
                    self.memu_service = Service(
                        api_key=self.api_key,  # memU API Key
                        # 可能需要其他配置参数
                    )
            except Exception as e:
                print(f"⚠️  memU Service 初始化失败: {e}")
                print("   将使用本地缓存模式")
        
        # 本地缓存路径
        self.base_path = Path(base_path)
        self.profiles_dir = self.base_path / "profiles"
        self.conversations_dir = self.base_path / "conversations"
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保缓存目录存在"""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
    
    # ========== 用户画像相关方法 ==========
    
    def save_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """
        保存用户画像到 memU 和本地缓存
        
        Args:
            user_id: 用户ID
            profile: 用户画像字典（符合profile_schema结构）
        
        Returns:
            bool: 是否保存成功
        """
        try:
            # 准备存储数据
            profile_data = {
                "user_id": user_id,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "profile": profile
            }
            
            # 1. 保存到 memU Cloud API
            if self.memu_service:
                try:
                    # 使用 memU 的 memorize() API 存储画像
                    # 参考：https://github.com/NevaMind-AI/memU
                    # 
                    # 方式1：将画像作为 conversation 资源存储
                    # 将 profile 转换为对话格式，然后调用 memorize
                    profile_text = json.dumps(profile, ensure_ascii=False, indent=2)
                    
                    # 创建临时文件或使用字符串作为资源
                    # memorize() 支持 resource_url 或直接传入内容
                    result = await self.memu_service.memorize(
                        resource_url=None,  # 如果使用文件路径
                        resource_content=profile_text,  # 或直接传入内容
                        modality="conversation",  # 或 "document"
                        user={"user_id": user_id}  # 用户隔离
                    )
                    
                    # result 包含 resource, items, categories
                    # 可以将画像维度存储为 items 或 categories
                    
                except Exception as e:
                    print(f"⚠️  memU API 保存失败: {e}")
                    print("   使用本地缓存保存")
                except Exception as e:
                    print(f"⚠️  memU API 保存失败: {e}")
                    print("   使用本地缓存保存")
            
            # 2. 保存到本地缓存（无论 API 是否成功）
            cache_path = self.profiles_dir / f"{user_id}.json"
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ 保存用户画像失败: {e}")
            return False
    
    def load_profile(self, user_id: str) -> Dict[str, Any]:
        """
        加载用户画像（优先从 memU，失败则从本地缓存）
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict: 用户画像字典，如果不存在则返回空画像
        """
        # 1. 尝试从 memU API 加载
        if self.memu_service:
            try:
                # 使用 memU 的 retrieve() API 检索画像
                # 参考：https://github.com/NevaMind-AI/memU
                #
                # 方式1：使用 RAG 检索（快速）
                result = await self.memu_service.retrieve(
                    queries=[
                        {"role": "user", "content": {"text": "用户画像信息"}}
                    ],
                    where={"user_id": user_id},  # 用户隔离
                    method="rag"  # 或 "llm" 用于深度检索
                )
                
                # result 包含 categories, items, resources
                # 从 items 或 categories 中提取画像信息
                # 需要根据实际返回结构解析
                
                # 方式2：检索特定 category
                # 如果画像存储在特定 category 中，可以检索该 category
                
            except Exception as e:
                print(f"⚠️  memU API 加载失败: {e}")
                print("   尝试从本地缓存加载")
            except Exception as e:
                print(f"⚠️  memU API 加载失败: {e}")
                print("   尝试从本地缓存加载")
        
        # 2. 从本地缓存加载
        cache_path = self.profiles_dir / f"{user_id}.json"
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("profile", {})
            except Exception as e:
                print(f"⚠️  本地缓存加载失败: {e}")
        
        # 3. 返回空画像
        return {}
    
    # ========== 对话历史相关方法（为阶段2准备）==========
    
    def append_message(self, user_id: str, role: str, content: str, 
                      timestamp: Optional[str] = None) -> bool:
        """
        追加一条对话消息到 memU 和本地缓存
        
        Args:
            user_id: 用户ID
            role: 角色（"user", "assistant", "system"）
            content: 消息内容
            timestamp: 时间戳，如果为None则自动生成
        
        Returns:
            bool: 是否保存成功
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = {
            "timestamp": timestamp,
            "role": role,
            "content": content
        }
        
        try:
            # 1. 保存到 memU API（如果可用）
            if self.memu_service:
                try:
                    # 使用 memU 的 memorize() API 存储对话
                    # 参考：https://github.com/NevaMind-AI/memU
                    #
                    # 将对话消息转换为 memU 可接受的格式
                    conversation_data = {
                        "messages": [
                            {"role": role, "content": content, "timestamp": timestamp}
                        ]
                    }
                    
                    result = await self.memu_service.memorize(
                        resource_content=json.dumps(conversation_data, ensure_ascii=False),
                        modality="conversation",
                        user={"user_id": user_id}
                    )
                    
                except Exception as e:
                    print(f"⚠️  memU API 保存对话失败: {e}")
                except Exception as e:
                    print(f"⚠️  memU API 保存对话失败: {e}")
            
            # 2. 保存到本地缓存
            cache_path = self.conversations_dir / f"{user_id}.json"
            messages = []
            
            if cache_path.exists():
                with open(cache_path, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
            
            messages.append(message)
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ 保存对话消息失败: {e}")
            return False
    
    def load_conversation(self, user_id: str) -> List[Dict[str, Any]]:
        """
        加载用户对话历史
        
        Args:
            user_id: 用户ID
        
        Returns:
            List[Dict]: 对话消息列表，如果不存在则返回空列表
        """
        # 1. 尝试从 memU API 加载
        if self.memu_service:
            try:
                # 使用 memU 的 retrieve() API 检索对话历史
                result = await self.memu_service.retrieve(
                    queries=[
                        {"role": "user", "content": {"text": "对话历史"}}
                    ],
                    where={"user_id": user_id},
                    method="rag"  # 快速检索
                )
                
                # 从 result.resources 中提取对话历史
                # 需要根据实际返回结构解析
                
            except Exception as e:
                print(f"⚠️  memU API 加载对话失败: {e}")
            except Exception as e:
                print(f"⚠️  memU API 加载对话失败: {e}")
        
        # 2. 从本地缓存加载
        cache_path = self.conversations_dir / f"{user_id}.json"
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  本地缓存加载对话失败: {e}")
        
        return []
```

---

## 📝 实现步骤

### 步骤1：安装和配置 memU SDK

1. **更新 requirements.txt**
   ```bash
   pip install memu
   ```
   
   **注意**：根据 [memU GitHub](https://github.com/NevaMind-AI/memU)，包名是 `memu`，不是 `memu-py`

2. **配置 API Key**
   - 在 `.env` 文件中添加 `MEMU_API_KEY=your-key`

3. **验证连接**
   - 创建测试脚本验证 memU 客户端能否正常连接

### 步骤2：实现 memory_store.py 基础框架

1. **创建文件结构**
   - 实现 `MemoryStore` 类
   - 实现本地缓存功能（先实现这部分，确保基础功能可用）

2. **实现本地缓存方法**
   - `save_profile()` - 保存到本地 JSON
   - `load_profile()` - 从本地 JSON 加载
   - `append_message()` - 追加对话到本地 JSON
   - `load_conversation()` - 加载对话历史

### 步骤3：集成 memU API（需要查阅 memU SDK 文档）

1. **查阅 memU SDK 文档**
   - 确认正确的导入方式
   - 确认 API 调用方法
   - 确认用户画像存储的最佳实践

2. **实现 memU API 调用**
   - 在 `save_profile()` 中添加 memU API 调用
   - 在 `load_profile()` 中添加 memU API 调用
   - 处理 API 异常和 fallback

### 步骤4：测试和验证

1. **单元测试**
   - 测试本地缓存功能
   - 测试 memU API 调用（如果可用）
   - 测试 fallback 机制

2. **集成测试**
   - 测试保存和加载用户画像
   - 测试多用户隔离
   - 测试程序重启后恢复

---

## ⚠️ 注意事项

### 1. memU SDK 核心 API（根据 GitHub 文档）

根据 [memU GitHub 仓库](https://github.com/NevaMind-AI/memU)，核心 API 包括：

#### `memorize()` - 提取和存储记忆
```python
result = await service.memorize(
    resource_url="path/to/file.json",  # 文件路径或 URL
    # 或 resource_content="...",  # 直接传入内容
    modality="conversation",            # conversation | document | image | video | audio
    user={"user_id": "123"}             # 用户隔离
)

# 返回：
# {
#     "resource": {...},      # 存储的资源元数据
#     "items": [...],         # 提取的记忆项
#     "categories": [...]     # 更新的类别摘要
# }
```

#### `retrieve()` - 查询记忆
```python
result = await service.retrieve(
    queries=[
        {"role": "user", "content": {"text": "用户画像信息"}}
    ],
    where={"user_id": "123"},  # 用户隔离过滤
    method="rag"  # "rag" 快速检索 或 "llm" 深度检索
)

# 返回：
# {
#     "categories": [...],     # 相关类别（RAG 方式包含相似度分数）
#     "items": [...],          # 相关记忆项
#     "resources": [...],      # 相关原始资源
#     "next_step_query": "..." # 重写的查询（如果适用）
# }
```

### 2. 用户隔离

memU 支持通过 `user` 参数和 `where` 过滤器实现用户隔离：
- `memorize()` 中使用 `user={"user_id": "123"}`
- `retrieve()` 中使用 `where={"user_id": "123"}`

### 3. 异步 API

memU SDK 使用异步 API（`async/await`），需要：
- 使用 `async def` 定义函数
- 使用 `await` 调用 memU API
- 或者使用同步包装器（如果 SDK 提供）

### 3. 错误处理

- memU API 调用失败时，自动 fallback 到本地缓存
- 本地缓存也失败时，返回空数据（不中断程序）
- 记录错误日志，便于调试

### 4. 数据格式

- 用户画像：使用 `profile_schema.py` 定义的结构
- 对话历史：使用标准格式（timestamp, role, content）
- JSON 序列化：使用 `ensure_ascii=False` 支持中文

---

## ✅ 完成标准

- [ ] `memory_store.py` 文件创建完成
- [ ] 本地缓存功能实现并测试通过
- [ ] memU API 集成完成（根据实际 SDK 调整）
- [ ] 错误处理和 fallback 机制完善
- [ ] 多用户隔离测试通过
- [ ] 程序重启后画像恢复测试通过
- [ ] 代码文档和注释完整

---

## 🔄 下一步

完成阶段1后，可以开始：
- **阶段2**：封装 LangChain Memory 层
- **阶段3**：改造 agent.py 整合记忆系统

---

## 📚 参考资源

- **memU GitHub 仓库**：https://github.com/NevaMind-AI/memU
- **memU 官方文档**：https://memu.pro/docs
- **memU Cloud API**：https://memu.pro/
- **memU Python SDK**：通过 `pip install memu` 安装

## ⚠️ 重要说明

### 1. 异步 API 处理

memU SDK 使用异步 API，需要：
- 方案A：使用 `async/await`（推荐）
- 方案B：使用同步包装器（如果 SDK 提供）
- 方案C：使用 `asyncio.run()` 包装异步调用

### 2. LLM Provider 配置

memU 需要 LLM provider（如 OpenAI）来提取和检索记忆：
- 需要在 `.env` 中配置 `OPENAI_API_KEY`
- 或者配置其他支持的 LLM provider

### 3. 画像存储策略

建议将用户画像存储为：
- **方式1**：作为 conversation 资源存储，memU 会自动提取 items 和 categories
- **方式2**：直接存储为 structured memory items，使用 memU 的 CRUD API（如果提供）

### 4. 实际实现时的调整

由于 memU SDK 的具体 API 可能需要查阅最新文档，建议：
1. 先实现本地缓存功能（确保基础可用）
2. 查阅 memU SDK 的实际 API 文档
3. 根据实际 API 调整代码
4. 逐步集成 memU Cloud API

