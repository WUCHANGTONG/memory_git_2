# MemU 本地部署计划

## 📋 项目概述

本计划旨在将 **memU-main** 框架部署到本地环境，并配置使用 **DashScope API**（阿里云通义千问），后续将融合到现有的 **code** 项目中。

## 🎯 部署目标

1. ✅ 在本地成功部署 memU 框架
2. ✅ 配置 DashScope API（使用 DASHSCOPE_API_KEY）
3. ✅ 验证框架基本功能（记忆存储和检索）
4. ✅ 为后续融合到 code 项目做准备

---

## 📦 阶段一：环境准备（安全升级方案）

### ⚠️ 重要提示

**不要直接升级系统 Python 版本！** 这可能会破坏现有项目的依赖。

**推荐方案**：使用虚拟环境隔离 memU 项目，保持现有项目不受影响。

### 1.0 兼容性检查（必须先执行）

在升级之前，先检查现有依赖是否兼容 Python 3.13：

```bash
# 运行兼容性检查脚本
cd memory/code
python check_python_compatibility.py
```

这个脚本会：
- ✅ 检查当前 Python 版本
- ✅ 检查 requirements.txt 中的包是否兼容 Python 3.13
- ✅ 提供升级建议

### 1.1 Python 版本管理方案

#### 方案 A：使用虚拟环境（推荐，不影响现有项目）

**优点**：
- ✅ 完全隔离，不影响现有项目
- ✅ 可以同时保留 Python 3.12 和 3.13 环境
- ✅ 易于管理和切换

**步骤**：

1. **安装 Python 3.13**（如果还没有）：
   ```bash
   # Windows: 从 python.org 下载安装
   # 或使用 pyenv-win (如果已安装)
   pyenv install 3.13.0
   ```

2. **为 memU 创建独立的虚拟环境**：
   ```bash
   # 使用 Python 3.13 创建虚拟环境
   python3.13 -m venv memu-env
   # 或如果 Python 3.13 在 PATH 中
   py -3.13 -m venv memu-env
   
   # 激活虚拟环境
   # Windows PowerShell:
   memu-env\Scripts\Activate.ps1
   # Windows CMD:
   memu-env\Scripts\activate.bat
   # Linux/Mac:
   source memu-env/bin/activate
   ```

3. **验证 Python 版本**：
   ```bash
   python --version
   # 应该显示 Python 3.13.x
   ```

#### 方案 B：使用 pyenv（多版本管理）

如果使用 pyenv，可以轻松管理多个 Python 版本：

```bash
# 安装 Python 3.13
pyenv install 3.13.0

# 在 memU-main 目录设置本地版本
cd memU-main
pyenv local 3.13.0

# 创建虚拟环境
python -m venv .venv
```

#### 方案 C：使用 conda（如果使用 Anaconda）

```bash
# 创建新的 conda 环境（Python 3.13）
conda create -n memu python=3.13
conda activate memu
```

### 1.2 系统要求检查

- [ ] **运行兼容性检查**：`python check_python_compatibility.py`
- [ ] **Python 3.13+**：在虚拟环境中安装（不升级系统 Python）
  ```bash
  # 检查虚拟环境中的 Python 版本
  python --version
  # 应该显示 Python 3.13.x
  ```

- [ ] **依赖管理工具**（可选）：
  - `uv`（推荐，memU 使用）
  - 或使用 `pip` 和 `venv`

### 1.2 环境变量配置

创建或更新 `.env` 文件（在 `memory/` 目录下）：

```bash
# DashScope API 配置
DASHSCOPE_API_KEY=sk-your-actual-api-key-here

# 可选：如果后续需要 OpenAI
# OPENAI_API_KEY=sk-...
```

**注意**：`.env` 文件应放在 `memory/` 目录（项目根目录），不是 `code/` 目录。

---

## 📦 阶段二：MemU 框架安装

### 2.1 进入 memU-main 目录

```bash
cd memU-main
```

### 2.2 安装方式选择

#### 方式 A：使用 uv（推荐，如果已安装）

```bash
# 安装 uv（如果未安装）
# Windows: 
# pip install uv
# 或下载: https://github.com/astral-sh/uv/releases

# 使用 uv 安装
make install
# 或直接使用:
uv sync
```

#### 方式 B：使用 pip（标准方式）

```bash
# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

# 安装 memU（开发模式）
pip install -e .
```

### 2.3 验证安装

```bash
# 检查 memU 是否可导入
python -c "from memu.app import MemoryService; print('✅ MemU 安装成功')"
```

---

## 📦 阶段三：DashScope 配置测试

### 3.1 创建测试脚本

在 `memU-main/` 目录下创建 `test_dashscope.py`：

```python
"""
测试 DashScope API 配置
"""
import asyncio
import os
from dotenv import load_dotenv
from memu.app import MemoryService

# 加载环境变量
load_dotenv(dotenv_path="../memory/.env")  # 从 memory 目录加载

async def main():
    """测试 DashScope 配置"""
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not dashscope_api_key:
        print("❌ 错误：未找到 DASHSCOPE_API_KEY 环境变量")
        print("请确保在 memory/.env 文件中设置了 DASHSCOPE_API_KEY")
        return
    
    print("=" * 60)
    print("测试 DashScope 配置")
    print("=" * 60)
    print(f"✅ API Key 已加载: {dashscope_api_key[:10]}...")
    
    # 初始化 MemoryService，使用 DashScope
    try:
        service = MemoryService(
            llm_profiles={
                "default": {
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "api_key": dashscope_api_key,
                    "chat_model": "qwen-max",  # 或 qwen-plus, qwen-turbo
                    "client_backend": "http"  # 使用 HTTP 客户端
                },
                # 如果需要单独的嵌入模型配置
                "embedding": {
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "api_key": dashscope_api_key,
                    "embed_model": "text-embedding-v2",  # DashScope 嵌入模型
                    "client_backend": "http"
                }
            },
            database_config={
                "metadata_store": {"provider": "inmemory"},  # 使用内存存储（无需数据库）
            },
        )
        print("✅ MemoryService 初始化成功")
        
        # 测试记忆功能（使用示例对话文件）
        test_file = "tests/example/example_conversation.json"
        if os.path.exists(test_file):
            print(f"\n📝 测试记忆功能：处理 {test_file}")
            result = await service.memorize(
                resource_url=test_file,
                modality="conversation",
                user={"user_id": "test_user"}
            )
            print(f"✅ 记忆提取成功")
            print(f"   - 提取了 {len(result.get('items', []))} 个记忆条目")
            print(f"   - 生成了 {len(result.get('categories', []))} 个类别")
            
            # 测试检索功能
            print(f"\n🔍 测试检索功能")
            queries = [
                {"role": "user", "content": {"text": "用户的偏好是什么？"}}
            ]
            retrieve_result = await service.retrieve(
                queries=queries,
                where={"user_id": "test_user"}
            )
            print(f"✅ 检索成功")
            print(f"   - 找到 {len(retrieve_result.get('items', []))} 个相关记忆条目")
        else:
            print(f"⚠️  测试文件不存在: {test_file}")
            print("   跳过记忆测试，但配置已成功")
        
        print("\n" + "=" * 60)
        print("✅ DashScope 配置测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3.2 运行测试

```bash
# 在 memU-main 目录下
python test_dashscope.py
```

**预期结果**：
- ✅ API Key 加载成功
- ✅ MemoryService 初始化成功
- ✅ 记忆提取成功
- ✅ 检索功能正常

---

## 📦 阶段四：与 Code 项目融合准备

### 4.1 架构分析

**当前 code 项目结构**：
- `agent.py`：主程序，对话循环
- `profile_extractor.py`：画像提取器（使用 LLM）
- `profile_schema.py`：画像结构定义
- `memory_store.py`：存储层（当前是本地 JSON）

**融合策略**：
1. **保留现有接口**：`MemoryStore` 类接口保持不变
2. **替换存储实现**：将 `memory_store.py` 中的本地存储替换为 memU 服务
3. **渐进式迁移**：先支持双存储（本地 + memU），再完全迁移

### 4.2 融合计划（后续实施）

#### 步骤 1：创建 memU 适配器

创建 `memory_store_memu.py`：

```python
"""
MemU 存储适配器
将 memU 框架集成到现有的 MemoryStore 接口
"""
from memu.app import MemoryService
from typing import Dict, Any, Optional, List
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class MemUAdapter:
    """MemU 服务适配器"""
    
    def __init__(self):
        dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
        if not dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY 未配置")
        
        self.service = MemoryService(
            llm_profiles={
                "default": {
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "api_key": dashscope_api_key,
                    "chat_model": "qwen-max",
                    "client_backend": "http"
                }
            },
            database_config={
                "metadata_store": {"provider": "inmemory"},
            },
        )
    
    async def save_conversation(self, user_id: str, conversation: List[Dict]):
        """将对话保存到 memU"""
        # 将对话转换为 memU 格式
        # 使用 memorize() 方法
        pass
    
    async def retrieve_profile(self, user_id: str, query: str):
        """从 memU 检索用户画像"""
        # 使用 retrieve() 方法
        pass
```

#### 步骤 2：更新 MemoryStore

修改 `memory_store.py`，添加 memU 支持：

```python
class MemoryStore:
    def __init__(self, use_memu: bool = False):
        self.use_memu = use_memu
        if use_memu:
            self.memu_adapter = MemUAdapter()
        # ... 保留原有本地存储逻辑
```

#### 步骤 3：更新 agent.py

在 `agent.py` 中启用 memU：

```python
# 使用 memU 存储
memory_store = MemoryStore(use_memu=True)
```

---

## 📋 部署检查清单

### 环境准备
- [ ] Python 3.13+ 已安装
- [ ] `.env` 文件已配置 DASHSCOPE_API_KEY
- [ ] 虚拟环境已创建（可选但推荐）

### MemU 安装
- [ ] memU 框架已安装（`pip install -e .` 或 `uv sync`）
- [ ] 可以成功导入 `from memu.app import MemoryService`

### 配置测试
- [ ] DashScope API Key 可以正常使用
- [ ] MemoryService 可以成功初始化
- [ ] 记忆提取功能测试通过
- [ ] 检索功能测试通过

### 融合准备
- [ ] 已理解 code 项目架构
- [ ] 已规划融合方案
- [ ] 已创建融合任务清单

---

## 🚀 快速开始命令

### 完整部署流程（一键执行）

```bash
# 1. 进入 memU-main 目录
cd memU-main

# 2. 创建虚拟环境（如果还没有）
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell

# 3. 安装 memU
pip install -e .

# 4. 验证安装
python -c "from memu.app import MemoryService; print('✅ 安装成功')"

# 5. 运行 DashScope 测试
python test_dashscope.py
```

---

## 📚 参考资源

### MemU 文档
- [MemU GitHub](https://github.com/NevaMind-AI/memU)
- [MemU 中文 README](memU-main/README_zh.md)
- [MemU API 文档](memU-main/README.md)

### DashScope 文档
- [DashScope API 文档](https://help.aliyun.com/zh/model-studio/)
- [通义千问模型列表](https://help.aliyun.com/zh/model-studio/developer-reference/model-list)

### 示例代码
- `memU-main/examples/example_1_conversation_memory.py`：对话记忆示例
- `memU-main/tests/test_inmemory.py`：内存存储测试

---

## ⚠️ 注意事项

1. **Python 版本管理**：
   - ⚠️ **不要直接升级系统 Python**，这可能会破坏现有项目
   - ✅ **推荐使用虚拟环境**隔离 memU 项目
   - ✅ 先运行 `check_python_compatibility.py` 检查兼容性
   - ✅ 在虚拟环境中安装 Python 3.13+，保持系统 Python 不变

2. **API Key 安全**：不要将 API Key 提交到 Git，使用 `.env` 文件并添加到 `.gitignore`

3. **存储选择**：
   - 开发测试：使用 `inmemory`（无需数据库）
   - 生产环境：建议使用 PostgreSQL + pgvector

4. **模型选择**：
   - `qwen-max`：最强性能，适合复杂任务
   - `qwen-plus`：平衡性能和速度
   - `qwen-turbo`：最快速度，适合简单任务

5. **环境隔离**：
   - memU 项目使用独立的虚拟环境（Python 3.13+）
   - code 项目保持原有环境（Python 3.12）
   - 两个项目互不影响

---

## 🔄 后续步骤

完成部署后，可以：

1. **探索 memU 功能**：
   - 尝试不同的记忆类别配置
   - 测试 RAG 和 LLM 两种检索方法
   - 处理多模态内容（文档、图像）

2. **开始融合**：
   - 创建 memU 适配器
   - 逐步替换现有存储层
   - 测试融合后的功能

3. **优化配置**：
   - 根据实际需求调整模型参数
   - 配置记忆类别
   - 优化检索策略

---

## 📞 问题排查

### 问题 1：Python 版本不匹配
**错误**：`requires-python = ">=3.13"`
**解决**：
1. **不要升级系统 Python**（可能破坏现有项目）
2. **使用虚拟环境**：创建独立的 Python 3.13 虚拟环境
3. **使用 pyenv**：如果已安装，可以管理多个 Python 版本
4. **先运行兼容性检查**：`python check_python_compatibility.py`

### 问题 2：API Key 未找到
**错误**：`DASHSCOPE_API_KEY 未配置`
**解决**：检查 `.env` 文件路径和内容，确保在正确目录

### 问题 3：导入错误
**错误**：`ModuleNotFoundError: No module named 'memu'`
**解决**：确保已安装 memU（`pip install -e .`），并激活了正确的虚拟环境

### 问题 4：DashScope API 调用失败
**错误**：API 调用返回错误
**解决**：
- 检查 API Key 是否有效
- 检查网络连接
- 查看 DashScope 服务状态
- 确认模型名称正确（如 `qwen-max`）

---

**最后更新**：2025-01-XX
**维护者**：开发团队

