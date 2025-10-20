# 🤖 DeepSeek API 集成指南

## 快速开始

### 1. 获取 DeepSeek API Key

1. 访问 [DeepSeek Platform](https://platform.deepseek.com)
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的 API Key
5. 复制 API Key（类似：`sk-xxx...`）

### 2. 设置环境变量

#### macOS/Linux:

```bash
# 临时设置（当前终端会话）
export DEEPSEEK_API_KEY="sk-your-api-key-here"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export DEEPSEEK_API_KEY="sk-your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

#### Windows (PowerShell):

```powershell
# 临时设置
$env:DEEPSEEK_API_KEY="sk-your-api-key-here"

# 永久设置
[System.Environment]::SetEnvironmentVariable('DEEPSEEK_API_KEY', 'sk-your-api-key-here', 'User')
```

### 3. 启动 AI Agent

```bash
cd /Users/lizhanbing12/ai-agent

# 使用 DeepSeek（默认）
python bio-clean-cli.py

# 或显式指定
python bio-clean-cli.py --llm deepseek
```

---

## 🎮 使用示例

### 示例 1: 完全自然语言交互

```
You: Hi, I need to clean some clinical trial data