"""
主程序 - 对话循环 + 画像更新

实现交互式对话循环，整合画像提取和 memU 存储。
支持多用户、多轮对话、角色区分、时间戳、持久画像。
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from memory_store import MemUStore
from chat_memory import ChatMemoryManager
from profile_extractor import update_profile
from profile_schema_optimized import init_optimized_profile

# 尝试导入个性化回答模块
try:
    from personalized_response import PersonalizedResponder
    PERSONALIZED_RESPONSE_AVAILABLE = True
except ImportError:
    PERSONALIZED_RESPONSE_AVAILABLE = False
    PersonalizedResponder = None
    print("[WARN] personalized_response 模块未找到，个性化回答功能不可用")

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# 从环境变量读取配置：是否开启个性化回答（默认开启）
ENABLE_PERSONALIZED_RESPONSE = os.getenv(
    "ENABLE_PERSONALIZED_RESPONSE", 
    "true"
).lower() in ("true", "1", "yes", "on")


def show_profile_summary(profile: Dict[str, Any]):
    """
    显示用户画像摘要（显示所有字段）- 优化版结构
    
    Args:
        profile: 用户画像字典（优化版结构）
    """
    def format_field_value(field_dict: Dict[str, Any], field_name: str) -> str:
        """格式化字段值显示"""
        value = field_dict.get("value")
        confidence = field_dict.get("confidence", 0.0)
        
        if value is None:
            display_value = "未设置"
        elif isinstance(value, list):
            if len(value) == 0:
                display_value = "[]"
            else:
                display_value = ", ".join(str(v) for v in value)
        else:
            display_value = str(value)
        
        # 如果有值，显示置信度
        if value is not None:
            return f"{field_name}: {display_value} (置信度: {confidence:.2f})"
        else:
            return f"{field_name}: {display_value}"
    
    print("\n" + "="*70)
    print("用户画像摘要（优化版）- 所有字段")
    print("="*70)
    
    # 身份与语言
    identity = profile.get("identity_language", {})
    print("\n【身份与语言】")
    print(f"  {format_field_value(identity.get('age', {}), '年龄')}")
    print(f"  {format_field_value(identity.get('gender', {}), '性别')}")
    print(f"  {format_field_value(identity.get('region', {}), '地区')}")
    print(f"  {format_field_value(identity.get('education_level', {}), '教育程度')}")
    print(f"  {format_field_value(identity.get('explanation_depth_preference', {}), '解释深度偏好')}")
    
    # 健康与安全
    health = profile.get("health_safety", {})
    print("\n【健康与安全】")
    print(f"  {format_field_value(health.get('chronic_conditions', {}), '慢性疾病')}")
    print(f"  {format_field_value(health.get('mobility_level', {}), '行动能力')}")
    print(f"  {format_field_value(health.get('daily_energy_level', {}), '日常精力水平')}")
    print(f"  {format_field_value(health.get('risk_sensitivity_level', {}), '风险敏感度')}")
    
    # 认知与交互
    cognitive = profile.get("cognitive_interaction", {})
    print("\n【认知与交互】")
    print(f"  {format_field_value(cognitive.get('attention_span', {}), '注意力持续时间')}")
    print(f"  {format_field_value(cognitive.get('processing_speed', {}), '信息处理速度')}")
    print(f"  {format_field_value(cognitive.get('digital_literacy', {}), '数字技能水平')}")
    print(f"  {format_field_value(cognitive.get('instruction_following_ability', {}), '指令理解能力')}")
    
    # 情感与支持
    emotional = profile.get("emotional_support", {})
    print("\n【情感与支持】")
    print(f"  {format_field_value(emotional.get('baseline_mood', {}), '基础情绪状态')}")
    print(f"  {format_field_value(emotional.get('loneliness_level', {}), '孤独感程度')}")
    print(f"  {format_field_value(emotional.get('emotional_support_need', {}), '情感支持需求强度')}")
    print(f"  {format_field_value(emotional.get('preferred_conversation_mode', {}), '偏好对话模式')}")
    
    # 生活方式与社交
    lifestyle = profile.get("lifestyle_social", {})
    print("\n【生活方式与社交】")
    print(f"  {format_field_value(lifestyle.get('living_situation', {}), '居住状况')}")
    print(f"  {format_field_value(lifestyle.get('social_support_level', {}), '社交支持水平')}")
    print(f"  {format_field_value(lifestyle.get('independence_level', {}), '独立性水平')}")
    print(f"  {format_field_value(lifestyle.get('core_interests', {}), '核心兴趣')}")
    
    # 价值观与偏好
    values = profile.get("values_preferences", {})
    print("\n【价值观与偏好】")
    print(f"  {format_field_value(values.get('topic_preferences', {}), '话题偏好')}")
    print(f"  {format_field_value(values.get('taboo_topics', {}), '敏感话题')}")
    print(f"  {format_field_value(values.get('value_orientation', {}), '价值观导向')}")
    print(f"  {format_field_value(values.get('motivational_factors', {}), '激励因素')}")
    
    # 生成风格控制器
    style = profile.get("response_style", {})
    print("\n【生成风格控制器】⭐")
    print(f"  {format_field_value(style.get('formality_level', {}), '正式程度')}")
    print(f"  {format_field_value(style.get('verbosity_level', {}), '详细程度')}")
    print(f"  {format_field_value(style.get('emotional_tone', {}), '情感语调')}")
    print(f"  {format_field_value(style.get('directive_strength', {}), '指导强度')}")
    print(f"  {format_field_value(style.get('information_density', {}), '信息密度')}")
    print(f"  {format_field_value(style.get('risk_cautiousness', {}), '风险谨慎度')}")
    
    # 交互历史（学习层）
    history = profile.get("interaction_history", {})
    print("\n【交互历史】（学习层，不直接用于生成）")
    print(f"  {format_field_value(history.get('successful_interaction_patterns', {}), '成功交互模式')}")
    print(f"  {format_field_value(history.get('failed_interaction_patterns', {}), '失败交互模式')}")
    print(f"  {format_field_value(history.get('preference_evolution_trend', {}), '偏好变化趋势')}")
    print(f"  {format_field_value(history.get('response_satisfaction_score', {}), '回答满意度')}")
    print(f"  {format_field_value(history.get('last_interaction_feedback', {}), '最近交互反馈')}")
    
    print("\n" + "="*70 + "\n")


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
                   memu_store: MemUStore,
                   responder: Optional[Any] = None,
                   enable_personalized_response: bool = True):
    """
    对话循环主函数
    
    Args:
        user_id: 用户ID
        profile: 用户画像字典
        memory_manager: Memory管理器
        memu_store: memU存储层
        responder: 个性化回答生成器（可选）
        enable_personalized_response: 是否开启个性化回答
    """
    print("\n" + "="*60)
    print("对话系统已启动")
    print("="*60)
    print("\n说明：")
    print("  - 输入对话内容，系统会提取并更新用户画像")
    if enable_personalized_response and responder:
        print("  - 系统会根据用户画像生成个性化回答")
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
                print("\n直接输入对话内容即可提取画像信息")
                if enable_personalized_response and responder:
                    print("系统会根据用户画像自动生成个性化回答\n")
                else:
                    print("（个性化回答功能已关闭）\n")
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
            
            # 生成个性化回答（如果启用）
            if enable_personalized_response and responder:
                try:
                    print("\n[INFO] 正在生成个性化回答...")
                    assistant_response = await responder.generate_response(
                        user_id, 
                        user_input, 
                        profile
                    )
                    
                    # 保存助手回复到对话历史
                    await memory_manager.add_message(
                        user_id, 
                        "assistant", 
                        assistant_response
                    )
                    
                    # 显示回答
                    print(f"\n助手: {assistant_response}\n")
                except Exception as e:
                    print(f"[WARN] 个性化回答生成失败: {e}")
                    print("[INFO] 继续对话，但不生成回答\n")
            else:
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
            profile = init_optimized_profile()
            print("[INFO] 新用户，已初始化空画像（优化版）")
        else:
            print("[OK] 已从 memU 加载历史画像（优化版）")
        
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
        
        # 5. 初始化个性化回答生成器（如果启用）
        responder = None
        if ENABLE_PERSONALIZED_RESPONSE and PERSONALIZED_RESPONSE_AVAILABLE:
            print("\n[INFO] 正在初始化个性化回答生成器...")
            try:
                responder = PersonalizedResponder(memu_store, memory_manager)
                print("[OK] 个性化回答生成器初始化成功")
            except Exception as e:
                print(f"[WARN] 个性化回答生成器初始化失败: {e}")
                print("[INFO] 将关闭个性化回答功能")
                responder = None
        elif not PERSONALIZED_RESPONSE_AVAILABLE:
            print("\n[WARN] 个性化回答模块不可用，功能已关闭")
        elif not ENABLE_PERSONALIZED_RESPONSE:
            print("\n[INFO] 个性化回答功能已通过配置关闭")
        
        # 6. 开始对话循环
        await chat_loop(
            user_id, 
            profile, 
            memory_manager, 
            memu_store,
            responder=responder,
            enable_personalized_response=ENABLE_PERSONALIZED_RESPONSE and responder is not None
        )
        
    except KeyboardInterrupt:
        print("\n\n[INFO] 程序被中断")
    except Exception as e:
        print(f"\n[ERROR] 程序启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())

