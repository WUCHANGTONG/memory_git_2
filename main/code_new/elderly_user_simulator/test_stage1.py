"""
阶段一功能测试脚本
测试 SimulatedUser 和 SimpleElderlyUserSimulator 的功能
"""

import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from profile_schema_optimized import init_optimized_profile
from elderly_user_simulator.elderly_user_simulator import SimulatedUser, SimpleElderlyUserSimulator

def test_simulated_user():
    """测试 SimulatedUser 类"""
    print("=" * 60)
    print("测试 1: SimulatedUser 初始化")
    print("=" * 60)
    
    # 创建测试画像
    profile = init_optimized_profile()
    profile['identity_language']['age']['value'] = 68
    profile['identity_language']['gender']['value'] = '女'
    profile['health_safety']['chronic_conditions']['value'] = ['高血压']
    
    # 初始化 SimulatedUser
    user = SimulatedUser(ground_truth_profile=profile)
    
    print(f"[OK] SimulatedUser 初始化成功")
    print(f"  - Ground truth age: {user.ground_truth_profile['identity_language']['age']['value']}")
    print(f"  - Ground truth gender: {user.ground_truth_profile['identity_language']['gender']['value']}")
    print(f"  - Expressed profile initialized: {user.expressed_profile is not None}")
    print(f"  - Noise model configured: {user.noise_model is not None}")
    print()

def test_simple_simulator():
    """测试 SimpleElderlyUserSimulator 类"""
    print("=" * 60)
    print("测试 2: SimpleElderlyUserSimulator 初始化")
    print("=" * 60)
    
    config_path = Path(__file__).parent / "elderly_user_simulator_config.json"
    
    if not config_path.exists():
        print(f"[ERROR] 配置文件不存在: {config_path}")
        return
    
    try:
        simulator = SimpleElderlyUserSimulator(str(config_path))
        print(f"[OK] SimpleElderlyUserSimulator 初始化成功")
        print(f"  - Has simulated_user: {hasattr(simulator, 'simulated_user')}")
        
        if hasattr(simulator, 'simulated_user'):
            gt = simulator.simulated_user.ground_truth_profile
            age = gt.get('identity_language', {}).get('age', {}).get('value', 'Not set')
            print(f"  - Ground truth age from config: {age}")
        
        print(f"  - LLM initialized: {simulator.llm is not None or simulator.dashscope_initialized}")
        print()
    except Exception as e:
        print(f"[ERROR] 初始化失败: {e}")
        print()

def test_evaluation():
    """测试画像提取准确性评估"""
    print("=" * 60)
    print("测试 3: 画像提取准确性评估")
    print("=" * 60)
    
    # 创建 ground truth profile
    gt_profile = init_optimized_profile()
    gt_profile['identity_language']['age']['value'] = 70
    gt_profile['identity_language']['gender']['value'] = '男'
    gt_profile['health_safety']['chronic_conditions']['value'] = ['高血压', '糖尿病']
    
    # 创建提取的画像（部分正确）
    extracted_profile = init_optimized_profile()
    extracted_profile['identity_language']['age']['value'] = 70  # 正确
    extracted_profile['identity_language']['gender']['value'] = '男'  # 正确
    extracted_profile['health_safety']['chronic_conditions']['value'] = ['高血压']  # 部分正确
    
    # 创建 SimulatedUser 并评估
    user = SimulatedUser(ground_truth_profile=gt_profile)
    result = user.evaluate_extraction_accuracy(extracted_profile)
    
    print(f"[OK] 评估完成")
    print(f"  - 总体准确率: {result['overall_accuracy']:.2%}")
    print(f"  - 总字段数: {result['total_fields']}")
    print(f"  - 正确字段数: {result['correct_fields']}")
    print(f"  - 各维度准确率:")
    for dim, acc in result['dimension_accuracy'].items():
        if result['total_fields'] > 0:
            print(f"    - {dim}: {acc:.2%}")
    print()

def test_noise_model():
    """测试噪声模型"""
    print("=" * 60)
    print("测试 4: 噪声模型")
    print("=" * 60)
    
    profile = init_optimized_profile()
    profile['identity_language']['age']['value'] = 68
    
    user = SimulatedUser(ground_truth_profile=profile)
    
    # 测试噪声应用
    fact = {'value': '68岁', 'confidence': 1.0}
    
    print(f"[OK] 噪声模型配置:")
    print(f"  - 遗忘率: {user.noise_model['forgetfulness_rate']}")
    print(f"  - 模糊率: {user.noise_model['vagueness_rate']}")
    print(f"  - 误导率: {user.noise_model['misleading_rate']}")
    print(f"  - 话题跳跃率: {user.noise_model['topic_hopping_rate']}")
    
    # 测试应用噪声（多次测试看效果）
    print(f"\n  测试噪声应用（10次）:")
    for i in range(10):
        result = user.apply_noise(fact.copy())
        if result is None:
            print(f"    第{i+1}次: 遗忘（不表达）")
        elif result['value'] != fact['value']:
            print(f"    第{i+1}次: {result['value']} (已添加噪声)")
        else:
            print(f"    第{i+1}次: {result['value']} (无噪声)")
    print()

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("阶段一功能测试")
    print("=" * 60 + "\n")
    
    try:
        test_simulated_user()
        test_simple_simulator()
        test_evaluation()
        test_noise_model()
        
        print("=" * 60)
        print("所有测试完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

