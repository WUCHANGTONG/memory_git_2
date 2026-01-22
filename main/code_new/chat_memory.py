"""
LangChain Memory 封装模块

为每个用户创建独立的 LangChain Memory 实例，与 memU 存储层同步。
支持 user/assistant/system 三种角色，自动加载和保存对话历史。
"""

import asyncio
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime

# 尝试导入 LangChain
if TYPE_CHECKING:
    # 类型检查时的占位符
    class ConversationBufferMemory:
        pass

try:
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
    LANGCHAIN_AVAILABLE = True
    
    # 创建一个简单的 Memory 实现（兼容 LangChain Memory 接口）
    class ConversationBufferMemory:
        """简单的对话缓冲区 Memory 实现"""
        def __init__(self, return_messages=True, memory_key="chat_history"):
            self.return_messages = return_messages
            self.memory_key = memory_key
            self.chat_memory = type('ChatMemory', (), {})()
            self.chat_memory.messages = []
            
            # 添加消息的方法
            def add_user(content):
                self.chat_memory.messages.append(HumanMessage(content=content))
            
            def add_ai(content):
                self.chat_memory.messages.append(AIMessage(content=content))
            
            self.chat_memory.add_user_message = add_user
            self.chat_memory.add_ai_message = add_ai
            
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ConversationBufferMemory = None  # 类型占位符
    HumanMessage = None
    AIMessage = None
    SystemMessage = None
    BaseMessage = None
    print("[WARN] langchain 未安装，部分功能可能不可用")
    print("      请安装: pip install langchain langchain-community")

from memory_store import MemUStore


class ChatMemoryManager:
    """
    LangChain Memory 管理器，与 memU 存储层同步
    
    功能：
    - 为每个用户创建独立的 Memory 实例
    - 自动从 memU 加载历史对话
    - 新增对话同步更新 Memory 和 memU
    - 支持 user/assistant/system 三种角色
    """
    
    def __init__(self, memu_store: MemUStore):
        """
        初始化 Memory 管理器
        
        Args:
            memu_store: memU 存储层实例
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("langchain 未安装，请先安装: pip install langchain")
        
        self.memu_store = memu_store
        self._memories: Dict[str, ConversationBufferMemory] = {}
    
    def get_memory_for_user(self, user_id: str) -> ConversationBufferMemory:
        """
        获取或创建用户的 Memory 实例
        
        Args:
            user_id: 用户ID
            
        Returns:
            ConversationBufferMemory: 用户的 Memory 实例
        """
        if user_id not in self._memories:
            # 创建新的 Memory 实例
            # return_messages=True 表示返回消息对象而不是字符串
            self._memories[user_id] = ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history"
            )
        return self._memories[user_id]
    
    async def add_message(self, user_id: str, role: str, content: str,
                         timestamp: Optional[str] = None) -> bool:
        """
        添加消息到 Memory 和 memU
        
        Args:
            user_id: 用户ID
            role: 角色（user/assistant/system）
            content: 消息内容
            timestamp: 时间戳，如果为 None 则使用当前时间
            
        Returns:
            bool: 是否添加成功
        """
        if not LANGCHAIN_AVAILABLE:
            # 如果 LangChain 不可用，只保存到 memU
            return await self.memu_store.append_message(user_id, role, content, timestamp)
        
        try:
            # 获取用户的 Memory 实例
            memory = self.get_memory_for_user(user_id)
            
            # 根据角色创建对应的消息对象并保存到 Memory
            if role == "user":
                message = HumanMessage(content=content)
                # 保存到 Memory
                memory.chat_memory.add_user_message(content)
            elif role == "assistant":
                message = AIMessage(content=content)
                # 保存到 Memory
                memory.chat_memory.add_ai_message(content)
            elif role == "system":
                message = SystemMessage(content=content)
                # 将 system 消息添加到消息历史中
                memory.chat_memory.messages.append(message)
            else:
                print(f"[WARN] 未知的角色: {role}，使用 user 角色")
                message = HumanMessage(content=content)
                memory.chat_memory.add_user_message(content)
            
            # 同步保存到 memU
            success = await self.memu_store.append_message(user_id, role, content, timestamp)
            
            return success
            
        except Exception as e:
            print(f"[ERROR] 添加消息失败: {e}")
            # 即使 Memory 失败，也尝试保存到 memU
            return await self.memu_store.append_message(user_id, role, content, timestamp)
    
    async def load_history_into_memory(self, user_id: str) -> bool:
        """
        从 memU 加载历史对话到 Memory
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否加载成功
        """
        if not LANGCHAIN_AVAILABLE:
            print("[WARN] LangChain 不可用，跳过 Memory 加载")
            return False
        
        try:
            # 从 memU 加载对话历史
            conversation_history = await self.memu_store.load_conversation(user_id)
            
            if not conversation_history:
                print(f"[INFO] 用户 {user_id} 没有历史对话")
                return True
            
            # 获取用户的 Memory 实例
            memory = self.get_memory_for_user(user_id)
            
            # 按时间戳顺序恢复对话
            # 确保按时间排序
            sorted_messages = sorted(
                conversation_history,
                key=lambda x: x.get("timestamp", "")
            )
            
            # 将历史消息添加到 Memory
            for msg in sorted_messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "user":
                    memory.chat_memory.add_user_message(content)
                elif role == "assistant":
                    memory.chat_memory.add_ai_message(content)
                elif role == "system":
                    # 处理 system 消息
                    if not hasattr(memory.chat_memory, 'messages'):
                        memory.chat_memory.messages = []
                    memory.chat_memory.messages.append(SystemMessage(content=content))
            
            print(f"[OK] 已加载 {len(sorted_messages)} 条历史对话到 Memory")
            return True
            
        except Exception as e:
            print(f"[ERROR] 加载历史对话到 Memory 失败: {e}")
            return False
    
    async def save_current_memory(self, user_id: str) -> bool:
        """
        将当前 Memory 内容保存到 memU
        
        注意：由于 add_message 已经同步保存，这个方法主要用于确保数据一致性
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否保存成功
        """
        if not LANGCHAIN_AVAILABLE:
            return True
        
        try:
            memory = self.get_memory_for_user(user_id)
            
            # 获取 Memory 中的所有消息
            messages = memory.chat_memory.messages if hasattr(memory.chat_memory, 'messages') else []
            
            # 由于 add_message 已经同步保存，这里主要是验证
            # 如果需要，可以重新保存所有消息
            print(f"[INFO] Memory 中有 {len(messages)} 条消息")
            return True
            
        except Exception as e:
            print(f"[ERROR] 保存 Memory 失败: {e}")
            return False
    
    def get_conversation_context(self, user_id: str, limit: int = 10) -> str:
        """
        获取对话上下文（用于画像提取和个性化回答）
        
        Args:
            user_id: 用户ID
            limit: 返回最近 N 条消息
            
        Returns:
            str: 对话上下文字符串
        """
        if not LANGCHAIN_AVAILABLE:
            # 如果 LangChain 不可用，从 memU 加载
            try:
                loop = asyncio.get_event_loop()
                conversation = loop.run_until_complete(
                    self.memu_store.load_conversation(user_id, limit=limit)
                )
                return self._format_conversation(conversation)
            except:
                return ""
        
        try:
            memory = self.get_memory_for_user(user_id)
            messages = memory.chat_memory.messages if hasattr(memory.chat_memory, 'messages') else []
            
            # 获取最近的消息
            recent_messages = messages[-limit:] if len(messages) > limit else messages
            
            # 格式化为字符串
            context_parts = []
            for msg in recent_messages:
                if isinstance(msg, HumanMessage):
                    context_parts.append(f"用户：{msg.content}")
                elif isinstance(msg, AIMessage):
                    context_parts.append(f"助手：{msg.content}")
                elif isinstance(msg, SystemMessage):
                    context_parts.append(f"系统：{msg.content}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"[ERROR] 获取对话上下文失败: {e}")
            return ""
    
    def _format_conversation(self, conversation: List[Dict[str, Any]]) -> str:
        """格式化对话列表为字符串"""
        parts = []
        for msg in conversation:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                parts.append(f"用户：{content}")
            elif role == "assistant":
                parts.append(f"助手：{content}")
            elif role == "system":
                parts.append(f"系统：{content}")
        return "\n".join(parts)
    
    def get_memory_messages(self, user_id: str) -> List[BaseMessage]:
        """
        获取用户的 Memory 消息列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[BaseMessage]: 消息列表
        """
        if not LANGCHAIN_AVAILABLE:
            return []
        
        try:
            memory = self.get_memory_for_user(user_id)
            return memory.chat_memory.messages if hasattr(memory.chat_memory, 'messages') else []
        except Exception as e:
            print(f"[ERROR] 获取 Memory 消息失败: {e}")
            return []
    
    def clear_memory(self, user_id: str):
        """
        清空用户的 Memory（不删除 memU 中的数据）
        
        Args:
            user_id: 用户ID
        """
        if user_id in self._memories:
            del self._memories[user_id]
            print(f"[INFO] 已清空用户 {user_id} 的 Memory")

