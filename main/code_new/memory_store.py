"""
memU 存储层封装

基于 memU 框架实现用户画像和对话历史的持久化存储。
支持多用户隔离、画像存储、对话记录和记忆检索。
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime
from dotenv import load_dotenv

# 尝试导入 memU
if TYPE_CHECKING:
    from memu.app import MemoryService

try:
    from memu.app import MemoryService
    MEMU_AVAILABLE = True
except ImportError:
    MEMU_AVAILABLE = False
    MemoryService = None  # 类型占位符
    print("[WARN] memU 未安装，请安装: pip install -e ../memU-main")

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


class MemUStore:
    """
    基于 memU 框架的记忆存储层
    
    功能：
    - 用户画像存储和加载（使用 document modality）
    - 对话历史存储（使用 conversation modality）
    - 记忆检索（用于个性化回答）
    - 多用户支持（通过 user_id 隔离）
    """
    
    def __init__(self, memu_service: Optional[Any] = None, 
                 use_local_cache: bool = True):
        """
        初始化 memU 存储层
        
        Args:
            memu_service: memU 服务实例，如果为 None 则自动创建
            use_local_cache: 是否使用本地缓存作为备份
        """
        self.use_local_cache = use_local_cache
        self._service = memu_service
        self._temp_dir = None
        
        # 本地缓存路径（可选）
        if use_local_cache:
            cache_dir = Path(__file__).parent / "data"
            self.cache_dir = cache_dir
            self.profiles_cache = cache_dir / "profiles"
            self.conversations_cache = cache_dir / "conversations"
            self._ensure_cache_directories()
    
    def _ensure_cache_directories(self):
        """确保缓存目录存在"""
        if self.use_local_cache:
            self.profiles_cache.mkdir(parents=True, exist_ok=True)
            self.conversations_cache.mkdir(parents=True, exist_ok=True)
    
    def _get_service(self) -> MemoryService:
        """获取或创建 memU 服务实例"""
        if self._service is None:
            self._service = self._create_service()
        return self._service
    
    def _create_service(self) -> MemoryService:
        """
        创建 memU 服务实例
        
        使用 DashScope API 配置
        """
        if not MEMU_AVAILABLE:
            raise ImportError("memU 未安装，请先安装 memU 框架")
        
        dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")
        if not dashscope_key:
            raise ValueError("未设置 DASHSCOPE_API_KEY，请在 .env 文件中配置")
        
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
                "metadata_store": {
                    "provider": "postgres",
                    "dsn": os.getenv(
                        "MEMU_DATABASE_URL",
                        "postgresql://memu:memu123@localhost:5433/memu_db"
                    )
                },
            },
            retrieve_config={"method": "rag"},
        )
        return service
    
    def _get_temp_dir(self) -> Path:
        """获取临时目录（用于存储临时文件）"""
        if self._temp_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp())
        return self._temp_dir
    
    # ========== 用户画像相关方法 ==========
    
    async def save_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """
        保存用户画像到 memU
        
        策略：将画像转换为 JSON 字符串，创建临时文件，使用 document modality 存储
        
        Args:
            user_id: 用户ID
            profile: 用户画像字典
            
        Returns:
            bool: 是否保存成功
        """
        try:
            service = self._get_service()
            
            # 准备画像数据（添加元数据）
            profile_data = {
                "user_id": user_id,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "profile": profile
            }
            
            # 将画像转换为 JSON 字符串
            profile_json = json.dumps(profile_data, ensure_ascii=False, indent=2)
            
            # 创建临时文件
            temp_dir = self._get_temp_dir()
            temp_file = temp_dir / f"profile_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            temp_file.write_text(profile_json, encoding='utf-8')
            
            # 使用 memU 存储（document modality）
            result = await service.memorize(
                resource_url=str(temp_file),
                modality="document",
                user={"user_id": user_id}
            )
            
            # 同时保存到本地缓存（如果启用）
            if self.use_local_cache:
                self._save_profile_to_cache(user_id, profile_data)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 保存画像到 memU 失败: {e}")
            # 降级到本地缓存
            if self.use_local_cache:
                try:
                    profile_data = {
                        "user_id": user_id,
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "profile": profile
                    }
                    self._save_profile_to_cache(user_id, profile_data)
                    print(f"[INFO] 已保存到本地缓存")
                    return True
                except Exception as e2:
                    print(f"[ERROR] 保存到本地缓存也失败: {e2}")
            return False
    
    async def load_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        从 memU 加载用户画像
        
        策略：使用 retrieve 查询用户的最新画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict]: 用户画像字典，如果不存在则返回 None
        """
        try:
            service = self._get_service()
            
            # 使用 retrieve 查询用户画像
            queries = [
                {"role": "user", "content": {"text": f"用户 {user_id} 的画像信息"}}
            ]
            
            result = await service.retrieve(
                queries=queries,
                where={"user_id": user_id}
            )
            
            # 从检索结果中提取画像
            # 查找包含 profile 信息的资源
            resources = result.get("resources", [])
            items = result.get("items", [])
            
            # 尝试从 items 中提取画像
            for item in items:
                if "profile" in item.get("summary", "").lower() or "画像" in item.get("summary", ""):
                    # 尝试解析 JSON
                    try:
                        # 这里需要根据实际返回格式解析
                        # 暂时返回 None，需要进一步处理
                        pass
                    except:
                        pass
            
            # 如果 memU 中没有，尝试从本地缓存加载
            if self.use_local_cache:
                cached_profile = self._load_profile_from_cache(user_id)
                if cached_profile:
                    return cached_profile.get("profile")
            
            return None
            
        except Exception as e:
            print(f"[ERROR] 从 memU 加载画像失败: {e}")
            # 降级到本地缓存
            if self.use_local_cache:
                try:
                    cached_profile = self._load_profile_from_cache(user_id)
                    if cached_profile:
                        return cached_profile.get("profile")
                except Exception as e2:
                    print(f"[ERROR] 从本地缓存加载也失败: {e2}")
            return None
    
    # ========== 对话历史相关方法 ==========
    
    async def append_message(self, user_id: str, role: str, content: str,
                           timestamp: Optional[str] = None) -> bool:
        """
        追加一条对话消息到 memU
        
        策略：将对话组织成 conversation 格式，使用 conversation modality 存储
        
        Args:
            user_id: 用户ID
            role: 角色（user/assistant/system）
            content: 消息内容
            timestamp: 时间戳，如果为 None 则使用当前时间
            
        Returns:
            bool: 是否保存成功
        """
        try:
            service = self._get_service()
            
            # 准备时间戳
            if timestamp is None:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 创建对话消息
            message = {
                "timestamp": timestamp,
                "role": role,
                "content": content
            }
            
            # 加载现有对话（如果存在）
            existing_conversation = await self.load_conversation(user_id)
            if existing_conversation:
                existing_conversation.append(message)
            else:
                existing_conversation = [message]
            
            # 创建对话 JSON 文件
            conversation_data = {
                "user_id": user_id,
                "messages": existing_conversation
            }
            
            conversation_json = json.dumps(conversation_data, ensure_ascii=False, indent=2)
            
            # 创建临时文件
            temp_dir = self._get_temp_dir()
            temp_file = temp_dir / f"conversation_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            temp_file.write_text(conversation_json, encoding='utf-8')
            
            # 使用 memU 存储（conversation modality）
            result = await service.memorize(
                resource_url=str(temp_file),
                modality="conversation",
                user={"user_id": user_id}
            )
            
            # 同时保存到本地缓存
            if self.use_local_cache:
                self._save_conversation_to_cache(user_id, existing_conversation)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 保存对话到 memU 失败: {e}")
            # 降级到本地缓存
            if self.use_local_cache:
                try:
                    existing_conversation = self._load_conversation_from_cache(user_id) or []
                    if timestamp is None:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    existing_conversation.append({
                        "timestamp": timestamp,
                        "role": role,
                        "content": content
                    })
                    self._save_conversation_to_cache(user_id, existing_conversation)
                    print(f"[INFO] 已保存到本地缓存")
                    return True
                except Exception as e2:
                    print(f"[ERROR] 保存到本地缓存也失败: {e2}")
            return False
    
    async def load_conversation(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        从 memU 加载用户对话历史
        
        策略：使用 retrieve 查询用户的对话历史
        
        Args:
            user_id: 用户ID
            limit: 返回的最大消息数量
            
        Returns:
            List[Dict]: 对话消息列表
        """
        try:
            service = self._get_service()
            
            # 使用 retrieve 查询对话历史
            queries = [
                {"role": "user", "content": {"text": f"用户 {user_id} 的对话历史"}}
            ]
            
            result = await service.retrieve(
                queries=queries,
                where={"user_id": user_id}
            )
            
            # 从检索结果中提取对话
            # 这里需要根据实际返回格式解析
            # 暂时返回空列表，需要进一步处理
            
            # 如果 memU 中没有，尝试从本地缓存加载
            if self.use_local_cache:
                cached_conversation = self._load_conversation_from_cache(user_id)
                if cached_conversation:
                    return cached_conversation[:limit]
            
            return []
            
        except Exception as e:
            print(f"[ERROR] 从 memU 加载对话失败: {e}")
            # 降级到本地缓存
            if self.use_local_cache:
                try:
                    cached_conversation = self._load_conversation_from_cache(user_id)
                    if cached_conversation:
                        return cached_conversation[:limit]
                except Exception as e2:
                    print(f"[ERROR] 从本地缓存加载也失败: {e2}")
            return []
    
    # ========== 记忆检索相关方法 ==========
    
    async def get_user_memory(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        使用 memU 检索用户记忆
        
        用于个性化回答时检索相关记忆
        
        Args:
            user_id: 用户ID
            query: 查询文本
            
        Returns:
            Dict: 检索结果，包含 categories, items, resources 等
        """
        try:
            service = self._get_service()
            
            queries = [
                {"role": "user", "content": {"text": query}}
            ]
            
            result = await service.retrieve(
                queries=queries,
                where={"user_id": user_id}
            )
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 检索用户记忆失败: {e}")
            return {
                "categories": [],
                "items": [],
                "resources": []
            }
    
    # ========== 本地缓存辅助方法 ==========
    
    def _save_profile_to_cache(self, user_id: str, profile_data: Dict[str, Any]):
        """保存画像到本地缓存"""
        cache_file = self.profiles_cache / f"{user_id}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)
    
    def _load_profile_from_cache(self, user_id: str) -> Optional[Dict[str, Any]]:
        """从本地缓存加载画像"""
        cache_file = self.profiles_cache / f"{user_id}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] 读取缓存文件失败: {e}")
        return None
    
    def _save_conversation_to_cache(self, user_id: str, conversation: List[Dict[str, Any]]):
        """保存对话到本地缓存"""
        cache_file = self.conversations_cache / f"{user_id}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(conversation, f, ensure_ascii=False, indent=2)
    
    def _load_conversation_from_cache(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """从本地缓存加载对话"""
        cache_file = self.conversations_cache / f"{user_id}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] 读取缓存文件失败: {e}")
        return None
    
    # ========== 工具方法 ==========
    
    def ensure_service_ready(self):
        """确保 memU 服务已初始化"""
        try:
            self._get_service()
            return True
        except Exception as e:
            print(f"[ERROR] memU 服务初始化失败: {e}")
            return False

