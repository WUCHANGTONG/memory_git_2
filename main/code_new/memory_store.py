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
            #memU 采用双模型架构：记忆组织靠 LLM，记忆检索靠 embedding
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
            #检索方式配置
            # method="rag": 使用向量检索（embedding-based vector search）
            #   - 快速：纯向量计算，使用余弦相似度
            #   - 可扩展：适用于大型记忆存储
            #   - 返回分数：每个结果包含相似度分数
            # method="llm": 使用 LLM 推理检索
            #   - 深度理解：LLM 理解上下文和细微差别
            #   - 查询重写：在每个层级自动优化查询
            #   - 自适应：当找到足够信息时提前停止
            # 注意：无论使用哪种方式，返回结果中都会包含 needs_retrieval, rewritten_query, 
            # next_step_query 等字段（这些是 route_intention 功能产生的，不是区分检索方式的标志）
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
            
            # 打印完整的 result 结构（用于调试）
            print(f"[DEBUG] 完整 result 结构: {json.dumps(result, ensure_ascii=False, indent=2, default=str)}")
            
            # 调试：打印存储结果
            items_count = len(result.get("items", []))
            resources_count = len(result.get("resources", []))
            resource = result.get("resource")  # 单个资源
            if resource:
                resources_count = 1
            print(f"[DEBUG] 画像存储结果: resource={resources_count}, items={items_count}")
            if resource:
                print(f"[DEBUG] 存储的 resource: id={resource.get('id', 'N/A')}, local_path={resource.get('local_path', 'N/A')}")
            elif result.get("resources"):
                for res in result.get("resources", []):
                    print(f"[DEBUG] 存储的 resource: url={res.get('url', 'N/A')}, id={res.get('id', 'N/A')}")
            
            # 立即验证：尝试检索刚存储的数据
            print(f"[DEBUG] 开始验证存储是否成功（立即检索）...")
            try:
                import asyncio
                await asyncio.sleep(0.5)  # 等待一小段时间确保数据已持久化
                
                # 调试：打印当前检索配置
                current_method = service.retrieve_config.method
                print(f"[DEBUG] 验证存储时的检索方式: method={current_method}")
                
                verify_result = await service.retrieve(
                    queries=[{"role": "user", "content": {"text": f"用户 {user_id} 的画像信息"}}],
                    where={"user_id": user_id}
                )
                
                verify_items_count = len(verify_result.get("items", []))
                verify_resources_count = len(verify_result.get("resources", []))
                verify_categories_count = len(verify_result.get("categories", []))
                
                print(f"[DEBUG] 检索验证结果: items={verify_items_count}, resources={verify_resources_count}, categories={verify_categories_count}")
                
                if verify_resources_count > 0 or verify_items_count > 0:
                    print(f"[INFO] ✅ 存储验证成功: 可以检索到存储的数据")
                    if verify_resources_count > 0:
                        print(f"[INFO]   - 找到 {verify_resources_count} 个资源")
                    if verify_items_count > 0:
                        print(f"[INFO]   - 找到 {verify_items_count} 个记忆项")
                else:
                    print(f"[WARN] ⚠️  存储验证: 暂时无法检索到数据（可能需要更多时间持久化，或数据未正确存储）")
                    
            except Exception as e:
                print(f"[DEBUG] 检索验证失败: {e}")
                import traceback
                traceback.print_exc()
            
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
        # 尝试从本地缓存加载的辅助函数
        def try_load_from_cache() -> Optional[Dict[str, Any]]:
            """尝试从本地缓存加载画像"""
            if self.use_local_cache:
                try:
                    cached_profile = self._load_profile_from_cache(user_id)
                    if cached_profile:
                        return cached_profile.get("profile")
                except Exception as e2:
                    print(f"[ERROR] 从本地缓存加载也失败: {e2}")
            return None
        
        # 标志变量：记录是否已经尝试过缓存
        cache_tried = False
        
        try:
            service = self._get_service()
            
            # 使用 retrieve 查询用户画像
            queries = [
                {"role": "user", "content": {"text": f"用户 {user_id} 的画像信息"}}
            ]
            
            # 调试：打印当前检索配置
            current_method = service.retrieve_config.method
            print(f"[DEBUG] 当前检索方式配置: method={current_method}")
            print(f"[DEBUG] retrieve_config 完整配置: {service.retrieve_config.model_dump()}")
            
            result = await service.retrieve(
                queries=queries,
                where={"user_id": user_id}
            )
            
            # 在返回结果中添加 method 信息以便调试
            result["_debug_retrieve_method"] = current_method
            
            # 调试：打印检索结果
            print(f"[DEBUG] retrieve 返回结果: categories={len(result.get('categories', []))}, "
                  f"items={len(result.get('items', []))}, resources={len(result.get('resources', []))}")
            print(f"[DEBUG] 实际使用的检索方式: {current_method} (RAG=向量检索, LLM=LLM推理检索)")
            
            # 从检索结果中提取画像
            # 查找包含 profile 信息的资源
            resources = result.get("resources", [])
            items = result.get("items", [])
            categories = result.get("categories", [])
            
            # 调试：打印详细信息
            if resources:
                print(f"[DEBUG] resources 数量: {len(resources)}")
                for idx, res in enumerate(resources[:3]):  # 只打印前3个
                    print(f"[DEBUG] resource[{idx}]: url={res.get('url', 'N/A')}, modality={res.get('modality', 'N/A')}")
            if items:
                print(f"[DEBUG] items 数量: {len(items)}")
                for idx, item in enumerate(items[:3]):  # 只打印前3个
                    print(f"[DEBUG] item[{idx}]: summary={item.get('summary', 'N/A')[:100]}")
            
            # 优先从 resources 中查找画像（因为画像是以 document modality 存储的）
            profile_found = False
            for resource in resources:
                url = resource.get("url", "")
                modality = resource.get("modality", "")
                local_path = resource.get("local_path", "")
                # 检查是否是画像文件
                if ("profile" in url.lower() or "profile" in local_path.lower()) and modality == "document":
                    try:
                        # 尝试读取文件内容（优先使用local_path，如果没有则使用url）
                        import json
                        from pathlib import Path
                        file_path = Path(local_path) if local_path else Path(url)
                        if file_path.exists():
                            profile_data = json.loads(file_path.read_text(encoding='utf-8'))
                            if "profile" in profile_data:
                                print(f"[INFO] 从 resource 中找到画像: {file_path}")
                                return profile_data.get("profile")
                    except Exception as e:
                        print(f"[DEBUG] 读取 resource 文件失败: {e}")
            
            # 如果retrieve没有返回resources，尝试直接查询database中的resources
            if not resources:
                print(f"[DEBUG] retrieve未返回resources，尝试直接查询database...")
                try:
                    store = service._get_database()
                    where_filters = {"user_id": user_id}
                    all_resources = store.resource_repo.list_resources(where_filters)
                    print(f"[DEBUG] 直接查询到 {len(all_resources)} 个resources")
                    for res_id, resource in all_resources.items():
                        url = resource.url
                        modality = resource.modality
                        local_path = resource.local_path
                        if ("profile" in url.lower() or (local_path and "profile" in local_path.lower())) and modality == "document":
                            try:
                                import json
                                from pathlib import Path
                                file_path = Path(local_path) if local_path else Path(url)
                                if file_path.exists():
                                    profile_data = json.loads(file_path.read_text(encoding='utf-8'))
                                    if "profile" in profile_data:
                                        print(f"[INFO] 从直接查询的resource中找到画像: {file_path}")
                                        return profile_data.get("profile")
                            except Exception as e:
                                print(f"[DEBUG] 读取直接查询的resource文件失败: {e}")
                except Exception as e:
                    print(f"[DEBUG] 直接查询resources失败: {e}")
            
            # 尝试从 items 中提取画像（items是memU从document中提取的记忆项）
            for item in items:
                summary = item.get("summary", "")
                if "profile" in summary.lower() or "画像" in summary:
                    # items通常不包含完整的JSON，所以这里只是标记找到了相关记忆
                    profile_found = True
                    print(f"[DEBUG] 在items中找到相关记忆，但无法直接提取完整画像: {summary[:100]}")
            
            # 如果 memU 中没有找到画像，打印提示并尝试从本地缓存加载
            if not profile_found:
                print(f"[WARN] memU 中未找到用户 {user_id} 的画像信息")
                cached_profile = try_load_from_cache()
                cache_tried = True
                if cached_profile:
                    return cached_profile
            
            return None
            
        except Exception as e:
            print(f"[ERROR] 从 memU 加载画像失败: {e}")
            # 降级到本地缓存（仅在未尝试过缓存时）
            if not cache_tried:
                cached_profile = try_load_from_cache()
                if cached_profile:
                    return cached_profile
            else:
                print(f"[INFO] 已尝试过本地缓存，跳过重复尝试")
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
            
            # 使用 retrieve 查询对话历史（使用英文查询以匹配 caption）
            queries = [
                {"role": "user", "content": {"text": "user conversation history"}}
            ]
            
            # 调试：打印当前检索配置
            current_method = service.retrieve_config.method
            print(f"[DEBUG] 当前检索方式配置: method={current_method}")
            
            result = await service.retrieve(
                queries=queries,
                where={"user_id": user_id}
            )
            
            # 在返回结果中添加 method 信息以便调试
            result["_debug_retrieve_method"] = current_method
            
            # 从检索结果中提取对话
            resources = result.get("resources", [])
            items = result.get("items", [])
            
            conversation_messages = []
            
            # 优先从 resources 中查找对话（对话是以 conversation modality 存储的）
            for resource in resources:
                modality = resource.get("modality", "")
                local_path = resource.get("local_path", "")
                url = resource.get("url", "")
                
                # 检查是否是对话资源
                if modality == "conversation":
                    try:
                        import json
                        from pathlib import Path
                        # 优先使用 local_path，如果没有则使用 url
                        file_path = Path(local_path) if local_path else Path(url)
                        if file_path.exists():
                            # 读取对话文件（可能是 JSON 格式）
                            content = file_path.read_text(encoding='utf-8')
                            # 尝试解析为 JSON
                            try:
                                parsed = json.loads(content)
                                # 如果是列表，直接使用
                                if isinstance(parsed, list):
                                    conversation_messages.extend(parsed)
                                # 如果是字典，尝试提取 messages 或 content
                                elif isinstance(parsed, dict):
                                    if "messages" in parsed:
                                        conversation_messages.extend(parsed["messages"])
                                    elif "content" in parsed and isinstance(parsed["content"], list):
                                        conversation_messages.extend(parsed["content"])
                            except json.JSONDecodeError:
                                # 如果不是 JSON，可能是文本格式，尝试解析
                                # 这里可以根据实际格式进行解析
                                pass
                    except Exception as e:
                        print(f"[DEBUG] 读取对话 resource 文件失败: {e}")
            
            # 如果从 resources 中找到了对话，返回
            if conversation_messages:
                # 按时间戳排序（如果有）
                try:
                    conversation_messages.sort(key=lambda x: x.get("timestamp", "") or x.get("created_at", ""))
                except:
                    pass
                return conversation_messages[:limit]
            
            # 如果 memU 中没有找到对话，尝试从本地缓存加载
            if self.use_local_cache:
                print(f"从本地加载历史对话")
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
            
            # 调试：打印当前检索配置
            current_method = service.retrieve_config.method
            print(f"[DEBUG] 当前检索方式配置: method={current_method}")
            
            result = await service.retrieve(
                queries=queries,
                where={"user_id": user_id}
            )
            
            # 在返回结果中添加 method 信息以便调试
            result["_debug_retrieve_method"] = current_method
            
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

