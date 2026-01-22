"""
主程序：用户画像提取测试系统

提供交互式对话界面，从用户输入中提取和更新用户画像。
当前版本专注于画像提取功能，暂不输出Agent回复。

功能：
- 支持多用户（通过user_id隔离）
- 画像持久化存储（重启后恢复）
- 对话历史记录
"""

from profile_schema import init_profile
from profile_extractor import update_profile, check_api_key
from memory_store import MemoryStore
from typing import Dict, Any
import json


def chat_loop() -> None:
    """
    主对话循环函数
    
    功能：
    - 检查API Key配置
    - 初始化存储层（MemoryStore）
    - 获取或创建用户ID
    - 加载历史画像和对话
    - 接收用户输入
    - 提取并更新用户画像（立即保存）
    - 记录对话历史（立即保存）
    - 显示更新结果
    
    支持的命令：
    - "show": 显示当前用户画像
    - "exit": 退出程序并显示最终画像
    
    注意：
        - 画像和对话历史都会持久化存储
        - 重启程序后会自动恢复历史数据
        - 支持多用户（通过user_id隔离）
    """
    # 启动时检查API Key配置
    key_info = check_api_key()
    print("=" * 60)
    print("用户画像提取测试系统")
    print("=" * 60)
    if key_info['status'] == 'missing':
        print("⚠️  警告：未配置API Key")
        for suggestion in key_info['suggestions']:
            print(f"   - {suggestion}")
        print("\n程序将继续运行，但在调用API时会失败。\n")
    else:
        print(f"✅ {key_info['message']}\n")
    
    # 初始化存储层
    memory_store = MemoryStore()
    print("✅ 存储层初始化完成\n")
    
    # 获取用户ID
    user_id = input("请输入用户ID（直接回车使用默认用户）: ").strip()
    if not user_id:
        user_id = "default_user"
    
    print(f"\n当前用户ID: {user_id}\n")
    
    # 加载历史画像
    profile = memory_store.load_profile(user_id)
    if not profile:
        # 如果用户不存在，初始化空画像
        profile = init_profile()
        print("📝 新用户，已初始化空画像")
    else:
        print("📂 已加载历史画像")
    
    # 加载历史对话
    conversation_history = memory_store.load_conversation(user_id)
    if conversation_history:
        print(f"📂 已加载 {len(conversation_history)} 条历史对话")
    
    print("\n说明：输入对话内容（模拟老年人），系统会提取并更新用户画像")
    print("输入 'exit' 结束，输入 'show' 查看当前画像\n")
    print("-" * 60 + "\n")

    while True:
        user_input = input("你（模拟老人）: ").strip()
        
        if user_input.lower() == "exit":
            # 保存最终状态
            print("\n💾 正在保存最终状态...")
            memory_store.save_profile(user_id, profile)
            print("✅ 画像已保存")
            
            print("\n对话结束，最终用户画像：")
            print(json.dumps(profile, ensure_ascii=False, indent=2))
            break
        
        if user_input.lower() == "show":
            print("\n📌 当前用户画像：")
            print(json.dumps(profile, ensure_ascii=False, indent=2))
            print("\n" + "-" * 60 + "\n")
            continue
        
        if not user_input:
            continue
        
        # 保存用户消息到对话历史
        memory_store.append_message(user_id, "user", user_input)
        
        # 更新画像（只使用用户输入，暂时不包含Agent回复）
        conversation_text = f"用户：{user_input}"
        print("\n🔄 正在提取画像信息...")
        
        old_profile_str = json.dumps(profile, ensure_ascii=False, indent=2)
        profile = update_profile(conversation_text, profile)
        new_profile_str = json.dumps(profile, ensure_ascii=False, indent=2)
        
        # 立即保存更新后的画像
        if old_profile_str != new_profile_str:
            memory_store.save_profile(user_id, profile)
            print("💾 画像已保存")
        
        # 显示更新后的画像
        print("\n📌 更新后的用户画像：")
        print(json.dumps(profile, ensure_ascii=False, indent=2))
        
        # 如果画像有变化，高亮显示
        if old_profile_str != new_profile_str:
            print("\n✅ 画像已更新")
        else:
            print("\nℹ️  本次对话未提取到新的画像信息")
        
        print("\n" + "-" * 60 + "\n")

if __name__ == "__main__":
    chat_loop()
