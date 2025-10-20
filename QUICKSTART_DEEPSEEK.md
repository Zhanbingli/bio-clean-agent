# ⚡ DeepSeek AI Agent 快速启动指南

## 📋 启动清单

- [ ] 获取 DeepSeek API Key
- [ ] 设置环境变量
- [ ] 安装依赖
- [ ] 启动 Agent
- [ ] 开始对话

---

## 🎯 三种启动方式

### 方式 1: 一键启动（最简单）⭐

```bash
cd /Users/lizhanbing12/ai-agent
./start_deepseek_agent.sh
```

脚本会自动：
- 检查 API Key
- 安装缺失的依赖
- 启动 DeepSeek Agent

---

### 方式 2: 手动启动（推荐学习）

```bash
# 1. 设置 API Key
export DEEPSEEK_API_KEY="sk-your-api-key-here"

# 2. 安装依赖（首次）
pip install openai rich pandas numpy scipy

# 3. 启动
cd /Users/lizhanbing12/ai-agent
python bio-clean-cli.py

# 或使用别名（更简洁）
python bio-clean-cli.py --user your_name
```

---

### 方式 3: 无 LLM 模式（离线/测试）

```bash
# 不使用 LLM，使用规则引擎
python bio-clean-cli.py --no-llm
```

---

## 💬 对话示例

### 示例 1: 基础数据清洗

```
You: Load data from data/trial_data.csv

🤔 Thinking...