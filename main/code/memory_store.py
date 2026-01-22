"""
memU Cloud API 存储层封装（本地缓存实现）

当前版本：先实现本地缓存功能，后续集成 memU API。

功能：
- 用户画像存储和加载（本地 JSON 文件）
- 对话历史存储（本地 JSON 文件）
- 多用户支持（通过 user_id 隔离）
- 为后续集成 memU API 预留接口
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# 加载环境变量（为后续 memU API 集成做准备）
load_dotenv()


class MemoryStore:
    """
    memU 存储层（当前版本：本地缓存实现）
    
    功能：
    - 用户画像存储和加载（本地 JSON 文件）
    - 对话历史存储（本地 JSON 文件）
    - 多用户支持（通过 user_id 隔离）
    - 为后续集成 memU API 预留接口
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化 MemoryStore
        
        Args:
            base_path: 本地缓存基础路径，如果为None则自动基于脚本位置确定
        """
        # 本地缓存路径：基于脚本文件位置，确保路径正确
        if base_path is None:
            # 基于当前脚本位置确定数据目录
            # memory_store.py 在 code/ 目录下，数据目录应该是 code/data/
            script_dir = Path(__file__).parent
            self.base_path = script_dir / "data"
        else:
            # 如果提供了路径，使用提供的路径（支持相对路径和绝对路径）
            self.base_path = Path(base_path)
        self.profiles_dir = self.base_path / "profiles"
        self.conversations_dir = self.base_path / "conversations"
        
        # 确保目录存在
        self.ensure_directories()
        
        # 为后续 memU API 集成预留
        self.memu_service = None
        self.memu_api_key = os.getenv("MEMU_API_KEY", "")
    
    def ensure_directories(self) -> None:
        """确保缓存目录存在"""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
    
    # ========== 用户画像相关方法 ==========
    
    def save_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """
        保存用户画像到本地缓存
        
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
            
            # 保存到本地缓存
            cache_path = self.profiles_dir / f"{user_id}.json"
            
            # 先备份旧文件（如果存在）
            if cache_path.exists():
                backup_path = cache_path.with_suffix('.json.bak')
                try:
                    cache_path.rename(backup_path)
                except Exception:
                    pass  # 备份失败不影响主流程
            
            # 写入新文件
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            
            # 删除备份文件（保存成功）
            backup_path = cache_path.with_suffix('.json.bak')
            if backup_path.exists():
                try:
                    backup_path.unlink()
                except Exception:
                    pass  # 删除备份失败不影响主流程
            
            return True
            
        except Exception as e:
            print(f"❌ 保存用户画像失败: {e}")
            # 尝试恢复备份
            cache_path = self.profiles_dir / f"{user_id}.json"
            backup_path = cache_path.with_suffix('.json.bak')
            if backup_path.exists():
                try:
                    backup_path.rename(cache_path)
                    print("   已恢复备份文件")
                except Exception:
                    pass
            return False
    
    def load_profile(self, user_id: str) -> Dict[str, Any]:
        """
        加载用户画像（从本地缓存）
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict: 用户画像字典，如果不存在则返回空字典
        """
        cache_path = self.profiles_dir / f"{user_id}.json"
        
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 返回 profile 字段，如果没有则返回整个数据
                    return data.get("profile", data)
            except json.JSONDecodeError as e:
                print(f"⚠️  用户画像 JSON 解析失败: {e}")
                # 尝试恢复备份
                backup_path = cache_path.with_suffix('.json.bak')
                if backup_path.exists():
                    try:
                        backup_path.rename(cache_path)
                        print("   已恢复备份文件，请重试")
                    except Exception:
                        pass
            except Exception as e:
                print(f"⚠️  加载用户画像失败: {e}")
        
        # 文件不存在或加载失败，返回空字典
        return {}
    
    def get_profile_path(self, user_id: str) -> Path:
        """
        获取用户画像文件路径
        
        Args:
            user_id: 用户ID
        
        Returns:
            Path: 画像文件路径
        """
        return self.profiles_dir / f"{user_id}.json"
    
    # ========== 对话历史相关方法 ==========
    
    def append_message(self, user_id: str, role: str, content: str, 
                      timestamp: Optional[str] = None) -> bool:
        """
        追加一条对话消息到本地缓存
        
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
            cache_path = self.conversations_dir / f"{user_id}.json"
            messages = []
            
            # 加载现有消息
            if cache_path.exists():
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        messages = json.load(f)
                        # 确保是列表格式
                        if not isinstance(messages, list):
                            messages = []
                except json.JSONDecodeError:
                    # JSON 损坏，从空列表开始
                    messages = []
                except Exception as e:
                    print(f"⚠️  加载对话历史失败: {e}")
                    messages = []
            
            # 追加新消息
            messages.append(message)
            
            # 保存到文件
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ 保存对话消息失败: {e}")
            return False
    
    def load_conversation(self, user_id: str) -> List[Dict[str, Any]]:
        """
        加载用户对话历史（从本地缓存）
        
        Args:
            user_id: 用户ID
        
        Returns:
            List[Dict]: 对话消息列表，如果不存在则返回空列表
        """
        cache_path = self.conversations_dir / f"{user_id}.json"
        
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                    # 确保返回列表
                    if isinstance(messages, list):
                        return messages
                    else:
                        return []
            except json.JSONDecodeError as e:
                print(f"⚠️  对话历史 JSON 解析失败: {e}")
            except Exception as e:
                print(f"⚠️  加载对话历史失败: {e}")
        
        # 文件不存在或加载失败，返回空列表
        return []
    
    def get_conversation_path(self, user_id: str) -> Path:
        """
        获取对话历史文件路径
        
        Args:
            user_id: 用户ID
        
        Returns:
            Path: 对话历史文件路径
        """
        return self.conversations_dir / f"{user_id}.json"
    
    # ========== 工具方法 ==========
    
    def user_exists(self, user_id: str) -> bool:
        """
        检查用户是否存在（是否有画像或对话历史）
        
        Args:
            user_id: 用户ID
        
        Returns:
            bool: 用户是否存在
        """
        profile_path = self.get_profile_path(user_id)
        conversation_path = self.get_conversation_path(user_id)
        return profile_path.exists() or conversation_path.exists()
    
    def delete_user_data(self, user_id: str) -> bool:
        """
        删除用户的所有数据（画像和对话历史）
        
        Args:
            user_id: 用户ID
        
        Returns:
            bool: 是否删除成功
        """
        success = True
        
        # 删除画像
        profile_path = self.get_profile_path(user_id)
        if profile_path.exists():
            try:
                profile_path.unlink()
            except Exception as e:
                print(f"⚠️  删除画像文件失败: {e}")
                success = False
        
        # 删除对话历史
        conversation_path = self.get_conversation_path(user_id)
        if conversation_path.exists():
            try:
                conversation_path.unlink()
            except Exception as e:
                print(f"⚠️  删除对话历史文件失败: {e}")
                success = False
        
        return success


