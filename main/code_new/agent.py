"""
主程序 - 对话循环 + 画像更新

实现交互式对话循环，整合画像提取和 memU 存储。
支持多用户、多轮对话、角色区分、时间戳、持久画像。
"""

import asyncio
import json
from typing import Dict, Any, Optional
from memory_store import MemUStore
from chat_memory import ChatMemoryManager
from profile_extractor import update_profile
from profile_schema import init_profile


def show_profile_summary(profile: Dict[str, Any]):
    """
    显示用户画像摘要（只显示有值的字段）
    
    Args:
        profile: 用户画像字典
    """
    print("\n" + "="*50)
    print("用户画像摘要")
    print("="*50)
    
    # 人口统计信息
    demo = profile.get("demographics", {})
    demo_info = []
    if demo.get("age", {}).get("value"):
        demo_info.append(f"年龄: {demo['age']['value']}岁")
    if demo.get("gender", {}).get("value"):
        demo_info.append(f"性别: {demo['gender']['value']}")
    if demo.get("city_level", {}).get("value"):
        demo_info.append(f"城市: {demo['city_level']['value']}")
    if demo.get("education", {}).get("value"):
        demo_info.append(f"教育: {demo['education']['value']}")
    if demo.get("marital_status", {}).get("value"):
        demo_info.append(f"婚姻: {demo['marital_status']['value']}")
    
    if demo_info:
        print("\n【人口统计】")
        print("  " + " | ".join(demo_info))
    
    # 健康状况
    health = profile.get("health", {})
    health_info = []
    if health.get("chronic_conditions", {}).get("value"):
        conditions = health['chronic_conditions']['value']
        if isinstance(conditions, list) and conditions:
            health_info.append(f"慢性病: {', '.join(conditions)}")
    if health.get("mobility", {}).get("value"):
        health_info.append(f"行动能力: {health['mobility']['value']}")
    if health.get("sleep_quality", {}).get("value"):
        health_info.append(f"睡眠质量: {health['sleep_quality']['value']}")
    if health.get("medication_adherence", {}).get("value"):
        health_info.append(f"用药情况: {health['medication_adherence']['value']}")
    
    if health_info:
        print("\n【健康状况】")
        print("  " + " | ".join(health_info))
    
    # 认知能力
    cognitive = profile.get("cognitive", {})
    cognitive_info = []
    if cognitive.get("memory_status", {}).get("value"):
        cognitive_info.append(f"记忆状况: {cognitive['memory_status']['value']}")
    if cognitive.get("digital_literacy", {}).get("value"):
        cognitive_info.append(f"数字能力: {cognitive['digital_literacy']['value']}")
    if cognitive.get("expression_fluency", {}).get("value"):
        cognitive_info.append(f"表达流畅度: {cognitive['expression_fluency']['value']}")
    
    if cognitive_info:
        print("\n【认知能力】")
        print("  " + " | ".join(cognitive_info))
    
    # 情感状态
    emotional = profile.get("emotional", {})
    emotional_info = []
    if emotional.get("baseline_mood", {}).get("value"):
        emotional_info.append(f"基础情绪: {emotional['baseline_mood']['value']}")
    if emotional.get("loneliness_level", {}).get("value"):
        emotional_info.append(f"孤独感: {emotional['loneliness_level']['value']}")
    if emotional.get("anxiety_level", {}).get("value"):
        emotional_info.append(f"焦虑程度: {emotional['anxiety_level']['value']}")
    
    if emotional_info:
        print("\n【情感状态】")
        print("  " + " | ".join(emotional_info))
    
    # 生活方式
    lifestyle = profile.get("lifestyle", {})
    lifestyle_info = []
    if lifestyle.get("living_arrangement", {}).get("value"):
        lifestyle_info.append(f"居住安排: {lifestyle['living_arrangement']['value']}")
    if lifestyle.get("daily_routine", {}).get("value"):
        lifestyle_info.append(f"日常作息: {lifestyle['daily_routine']['value']}")
    if lifestyle.get("hobbies", {}).get("value"):
        hobbies = lifestyle['hobbies']['value']
        if isinstance(hobbies, list) and hobbies:
            lifestyle_info.append(f"兴趣爱好: {', '.join(hobbies)}")
    
    if lifestyle_info:
        print("\n【生活方式】")
        print("  " + " | ".join(lifestyle_info))
    
    # 偏好设置
    preferences = profile.get("preferences", {})
    preferences_info = []
    if preferences.get("communication_style", {}).get("value"):
        preferences_info.append(f"沟通风格: {preferences['communication_style']['value']}")
    if preferences.get("service_channel_preference", {}).get("value"):
        preferences_info.append(f"服务渠道: {preferences['service_channel_preference']['value']}")
    if preferences.get("privacy_sensitivity", {}).get("value"):
        preferences_info.append(f"隐私敏感度: {preferences['privacy_sensitivity']['value']}")
    
    if preferences_info:
        print("\n【偏好设置】")
        print("  " + " | ".join(preferences_info))
    
    # 如果没有信息
    if not any([demo_info, health_info, cognitive_info, emotional_info, lifestyle_info, preferences_info]):
        print("\n[提示] 当前画像为空，请开始对话以提取用户信息")
    
    print("="*50 + "\n")


def show_profile_updates(profile: Dict[str, Any], user_input: str):
    """
    显示画像更新摘要（显示最近更新的字段）
    
    Args:
        profile: 更新后的用户画像字典
        user_input: 用户输入内容
    """
    # 这里可以添加更详细的更新提示
    # 目前简化处理，只显示提示信息
    print("[INFO] 画像已更新，输入 'show' 查看画像摘要，输入 'profile' 查看完整画像")


async def chat_loop(user_id: str, profile: Dict[str, Any], 
                   memory_manager: ChatMemoryManager, 
                   memu_store: MemUStore):
    """
    对话循环主函数
    
    Args:
        user_id: 用户ID
        profile: 用户画像字典
        memory_manager: Memory管理器
        memu_store: memU存储层
    """
    print("\n" + "="*60)
    print("对话系统已启动")
    print("="*60)
    print("\n说明：")
    print("  - 输入对话内容，系统会提取并更新用户画像")
    print("  - 输入 'show' 查看当前画像摘要")
    print("  - 输入 'profile' 查看完整画像（JSON格式）")
    print("  - 输入 'exit' 结束对话并保存数据")
    print("  - 输入 'help' 查看帮助信息")
    print("\n" + "-"*60 + "\n")
    
    while True:
        try:
            user_input = input("你: ").strip()
            
            # 处理空输入
            if not user_input:
                continue
            
            # 处理命令
            if user_input.lower() == "exit":
                # 保存最终状态
                print("\n[INFO] 正在保存数据...")
                await memu_store.save_profile(user_id, profile)
                await memory_manager.save_current_memory(user_id)
                print("[OK] 数据已保存")
                print("\n最终用户画像：")
                print(json.dumps(profile, ensure_ascii=False, indent=2))
                print("\n对话已结束，再见！")
                break
            
            if user_input.lower() == "show":
                # 显示画像摘要
                show_profile_summary(profile)
                continue
            
            if user_input.lower() == "profile":
                # 显示完整画像
                print("\n" + "="*60)
                print("完整用户画像（JSON格式）")
                print("="*60)
                print(json.dumps(profile, ensure_ascii=False, indent=2))
                print("="*60 + "\n")
                continue
            
            if user_input.lower() == "help":
                print("\n可用命令：")
                print("  show     - 查看用户画像摘要")
                print("  profile  - 查看完整用户画像（JSON格式）")
                print("  exit     - 结束对话并保存数据")
                print("  help     - 显示帮助信息")
                print("\n直接输入对话内容即可提取画像信息\n")
                continue
            
            # 添加用户消息到 Memory 和 memU
            print(f"\n[INFO] 正在保存用户消息...")
            await memory_manager.add_message(user_id, "user", user_input)
            print("[OK] 消息已保存")
            
            # 获取对话上下文（用于画像提取）
            conversation_context = memory_manager.get_conversation_context(user_id, limit=10)
            
            # 更新画像（只使用用户消息，不包括助手回复）
            print("[INFO] 正在提取画像信息...")
            try:
                # 只从用户消息中提取画像
                profile = update_profile(user_input, profile)
                print("[OK] 画像提取完成")
            except Exception as e:
                print(f"[WARN] 画像提取失败: {e}")
                print("[INFO] 继续使用当前画像")
            
            # 立即保存画像到 memU
            print("[INFO] 正在保存画像到 memU...")
            success = await memu_store.save_profile(user_id, profile)
            if success:
                print("[OK] 画像已更新并保存到 memU")
            else:
                print("[WARN] 画像保存到 memU 失败，已保存到本地缓存")
            
            # 显示更新摘要
            show_profile_updates(profile, user_input)
            print()  # 空行
            
        except KeyboardInterrupt:
            print("\n\n[INFO] 检测到中断信号，正在保存数据...")
            await memu_store.save_profile(user_id, profile)
            await memory_manager.save_current_memory(user_id)
            print("[OK] 数据已保存")
            print("\n对话已中断，再见！")
            break
        except Exception as e:
            print(f"\n[ERROR] 发生错误: {e}")
            print("[INFO] 继续对话...\n")


async def main():
    """
    主函数 - 启动流程
    """
    print("="*60)
    print("用户画像记忆系统")
    print("="*60)
    
    try:
        # 1. 初始化 memU 存储层
        print("\n[INFO] 正在初始化 memU 存储层...")
        memu_store = MemUStore(use_local_cache=True)
        
        # 检查服务是否就绪
        if not memu_store.ensure_service_ready():
            print("[WARN] memU 服务初始化失败，将使用本地缓存")
        else:
            print("[OK] memU 存储层初始化成功")
        
        # 2. 获取用户ID
        print("\n" + "-"*60)
        user_id = input("请输入用户ID（直接回车使用默认 'default_user'）: ").strip()
        if not user_id:
            user_id = "default_user"
        print(f"[INFO] 当前用户ID: {user_id}")
        
        # 3. 从 memU 加载历史画像
        print("\n[INFO] 正在加载历史画像...")
        profile = await memu_store.load_profile(user_id)
        if not profile:
            profile = init_profile()
            print("[INFO] 新用户，已初始化空画像")
        else:
            print("[OK] 已从 memU 加载历史画像")
        
        # 4. 初始化 Memory
        print("\n[INFO] 正在初始化 Memory...")
        memory_manager = ChatMemoryManager(memu_store)
        await memory_manager.load_history_into_memory(user_id)
        memory = memory_manager.get_memory_for_user(user_id)
        print("[OK] Memory 初始化成功")
        
        # 显示已加载的消息数量
        messages = memory_manager.get_memory_messages(user_id)
        if messages:
            print(f"[INFO] 已加载 {len(messages)} 条历史对话")
        
        # 5. 开始对话循环
        await chat_loop(user_id, profile, memory_manager, memu_store)
        
    except KeyboardInterrupt:
        print("\n\n[INFO] 程序被中断")
    except Exception as e:
        print(f"\n[ERROR] 程序启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())

