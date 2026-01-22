"""
Python 版本兼容性检查脚本

用于检查当前环境和依赖包是否兼容 Python 3.13
在升级 Python 版本之前运行此脚本，确保不会破坏现有包
"""
import sys
import subprocess
import json
import io
from pathlib import Path
from typing import Dict, List, Tuple

# 设置输出编码（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def get_current_python_version() -> Tuple[int, int, int]:
    """获取当前 Python 版本"""
    return sys.version_info[:3]

def get_installed_packages() -> Dict[str, str]:
    """获取当前环境中已安装的包及其版本"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        packages = json.loads(result.stdout)
        return {pkg["name"].lower(): pkg["version"] for pkg in packages}
    except Exception as e:
        print(f"[ERROR] 无法获取已安装包列表: {e}")
        return {}

def check_package_compatibility(package_name: str, version: str) -> Dict[str, any]:
    """
    检查包是否兼容 Python 3.13
    通过查询 PyPI API 获取包的元数据
    """
    import urllib.request
    import urllib.error
    
    try:
        # 查询 PyPI JSON API
        url = f"https://pypi.org/pypi/{package_name}/{version}/json"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())
            
        # 检查 requires_python 字段
        requires_python = data.get("info", {}).get("requires_python", "")
        
        # 检查是否支持 Python 3.13
        # 简单检查：如果 requires_python 包含 ">=3.13" 或 ">=3.12" 或为空，认为可能兼容
        compatible = True
        reason = ""
        
        if requires_python:
            # 解析版本要求（简化版）
            if "3.13" in requires_python or ">=3.13" in requires_python:
                compatible = True
                reason = f"明确支持 Python 3.13 ({requires_python})"
            elif "<3.13" in requires_python or "<=3.12" in requires_python:
                compatible = False
                reason = f"不支持 Python 3.13 ({requires_python})"
            elif ">=3.12" in requires_python or ">=3.11" in requires_python:
                compatible = True  # 可能兼容，需要测试
                reason = f"可能兼容 ({requires_python})"
            else:
                compatible = True  # 默认认为可能兼容
                reason = f"未明确限制 ({requires_python})"
        else:
            compatible = True
            reason = "未指定 Python 版本要求"
            
        return {
            "compatible": compatible,
            "reason": reason,
            "requires_python": requires_python
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {
                "compatible": None,
                "reason": "包版本在 PyPI 上不存在",
                "requires_python": None
            }
        return {
            "compatible": None,
            "reason": f"查询失败: {e}",
            "requires_python": None
        }
    except Exception as e:
        return {
            "compatible": None,
            "reason": f"检查失败: {e}",
            "requires_python": None
        }

def check_requirements_file(requirements_path: Path) -> List[Dict[str, any]]:
    """检查 requirements.txt 文件中的包"""
    if not requirements_path.exists():
        return []
    
    results = []
    with open(requirements_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 解析包名和版本
            # 格式可能是: package==1.0.0 或 package>=1.0.0 等
            parts = line.split('==')
            if len(parts) == 2:
                package_name = parts[0].strip()
                version = parts[1].strip()
            else:
                # 处理其他格式，如 >=, <= 等
                import re
                match = re.match(r'([a-zA-Z0-9_-]+)(.*)', line)
                if match:
                    package_name = match.group(1)
                    version = "latest"  # 无法确定版本
                else:
                    continue
            
            print(f"  检查 {package_name}...", end=" ", flush=True)
            compat_info = check_package_compatibility(package_name, version if version != "latest" else "")
            results.append({
                "package": package_name,
                "version": version,
                **compat_info
            })
            
            if compat_info["compatible"]:
                print("[OK]")
            elif compat_info["compatible"] is False:
                print("[FAIL]")
            else:
                print("[?]")
    
    return results

def main():
    """主函数"""
    print("=" * 60)
    print("Python 版本兼容性检查")
    print("=" * 60)
    print()
    
    # 1. 检查当前 Python 版本
    current_version = get_current_python_version()
    print(f"[*] 当前 Python 版本: {current_version[0]}.{current_version[1]}.{current_version[2]}")
    
    if current_version[0] == 3 and current_version[1] >= 13:
        print("[OK] 当前 Python 版本已满足 memU 要求（3.13+）")
        return
    else:
        print(f"[!] 当前 Python 版本低于 memU 要求（需要 3.13+）")
        print()
    
    # 2. 检查 requirements.txt
    code_dir = Path(__file__).parent
    requirements_path = code_dir / "requirements.txt"
    
    print("[*] 检查 requirements.txt 中的依赖包...")
    print()
    
    if requirements_path.exists():
        results = check_requirements_file(requirements_path)
        
        # 统计结果
        compatible = [r for r in results if r.get("compatible") is True]
        incompatible = [r for r in results if r.get("compatible") is False]
        unknown = [r for r in results if r.get("compatible") is None]
        
        print()
        print("=" * 60)
        print("兼容性检查结果")
        print("=" * 60)
        print()
        
        if incompatible:
            print("[FAIL] 不兼容的包（需要处理）：")
            for r in incompatible:
                print(f"   - {r['package']} {r.get('version', '')}")
                print(f"     原因: {r.get('reason', '未知')}")
            print()
        
        if unknown:
            print("[?] 无法确定兼容性的包（需要手动测试）：")
            for r in unknown:
                print(f"   - {r['package']} {r.get('version', '')}")
                print(f"     原因: {r.get('reason', '未知')}")
            print()
        
        if compatible:
            print(f"[OK] 兼容的包: {len(compatible)} 个")
            print()
        
        # 总结
        print("=" * 60)
        print("建议")
        print("=" * 60)
        print()
        
        if incompatible:
            print("[!] 发现不兼容的包，建议：")
            print("   1. 检查是否有这些包的更新版本支持 Python 3.13")
            print("   2. 考虑使用替代包")
            print("   3. 在虚拟环境中测试升级后的兼容性")
        else:
            print("[OK] 未发现明显不兼容的包")
            print("   建议：")
            print("   1. 使用虚拟环境隔离 memU 项目（推荐）")
            print("   2. 在虚拟环境中安装 Python 3.13+")
            print("   3. 测试所有功能是否正常")
        
        print()
        print("[TIP] 推荐方案：使用虚拟环境，而不是升级系统 Python")
        print("   这样可以保持现有项目不受影响")
        print()
    else:
        print(f"[!] 未找到 requirements.txt: {requirements_path}")
        print()

if __name__ == "__main__":
    main()

