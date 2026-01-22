# code_new 用户画像记忆系统开发计划

## 📋 项目现状分析

### 当前代码结构（code_new）
```
main/
├── code_new/
│   ├── profile_schema.py         # ✅ 已完成：画像结构定义（Pydantic 2.x）
│   ├── profile_extractor.py      # ✅ 已完成：画像提取逻辑（支持 DashScope）
│   ├── test_profile_extraction.py # ✅ 已完成：测试脚本
│   ├── requirements.txt          # ✅ 已完成：依赖列表
│   └── README.md                 # ✅ 已完成：使用文档
├── .env                          # ✅ 已有：环境配置（DASHSCOPE_API_KEY, MEMU_API_KEY）
└── memU-main/                    # ✅ 已安装：memU 框架（本地部署）
```

### 当前功能
- ✅ 6个画像维度定义（profile_schema.py）
- ✅ 画像提取和更新（profile_extractor.py）
- ✅ 使用 Pydantic 2.x（兼容当前环境）
- ✅ 支持 DashScope API 调用
- ❌ 画像持久化（重启后丢失）
- ❌ 对话历史管理（无 LangChain Memory）
- ❌ 多用户支持（单用户）
- ❌ memU 框架集成
- ❌ 个性化回答功能

---

## 🎯 最终目标

👉 **Python + LangChain + memU（本地部署）**
👉 **支持多用户、多轮对话、角色区分、时间戳、持久画像**
👉 **通过对话不断完善用户画像**
👉 **根据用户画像提供个性化回答**

---

## 🧭 7阶段开发计划（按顺序执行）

### ✅ 阶段 0：基础功能完成（已完成）

**目标**：实现用户画像提取的核心功能

**已完成**：
- [x] `profile_schema.py` - 画像结构定义（Pydantic 2.x）
- [x] `profile_extractor.py` - 画像提取逻辑
- [x] 测试脚本和文档

**完成标准**：✅ 已完成

---

### 🧱 阶段 1：实现 memU 存储层（memory_store.py）

**目标**：集成 memU 框架，实现用户画像和对话历史的持久化存储

**新建文件**：`code_new/memory_store.py`

**目录结构设计**：
```
main/
├── code_new/
│   ├── memory_store.py          # 新建：memU 存储层封装
│   ├── data/                     # 新建，用于本地缓存（可选）
│   │   ├── profiles/             # 本地画像缓存
│   │   └── conversations/        # 本地对话缓存
│   └── ...
└── memU-main/                    # memU 框架（已安装）
```

**需要实现的接口**：

```python
from memu.app import MemoryService
from typing import Dict, Any, Optional, List
from datetime import datetime

class MemUStore:
    """基于 memU 框架的记忆存储层"""
    
    def __init__(self, memu_service: Optional[MemoryService] = None):
        """
        初始化 memU 存储层
        
        Args:
            memu_service: memU 服务实例，如果为 None 则自动创建
        """
        pass
    
    # 1. 用户画像存取（使用 memU 的 memorize 和 retrieve）
    def save_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """
        保存用户画像到 memU
        
        策略：将画像转换为 JSON 字符串，作为 document 存储
        """
        pass
    
    def load_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        从 memU 加载用户画像
        
        策略：使用 retrieve 查询用户的最新画像
        """
        pass
    
    # 2. 对话记录存取（使用 memU 的 memorize）
    def append_message(self, user_id: str, role: str, content: str, 
                      timestamp: Optional[str] = None) -> bool:
        """
        追加一条对话消息到 memU
        
        策略：将对话作为 conversation 资源存储
        """
        pass
    
    def load_conversation(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        从 memU 加载用户对话历史
        
        策略：使用 retrieve 查询用户的对话历史
        """
        pass
    
    # 3. 工具方法
    def get_user_memory(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        使用 memU 检索用户记忆
        
        用于个性化回答时检索相关记忆
        """
        pass
    
    def ensure_service_ready(self):
        """确保 memU 服务已初始化"""
        pass
```

**memU 集成策略**：

1. **画像存储**：
   - 将用户画像转换为 JSON 字符串
   - 使用 `memorize()` 方法，modality="document"
   - 使用 user_id 作为用户标识

2. **对话存储**：
   - 将对话消息组织成 conversation 格式
   - 使用 `memorize()` 方法，modality="conversation"
   - 每次对话追加到现有资源或创建新资源

3. **记忆检索**：
   - 使用 `retrieve()` 方法查询用户相关记忆
   - 支持 RAG 和 LLM 两种检索方式

**完成标准**：
- ✅ 可以独立运行测试脚本写入/读取数据
- ✅ 重启程序后成功从 memU 加载历史数据
- ✅ 多用户数据通过 user_id 隔离
- ✅ memU 服务初始化失败时有降级方案（本地缓存）

**注意事项**：
- memU 服务需要配置 LLM（使用 DashScope）
- 需要处理 memU API 调用失败的情况
- 考虑添加本地缓存作为备份

---

### 🧠 阶段 2：封装 LangChain Memory 层（chat_memory.py）

**目标**：为每个用户创建独立的 LangChain Memory 实例，与 memU 同步

**新建文件**：`code_new/chat_memory.py`

**需要实现的接口**：

```python
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from memory_store import MemUStore
from typing import Optional

class ChatMemoryManager:
    """LangChain Memory 管理器，与 memU 同步"""
    
    def __init__(self, memu_store: MemUStore):
        self.memu_store = memu_store
        self._memories = {}  # {user_id: ConversationBufferMemory}
    
    def get_memory_for_user(self, user_id: str) -> ConversationBufferMemory:
        """获取或创建用户的Memory实例"""
        pass
    
    def add_message(self, user_id: str, role: str, content: str):
        """
        添加消息到Memory和memU
        
        Args:
            user_id: 用户ID
            role: 角色（user/assistant/system）
            content: 消息内容
        """
        pass
    
    def load_history_into_memory(self, user_id: str):
        """从memU加载历史对话到Memory"""
        pass
    
    def save_current_memory(self, user_id: str):
        """将当前Memory内容保存到memU"""
        pass
    
    def get_conversation_context(self, user_id: str) -> str:
        """获取对话上下文（用于画像提取和个性化回答）"""
        pass
```

**完成标准**：
- ✅ 启动时自动从 memU 加载历史对话到 Memory
- ✅ 新增对话同步更新 Memory 和 memU
- ✅ 不同用户的 Memory 实例独立
- ✅ 支持 user/assistant/system 三种角色

**注意事项**：
- ConversationBufferMemory 需要 `return_messages=True`
- 消息格式需要符合 LangChain 的 Message 类型
- 加载历史时按时间戳顺序恢复

---

### 🔁 阶段 3：实现主程序 agent.py（对话循环 + 画像更新）

**目标**：实现交互式对话循环，整合画像提取和 memU 存储

**新建文件**：`code_new/agent.py`

**功能设计**：

1. **启动流程**：
```python
def main():
    # 1. 初始化 memU 存储层
    memu_store = MemUStore()
    
    # 2. 获取用户ID
    user_id = input("请输入用户ID（直接回车使用默认）: ").strip() or "default_user"
    
    # 3. 从 memU 加载历史画像
    profile = memu_store.load_profile(user_id)
    if not profile:
        profile = init_profile()
        print("[INFO] 新用户，已初始化空画像")
    else:
        print(f"[INFO] 已从 memU 加载历史画像")
    
    # 4. 初始化 Memory
    memory_manager = ChatMemoryManager(memu_store)
    memory_manager.load_history_into_memory(user_id)
    memory = memory_manager.get_memory_for_user(user_id)
    
    # 5. 开始对话循环
    chat_loop(user_id, profile, memory_manager, memu_store)
```

2. **对话循环**：
```python
def chat_loop(user_id, profile, memory_manager, memu_store):
    print("\n说明：输入对话内容，系统会提取并更新用户画像")
    print("输入 'exit' 结束，输入 'show' 查看当前画像，输入 'profile' 查看完整画像\n")
    
    while True:
        user_input = input("你: ").strip()
        
        if user_input.lower() == "exit":
            # 保存最终状态
            memu_store.save_profile(user_id, profile)
            memory_manager.save_current_memory(user_id)
            print("\n对话结束，最终用户画像：")
            print(json.dumps(profile, ensure_ascii=False, indent=2))
            break
        
        if user_input.lower() == "show":
            # 显示画像摘要
            show_profile_summary(profile)
            continue
        
        if user_input.lower() == "profile":
            # 显示完整画像
            print(json.dumps(profile, ensure_ascii=False, indent=2))
            continue
        
        # 添加用户消息到 Memory 和 memU
        memory_manager.add_message(user_id, "user", user_input)
        
        # 更新画像
        print("\n[INFO] 正在提取画像信息...")
        profile = update_profile(user_input, profile)
        
        # 立即保存画像到 memU
        memu_store.save_profile(user_id, profile)
        print("[OK] 画像已更新并保存到 memU")
        
        # 显示更新摘要
        show_profile_updates(profile, user_input)
```

**完成标准**：
- ✅ 重启后对话历史和画像都能从 memU 恢复
- ✅ 切换 user_id 后数据互不干扰
- ✅ 每次画像更新后立即保存到 memU
- ✅ 退出时确保所有数据已保存

**注意事项**：
- 保持 `show` 和 `exit` 命令
- 画像更新后立即保存，不要等到退出
- 错误处理：memU 调用失败时回退到本地缓存

---

### 🎯 阶段 4：实现个性化回答功能（personalized_response.py）

**目标**：根据用户画像和对话历史，生成个性化回答

**新建文件**：`code_new/personalized_response.py`

**功能设计**：

```python
from langchain_community.chat_models import ChatTongyi
from langchain.prompts import ChatPromptTemplate
from memory_store import MemUStore
from chat_memory import ChatMemoryManager
from typing import Dict, Any

class PersonalizedResponder:
    """个性化回答生成器"""
    
    def __init__(self, memu_store: MemUStore, memory_manager: ChatMemoryManager):
        self.memu_store = memu_store
        self.memory_manager = memory_manager
        self.llm = None  # 延迟初始化
    
    def generate_response(self, user_id: str, user_input: str, 
                         profile: Dict[str, Any]) -> str:
        """
        根据用户画像和对话历史生成个性化回答
        
        流程：
        1. 从 memU 检索相关记忆
        2. 构建包含画像和记忆的提示词
        3. 调用 LLM 生成回答
        4. 返回个性化回答
        """
        # 1. 检索相关记忆
        memory_context = self.memu_store.get_user_memory(
            user_id, 
            user_input
        )
        
        # 2. 获取对话历史
        conversation_context = self.memory_manager.get_conversation_context(user_id)
        
        # 3. 构建提示词
        prompt = self._build_prompt(
            user_input=user_input,
            profile=profile,
            memory_context=memory_context,
            conversation_context=conversation_context
        )
        
        # 4. 调用 LLM
        response = self._call_llm(prompt)
        
        return response
    
    def _build_prompt(self, user_input: str, profile: Dict[str, Any],
                     memory_context: Dict[str, Any],
                     conversation_context: str) -> str:
        """构建个性化回答提示词"""
        pass
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成回答"""
        pass
```

**提示词模板设计**：

```python
PERSONALIZED_RESPONSE_PROMPT = """
你是一个贴心的AI助手，专门为老年人提供个性化服务。

## 用户画像信息
{profile_summary}

## 相关记忆
{memory_context}

## 对话历史
{conversation_context}

## 当前问题
用户：{user_input}

## 回答要求
1. 根据用户画像信息，提供个性化的回答
2. 考虑用户的年龄、健康状况、生活方式等
3. 使用适合老年人的语言风格（简单、亲切、耐心）
4. 如果用户画像中有相关信息，要充分利用
5. 回答要具体、实用、有帮助

请生成个性化回答：
"""
```

**完成标准**：
- ✅ 能够根据用户画像生成个性化回答
- ✅ 回答风格适合老年人
- ✅ 充分利用用户画像信息
- ✅ 回答自然、流畅、有帮助

**注意事项**：
- 使用 DashScope API（与画像提取一致）
- 提示词要清晰，包含所有必要信息
- 考虑回答长度和可读性

---

### 🔄 阶段 5：整合个性化回答到主程序

**目标**：在 agent.py 中集成个性化回答功能

**修改文件**：`code_new/agent.py`

**改造要点**：

```python
def chat_loop(user_id, profile, memory_manager, memu_store):
    # 初始化个性化回答器
    responder = PersonalizedResponder(memu_store, memory_manager)
    
    while True:
        user_input = input("你: ").strip()
        
        # ... 处理命令 ...
        
        # 添加用户消息
        memory_manager.add_message(user_id, "user", user_input)
        
        # 更新画像
        profile = update_profile(user_input, profile)
        memu_store.save_profile(user_id, profile)
        
        # 生成个性化回答
        print("\n[INFO] 正在生成个性化回答...")
        response = responder.generate_response(user_id, user_input, profile)
        
        # 添加助手回答
        memory_manager.add_message(user_id, "assistant", response)
        
        # 显示回答
        print(f"\n助手: {response}\n")
```

**完成标准**：
- ✅ 每次用户输入后自动生成个性化回答
- ✅ 回答基于用户画像和对话历史
- ✅ 回答风格适合老年人
- ✅ 对话历史完整保存

**注意事项**：
- 可以添加开关控制是否生成回答（用于测试）
- 回答生成失败时要有友好提示
- 考虑回答的延迟和用户体验

---

### 🧪 阶段 6：完善角色支持和数据验证

**目标**：完善角色区分，添加数据验证和错误处理

**修改文件**：
- `code_new/memory_store.py` - 确保支持所有角色
- `code_new/chat_memory.py` - 完善角色处理
- `code_new/agent.py` - 画像提取时只处理 user 内容

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

3. **数据验证**：
```python
from profile_schema import UserProfile

def validate_profile(profile: Dict[str, Any]) -> bool:
    """验证画像结构是否符合 schema"""
    try:
        UserProfile.from_dict(profile)
        return True
    except Exception as e:
        print(f"[WARN] 画像结构验证失败: {e}")
        return False
```

**完成标准**：
- ✅ 系统可以区分三种角色
- ✅ 画像提取只使用 user 内容
- ✅ 画像结构验证通过
- ✅ 对话历史包含所有角色

---

### 🧰 阶段 7：健壮性增强和优化

**目标**：提高系统稳定性，优化性能和用户体验

**增强点**：

1. **错误处理**：
   - memU 调用失败时的降级方案
   - 画像提取失败时的处理
   - 回答生成失败时的处理

2. **性能优化**：
   - 画像更新频率控制（避免频繁调用 API）
   - 记忆检索优化（使用缓存）
   - 批量保存机制

3. **用户体验**：
   - 添加进度提示
   - 优化输出格式
   - 添加帮助命令

4. **日志和监控**：
   - 添加操作日志
   - 记录 API 调用次数
   - 监控错误率

**完成标准**：
- ✅ 所有异常都有安全回退
- ✅ 数据不会因异常而丢失
- ✅ 性能满足基本使用需求
- ✅ 用户体验良好

---

## 📁 最终文件结构

```
main/
├── code_new/
│   ├── agent.py                  # 主程序（对话循环 + 个性化回答）
│   ├── memory_store.py           # memU 存储层封装
│   ├── chat_memory.py            # LangChain Memory 封装
│   ├── personalized_response.py  # 个性化回答生成器
│   ├── profile_schema.py         # 画像结构定义 ✅
│   ├── profile_extractor.py      # 画像提取逻辑 ✅
│   ├── test_profile_extraction.py # 测试脚本 ✅
│   ├── test_memory_store.py      # 存储层测试（新建）
│   ├── test_agent.py             # 主程序测试（新建）
│   ├── requirements.txt          # 依赖列表 ✅
│   ├── README.md                 # 使用文档 ✅
│   └── DEVELOPMENT_PLAN.md       # 本文件
├── .env                          # 环境配置（DASHSCOPE_API_KEY, MEMU_API_KEY）
└── memU-main/                    # memU 框架（已安装）
```

---

## 🔄 开发顺序总结

1. **阶段 0**：基础功能 ✅（已完成）
2. **阶段 1**：memU 存储层 🧱（核心基础）
3. **阶段 2**：LangChain Memory 🧠（记忆管理）
4. **阶段 3**：主程序实现 🔁（对话循环）
5. **阶段 4**：个性化回答 🎯（核心功能）
6. **阶段 5**：功能整合 🔄（完整流程）
7. **阶段 6**：角色支持 🧪（完善功能）
8. **阶段 7**：健壮性 🧰（生产就绪）

---

## ⚠️ 重要注意事项

1. **memU 框架集成**：
   - 使用已安装的 memU 框架（memU-main）
   - 配置 DashScope API Key（与画像提取共用）
   - 处理 memU 服务初始化失败的情况

2. **数据存储策略**：
   - 画像：使用 memU 的 document 模式存储
   - 对话：使用 memU 的 conversation 模式存储
   - 记忆检索：使用 memU 的 retrieve 方法

3. **向后兼容**：
   - 保持现有接口不变（`init_profile`, `update_profile`）
   - 新增功能通过新模块实现

4. **测试策略**：
   - 每个阶段完成后独立测试
   - 确保前一阶段功能不受影响
   - 测试 memU 集成是否正常

---

## 🎯 关键实现点

### memU 服务初始化

```python
from memu.app import MemoryService

def create_memu_service():
    """创建 memU 服务实例"""
    # 从环境变量读取 DashScope API Key
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    
    service = MemoryService(
        llm_profiles={
            "default": {
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": dashscope_key,
                "chat_model": "qwen3-max",
                "client_backend": "sdk"
            },
            "embedding": {
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": dashscope_key,
                "embed_model": "text-embedding-v2",
                "client_backend": "sdk"
            }
        },
        database_config={
            "metadata_store": {"provider": "inmemory"},  # 或使用 sqlite/postgres
        },
        retrieve_config={"method": "rag"},
    )
    return service
```

### 画像存储到 memU

```python
async def save_profile_to_memu(service: MemoryService, user_id: str, profile: Dict):
    """将用户画像保存到 memU"""
    # 将画像转换为 JSON 字符串
    profile_json = json.dumps(profile, ensure_ascii=False)
    
    # 创建临时文件或直接使用字符串
    # 使用 memorize 方法存储
    result = await service.memorize(
        resource_url=profile_json,  # 或文件路径
        modality="document",
        user={"user_id": user_id}
    )
    return result
```

---

## 📝 下一步行动

**立即开始阶段 1**：实现 memU 存储层

1. 创建 `memory_store.py`
2. 实现 memU 服务初始化
3. 实现画像和对话的存储/加载
4. 编写测试脚本验证功能

---

**文档创建时间**: 2026-01-22  
**当前进度**: 阶段 0 已完成，准备开始阶段 1

