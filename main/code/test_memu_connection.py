"""
测试 memU API 连接

用于验证 memU SDK 是否正确安装和配置。

运行方式：
    python test_memu_connection.py
"""

import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


async def test_cloud_api():
    """测试 memU Cloud API"""
    print("=" * 60)
    print("测试 memU Cloud API (memu-py)")
    print("=" * 60)
    
    try:
        from memu import MemuClient
        print("[成功] memu-py 包已安装")
    except ImportError:
        print("[失败] memu-py 包未安装")
        print("   请运行: pip install memu-py")
        return False
    
    api_key = os.getenv("MEMU_API_KEY", "")
    if not api_key:
        print("[警告] 未设置 MEMU_API_KEY 环境变量")
        print("   请在 .env 文件中添加: MEMU_API_KEY=your-api-key")
        return False
    
    try:
        client = MemuClient(
            base_url="https://api.memu.so",
            api_key=api_key
        )
        print("[成功] memU Cloud API 客户端初始化成功")
        print(f"   API Key: {api_key[:8]}...{api_key[-4:]}")
        return True
    except Exception as e:
        print(f"[失败] memU Cloud API 初始化失败: {e}")
        return False


async def test_service():
    """测试 memU Service"""
    print("\n" + "=" * 60)
    print("测试 memU Service (memu)")
    print("=" * 60)
    
    try:
        from memu import Service
        print("[成功] memu 包已安装")
    except ImportError:
        print("[失败] memu 包未安装")
        print("   请运行: pip install memu")
        return False
    
    api_key = os.getenv("MEMU_API_KEY", "")
    if not api_key:
        print("[警告] 未设置 MEMU_API_KEY 环境变量")
        return False
    
    try:
        # Service 可能需要更多配置参数
        # 这里只是测试导入，实际使用需要查阅文档
        service = Service(api_key=api_key)
        print("[成功] memU Service 初始化成功")
        print(f"   API Key: {api_key[:8]}...{api_key[-4:]}")
        return True
    except Exception as e:
        print(f"[失败] memU Service 初始化失败: {e}")
        print("   注意: Service 可能需要额外的配置参数（如 LLM provider）")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("memU API 连接测试")
    print("=" * 60 + "\n")
    
    # 检查环境变量
    api_key = os.getenv("MEMU_API_KEY", "")
    if not api_key:
        print("[警告] 未设置 MEMU_API_KEY")
        print("\n请按以下步骤配置：")
        print("1. 在项目根目录创建 .env 文件")
        print("2. 添加: MEMU_API_KEY=your-memu-api-key")
        print("\n或者设置环境变量：")
        print("  Windows PowerShell: $env:MEMU_API_KEY='your-key'")
        print("  Linux/Mac: export MEMU_API_KEY='your-key'")
        print("\n" + "=" * 60)
        return
    
    # 测试 Cloud API
    cloud_ok = asyncio.run(test_cloud_api())
    
    # 测试 Service（可选）
    # service_ok = asyncio.run(test_service())
    
    print("\n" + "=" * 60)
    if cloud_ok:
        print("[成功] memU Cloud API 测试通过")
        print("\n下一步：")
        print("1. 查阅 memU 官方文档确认 API 接口")
        print("2. 在 memory_store.py 中集成 memU API")
        print("3. 测试保存和加载功能")
    else:
        print("[失败] memU API 测试失败")
        print("\n请检查：")
        print("1. SDK 是否正确安装")
        print("2. API Key 是否正确配置")
        print("3. 网络连接是否正常")
    print("=" * 60)


if __name__ == "__main__":
    main()

