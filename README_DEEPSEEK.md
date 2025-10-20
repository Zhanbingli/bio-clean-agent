# 🤖 Bio Clean Agent - DeepSeek AI 驱动版

> **世界级 AI Agent**：结合 DeepSeek 大语言模型和专业数据清洗工具，提供类似 Claude Code 的交互体验！

## ✨ 核心亮点

### 🎯 真正的 AI 理解
- 💬 **自然对话**：用人类语言描述需求，AI 自动理解意图
- 🧠 **智能规划**：AI 自动选择合适的工具和执行顺序
- 🔄 **上下文感知**：记住整个对话，理解复杂的多步骤任务
- 📊 **结果解释**：AI 用清晰的语言解释每个操作和结果

### 🛠️ 专业工具集成
- 15+ 专业数据清洗工具
- 50+ 医学标准知识库
- 70+ 证据驱动的清洗策略
- ISO 8000 质量评估
- FDA 21 CFR Part 11 合规

### 🎨 漂亮的界面
- Rich 库精美终端 UI
- 实时进度显示
- 彩色表格和面板
- 类似 Claude Code 的体验

---

## 🚀 5 分钟快速开始

### 步骤 1: 获取 DeepSeek API Key

```bash
# 1. 访问 https://platform.deepseek.com
# 2. 注册/登录
# 3. 创建 API Key
# 4. 复制 key（sk-xxx...）
```

### 步骤 2: 设置 API Key

```bash
# 设置环境变量
export DEEPSEEK_API_KEY="sk-your-api-key-here"

# 验证
echo $DEEPSEEK_API_KEY
```

### 步骤 3: 安装依赖

```bash
cd /Users/lizhanbing12/ai-agent

# 安装必需的包
pip install openai rich pandas numpy scipy
```

### 步骤 4: 启动 AI Agent

```bash
# 方法 1: 使用快速启动脚本（推荐）
./start_deepseek_agent.sh

# 方法 2: 直接运行
python bio-clean-cli.py

# 方法 3: 指定用户
python bio-clean-cli.py --user analyst_jane
```

### 步骤 5: 开始对话！

```
🧬 Bio Clean Agent - AI-Powered Interactive CLI

✓ LLM Enabled: deepseek-chat

You: Hi, I have a clinical trial dataset that needs cleaning