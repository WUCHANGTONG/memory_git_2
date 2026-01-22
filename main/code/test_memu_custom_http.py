"""
自定义 HTTP 请求测试 memU API（绕过 SDK 限制）

用于测试项目上下文（project_slug）的不同传递方式
"""

import asyncio
import os
import json
import httpx
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any, Optional

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


async def test_method1_url_path():
    """方法1: 通过 URL 路径传递 project_slug"""
    print("=" * 60)
    print("方法1: 通过 URL 路径传递 project_slug")
    print("=" * 60)
    
    api_key = os.getenv("MEMU_API_KEY", "")
    project_slug = os.getenv("MEMU_PROJECT_SLUG", "872227535-org-proj-26012201")
    
    if not api_key:
        print("[失败] 未设置 MEMU_API_KEY")
        return None
    
    base_url = "https://api.memu.so"
    
    # 方式1A: 在 URL 路径中包含 project_slug
    endpoint_v3 = f"/api/v3/memory/{project_slug}/memorize"
    url_v3 = f"{base_url}{endpoint_v3}"
    
    # 方式1B: 使用 v2 路径
    endpoint_v2 = "/api/v2/memory/memorize"
    url_v2 = f"{base_url}{endpoint_v2}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "conversation": [
            {"role": "user", "content": "我是石家庄人，今年68岁了"},
            {"role": "assistant", "content": "您好！很高兴认识您"}
        ],
        "user_id": "test_custom_user_001",
        "user_name": "测试用户",
        "agent_id": "test_agent_001",  # 可能需要真实的 agent_id
        "agent_name": "测试Agent"
    }
    
    print(f"\n测试 URL v3 路径: {url_v3}")
    print(f"Project Slug: {project_slug}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 尝试 v3 路径
            response = await client.post(url_v3, json=payload, headers=headers)
            print(f"\n响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("[成功] v3 路径调用成功！")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return result
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                print(f"[失败] v3 路径失败: {json.dumps(error_data, ensure_ascii=False, indent=2) if isinstance(error_data, dict) else error_data}")
                
                # 如果 v3 失败，尝试 v2
                print(f"\n尝试 v2 路径: {url_v2}")
                response_v2 = await client.post(url_v2, json=payload, headers=headers)
                print(f"响应状态码: {response_v2.status_code}")
                
                if response_v2.status_code == 200:
                    result = response_v2.json()
                    print("[成功] v2 路径调用成功！")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    return result
                else:
                    error_data = response_v2.json() if response_v2.headers.get("content-type", "").startswith("application/json") else response_v2.text
                    print(f"[失败] v2 路径也失败: {json.dumps(error_data, ensure_ascii=False, indent=2) if isinstance(error_data, dict) else error_data}")
                    
    except Exception as e:
        print(f"[失败] 请求失败: {e}")
        import traceback
        traceback.print_exc()
    
    return None


async def test_method2_request_header():
    """方法2: 通过请求头传递 project_slug"""
    print("\n" + "=" * 60)
    print("方法2: 通过请求头传递 project_slug")
    print("=" * 60)
    
    api_key = os.getenv("MEMU_API_KEY", "")
    project_slug = os.getenv("MEMU_PROJECT_SLUG", "872227535-org-proj-26012201")
    
    if not api_key:
        print("[失败] 未设置 MEMU_API_KEY")
        return None
    
    base_url = "https://api.memu.so"
    endpoint = "/api/v3/memory/memorize"
    url = f"{base_url}{endpoint}"
    
    # 尝试不同的请求头名称
    header_options = [
        ("X-Project-Slug", project_slug),
        ("X-Project-ID", project_slug),
        ("Project-Slug", project_slug),
        ("Project-ID", project_slug),
        ("X-Memory-Project-Slug", project_slug),
    ]
    
    payload = {
        "conversation": [
            {"role": "user", "content": "我是石家庄人，今年68岁了"},
            {"role": "assistant", "content": "您好！很高兴认识您"}
        ],
        "user_id": "test_custom_user_002",
        "user_name": "测试用户",
        "agent_id": "test_agent_001",
        "agent_name": "测试Agent"
    }
    
    for header_name, header_value in header_options:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            header_name: header_value
        }
        
        print(f"\n尝试请求头: {header_name} = {header_value}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                print(f"响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[成功] 使用 {header_name} 调用成功！")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    return result
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                    if isinstance(error_data, dict):
                        error_msg = error_data.get("message", str(error_data))
                        print(f"[失败] {error_msg}")
                    else:
                        print(f"[失败] {error_data}")
                        
        except Exception as e:
            print(f"[失败] 请求失败: {e}")
    
    return None


async def test_method3_request_body():
    """方法3: 通过请求体传递 project_slug"""
    print("\n" + "=" * 60)
    print("方法3: 通过请求体传递 project_slug")
    print("=" * 60)
    
    api_key = os.getenv("MEMU_API_KEY", "")
    project_slug = os.getenv("MEMU_PROJECT_SLUG", "872227535-org-proj-26012201")
    
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
    
    # 尝试在请求体中添加 project_slug
    payload_options = [
        {"project_slug": project_slug},
        {"project_id": project_slug},
        {"project": {"slug": project_slug}},
        {"project": {"id": project_slug}},
    ]
    
    base_payload = {
        "conversation": [
            {"role": "user", "content": "我是石家庄人，今年68岁了"},
            {"role": "assistant", "content": "您好！很高兴认识您"}
        ],
        "user_id": "test_custom_user_003",
        "user_name": "测试用户",
        "agent_id": "test_agent_001",
        "agent_name": "测试Agent"
    }
    
    for extra_field in payload_options:
        payload = {**base_payload, **extra_field}
        field_name = list(extra_field.keys())[0]
        
        print(f"\n尝试在请求体中添加: {field_name}")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                print(f"响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[成功] 使用 {field_name} 调用成功！")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    return result
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                    if isinstance(error_data, dict):
                        error_msg = error_data.get("message", str(error_data))
                        print(f"[失败] {error_msg}")
                    else:
                        print(f"[失败] {error_data}")
                        
        except Exception as e:
            print(f"[失败] 请求失败: {e}")
    
    return None


async def test_method4_query_params():
    """方法4: 通过查询参数传递 project_slug"""
    print("\n" + "=" * 60)
    print("方法4: 通过查询参数传递 project_slug")
    print("=" * 60)
    
    api_key = os.getenv("MEMU_API_KEY", "")
    project_slug = os.getenv("MEMU_PROJECT_SLUG", "872227535-org-proj-26012201")
    
    if not api_key:
        print("[失败] 未设置 MEMU_API_KEY")
        return None
    
    base_url = "https://api.memu.so"
    endpoint = "/api/v3/memory/memorize"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "conversation": [
            {"role": "user", "content": "我是石家庄人，今年68岁了"},
            {"role": "assistant", "content": "您好！很高兴认识您"}
        ],
        "user_id": "test_custom_user_004",
        "user_name": "测试用户",
        "agent_id": "test_agent_001",
        "agent_name": "测试Agent"
    }
    
    # 尝试不同的查询参数名称
    param_options = [
        {"project_slug": project_slug},
        {"project_id": project_slug},
        {"project": project_slug},
    ]
    
    for params in param_options:
        url = f"{base_url}{endpoint}?{list(params.keys())[0]}={list(params.values())[0]}"
        param_name = list(params.keys())[0]
        
        print(f"\n尝试查询参数: {param_name}={params[param_name]}")
        print(f"URL: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                print(f"响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[成功] 使用查询参数 {param_name} 调用成功！")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    return result
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                    if isinstance(error_data, dict):
                        error_msg = error_data.get("message", str(error_data))
                        print(f"[失败] {error_msg}")
                    else:
                        print(f"[失败] {error_data}")
                        
        except Exception as e:
            print(f"[失败] 请求失败: {e}")
    
    return None


async def main():
    """运行所有测试方法"""
    print("\n" + "=" * 60)
    print("memU API 自定义 HTTP 请求测试")
    print("测试不同的项目上下文传递方式")
    print("=" * 60 + "\n")
    
    api_key = os.getenv("MEMU_API_KEY", "")
    if not api_key:
        print("[失败] 未设置 MEMU_API_KEY")
        print("\n请按以下步骤配置：")
        print("1. 在项目根目录创建 .env 文件")
        print("2. 添加: MEMU_API_KEY=your-memu-api-key")
        print("3. 可选: MEMU_PROJECT_SLUG=your-project-slug")
        return
    
    print(f"[信息] API Key: {api_key[:8]}...{api_key[-4:]}")
    
    project_slug = os.getenv("MEMU_PROJECT_SLUG", "")
    if project_slug:
        print(f"[信息] Project Slug: {project_slug}")
    else:
        print("[警告] 未设置 MEMU_PROJECT_SLUG，将使用默认值: 872227535-org-proj-26012201")
        print("   如需使用其他值，请在 .env 文件中添加: MEMU_PROJECT_SLUG=your-project-slug")
    
    print("\n" + "-" * 60)
    print("开始测试...")
    print("-" * 60)
    
    # 测试方法1: URL 路径
    result1 = await test_method1_url_path()
    if result1:
        print("\n✅ 方法1 成功！项目上下文可以通过 URL 路径传递")
        return
    
    # 测试方法2: 请求头
    result2 = await test_method2_request_header()
    if result2:
        print("\n✅ 方法2 成功！项目上下文可以通过请求头传递")
        return
    
    # 测试方法3: 请求体
    result3 = await test_method3_request_body()
    if result3:
        print("\n✅ 方法3 成功！项目上下文可以通过请求体传递")
        return
    
    # 测试方法4: 查询参数
    result4 = await test_method4_query_params()
    if result4:
        print("\n✅ 方法4 成功！项目上下文可以通过查询参数传递")
        return
    
    # 所有方法都失败
    print("\n" + "=" * 60)
    print("所有方法都失败了")
    print("=" * 60)
    print("\n可能的原因：")
    print("1. API Key 不是来自 Memory 项目")
    print("2. Project Slug 不正确")
    print("3. agent_id 不存在（需要使用控制台中真实的 agent_id）")
    print("4. API 版本或接口格式已变更")
    print("\n建议：")
    print("1. 确认 API Key 来自正确的 Memory 项目")
    print("2. 从控制台获取真实的 agent_id 并更新测试代码")
    print("3. 检查 memU 官方文档确认最新的 API 格式")


if __name__ == "__main__":
    asyncio.run(main())

