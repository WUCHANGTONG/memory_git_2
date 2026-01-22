"""
memU 存储层测试脚本

测试 memory_store.py 的基本功能：
- 画像存储和加载
- 对话历史存储和加载
- 记忆检索
- 多用户隔离
"""

import asyncio
import json
from memory_store import MemUStore
from profile_schema import init_profile


async def test_save_and_load_profile():
    """测试画像存储和加载"""
    print("=" * 60)
    print("测试1: 画像存储和加载")
    print("=" * 60)
    
    store = MemUStore(use_local_cache=True)
    
    # 检查服务是否就绪
    if not store.ensure_service_ready():
        print("[WARN] memU 服务未就绪，将使用本地缓存")
    
    # 创建测试画像
    user_id = "test_user_001"
    profile = init_profile()
    
    # 添加一些测试数据
    profile["demographics"]["age"]["value"] = 68
    profile["demographics"]["age"]["confidence"] = 0.9
    profile["demographics"]["city_level"]["value"] = "石家庄"
    profile["demographics"]["city_level"]["confidence"] = 0.9
    
    # 保存画像
    print(f"\n保存用户 {user_id} 的画像...")
    success = await store.save_profile(user_id, profile)
    if success:
        print("[OK] 画像保存成功")
    else:
        print("[ERROR] 画像保存失败")
        return
    
    # 加载画像
    print(f"\n加载用户 {user_id} 的画像...")
    loaded_profile = await store.load_profile(user_id)
    
    if loaded_profile:
        print("[OK] 画像加载成功")
        print(f"   年龄: {loaded_profile.get('demographics', {}).get('age', {}).get('value')}")
        print(f"   城市: {loaded_profile.get('demographics', {}).get('city_level', {}).get('value')}")
    else:
        print("[WARN] 画像加载失败或不存在（可能 memU 检索需要时间）")
        print("   检查本地缓存...")
        # 检查本地缓存
        from pathlib import Path
        cache_file = Path(__file__).parent / "data" / "profiles" / f"{user_id}.json"
        if cache_file.exists():
            print(f"[OK] 本地缓存存在: {cache_file}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                print(f"   缓存中的年龄: {cached.get('profile', {}).get('demographics', {}).get('age', {}).get('value')}")
    
    print()


async def test_append_and_load_conversation():
    """测试对话历史存储和加载"""
    print("=" * 60)
    print("测试2: 对话历史存储和加载")
    print("=" * 60)
    
    store = MemUStore(use_local_cache=True)
    
    user_id = "test_user_001"
    
    # 添加对话消息
    print(f"\n添加对话消息...")
    success1 = await store.append_message(user_id, "user", "你好，我是石家庄人，今年68岁了")
    success2 = await store.append_message(user_id, "assistant", "您好！很高兴认识您")
    success3 = await store.append_message(user_id, "user", "我有点高血压")
    
    if success1 and success2 and success3:
        print("[OK] 对话消息保存成功")
    else:
        print("[ERROR] 部分对话消息保存失败")
    
    # 加载对话历史
    print(f"\n加载用户 {user_id} 的对话历史...")
    conversation = await store.load_conversation(user_id)
    
    if conversation:
        print(f"[OK] 对话历史加载成功，共 {len(conversation)} 条消息")
        for i, msg in enumerate(conversation[:3], 1):
            print(f"   {i}. [{msg.get('role')}] {msg.get('content')[:50]}...")
    else:
        print("[WARN] 对话历史加载失败或不存在（可能 memU 检索需要时间）")
        print("   检查本地缓存...")
        from pathlib import Path
        cache_file = Path(__file__).parent / "data" / "conversations" / f"{user_id}.json"
        if cache_file.exists():
            print(f"[OK] 本地缓存存在: {cache_file}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                print(f"   缓存中的消息数: {len(cached)}")
                for i, msg in enumerate(cached[:3], 1):
                    print(f"   {i}. [{msg.get('role')}] {msg.get('content')[:50]}...")
    
    print()


async def test_multiple_users():
    """测试多用户隔离"""
    print("=" * 60)
    print("测试3: 多用户隔离")
    print("=" * 60)
    
    store = MemUStore(use_local_cache=True)
    
    # 用户1
    user1_id = "test_user_001"
    profile1 = init_profile()
    profile1["demographics"]["age"]["value"] = 68
    profile1["demographics"]["city_level"]["value"] = "石家庄"
    
    # 用户2
    user2_id = "test_user_002"
    profile2 = init_profile()
    profile2["demographics"]["age"]["value"] = 75
    profile2["demographics"]["city_level"]["value"] = "北京"
    
    # 保存两个用户的画像
    print(f"\n保存用户 {user1_id} 的画像...")
    await store.save_profile(user1_id, profile1)
    
    print(f"保存用户 {user2_id} 的画像...")
    await store.save_profile(user2_id, profile2)
    
    # 加载并验证
    print(f"\n加载用户 {user1_id} 的画像...")
    loaded1 = await store.load_profile(user1_id)
    
    print(f"加载用户 {user2_id} 的画像...")
    loaded2 = await store.load_profile(user2_id)
    
    # 验证数据隔离
    if loaded1 and loaded2:
        age1 = loaded1.get("demographics", {}).get("age", {}).get("value")
        age2 = loaded2.get("demographics", {}).get("age", {}).get("value")
        city1 = loaded1.get("demographics", {}).get("city_level", {}).get("value")
        city2 = loaded2.get("demographics", {}).get("city_level", {}).get("value")
        
        if age1 == 68 and age2 == 75 and city1 == "石家庄" and city2 == "北京":
            print("[OK] 多用户数据隔离正常")
        else:
            print("[ERROR] 多用户数据隔离异常")
            print(f"   用户1: 年龄={age1}, 城市={city1}")
            print(f"   用户2: 年龄={age2}, 城市={city2}")
    else:
        print("[WARN] 无法验证多用户隔离（数据可能未完全加载）")
    
    print()


async def test_memory_retrieval():
    """测试记忆检索"""
    print("=" * 60)
    print("测试4: 记忆检索")
    print("=" * 60)
    
    store = MemUStore(use_local_cache=True)
    
    if not store.ensure_service_ready():
        print("[WARN] memU 服务未就绪，跳过检索测试")
        return
    
    user_id = "test_user_001"
    query = "用户的年龄和城市信息"
    
    print(f"\n检索用户 {user_id} 的记忆: {query}")
    result = await store.get_user_memory(user_id, query)
    
    print(f"[INFO] 检索结果:")
    print(f"   类别数: {len(result.get('categories', []))}")
    print(f"   项目数: {len(result.get('items', []))}")
    print(f"   资源数: {len(result.get('resources', []))}")
    
    if result.get('categories') or result.get('items'):
        print("[OK] 检索到相关记忆")
    else:
        print("[WARN] 未检索到记忆（可能 memU 中还没有足够的数据）")
    
    print()


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("memU 存储层功能测试")
    print("=" * 60 + "\n")
    
    try:
        await test_save_and_load_profile()
        await test_append_and_load_conversation()
        await test_multiple_users()
        await test_memory_retrieval()
        
        print("=" * 60)
        print("[OK] 所有测试完成")
        print("=" * 60)
        print("\n注意：")
        print("- 如果 memU 服务未就绪，会使用本地缓存")
        print("- memU 的检索功能可能需要一些时间才能生效")
        print("- 建议检查 data/ 目录下的本地缓存文件")
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

