"""
测试 memU API 的实际调用

验证：
1. memorize_conversation() 的参数格式和返回值
2. get_task_status() 的返回值结构
3. retrieve_related_memory_items() 的参数和返回值
4. 错误处理机制

运行方式：
    python test_memu_api.py
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any, Optional

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


async def test_memorize_conversation():
    """测试 memorize_conversation API"""
    print("=" * 60)
    print("测试1: memorize_conversation() - 存储记忆")
    print("=" * 60)
    
    try:
        from memu import MemuClient
        
        api_key = os.getenv("MEMU_API_KEY", "")
        if not api_key:
            print("[失败] 未设置 MEMU_API_KEY")
            return None
        
        # 初始化客户端
        client = MemuClient(
            base_url="https://api.memu.so",
            api_key=api_key
        )
        
        # 测试数据：用户画像信息
        user_id = "test_api_user_001"
        conversation = [
            {"role": "user", "content": "我是石家庄人，今年68岁了"},
            {"role": "assistant", "content": "您好！很高兴认识您"}
        ]
        
        print(f"\n提交记忆任务...")
        print(f"  User ID: {user_id}")
        print(f"  对话内容: {conversation}")
        
        # 调用 API（注意：agent_id 和 agent_name 是必需参数）
        result = await client.memorize_conversation(
            conversation=conversation,
            user_id=user_id,
            user_name="测试用户",
            agent_id="test_agent_001",
            agent_name="测试Agent"
        )
        
        print(f"\n[成功] API 调用成功")
        print(f"返回值类型: {type(result)}")
        print(f"返回值内容:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 提取 task_id
        task_id = None
        if isinstance(result, dict):
            task_id = result.get("task_id") or result.get("taskId")
        elif hasattr(result, "task_id"):
            task_id = result.task_id
        elif hasattr(result, "taskId"):
            task_id = result.taskId
        
        if task_id:
            print(f"\n任务ID: {task_id}")
            return task_id
        else:
            print("\n[警告] 未找到 task_id，返回值结构可能不同")
            return result
        
    except ImportError as e:
        print(f"[失败] 导入错误: {e}")
        print("   请确保已安装: pip install memu-py")
        return None
    except Exception as e:
        print(f"[失败] API 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_get_task_status(task_id: Any):
    """测试 get_task_status API"""
    print("\n" + "=" * 60)
    print("测试2: get_task_status() - 查询任务状态")
    print("=" * 60)
    
    if not task_id:
        print("[跳过] 没有有效的 task_id")
        return
    
    try:
        from memu import MemuClient
        
        api_key = os.getenv("MEMU_API_KEY", "")
        client = MemuClient(
            base_url="https://api.memu.so",
            api_key=api_key
        )
        
        print(f"\n查询任务状态...")
        print(f"  Task ID: {task_id}")
        
        # 调用 API
        status = await client.get_task_status(task_id=task_id)
        
        print(f"\n[成功] API 调用成功")
        print(f"返回值类型: {type(status)}")
        print(f"返回值内容:")
        print(json.dumps(status, ensure_ascii=False, indent=2, default=str))
        
        # 提取状态信息
        if isinstance(status, dict):
            status_value = status.get("status") or status.get("state")
            print(f"\n任务状态: {status_value}")
            
            if status_value == "COMPLETE" or status_value == "DONE":
                result = status.get("result") or status.get("data")
                if result:
                    items = result.get("items", [])
                    categories = result.get("categories", [])
                    print(f"  记忆项数量: {len(items)}")
                    print(f"  类别数量: {len(categories)}")
        elif hasattr(status, "status"):
            print(f"\n任务状态: {status.status}")
        
    except Exception as e:
        print(f"[失败] API 调用失败: {e}")
        import traceback
        traceback.print_exc()


async def test_retrieve_related_memory_items():
    """测试 retrieve_related_memory_items API"""
    print("\n" + "=" * 60)
    print("测试3: retrieve_related_memory_items() - 检索记忆项")
    print("=" * 60)
    
    try:
        from memu import MemuClient
        
        api_key = os.getenv("MEMU_API_KEY", "")
        client = MemuClient(
            base_url="https://api.memu.so",
            api_key=api_key
        )
        
        user_id = "test_api_user_001"
        query = "用户的偏好和习惯"
        
        print(f"\n检索记忆项...")
        print(f"  User ID: {user_id}")
        print(f"  查询内容: {query}")
        
        # 调用 API（注意：需要 agent_id）
        print("\n尝试调用 API...")
        try:
            result = await client.retrieve_related_memory_items(
                query=query,
                user_id=user_id,
                agent_id="test_agent_001"  # 可能需要 agent_id
            )
            print(f"[成功] API 调用成功")
            print(f"返回值类型: {type(result)}")
            print(f"返回值内容:")
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            
            # 提取结果
            if isinstance(result, dict):
                items = result.get("items", [])
                categories = result.get("categories", [])
                print(f"\n  记忆项数量: {len(items)}")
                print(f"  类别数量: {len(categories)}")
        except TypeError as e:
            # 如果参数不对，尝试其他组合
            print(f"[信息] 参数错误: {e}")
            print("   尝试不带 agent_id...")
            try:
                result = await client.retrieve_related_memory_items(
                    query=query,
                    user_id=user_id
                )
                print(f"[成功] 不带 agent_id 调用成功")
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            except Exception as e2:
                print(f"[失败] 调用失败: {e2}")
        except Exception as e:
            print(f"[失败] API 调用失败: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"[失败] API 调用失败: {e}")
        import traceback
        traceback.print_exc()


async def test_retrieve_default_categories():
    """测试 retrieve_default_categories API"""
    print("\n" + "=" * 60)
    print("测试4: retrieve_default_categories() - 获取默认类别")
    print("=" * 60)
    
    try:
        from memu import MemuClient
        
        api_key = os.getenv("MEMU_API_KEY", "")
        client = MemuClient(
            base_url="https://api.memu.so",
            api_key=api_key
        )
        
        user_id = "test_api_user_001"
        
        print(f"\n获取默认类别...")
        print(f"  User ID: {user_id}")
        
        # 调用 API（尝试不同的参数组合）
        print("\n尝试调用 API...")
        try:
            result = await client.retrieve_default_categories(
                user_id=user_id
            )
        except TypeError as e:
            print(f"[信息] 参数错误: {e}")
            print("   尝试其他参数组合...")
            # 尝试带 agent_id
            try:
                result = await client.retrieve_default_categories(
                    user_id=user_id,
                    agent_id="test_agent_001"
                )
            except Exception as e2:
                print(f"[失败] 调用失败: {e2}")
                return
        
        print(f"\n[成功] API 调用成功")
        print(f"返回值类型: {type(result)}")
        print(f"返回值内容:")
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        
        # 提取类别信息
        if isinstance(result, dict):
            categories = result.get("categories", [])
            print(f"\n  类别数量: {len(categories)}")
            for i, cat in enumerate(categories[:3], 1):  # 只显示前3个
                name = cat.get("name", "未知")
                summary = cat.get("summary", "")
                print(f"  {i}. {name}: {summary[:50]}...")
        
    except Exception as e:
        print(f"[失败] API 调用失败: {e}")
        import traceback
        traceback.print_exc()


async def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试5: 错误处理")
    print("=" * 60)
    
    try:
        from memu import MemuClient
        
        api_key = os.getenv("MEMU_API_KEY", "")
        client = MemuClient(
            base_url="https://api.memu.so",
            api_key=api_key
        )
        
        # 测试1: 无效的 user_id
        print("\n测试1: 使用无效参数")
        try:
            result = await client.memorize_conversation(
                conversation=[],
                user_id="",  # 空字符串
                user_name="",
                agent_id="",
                agent_name=""
            )
            print("[警告] 空 user_id 未触发错误")
        except Exception as e:
            print(f"[成功] 正确捕获错误: {type(e).__name__}: {e}")
        
        # 测试2: 无效的 API Key（如果可能）
        print("\n测试2: 使用无效的 API Key")
        try:
            invalid_client = MemuClient(
                base_url="https://api.memu.so",
                api_key="invalid_key_12345"
            )
            result = await invalid_client.memorize_conversation(
                conversation=[{"role": "user", "content": "test"}],
                user_id="test",
                user_name="test",
                agent_id="test",
                agent_name="test"
            )
            print("[警告] 无效 API Key 未触发错误")
        except Exception as e:
            print(f"[成功] 正确捕获认证错误: {type(e).__name__}: {e}")
        
    except Exception as e:
        print(f"[失败] 错误处理测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("memU API 实际调用测试")
    print("=" * 60 + "\n")
    
    # 检查 API Key
    api_key = os.getenv("MEMU_API_KEY", "")
    if not api_key:
        print("[失败] 未设置 MEMU_API_KEY")
        print("\n请按以下步骤配置：")
        print("1. 在项目根目录创建 .env 文件")
        print("2. 添加: MEMU_API_KEY=your-memu-api-key")
        return
    
    print(f"[信息] API Key: {api_key[:8]}...{api_key[-4:]}\n")
    
    # 测试1: memorize_conversation
    task_id = await test_memorize_conversation()
    
    # 测试2: get_task_status（如果有 task_id）
    if task_id:
        await test_get_task_status(task_id)
        # 等待一下，让任务有时间处理
        print("\n等待3秒后继续测试...")
        await asyncio.sleep(3)
        # 再次查询状态
        await test_get_task_status(task_id)
    
    # 测试3: retrieve_related_memory_items
    await test_retrieve_related_memory_items()
    
    # 测试4: retrieve_default_categories
    await test_retrieve_default_categories()
    
    # 测试5: 错误处理
    await test_error_handling()
    
    print("\n" + "=" * 60)
    print("[完成] 所有测试执行完毕")
    print("=" * 60)
    print("\n请查看上面的输出，确认 API 的实际行为：")
    print("1. 参数格式是否正确")
    print("2. 返回值结构是什么")
    print("3. 错误处理是否正常")
    print("4. 异步任务的处理流程")


if __name__ == "__main__":
    asyncio.run(main())

