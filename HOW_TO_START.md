# 🚀 如何启动 AI Agent

## 最快启动方式（30秒）

```bash
# 1. 设置 DeepSeek API Key
export DEEPSEEK_API_KEY="sk-your-api-key-here"

# 2. 启动
cd /Users/lizhanbing12/ai-agent
python bio-clean-cli.py
```

就这么简单！🎉

---

## 完整说明

### ✅ 前置要求

1. **Python 3.10+**
   ```bash
   python --version  # 检查版本
   ```

2. **DeepSeek API Key**
   - 访问：https://platform.deepseek.com
   - 注册并创建 API Key
   - 复制 key（格式：`sk-xxx...`）

3. **依赖包**
   ```bash
   pip install openai rich pandas numpy scipy
   ```

---

### 🎮 启动命令

#### 使用 DeepSeek（AI 驱动）

```bash
# 默认使用 DeepSeek
python bio-clean-cli.py

# 或显式指定
python bio-clean-cli.py --llm deepseek --user analyst01
```

#### 使用 OpenAI（可选）

```bash
export OPENAI_API_KEY="sk-your-openai-key"
python bio-clean-cli.py --llm openai
```

#### 不使用 LLM（规则模式）

```bash
python bio-clean-cli.py --no-llm
```

---

### 💡 使用示例

启动后，你可以这样对话：

```
You: Load clinical trial data from trial_data.csv