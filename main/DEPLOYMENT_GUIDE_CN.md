# MemU 本地部署和测试指南

## 📋 部署步骤

### 1. 环境准备

**必需组件：**
- ✅ Python 3.13+ 已安装
- ✅ Rust 和 Cargo（项目包含 Rust 扩展，需要编译）
- ✅ 进入项目目录：`cd memU-main`

**安装 Rust（如果未安装）：**

Windows 上安装 Rust：
```powershell
# 方法1：使用 rustup（推荐）
# 访问 https://rustup.rs/ 下载并运行 rustup-init.exe
# 或使用 PowerShell 命令：
Invoke-WebRequest https://win.rustup.rs/x86_64 -OutFile rustup-init.exe
.\rustup-init.exe

# 方法2：使用 Chocolatey（如果已安装）
choco install rust

# 安装后，重启终端或运行：
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 验证安装
rustc --version
cargo --version
```

### 2. 创建和激活虚拟环境

**方式一：使用 venv（推荐初学者）**

如果虚拟环境已存在（项目根目录下有 `venv` 文件夹），直接激活即可：

```powershell
# 进入项目目录
cd memU-main

# 激活虚拟环境（Windows PowerShell）
.\venv\Scripts\Activate.ps1

# 如果遇到执行策略错误，先运行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 激活虚拟环境（Windows CMD）
venv\Scripts\activate.bat
```

如果虚拟环境不存在或需要重新创建：

```powershell
# 创建虚拟环境
python -m venv venv

# 然后激活（同上）
.\venv\Scripts\Activate.ps1
```

**验证虚拟环境是否激活成功：**
```powershell
# 检查 Python 路径（应该指向 venv 目录）
python -c "import sys; print(sys.executable)"

# 检查环境变量（PowerShell）
echo $env:VIRTUAL_ENV

# 应该显示类似：E:\Cursor_workspace\memory_git_2\memU-main\venv
```

**方式二：使用 uv（项目推荐，需要 Python 3.13+）**

```powershell
# 安装 uv（如果未安装）
pip install uv

# 或使用官方安装脚本（推荐）
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 创建虚拟环境并安装依赖
cd memU-main
uv venv
uv pip install -e .

# 激活虚拟环境
.\venv\Scripts\Activate.ps1
```

### 3. 安装项目依赖

**重要：** 在安装依赖前，确保虚拟环境已激活（命令提示符前应显示 `(venv)`）

**如果使用 venv：**
```powershell
# 确保虚拟环境已激活
# 如果未激活，运行：.\venv\Scripts\Activate.ps1

# 升级 pip
python -m pip install --upgrade pip

# 安装项目（开发模式）
pip install -e .

# 验证安装
python -c "import memu; print('MemU 安装成功！')"
```

**如果使用 uv：**
```powershell
# 使用 Makefile（推荐，需要安装 make 或使用 Git Bash）
make install

# 或手动安装
uv sync

# 或使用 uv pip
uv pip install -e .
```

**检查已安装的包：**
```powershell
pip list
# 应该能看到 memu-py 及其依赖项
```

### 4. 配置 API 密钥

设置 OpenAI API 密钥（必需）：
```powershell
# Windows PowerShell
$env:OPENAI_API_KEY="your_api_key_here"

# Windows CMD
set OPENAI_API_KEY=your_api_key_here

# 永久设置（可选）
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'your_api_key_here', 'User')
```

### 5. 运行测试

#### 测试 1：基础功能测试（In-Memory存储）
```powershell
cd tests
python test_inmemory.py
```

#### 测试 2：示例1 - 对话记忆提取
```powershell
cd examples
python example_1_conversation_memory.py
```

#### 测试 3：示例2 - 技能提取
```powershell
python example_2_skill_extraction.py
```

#### 测试 4：示例3 - 多模态记忆
```powershell
python example_3_multimodal_memory.py
```

## 📊 预期输出

### test_inmemory.py 输出
- 显示提取的记忆类别（Categories）
- RAG检索结果（带相似度分数）
- LLM检索结果（深度语义理解）

### example_1_conversation_memory.py 输出
- 处理多个对话文件
- 生成记忆类别 Markdown 文件
- 输出目录：`examples/output/conversation_example/`

## 🔍 验证清单

- [ ] 虚拟环境创建成功
- [ ] 依赖安装完成（无错误）
- [ ] API 密钥已设置
- [ ] test_inmemory.py 运行成功
- [ ] 示例脚本运行成功
- [ ] 输出文件生成正确

## 🐛 常见问题

### 问题1：找不到模块 memu
**解决**：确保在项目根目录（memU-main）下运行，且已安装项目：
```powershell
# 确保虚拟环境已激活
.\venv\Scripts\Activate.ps1

# 重新安装项目
pip install -e .
```

### 问题2：虚拟环境激活失败（PowerShell 执行策略错误）
**错误信息**：`无法加载文件，因为在此系统上禁止运行脚本`

**解决**：
```powershell
# 方法1：临时允许（推荐）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 方法2：使用 CMD 激活
venv\Scripts\activate.bat

# 方法3：直接使用完整路径运行 Python
.\venv\Scripts\python.exe your_script.py
```

### 问题3：虚拟环境未激活（在 base 环境中）
**检查方法**：
```powershell
# 检查 Python 路径
python -c "import sys; print(sys.executable)"
# 如果显示 D:\anaconda\python.exe 或类似系统路径，说明未激活

# 检查环境变量
echo $env:VIRTUAL_ENV
# 如果为空，说明未激活
```

**解决**：
```powershell
# 激活虚拟环境
cd memU-main
.\venv\Scripts\Activate.ps1

# 再次检查，应该显示 venv 路径
echo $env:VIRTUAL_ENV
```

### 问题4：API 密钥错误
**解决**：检查环境变量是否正确设置：
```powershell
echo $env:OPENAI_API_KEY  # PowerShell
echo %OPENAI_API_KEY%     # CMD
```

### 问题5：缺少依赖包
**解决**：重新安装依赖：
```powershell
# 确保虚拟环境已激活
.\venv\Scripts\Activate.ps1

# 重新安装
pip install -e . --force-reinstall
```

### 问题6：Python 版本不匹配
**项目要求**：Python 3.13+（但当前环境是 3.12.4）

**解决**：
- 如果使用 venv：可以继续使用，但某些功能可能受限
- 如果使用 uv：需要升级到 Python 3.13+
- 或者使用 conda 创建 Python 3.13 环境：
```powershell
conda create -n memu python=3.13
conda activate memu
cd memU-main
pip install -e .
```

### 问题7：安装失败 - 缺少 Rust/Cargo
**错误信息**：`Cargo, the Rust package manager, is not installed or is not on PATH`

**原因**：项目包含 Rust 扩展模块，需要 Rust 工具链来编译

**解决**：
```powershell
# 1. 安装 Rust（见上面的"环境准备"部分）
# 2. 安装后重启终端或重新加载 PATH
# 3. 验证安装
rustc --version
cargo --version

# 4. 重新安装项目
pip install -e .
```

**替代方案**：如果不想安装 Rust，可以尝试安装预编译的 wheel 包（如果有）：
```powershell
# 从 PyPI 安装（如果有预编译版本）
pip install memu-py
```

## 📚 下一步

完成基础测试后，可以：
1. 查看生成的记忆类别文件
2. 尝试自定义对话数据
3. 探索其他示例脚本
4. 阅读 API 文档进行深度集成



