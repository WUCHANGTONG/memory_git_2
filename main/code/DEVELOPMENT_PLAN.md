# 用户画像记忆系统开发计划

## 📋 项目现状分析

### 当前代码结构
```
memory/
├── code/
│   ├── agent.py              # 主程序（对话循环）
│   ├── profile_schema.py     # 画像结构定义
│   ├── profile_extractor.py  # 画像提取逻辑
│   ├── requirements.txt     # 依赖管理
│   └── README.md
├── data/                     # 数据集目录（已有，不修改）
└── .env                      # 环境配置
```

### 当前功能
- ✅ 6个画像维度定义（profile_schema.py）
- ✅ 画像提取和更新（profile_extractor.py）
- ✅ 对话循环（agent.py）
- ❌ 画像持久化（重启后丢失）
- ❌ 对话历史管理（无LangChain Memory）
- ❌ 多用户支持（单用户）

---

## 🎯 最终目标

👉 **Python + LangChain + memU（文件存储）**
👉 **支持多用户、多轮对话、角色区分、时间戳、持久画像**

---

## 🧭 6阶段开发计划（按顺序执行）

### ✅ 阶段 0：整理当前代码结构（不改逻辑）

**目标**：模块化现有代码，为接入记忆系统做准备

**任务清单**：
- [x] 确认 `profile_schema.py` 的 `init_profile()` 接口稳定
- [x] 确认 `profile_extractor.py` 的 `update_profile()` 接口稳定
- [ ] 确认 `agent.py` 的对话循环逻辑清晰
- [ ] 添加必要的类型提示和文档字符串

**完成标准**：
- ✅ 所有模块接口清晰，功能不变
- ✅ 代码结构便于后续扩展

**注意事项**：
- 保持 `agent.py` 文件名（符合项目命名习惯）
- 不改变现有功能逻辑

---

### 🧱 阶段 1：实现 memU 存储层（memory_store.py）

**目标**：实现文件存储的核心层，支持多用户数据持久化

**新建文件**：`code/memory_store.py`

**目录结构设计**：
```
memory/
├── code/
│   ├── memory_store.py      # 新建
│   ├── data/                 # 新建，用于存储用户数据
│   │   ├── profiles/         # 用户画像存储
│   │   │   ├── user_001.json
│   │   │   └── user_002.json
│   │   └── conversations/    # 对话历史存储
│   │       ├── user_001.json
│   │       └── user_002.json
│   └── ...
└── data/                     # 原有数据集目录（不变）
```

**需要实现的接口**：

```python
class MemoryStore:
    """基于文件系统的记忆存储层（memU实现）"""
    
    # 1. 用户画像存取
    def load_profile(self, user_id: str) -> dict:
        """加载用户画像，不存在则返回空画像"""
        pass
    
    def save_profile(self, user_id: str, profile_dict: dict) -> bool:
        """保存用户画像到文件"""
        pass
    
    # 2. 对话记录存取
    def append_message(self, user_id: str, role: str, content: str, 
                      timestamp: Optional[str] = None) -> bool:
        """追加一条对话消息"""
        pass
    
    def load_conversation(self, user_id: str) -> list[dict]:
        """加载用户对话历史，不存在则返回空列表"""
        pass
    
    # 3. 工具方法
    def get_profile_path(self, user_id: str) -> Path:
        """获取用户画像文件路径"""
        pass
    
    def get_conversation_path(self, user_id: str) -> Path:
        """获取对话历史文件路径"""
        pass
    
    def ensure_directories(self):
        """确保存储目录存在"""
        pass
```

**数据格式设计**：

**profile.json**：
```json
{
  "user_id": "user_001",
  "last_updated": "2025-01-XX XX:XX:XX",
  "profile": {
    "demographics": {...},
    "health": {...},
    ...
  }
}
```

**conversation.json**：
```json
[
  {
    "timestamp": "2025-01-XX XX:XX:XX",
    "role": "user",
    "content": "你好，我是石家庄人"
  },
  {
    "timestamp": "2025-01-XX XX:XX:XX",
    "role": "assistant",
    "content": "您好！很高兴认识您..."
  }
]
```

**完成标准**：
- ✅ 可以独立运行测试脚本写入/读取数据
- ✅ 重启程序后成功加载历史数据
- ✅ 多用户数据互不干扰
- ✅ 文件不存在时自动创建空结构

**注意事项**：
- 使用 `code/data/` 目录，避免与根目录的 `data/` 混淆
- JSON 文件使用 UTF-8 编码，支持中文
- 时间戳格式：`YYYY-MM-DD HH:MM:SS`

---

### 🧠 阶段 2：封装 LangChain Memory 层（chat_memory.py）

**目标**：为每个用户创建独立的 LangChain Memory 实例，与 memU 同步

**新建文件**：`code/chat_memory.py`

**需要实现的接口**：

```python
from langchain.memory import ConversationBufferMemory

class ChatMemoryManager:
    """LangChain Memory 管理器"""
    
    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
        self._memories = {}  # {user_id: ConversationBufferMemory}
    
    def get_memory_for_user(self, user_id: str) -> ConversationBufferMemory:
        """获取或创建用户的Memory实例"""
        pass
    
    def add_message(self, user_id: str, role: str, content: str):
        """添加消息到Memory和文件存储"""
        pass
    
    def load_history_into_memory(self, user_id: str):
        """从文件加载历史对话到Memory"""
        pass
    
    def save_current_memory(self, user_id: str):
        """将当前Memory内容保存到文件"""
        pass
```

**完成标准**：
- ✅ 启动时自动加载历史对话到 Memory
- ✅ 新增对话同步更新 Memory 和文件
- ✅ 不同用户的 Memory 实例独立
- ✅ 支持 user/assistant/system 三种角色

**注意事项**：
- ConversationBufferMemory 需要 `return_messages=True`
- 消息格式需要符合 LangChain 的 Message 类型
- 加载历史时按时间戳顺序恢复

---

### 🔁 阶段 3：改造 agent.py（引入多用户 + 持久记忆）

**目标**：整合记忆系统到主流程，支持多用户和持久化

**修改文件**：`code/agent.py`

**改造要点**：

1. **启动流程改造**：
```python
def chat_loop():
    # 1. 初始化存储层
    memory_store = MemoryStore()
    
    # 2. 获取或创建 user_id
    user_id = input("请输入用户ID（直接回车使用默认）: ").strip() or "default_user"
    
    # 3. 加载历史数据
    profile = memory_store.load_profile(user_id)
    if not profile.get("profile"):
        profile = init_profile()
    
    # 4. 初始化 Memory
    memory_manager = ChatMemoryManager(memory_store)
    memory_manager.load_history_into_memory(user_id)
    memory = memory_manager.get_memory_for_user(user_id)
    
    # 5. 开始对话循环...
```

2. **对话循环改造**：
```python
while True:
    user_input = input("你（模拟老人）: ").strip()
    
    if user_input.lower() == "exit":
        # 保存最终状态
        memory_store.save_profile(user_id, profile)
        memory_manager.save_current_memory(user_id)
        break
    
    # 添加消息到 Memory 和文件
    memory_manager.add_message(user_id, "user", user_input)
    
    # 更新画像
    conversation_text = f"用户：{user_input}"
    profile = update_profile(conversation_text, profile)
    
    # 立即保存画像
    memory_store.save_profile(user_id, {"profile": profile, "user_id": user_id})
    
    # 显示结果...
```

**完成标准**：
- ✅ 重启后对话历史和画像都能恢复
- ✅ 切换 user_id 后数据互不干扰
- ✅ 每次画像更新后立即保存
- ✅ 退出时确保所有数据已落盘

**注意事项**：
- 保持现有的 `show` 和 `exit` 命令
- 画像更新后立即保存，不要等到退出
- 错误处理：文件损坏时回退到空状态

---

### 🧪 阶段 4：加入 system/assistant 角色支持

**目标**：完善角色区分，为未来 Agent 回复做准备

**修改文件**：
- `code/memory_store.py` - 确保 `append_message` 支持所有角色
- `code/chat_memory.py` - 确保 Memory 支持三种角色
- `code/agent.py` - 画像提取时只处理 user 角色的内容

**改造要点**：

1. **角色定义**：
```python
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_SYSTEM = "system"
```

2. **画像提取逻辑**：
```python
# 只从 user 角色的消息中提取画像
user_messages = [msg for msg in conversation if msg["role"] == "user"]
conversation_text = "\n".join([f"用户：{msg['content']}" for msg in user_messages])
profile = update_profile(conversation_text, profile)
```

**完成标准**：
- ✅ 系统可以区分三种角色
- ✅ 画像提取只使用 user 内容
- ✅ 未来加入 Agent 回复不会污染画像
- ✅ 对话历史包含所有角色

**注意事项**：
- 当前阶段 Agent 不输出回复，但结构要支持
- system 消息可用于设置 Agent 角色和提示词

---

### 🧰 阶段 5：健壮性增强

**目标**：提高系统稳定性，处理各种异常情况

**增强点**：

1. **文件异常处理**：
```python
def load_profile(self, user_id: str) -> dict:
    try:
        # 尝试加载
    except json.JSONDecodeError:
        # JSON 损坏：备份原文件，返回空画像
    except FileNotFoundError:
        # 文件不存在：返回空画像
    except Exception as e:
        # 其他异常：记录日志，返回空画像
```

2. **数据验证**：
- 验证 profile 结构是否符合 schema
- 验证 conversation 格式是否正确
- 自动修复常见问题（如缺少字段）

3. **备份机制**：
- 保存前备份旧文件（.bak）
- 保存成功后删除备份
- 失败时恢复备份

4. **并发安全**（可选）：
- 使用文件锁（`fcntl` 或 `msvcrt`）
- 或使用原子写入（先写临时文件，再重命名）

**完成标准**：
- ✅ 文件损坏时程序不崩溃
- ✅ 所有异常都有安全回退
- ✅ 数据不会因异常而丢失
- ✅ 有清晰的错误日志

**注意事项**：
- 原型阶段可以简化，但核心异常必须处理
- 日志可以输出到控制台，后续可改为文件

---

### 🚀 阶段 6：预留升级接口（设计时考虑）

**目标**：为未来扩展预留接口，当前不实现

**设计要点**：

1. **存储后端抽象**：
```python
class MemoryStoreBackend(ABC):
    """存储后端抽象接口"""
    
    @abstractmethod
    def load_profile(self, user_id: str) -> dict:
        pass
    
    @abstractmethod
    def save_profile(self, user_id: str, profile_dict: dict) -> bool:
        pass

class FileMemoryStore(MemoryStoreBackend):
    """文件存储实现"""
    pass

# 未来可扩展：
# class DatabaseMemoryStore(MemoryStoreBackend):
# class Mem0MemoryStore(MemoryStoreBackend):
```

2. **配置化**：
```python
# config.py
STORAGE_BACKEND = "file"  # 未来可改为 "db", "mem0" 等
STORAGE_PATH = "code/data"
```

**完成标准**：
- ✅ 代码结构允许替换存储后端
- ✅ 接口设计清晰，易于扩展
- ✅ 当前只实现文件存储

**注意事项**：
- 这一步主要是设计考虑，不强制实现抽象类
- 但要保证代码结构便于未来扩展

---

## 📁 最终文件结构

```
memory/
├── code/
│   ├── agent.py                 # 主程序（改造）
│   ├── memory_store.py           # memU存储层（新建）
│   ├── chat_memory.py            # LangChain Memory封装（新建）
│   ├── profile_schema.py         # 画像结构（已有）
│   ├── profile_extractor.py      # 画像提取（已有）
│   ├── requirements.txt          # 依赖（更新）
│   ├── README.md                 # 文档（更新）
│   ├── DEVELOPMENT_PLAN.md       # 本文件
│   └── data/                     # 用户数据存储（新建）
│       ├── profiles/
│       │   ├── user_001.json
│       │   └── default_user.json
│       └── conversations/
│           ├── user_001.json
│           └── default_user.json
├── data/                         # 数据集目录（已有，不变）
└── .env                          # 环境配置（已有）
```

---

## 🔄 开发顺序总结

1. **阶段 0**：整理代码 ✅（快速完成）
2. **阶段 1**：memU 存储层 🧱（核心基础）
3. **阶段 2**：LangChain Memory 🧠（记忆管理）
4. **阶段 3**：整合到主流程 🔁（功能完整）
5. **阶段 4**：角色支持 🧪（完善功能）
6. **阶段 5**：健壮性 🧰（生产就绪）
7. **阶段 6**：预留接口 🚀（设计考虑）

---

## ⚠️ 重要注意事项

1. **目录结构**：
   - 使用 `code/data/` 存储用户数据，避免与根目录 `data/`（数据集）混淆
   - 所有代码文件保持在 `code/` 目录

2. **向后兼容**：
   - 保持现有接口不变（`init_profile`, `update_profile`）
   - 新增功能通过新模块实现

3. **测试策略**：
   - 每个阶段完成后独立测试
   - 确保前一阶段功能不受影响

4. **memU 实现**：
   - 如果没有现成的 memU 库，我们自己实现简单的文件存储层
   - 命名为 `memory_store.py`，功能等同于 memU

---

## 📝 下一步行动

建议从**阶段 0**开始，逐步推进。每个阶段完成后可以暂停，测试验证后再继续下一阶段。

您觉得这个调整后的计划如何？有什么需要修改或补充的吗？

