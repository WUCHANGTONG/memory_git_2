"""
根据 memU 官方文档验证 API 调用方式

参考: https://memu.pro/docs#cloud-version
"""

import asyncio
import os
import json
import httpx
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


async def test_basic_request_no_project_context():
    """
    测试1: 基础请求（不带项目上下文）
    
    根据文档，API Key 应该在创建时就关联到 Memory 项目，
    理论上不需要在请求中传递 project_slug
    """
    print("=" * 60)
    print("测试1: 基础请求（不带项目上下文）")
    print("根据文档，API Key 应该在创建时就关联到项目")
    print("=" * 60)
    
    api_key = os.getenv("MEMU_API_KEY", "")
    if not api_key:
        print("[失败] 未设置 MEMU_API_KEY")
        return None
    
    base_url = "https://api.memu.so"
    endpoint = "/api/v3/memory/memorize"
    url = f"{base_url}{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "conversation": [
            {"role": "user", "content": "我是石家庄人，今年68岁了"},
            {"role": "assistant", "content": "您好！很高兴认识您"}
        ],
        "user_id": "test_doc_user_001",
        "user_name": "测试用户",
        "agent_id": "test_agent_001",
        "agent_name": "测试Agent"
    }
    
    print(f"\n请求 URL: {url}")
    print(f"Headers: Authorization: Bearer {api_key[:8]}...{api_key[-4:]}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"\n响应状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("[成功] 基础请求成功！")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return result
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                print(f"\n响应内容:")
                if isinstance(error_data, dict):
                    print(json.dumps(error_data, ensure_ascii=False, indent=2))
                    error_msg = error_data.get("message", "")
                    error_code = error_data.get("error_code", "")
                    
                    if error_code == "BAD_REQUEST" and "Memory project" in error_msg:
                        print("\n[分析] 错误信息表明：")
                        print("  - API Key 可能不是从 Memory 项目创建的")
                        print("  - 或者需要在控制台确认 Key 的关联项目")
                else:
                    print(error_data)
                    
    except Exception as e:
        print(f"[失败] 请求失败: {e}")
        import traceback
        traceback.print_exc()
    
    return None


async def test_with_project_slug_header():
    """
    测试2: 带项目上下文的请求（通过请求头）
    
    如果基础请求失败，尝试添加项目上下文
    """
    print("\n" + "=" * 60)
    print("测试2: 带项目上下文的请求（通过请求头）")
    print("=" * 60)
    
    api_key = os.getenv("MEMU_API_KEY", "")
    project_slug = os.getenv("MEMU_PROJECT_SLUG", "872227535-org-proj-26012201")
    
    if not api_key:
        print("[失败] 未设置 MEMU_API_KEY")
        return None
    
    base_url = "https://api.memu.so"
    endpoint = "/api/v3/memory/memorize"
    url = f"{base_url}{endpoint}"
    
    # 使用最可能有效的请求头名称
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Project-Slug": project_slug  # 最可能有效的格式
    }
    
    payload = {
        "conversation": [
            {"role": "user", "content": "我是石家庄人，今年68岁了"},
            {"role": "assistant", "content": "您好！很高兴认识您"}
        ],
        "user_id": "test_doc_user_002",
        "user_name": "测试用户",
        "agent_id": "test_agent_001",
        "agent_name": "测试Agent"
    }
    
    print(f"\n请求 URL: {url}")
    print(f"Headers: X-Project-Slug = {project_slug}")
    print(f"Project Slug: {project_slug}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"\n响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("[成功] 带项目上下文的请求成功！")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return result
            elif response.status_code == 402:
                print("[部分成功] 认证通过，但账户余额不足")
                print("这说明：")
                print("  [成功] API Key 正确")
                print("  [成功] 项目上下文传递成功")
                print("  [成功] 认证通过")
                print("  [警告] 需要充值账户余额")
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                print(f"\n响应内容: {error_data}")
                return "SUCCESS_BUT_INSUFFICIENT_BALANCE"
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                print(f"\n响应内容:")
                if isinstance(error_data, dict):
                    print(json.dumps(error_data, ensure_ascii=False, indent=2))
                else:
                    print(error_data)
                    
    except Exception as e:
        print(f"[失败] 请求失败: {e}")
        import traceback
        traceback.print_exc()
    
    return None


async def test_retrieve_endpoint():
    """
    测试3: 测试 retrieve 端点（可能不需要项目上下文）
    """
    print("\n" + "=" * 60)
    print("测试3: 测试 retrieve 端点")
    print("=" * 60)
    
    api_key = os.getenv("MEMU_API_KEY", "")
    if not api_key:
        print("[失败] 未设置 MEMU_API_KEY")
        return None
    
    base_url = "https://api.memu.so"
    endpoint = "/api/v3/memory/retrieve/related-memory-items"
    url = f"{base_url}{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": "用户的偏好和习惯",
        "user_id": "test_doc_user_001"
    }
    
    print(f"\n请求 URL: {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"\n响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("[成功] retrieve 请求成功！")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return result
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                print(f"\n响应内容:")
                if isinstance(error_data, dict):
                    print(json.dumps(error_data, ensure_ascii=False, indent=2))
                else:
                    print(error_data)
                    
    except Exception as e:
        print(f"[失败] 请求失败: {e}")
        import traceback
        traceback.print_exc()
    
    return None


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("根据 memU 官方文档验证 API 调用")
    print("参考: https://memu.pro/docs#cloud-version")
    print("=" * 60 + "\n")
    
    api_key = os.getenv("MEMU_API_KEY", "")
    if not api_key:
        print("[失败] 未设置 MEMU_API_KEY")
        return
    
    print(f"[信息] API Key: {api_key[:8]}...{api_key[-4:]}")
    
    project_slug = os.getenv("MEMU_PROJECT_SLUG", "")
    if project_slug:
        print(f"[信息] Project Slug: {project_slug}")
    else:
        print("[信息] 未设置 MEMU_PROJECT_SLUG，将使用默认值")
    
    print("\n" + "-" * 60)
    print("根据文档分析：")
    print("1. API Key 应该在创建时就关联到 Memory 项目")
    print("2. 理论上不需要在请求中传递 project_slug")
    print("3. 如果出现 'API key does not come from a Memory project' 错误")
    print("   说明 Key 可能不是从 Memory 项目创建的")
    print("-" * 60)
    
    # 测试1: 基础请求（不带项目上下文）
    result1 = await test_basic_request_no_project_context()
    
    if result1:
        print("\n✅ 基础请求成功！说明 API Key 正确关联到 Memory 项目")
        return
    
    # 测试2: 带项目上下文
    result2 = await test_with_project_slug_header()
    
    if result2 == "SUCCESS_BUT_INSUFFICIENT_BALANCE":
        print("\n✅ 带项目上下文的请求认证通过！")
        print("   虽然余额不足，但说明配置正确")
        return
    
    # 测试3: retrieve 端点
    await test_retrieve_endpoint()
    
    print("\n" + "=" * 60)
    print("总结和建议：")
    print("=" * 60)
    print("\n如果所有测试都返回 'API key does not come from a Memory project'：")
    print("1. 登录 memU 控制台: https://memu.pro")
    print("2. 确认当前 API Key 是从 Memory 项目创建的")
    print("3. 如果不是，请创建一个新的 Memory 项目并生成新的 API Key")
    print("4. 确认项目类型是 'Memory' 而不是其他类型")
    print("\n如果返回 402 错误（余额不足）：")
    print("1. 说明认证和项目上下文都正确")
    print("2. 只需要充值账户余额即可正常使用")


if __name__ == "__main__":
    asyncio.run(main())

