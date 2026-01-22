"""
LangChain Memory 封装测试脚本

测试 chat_memory.py 的基本功能：
- Memory 实例创建
- 消息添加
- 历史对话加载
- 对话上下文获取
- 多用户隔离
"""

import asyncio
from chat_memory import ChatMemoryManager
from memory_store import MemUStore


async def test_memory_creation():
    """测试 Memory 实例创建"""
    print("=" * 60)
    print("测试1: Memory 实例创建")
    print("=" * 60)
    
    store = MemUStore(use_local_cache=True)
    manager = ChatMemoryManager(store)
    
    user_id = "test_user_001"
    memory = manager.get_memory_for_user(user_id)
    
    print(f"[OK] 为用户 {user_id} 创建 Memory 实例")
    print(f"    Memory 类型: {type(memory).__name__}")
    print(f"    return_messages: {memory.return_messages}")
    print()


async def test_add_messages():
    """测试添加消息"""
    print("=" * 60)
    print("测试2: 添加消息到 Memory 和 memU")
    print("=" * 60)
    
    store = MemUStore(use_local_cache=True)
    manager = ChatMemoryManager(store)
    
    user_id = "test_user_001"
    
    # 添加用户消息
    print(f"\n添加用户消息...")
    success1 = await manager.add_message(user_id, "user", "你好，我是石家庄人，今年68岁了")
    if success1:
        print("[OK] 用户消息添加成功")
    else:
        print("[ERROR] 用户消息添加失败")
    
    # 添加助手消息
    print(f"\n添加助手消息...")
    success2 = await manager.add_message(user_id, "assistant", "您好！很高兴认识您")
    if success2:
        print("[OK] 助手消息添加成功")
    else:
        print("[ERROR] 助手消息添加失败")
    
    # 添加系统消息
    print(f"\n添加系统消息...")
    success3 = await manager.add_message(user_id, "system", "这是一个测试对话")
    if success3:
        print("[OK] 系统消息添加成功")
    else:
        print("[ERROR] 系统消息添加失败")
    
    # 检查 Memory 中的消息
    memory = manager.get_memory_for_user(user_id)
    messages = manager.get_memory_messages(user_id)
    print(f"\n[INFO] Memory 中有 {len(messages)} 条消息")
    for i, msg in enumerate(messages, 1):
        msg_type = type(msg).__name__
        content = msg.content[:50] if hasattr(msg, 'content') else str(msg)[:50]
        print(f"   {i}. [{msg_type}] {content}...")
    
    print()


async def test_load_history():
    """测试加载历史对话"""
    print("=" * 60)
    print("测试3: 从 memU 加载历史对话到 Memory")
    print("=" * 60)
    
    store = MemUStore(use_local_cache=True)
    manager = ChatMemoryManager(store)
    
    user_id = "test_user_001"
    
    # 先添加一些消息到 memU
    print(f"\n准备测试数据...")
    await manager.add_message(user_id, "user", "测试消息1")
    await manager.add_message(user_id, "assistant", "测试回复1")
    await manager.add_message(user_id, "user", "测试消息2")
    
    # 创建新的 Memory 管理器（模拟重启）
    print(f"\n创建新的 Memory 管理器（模拟重启）...")
    new_manager = ChatMemoryManager(store)
    
    # 加载历史对话
    print(f"加载历史对话...")
    success = await new_manager.load_history_into_memory(user_id)
    
    if success:
        print("[OK] 历史对话加载成功")
        messages = new_manager.get_memory_messages(user_id)
        print(f"   加载了 {len(messages)} 条消息")
    else:
        print("[WARN] 历史对话加载失败或没有历史数据")
    
    print()


async def test_conversation_context():
    """测试获取对话上下文"""
    print("=" * 60)
    print("测试4: 获取对话上下文")
    print("=" * 60)
    
    store = MemUStore(use_local_cache=True)
    manager = ChatMemoryManager(store)
    
    user_id = "test_user_001"
    
    # 添加一些对话
    await manager.add_message(user_id, "user", "你好")
    await manager.add_message(user_id, "assistant", "您好！")
    await manager.add_message(user_id, "user", "我今年68岁")
    
    # 获取对话上下文
    print(f"\n获取对话上下文...")
    context = manager.get_conversation_context(user_id, limit=5)
    
    if context:
        print("[OK] 对话上下文获取成功")
        print("上下文内容:")
        print(context)
    else:
        print("[WARN] 对话上下文为空")
    
    print()


async def test_multiple_users():
    """测试多用户隔离"""
    print("=" * 60)
    print("测试5: 多用户隔离")
    print("=" * 60)
    
    store = MemUStore(use_local_cache=True)
    manager = ChatMemoryManager(store)
    
    # 用户1
    user1_id = "test_user_001"
    await manager.add_message(user1_id, "user", "我是用户1")
    await manager.add_message(user1_id, "assistant", "你好用户1")
    
    # 用户2
    user2_id = "test_user_002"
    await manager.add_message(user2_id, "user", "我是用户2")
    await manager.add_message(user2_id, "assistant", "你好用户2")
    
    # 检查隔离
    messages1 = manager.get_memory_messages(user1_id)
    messages2 = manager.get_memory_messages(user2_id)
    
    print(f"\n用户 {user1_id} 的消息数: {len(messages1)}")
    print(f"用户 {user2_id} 的消息数: {len(messages2)}")
    
    if len(messages1) == 2 and len(messages2) == 2:
        print("[OK] 多用户隔离正常")
    else:
        print("[ERROR] 多用户隔离异常")
    
    print()


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("LangChain Memory 封装功能测试")
    print("=" * 60 + "\n")
    
    try:
        await test_memory_creation()
        await test_add_messages()
        await test_load_history()
        await test_conversation_context()
        await test_multiple_users()
        
        print("=" * 60)
        print("[OK] 所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

