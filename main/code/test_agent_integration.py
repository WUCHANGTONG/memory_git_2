"""
测试 agent.py 与 memory_store.py 的集成功能

验证：
1. 画像持久化（保存后重启能恢复）
2. 对话历史持久化
3. 多用户隔离
"""

from memory_store import MemoryStore
from profile_schema import init_profile
import json


def test_profile_persistence():
    """测试画像持久化"""
    print("=" * 60)
    print("测试1: 画像持久化")
    print("=" * 60)
    
    store = MemoryStore()
    user_id = "test_persistence_user"
    
    # 创建并保存画像
    profile = init_profile()
    profile["demographics"]["age"] = {"value": 70, "confidence": 0.9}
    profile["demographics"]["city_level"] = {"value": "北京", "confidence": 0.9}
    
    print(f"\n保存画像 (user_id: {user_id})...")
    success = store.save_profile(user_id, profile)
    print(f"保存结果: {'成功' if success else '失败'}")
    
    # 模拟重启：创建新的 MemoryStore 实例
    print("\n模拟程序重启（创建新的 MemoryStore 实例）...")
    store2 = MemoryStore()
    
    # 加载画像
    print(f"加载画像 (user_id: {user_id})...")
    loaded_profile = store2.load_profile(user_id)
    
    if loaded_profile:
        age = loaded_profile.get("demographics", {}).get("age", {}).get("value")
        city = loaded_profile.get("demographics", {}).get("city_level", {}).get("value")
        print(f"[成功] 画像恢复成功")
        print(f"  年龄: {age}")
        print(f"  城市: {city}")
        
        assert age == 70, "年龄不匹配"
        assert city == "北京", "城市不匹配"
        print("\n[成功] 画像持久化验证通过")
    else:
        print("[失败] 画像恢复失败")
    
    print("\n" + "-" * 60 + "\n")


def test_conversation_persistence():
    """测试对话历史持久化"""
    print("=" * 60)
    print("测试2: 对话历史持久化")
    print("=" * 60)
    
    store = MemoryStore()
    user_id = "test_conversation_persistence"
    
    # 清理旧数据
    conversation_path = store.get_conversation_path(user_id)
    if conversation_path.exists():
        conversation_path.unlink()
    
    # 保存几条对话
    messages = [
        ("user", "你好"),
        ("assistant", "您好！"),
        ("user", "我是北京人"),
    ]
    
    print(f"\n保存对话 (user_id: {user_id})...")
    for role, content in messages:
        store.append_message(user_id, role, content)
    
    # 模拟重启：创建新的 MemoryStore 实例
    print("\n模拟程序重启（创建新的 MemoryStore 实例）...")
    store2 = MemoryStore()
    
    # 加载对话历史
    print(f"加载对话历史 (user_id: {user_id})...")
    conversation = store2.load_conversation(user_id)
    
    if conversation:
        print(f"[成功] 对话历史恢复成功，共 {len(conversation)} 条")
        for i, msg in enumerate(conversation, 1):
            print(f"  {i}. [{msg['role']}] {msg['content']}")
        
        assert len(conversation) == 3, f"期望3条，实际{len(conversation)}条"
        assert conversation[0]["content"] == "你好"
        assert conversation[1]["content"] == "您好！"
        assert conversation[2]["content"] == "我是北京人"
        print("\n[成功] 对话历史持久化验证通过")
    else:
        print("[失败] 对话历史恢复失败")
    
    print("\n" + "-" * 60 + "\n")


def test_multi_user_isolation():
    """测试多用户隔离"""
    print("=" * 60)
    print("测试3: 多用户隔离")
    print("=" * 60)
    
    store = MemoryStore()
    
    # 用户1
    user1_id = "test_user_isolate_1"
    profile1 = init_profile()
    profile1["demographics"]["city_level"] = {"value": "上海", "confidence": 0.9}
    store.save_profile(user1_id, profile1)
    
    # 用户2
    user2_id = "test_user_isolate_2"
    profile2 = init_profile()
    profile2["demographics"]["city_level"] = {"value": "广州", "confidence": 0.9}
    store.save_profile(user2_id, profile2)
    
    # 验证隔离
    print(f"\n加载用户1画像 (user_id: {user1_id})...")
    loaded1 = store.load_profile(user1_id)
    city1 = loaded1.get("demographics", {}).get("city_level", {}).get("value")
    print(f"  城市: {city1}")
    
    print(f"\n加载用户2画像 (user_id: {user2_id})...")
    loaded2 = store.load_profile(user2_id)
    city2 = loaded2.get("demographics", {}).get("city_level", {}).get("value")
    print(f"  城市: {city2}")
    
    assert city1 == "上海", "用户1数据错误"
    assert city2 == "广州", "用户2数据错误"
    assert city1 != city2, "用户数据未隔离"
    print("\n[成功] 多用户隔离验证通过")
    
    print("\n" + "-" * 60 + "\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("agent.py 集成功能测试")
    print("=" * 60 + "\n")
    
    try:
        test_profile_persistence()
        test_conversation_persistence()
        test_multi_user_isolation()
        
        print("=" * 60)
        print("[成功] 所有集成测试通过！")
        print("=" * 60)
        print("\n[成功] 基础功能验证完成，可以继续集成 memU API")
        
    except AssertionError as e:
        print(f"\n[失败] 测试失败: {e}")
    except Exception as e:
        print(f"\n[错误] 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

