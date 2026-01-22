"""检查 .env 文件配置"""
import os
from dotenv import load_dotenv
from pathlib import Path

# 检查项目根目录的 .env 文件
env_path = Path(__file__).parent.parent / '.env'
print(f"检查 .env 文件: {env_path}")
print(f"文件存在: {env_path.exists()}")

if env_path.exists():
    load_dotenv(env_path)
    print("\n环境变量:")
    api_key = os.getenv("MEMU_API_KEY", "")
    
    print(f"  MEMU_API_KEY: {'已设置' if api_key else '未设置'}")
    if api_key:
        print(f"    值: {api_key[:8]}...{api_key[-4:]}")
    
    # 读取文件内容（显示 MEMU 相关行）
    print("\n.env 文件中的 MEMU 相关配置:")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if 'MEMU_API_KEY' in line.upper():
                print(f"  {line.strip()}")
else:
    print("\n.env 文件不存在，请创建它并添加配置")

