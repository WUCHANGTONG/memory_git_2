"""
测试 memory_store.py 的本地缓存功能

运行方式：
    python test_memory_store.py
"""

from memory_store import MemoryStore
from profile_schema import init_profile
import json


def test_save_and_load_profile():
    """测试保存和加载用户画像"""
    print("=" * 60)
    print("测试1: 保存和加载用户画像")
    print("=" * 60)
    
    store = MemoryStore()
    user_id = "test_user_001"
    
    # 创建测试画像
    profile = init_profile()
    profile["demographics"]["age"] = {"value": 68, "confidence": 0.9}
    profile["demographics"]["city_level"] = {"value": "石家庄", "confidence": 0.9}
    profile["health"]["chronic_conditions"] = {"value": ["高血压"], "confidence": 0.8}
    
    # 保存画像
    print(f"\n保存用户画像 (user_id: {user_id})...")
    success = store.save_profile(user_id, profile)
    print(f"保存结果: {'成功' if success else '失败'}")
    
    # 加载画像
    print(f"\n加载用户画像 (user_id: {user_id})...")
    loaded_profile = store.load_profile(user_id)
    
    if loaded_profile:
        print("[成功] 加载成功")
        print("\n加载的画像内容:")
        print(json.dumps(loaded_profile, ensure_ascii=False, indent=2))
        
        # 验证数据
        assert loaded_profile["demographics"]["age"]["value"] == 68
        assert loaded_profile["demographics"]["city_level"]["value"] == "石家庄"
        assert "高血压" in loaded_profile["health"]["chronic_conditions"]["value"]
        print("\n[成功] 数据验证通过")
    else:
        print("❌ 加载失败")
    
    print("\n" + "-" * 60 + "\n")


def test_append_and_load_conversation():
    """测试追加和加载对话历史"""
    print("=" * 60)
    print("测试2: 追加和加载对话历史")
    print("=" * 60)
    
    store = MemoryStore()
    user_id = "test_user_conversation"  # 使用独立的测试用户ID
    
    # 先清理该用户的对话历史（如果存在）
    conversation_path = store.get_conversation_path(user_id)
    if conversation_path.exists():
        conversation_path.unlink()
    
    # 追加几条消息
    messages = [
        ("user", "你好，我是石家庄人"),
        ("user", "我今年68岁了"),
        ("assistant", "您好！很高兴认识您"),
    ]
    
    print(f"\n追加对话消息 (user_id: {user_id})...")
    for role, content in messages:
        success = store.append_message(user_id, role, content)
        print(f"  {role}: {content[:30]}... {'[OK]' if success else '[FAIL]'}")
    
    # 加载对话历史
    print(f"\n加载对话历史 (user_id: {user_id})...")
    conversation = store.load_conversation(user_id)
    
    if conversation:
        print(f"[成功] 加载成功，共 {len(conversation)} 条消息")
        print("\n对话历史:")
        for msg in conversation:
            print(f"  [{msg['timestamp']}] {msg['role']}: {msg['content']}")
        
        # 验证数据
        assert len(conversation) == 3, f"期望3条消息，实际{len(conversation)}条"
        # 检查最后3条消息（因为可能有历史数据）
        last_3_messages = conversation[-3:]
        assert last_3_messages[0]["role"] == "user"
        assert last_3_messages[0]["content"] == "你好，我是石家庄人"
        assert last_3_messages[1]["role"] == "user"
        assert last_3_messages[1]["content"] == "我今年68岁了"
        assert last_3_messages[2]["role"] == "assistant"
        assert last_3_messages[2]["content"] == "您好！很高兴认识您"
        print("\n[成功] 数据验证通过")
    else:
        print("[失败] 加载失败")
    
    print("\n" + "-" * 60 + "\n")


def test_multiple_users():
    """测试多用户隔离"""
    print("=" * 60)
    print("测试3: 多用户隔离")
    print("=" * 60)
    
    store = MemoryStore()
    
    # 用户1
    user1_id = "test_user_001"
    profile1 = init_profile()
    profile1["demographics"]["city_level"] = {"value": "北京", "confidence": 0.9}
    store.save_profile(user1_id, profile1)
    
    # 用户2
    user2_id = "test_user_002"
    profile2 = init_profile()
    profile2["demographics"]["city_level"] = {"value": "上海", "confidence": 0.9}
    store.save_profile(user2_id, profile2)
    
    # 验证隔离
    print(f"\n加载用户1画像 (user_id: {user1_id})...")
    loaded1 = store.load_profile(user1_id)
    print(f"  城市: {loaded1.get('demographics', {}).get('city_level', {}).get('value')}")
    
    print(f"\n加载用户2画像 (user_id: {user2_id})...")
    loaded2 = store.load_profile(user2_id)
    print(f"  城市: {loaded2.get('demographics', {}).get('city_level', {}).get('value')}")
    
    # 验证隔离
    assert loaded1["demographics"]["city_level"]["value"] == "北京"
    assert loaded2["demographics"]["city_level"]["value"] == "上海"
    print("\n[成功] 多用户隔离验证通过")
    
    print("\n" + "-" * 60 + "\n")


def test_nonexistent_user():
    """测试不存在的用户"""
    print("=" * 60)
    print("测试4: 不存在的用户")
    print("=" * 60)
    
    store = MemoryStore()
    user_id = "nonexistent_user"
    
    # 加载不存在的用户
    profile = store.load_profile(user_id)
    conversation = store.load_conversation(user_id)
    
    print(f"\n加载不存在的用户画像...")
    if not profile:
        print("[成功] 返回空字典（符合预期）")
    else:
        print("[失败] 应该返回空字典")
    
    print(f"\n加载不存在的用户对话历史...")
    if not conversation:
        print("[成功] 返回空列表（符合预期）")
    else:
        print("[失败] 应该返回空列表")
    
    print("\n" + "-" * 60 + "\n")


def test_user_exists():
    """测试用户存在检查"""
    print("=" * 60)
    print("测试5: 用户存在检查")
    print("=" * 60)
    
    store = MemoryStore()
    
    # 创建用户
    user_id = "test_user_exists"
    profile = init_profile()
    store.save_profile(user_id, profile)
    
    # 检查存在
    exists = store.user_exists(user_id)
    print(f"\n用户 {user_id} 是否存在: {exists}")
    assert exists == True
    print("[成功] 用户存在检查通过")
    
    # 检查不存在
    nonexistent_id = "nonexistent_user_999"
    exists = store.user_exists(nonexistent_id)
    print(f"\n用户 {nonexistent_id} 是否存在: {exists}")
    assert exists == False
    print("[成功] 用户不存在检查通过")
    
    print("\n" + "-" * 60 + "\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("memory_store.py 本地缓存功能测试")
    print("=" * 60 + "\n")
    
    try:
        test_save_and_load_profile()
        test_append_and_load_conversation()
        test_multiple_users()
        test_nonexistent_user()
        test_user_exists()
        
        print("=" * 60)
        print("[成功] 所有测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n[失败] 测试失败: {e}")
    except Exception as e:
        print(f"\n[错误] 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

