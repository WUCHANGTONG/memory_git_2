"""
主程序 - 对话循环 + 画像更新

实现交互式对话循环，整合画像提取和 memU 存储。
支持多用户、多轮对话、角色区分、时间戳、持久画像。
"""

import asyncio
import json
import os
import sys
import threading
import time
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

# 从环境变量读取配置：交互模式（real_user / simulated_user）
INTERACTION_MODE = os.getenv("INTERACTION_MODE", "real_user").lower()

# 尝试导入用户模拟器模块（包方式导入）
try:
    from elderly_user_simulator.elderly_user_simulator import SimpleElderlyUserSimulator
    USER_SIMULATOR_AVAILABLE = True
except ImportError:
    USER_SIMULATOR_AVAILABLE = False
    SimpleElderlyUserSimulator = None
    if INTERACTION_MODE == "simulated_user":
        print("[WARN] elderly_user_simulator 模块未找到，模拟用户模式不可用")


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


async def process_user_message(
    user_id: str,
    user_input: str,
    profile: Dict[str, Any],
    memory_manager: ChatMemoryManager,
    memu_store: MemUStore,
    responder: Optional[Any] = None,
    enable_personalized_response: bool = True
) -> Dict[str, Any]:
    """
    处理用户消息（可被用户模拟器调用）
    
    Args:
        user_id: 用户ID
        user_input: 用户输入
        profile: 当前用户画像
        memory_manager: Memory管理器
        memu_store: memU存储层
        responder: 个性化回答生成器（可选）
        enable_personalized_response: 是否开启个性化回答
        
    Returns:
        {
            "assistant_response": str,  # 助手回复
            "updated_profile": Dict,     # 更新后的画像
            "extraction_success": bool   # 画像提取是否成功
        }
    """
    # 1. 保存用户消息
    await memory_manager.add_message(user_id, "user", user_input)
    
    # 2. 提取画像
    extraction_success = True
    try:
        updated_profile = update_profile(user_input, profile)
    except Exception as e:
        print(f"[WARN] 画像提取失败: {e}")
        updated_profile = profile
        extraction_success = False
    
    # 3. 保存画像
    await memu_store.save_profile(user_id, updated_profile)
    
    # 4. 生成个性化回答（如果启用）
    assistant_response = ""
    if enable_personalized_response and responder:
        try:
            assistant_response = await responder.generate_response(
                user_id,
                user_input,
                updated_profile
            )
            await memory_manager.add_message(user_id, "assistant", assistant_response)
        except Exception as e:
            print(f"[WARN] 个性化回答生成失败: {e}")
            assistant_response = "[助手回复生成失败]"
    else:
        assistant_response = "[个性化回答功能已关闭]"
    
    return {
        "assistant_response": assistant_response,
        "updated_profile": updated_profile,
        "extraction_success": extraction_success
    }


def input_with_countdown(
    prompt: str,
    countdown_seconds: int = 5,
    default_choice: str = "y"
) -> str:
    """
    带倒计时的输入函数
    
    只显示一次提示信息，用户可以在提示后直接输入。
    如果倒计时结束前没有输入，返回默认值。
    
    Args:
        prompt: 提示信息
        countdown_seconds: 倒计时秒数
        default_choice: 默认选择（倒计时结束后返回的值）
        
    Returns:
        用户输入或默认选择
    """
    result_queue = []
    input_received = threading.Event()
    
    def get_input():
        """在单独线程中获取输入"""
        try:
            # 注意：这里不使用 input(prompt)，因为 prompt 已经在主线程中输出了
            user_input = input().strip().lower()
            result_queue.append(user_input)
            input_received.set()
        except EOFError:
            result_queue.append(default_choice)
            input_received.set()
    
    # 显示提示信息（只显示一次，不换行）
    sys.stdout.write(f"{prompt}[{countdown_seconds}秒后自动继续] ")
    sys.stdout.flush()
    
    # 启动输入线程
    input_thread = threading.Thread(target=get_input, daemon=True)
    input_thread.start()
    
    # 等待用户输入或倒计时结束
    start_time = time.time()
    while True:
        if input_received.is_set():
            # 用户已输入，等待线程完成
            input_thread.join(timeout=0.1)
            break
        
        elapsed = time.time() - start_time
        if elapsed >= countdown_seconds:
            # 倒计时结束，输出换行并返回默认值
            print()  # 换行
            return default_choice
        
        # 短暂休眠，避免CPU占用过高
        time.sleep(0.1)
    
    # 返回用户输入或默认值
    if result_queue:
        return result_queue[0]
    else:
        return default_choice


async def chat_loop(user_id: str, profile: Dict[str, Any], 
                   memory_manager: ChatMemoryManager, 
                   memu_store: MemUStore,
                   responder: Optional[Any] = None,
                   enable_personalized_response: bool = True,
                   interaction_mode: str = "real_user",
                   user_simulator: Optional[Any] = None):
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
    
    # 根据模式显示不同的说明
    if interaction_mode == "simulated_user":
        print("\n模式：模拟用户模式")
        print("  - 模拟老年人用户将自动生成对话")
        print("  - 系统会提取并更新用户画像")
        if enable_personalized_response and responder:
            print("  - 系统会根据用户画像生成个性化回答")
        
        # 读取倒计时配置
        countdown_enabled = True
        countdown_seconds = 5
        auto_continue = True
        max_turns = None
        
        if user_simulator and hasattr(user_simulator, 'config'):
            conv_config = user_simulator.config.get("conversation_config", {})
            countdown_enabled = conv_config.get("countdown_enabled", True)
            countdown_seconds = conv_config.get("countdown_seconds", 5)
            auto_continue = conv_config.get("auto_continue", True)
            max_turns = conv_config.get("max_turns", None)
        
        if countdown_enabled:
            print(f"  - 每轮对话后有{countdown_seconds}秒倒计时，结束后自动继续")
        else:
            print("  - 每轮对话后会询问是否继续")
        print("\n" + "-"*60 + "\n")
        
        # 等待用户输入开始
        input("按回车键开始对话...")
        print("\n开始对话...\n")
        
        # 模拟用户模式对话循环
        conversation_history = []
        turn = 0
        
        while True:
            try:
                # 检查最大轮数限制
                if max_turns is not None and turn >= max_turns:
                    print(f"\n[INFO] 已达到最大对话轮数 ({max_turns})，结束对话")
                    break
                
                turn += 1
                print(f"\n--- 第 {turn} 轮对话 ---\n")
                
                # 1. 生成用户消息
                print("[INFO] 正在生成用户消息...")
                try:
                    user_message = user_simulator.generate_user_message(conversation_history)
                    if not user_message or not user_message.strip():
                        print("[WARN] 生成的消息为空，跳过本轮")
                        continue
                    print(f"用户: {user_message}\n")
                except Exception as e:
                    print(f"[ERROR] 生成用户消息失败: {e}")
                    import traceback
                    traceback.print_exc()
                    continue_choice = input("\n是否继续对话？(y/n): ").strip().lower()
                    if continue_choice in ("n", "no", "exit", "quit"):
                        break
                    continue
                
                # 2. 处理用户消息（保存、提取画像、生成回复）
                print("[INFO] 正在处理用户消息...")
                try:
                    result = await process_user_message(
                        user_id=user_id,
                        user_input=user_message,
                        profile=profile,
                        memory_manager=memory_manager,
                        memu_store=memu_store,
                        responder=responder,
                        enable_personalized_response=enable_personalized_response
                    )
                    
                    # 更新画像和对话历史
                    profile = result["updated_profile"]
                    assistant_response = result["assistant_response"]
                    
                    # 更新对话历史
                    conversation_history.append({"role": "user", "content": user_message})
                    conversation_history.append({"role": "assistant", "content": assistant_response})
                    
                    if result["extraction_success"]:
                        print("[OK] 画像提取完成")
                    else:
                        print("[WARN] 画像提取失败，使用当前画像")
                    
                    print(f"助手: {assistant_response}\n")
                    
                except Exception as e:
                    print(f"[ERROR] 处理用户消息失败: {e}")
                    import traceback
                    traceback.print_exc()
                    # 即使失败也记录对话历史
                    conversation_history.append({"role": "user", "content": user_message})
                    conversation_history.append({"role": "assistant", "content": "[处理失败]"})
                
                # 6. 询问是否继续（带倒计时）
                print("-" * 60)
                if countdown_enabled:
                    continue_choice = input_with_countdown(
                        "\n是否继续对话？(y/n，或输入 'exit' 退出): ",
                        countdown_seconds=countdown_seconds,
                        default_choice="y" if auto_continue else "n"
                    )
                else:
                    continue_choice = input("\n是否继续对话？(y/n，或输入 'exit' 退出): ").strip().lower()
                
                if continue_choice in ("n", "no", "exit", "quit"):
                    print("\n[INFO] 正在保存数据...")
                    await memu_store.save_profile(user_id, profile)
                    await memory_manager.save_current_memory(user_id)
                    print("[OK] 数据已保存")
                    print("\n对话已结束，再见！")
                    break
                elif continue_choice not in ("y", "yes", ""):
                    print("[INFO] 输入无效，默认继续对话")
                
            except KeyboardInterrupt:
                print("\n\n[INFO] 检测到中断信号，正在保存数据...")
                await memu_store.save_profile(user_id, profile)
                await memory_manager.save_current_memory(user_id)
                print("[OK] 数据已保存")
                print("\n对话已中断，再见！")
                break
            except Exception as e:
                print(f"\n[ERROR] 发生错误: {e}")
                import traceback
                traceback.print_exc()
                continue_choice = input("\n是否继续对话？(y/n): ").strip().lower()
                if continue_choice in ("n", "no", "exit", "quit"):
                    break
        
        return
    
    # 真实用户模式
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
        
        # 6. 初始化用户模拟器（如果使用模拟用户模式）
        user_simulator = None
        interaction_mode = INTERACTION_MODE  # 初始化交互模式
        if INTERACTION_MODE == "simulated_user":
            if not USER_SIMULATOR_AVAILABLE:
                print("\n[ERROR] 模拟用户模式需要 elderly_user_simulator 模块")
                print("[INFO] 切换到真实用户模式")
                interaction_mode = "real_user"
            else:
                print("\n[INFO] 正在初始化用户模拟器...")
                try:
                    config_path = os.getenv("ELDERLY_USER_CONFIG", None)
                    user_simulator = SimpleElderlyUserSimulator(config_path)
                    print("[OK] 用户模拟器初始化成功")
                except Exception as e:
                    print(f"[WARN] 用户模拟器初始化失败: {e}")
                    print("[INFO] 切换到真实用户模式")
                    interaction_mode = "real_user"
                    user_simulator = None
        
        # 7. 开始对话循环
        await chat_loop(
            user_id, 
            profile, 
            memory_manager, 
            memu_store,
            responder=responder,
            enable_personalized_response=ENABLE_PERSONALIZED_RESPONSE and responder is not None,
            interaction_mode=interaction_mode,
            user_simulator=user_simulator
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

