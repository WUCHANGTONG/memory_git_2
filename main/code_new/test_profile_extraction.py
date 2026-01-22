"""
用户画像提取功能测试脚本

测试 profile_schema 和 profile_extractor 的基本功能。
"""

import json
from profile_schema import init_profile
from profile_extractor import update_profile, check_api_key


def test_init_profile():
    """测试初始化空画像"""
    print("=" * 60)
    print("测试1: 初始化空画像")
    print("=" * 60)
    
    profile = init_profile()
    
    # 验证结构
    assert "demographics" in profile
    assert "health" in profile
    assert "cognitive" in profile
    assert "emotional" in profile
    assert "lifestyle" in profile
    assert "preferences" in profile
    
    # 验证字段结构
    assert "age" in profile["demographics"]
    assert "value" in profile["demographics"]["age"]
    assert "confidence" in profile["demographics"]["age"]
    
    print("[OK] 画像结构正确")
    print(f"   维度数量: {len(profile)}")
    print(f"   示例字段: demographics.age = {profile['demographics']['age']}")
    print()


def test_api_key_check():
    """测试 API Key 检查"""
    print("=" * 60)
    print("测试2: API Key 检查")
    print("=" * 60)
    
    key_info = check_api_key()
    print(f"状态: {key_info['status']}")
    print(f"消息: {key_info['message']}")
    
    if key_info['status'] == 'missing':
        print("\n[WARN] 警告: API Key 未配置")
        print("配置建议:")
        for suggestion in key_info.get('suggestions', []):
            print(f"   - {suggestion}")
    else:
        print(f"[OK] API Key 已配置")
        if 'key_preview' in key_info:
            print(f"   Key 预览: {key_info['key_preview']}")
    print()


def test_profile_extraction():
    """测试画像提取（需要 API Key）"""
    print("=" * 60)
    print("测试3: 画像提取")
    print("=" * 60)
    
    key_info = check_api_key()
    if key_info['status'] == 'missing':
        print("[WARN] 跳过测试: API Key 未配置")
        print("   请先配置 DASHSCOPE_API_KEY 后再运行此测试")
        return
    
    # 初始化画像
    profile = init_profile()
    print("初始画像已创建")
    
    # 测试对话1: 基本信息
    conversation1 = "你好，我是石家庄人，今年68岁了"
    print(f"\n对话1: {conversation1}")
    print("正在提取画像信息...")
    
    try:
        profile = update_profile(conversation1, profile)
        print("[OK] 画像提取成功")
        
        # 检查是否提取到信息
        age = profile["demographics"]["age"]["value"]
        city = profile["demographics"]["city_level"]["value"]
        
        if age is not None:
            print(f"   提取到年龄: {age} (置信度: {profile['demographics']['age']['confidence']})")
        if city is not None:
            print(f"   提取到城市: {city} (置信度: {profile['demographics']['city_level']['confidence']})")
        
    except Exception as e:
        print(f"[ERROR] 画像提取失败: {e}")
        return
    
    # 测试对话2: 健康信息
    conversation2 = "我有点高血压，每天都要吃药"
    print(f"\n对话2: {conversation2}")
    print("正在提取画像信息...")
    
    try:
        profile = update_profile(conversation2, profile)
        print("[OK] 画像提取成功")
        
        # 检查是否提取到信息
        conditions = profile["health"]["chronic_conditions"]["value"]
        medication = profile["health"]["medication_adherence"]["value"]
        
        if conditions:
            print(f"   提取到慢性疾病: {conditions}")
        if medication is not None:
            print(f"   提取到用药情况: {medication}")
        
    except Exception as e:
        print(f"[ERROR] 画像提取失败: {e}")
        return
    
    # 显示最终画像
    print("\n最终用户画像:")
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("用户画像提取功能测试")
    print("=" * 60 + "\n")
    
    try:
        test_init_profile()
        test_api_key_check()
        test_profile_extraction()
        
        print("=" * 60)
        print("[OK] 所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

