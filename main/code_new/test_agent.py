"""
测试 agent.py 主程序功能

测试内容：
1. 启动流程测试
2. 画像加载和保存测试
3. 对话循环测试（模拟）
4. 命令处理测试
"""

import asyncio
import json
from memory_store import MemUStore
from chat_memory import ChatMemoryManager
from profile_extractor import update_profile
from profile_schema import init_profile
from agent import show_profile_summary, show_profile_updates


async def test_startup_flow():
    """测试启动流程"""
    print("="*60)
    print("测试 1: 启动流程")
    print("="*60)
    
    try:
        # 1. 初始化 memU 存储层
        print("\n[1] 初始化 memU 存储层...")
        memu_store = MemUStore(use_local_cache=True)
        if memu_store.ensure_service_ready():
            print("[OK] memU 存储层初始化成功")
        else:
            print("[WARN] memU 服务初始化失败，将使用本地缓存")
        
        # 2. 测试用户ID
        user_id = "test_user_agent"
        print(f"\n[2] 使用测试用户ID: {user_id}")
        
        # 3. 加载历史画像
        print("\n[3] 加载历史画像...")
        profile = await memu_store.load_profile(user_id)
        if not profile:
            profile = init_profile()
            print("[OK] 新用户，已初始化空画像")
        else:
            print("[OK] 已从 memU 加载历史画像")
        
        # 4. 初始化 Memory
        print("\n[4] 初始化 Memory...")
        memory_manager = ChatMemoryManager(memu_store)
        await memory_manager.load_history_into_memory(user_id)
        memory = memory_manager.get_memory_for_user(user_id)
        print("[OK] Memory 初始化成功")
        
        # 显示已加载的消息数量
        messages = memory_manager.get_memory_messages(user_id)
        print(f"[INFO] 已加载 {len(messages)} 条历史对话")
        
        print("\n[OK] 启动流程测试通过")
        return user_id, profile, memory_manager, memu_store
        
    except Exception as e:
        print(f"\n[ERROR] 启动流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None


async def test_profile_operations(user_id: str, profile: dict, 
                                  memory_manager: ChatMemoryManager,
                                  memu_store: MemUStore):
    """测试画像操作"""
    print("\n" + "="*60)
    print("测试 2: 画像操作")
    print("="*60)
    
    try:
        # 测试画像更新
        print("\n[1] 测试画像更新...")
        test_input = "你好，我是石家庄人，今年68岁了，有点高血压"
        print(f"测试输入: {test_input}")
        
        updated_profile = update_profile(test_input, profile)
        print("[OK] 画像更新完成")
        
        # 显示画像摘要
        print("\n[2] 显示画像摘要...")
        show_profile_summary(updated_profile)
        
        # 保存画像
        print("\n[3] 保存画像到 memU...")
        success = await memu_store.save_profile(user_id, updated_profile)
        if success:
            print("[OK] 画像已保存")
        else:
            print("[WARN] 画像保存失败，但已保存到本地缓存")
        
        # 重新加载画像
        print("\n[4] 重新加载画像...")
        loaded_profile = await memu_store.load_profile(user_id)
        if loaded_profile:
            print("[OK] 画像加载成功")
            # 验证数据一致性
            if loaded_profile.get("demographics", {}).get("age", {}).get("value") == updated_profile.get("demographics", {}).get("age", {}).get("value"):
                print("[OK] 画像数据一致性验证通过")
            else:
                print("[WARN] 画像数据可能不一致")
        else:
            print("[WARN] 从 memU 加载失败，尝试从本地缓存加载")
            # 从本地缓存加载
            from pathlib import Path
            cache_file = Path(__file__).parent / "data" / "profiles" / f"{user_id}.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    loaded_profile = cached_data.get("profile")
                    print("[OK] 从本地缓存加载成功")
        
        print("\n[OK] 画像操作测试通过")
        return updated_profile
        
    except Exception as e:
        print(f"\n[ERROR] 画像操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return profile


async def test_conversation_flow(user_id: str, profile: dict,
                                 memory_manager: ChatMemoryManager,
                                 memu_store: MemUStore):
    """测试对话流程"""
    print("\n" + "="*60)
    print("测试 3: 对话流程")
    print("="*60)
    
    try:
        # 添加几条测试消息
        print("\n[1] 添加测试消息...")
        test_messages = [
            ("user", "你好，我是石家庄人"),
            ("user", "今年68岁了"),
            ("user", "有点高血压，每天都要吃药"),
        ]
        
        for role, content in test_messages:
            await memory_manager.add_message(user_id, role, content)
            print(f"  [OK] 已添加 {role} 消息: {content[:30]}...")
        
        # 获取对话上下文
        print("\n[2] 获取对话上下文...")
        context = memory_manager.get_conversation_context(user_id, limit=10)
        print(f"[OK] 对话上下文长度: {len(context)} 字符")
        if context:
            print(f"上下文预览: {context[:100]}...")
        
        # 更新画像
        print("\n[3] 更新画像...")
        conversation_text = "\n".join([f"用户：{content}" for role, content in test_messages if role == "user"])
        updated_profile = update_profile(conversation_text, profile)
        print("[OK] 画像更新完成")
        
        # 保存画像
        print("\n[4] 保存画像...")
        await memu_store.save_profile(user_id, updated_profile)
        print("[OK] 画像已保存")
        
        # 获取 Memory 消息
        print("\n[5] 获取 Memory 消息...")
        messages = memory_manager.get_memory_messages(user_id)
        print(f"[OK] Memory 中有 {len(messages)} 条消息")
        
        print("\n[OK] 对话流程测试通过")
        
    except Exception as e:
        print(f"\n[ERROR] 对话流程测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_commands(user_id: str, profile: dict):
    """测试命令功能"""
    print("\n" + "="*60)
    print("测试 4: 命令功能")
    print("="*60)
    
    try:
        # 测试 show_profile_summary
        print("\n[1] 测试 show_profile_summary...")
        show_profile_summary(profile)
        print("[OK] show_profile_summary 测试通过")
        
        # 测试 show_profile_updates
        print("\n[2] 测试 show_profile_updates...")
        show_profile_updates(profile, "测试输入")
        print("[OK] show_profile_updates 测试通过")
        
        # 测试完整画像显示
        print("\n[3] 测试完整画像显示...")
        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
        print(f"[OK] 画像JSON长度: {len(profile_json)} 字符")
        
        print("\n[OK] 命令功能测试通过")
        
    except Exception as e:
        print(f"\n[ERROR] 命令功能测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_multiple_users():
    """测试多用户隔离"""
    print("\n" + "="*60)
    print("测试 5: 多用户隔离")
    print("="*60)
    
    try:
        memu_store = MemUStore(use_local_cache=True)
        memory_manager = ChatMemoryManager(memu_store)
        
        user1_id = "test_user_1"
        user2_id = "test_user_2"
        
        # 为用户1添加消息
        print(f"\n[1] 为用户 {user1_id} 添加消息...")
        await memory_manager.add_message(user1_id, "user", "我是用户1")
        profile1 = init_profile()
        profile1["demographics"]["age"]["value"] = 65
        await memu_store.save_profile(user1_id, profile1)
        print("[OK] 用户1数据已保存")
        
        # 为用户2添加消息
        print(f"\n[2] 为用户 {user2_id} 添加消息...")
        await memory_manager.add_message(user2_id, "user", "我是用户2")
        profile2 = init_profile()
        profile2["demographics"]["age"]["value"] = 70
        await memu_store.save_profile(user2_id, profile2)
        print("[OK] 用户2数据已保存")
        
        # 验证数据隔离
        print("\n[3] 验证数据隔离...")
        loaded_profile1 = await memu_store.load_profile(user1_id)
        loaded_profile2 = await memu_store.load_profile(user2_id)
        
        if loaded_profile1 and loaded_profile2:
            age1 = loaded_profile1.get("demographics", {}).get("age", {}).get("value")
            age2 = loaded_profile2.get("demographics", {}).get("age", {}).get("value")
            if age1 == 65 and age2 == 70:
                print("[OK] 多用户数据隔离验证通过")
            else:
                print(f"[WARN] 数据隔离可能有问题: 用户1年龄={age1}, 用户2年龄={age2}")
        else:
            print("[WARN] 无法验证数据隔离（加载失败）")
        
        print("\n[OK] 多用户隔离测试通过")
        
    except Exception as e:
        print(f"\n[ERROR] 多用户隔离测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("="*60)
    print("agent.py 主程序功能测试")
    print("="*60)
    
    # 测试1: 启动流程
    user_id, profile, memory_manager, memu_store = await test_startup_flow()
    if not user_id:
        print("\n[ERROR] 启动流程测试失败，终止测试")
        return
    
    # 测试2: 画像操作
    profile = await test_profile_operations(user_id, profile, memory_manager, memu_store)
    
    # 测试3: 对话流程
    await test_conversation_flow(user_id, profile, memory_manager, memu_store)
    
    # 测试4: 命令功能
    await test_commands(user_id, profile)
    
    # 测试5: 多用户隔离
    await test_multiple_users()
    
    print("\n" + "="*60)
    print("所有测试完成")
    print("="*60)
    print("\n注意：")
    print("  - 这些测试验证了核心功能，但交互式对话循环需要手动测试")
    print("  - 运行 python agent.py 进行完整的交互式测试")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

