# 🎮 交互式 CLI 使用指南 - Claude Code 风格

## 快速启动

### 方法 1: 直接运行脚本

```bash
cd /Users/lizhanbing12/ai-agent

# 启动交互式 CLI
python bio-clean-cli.py

# 或使用自定义用户 ID
python bio-clean-cli.py --user your_name
```

### 方法 2: 作为模块运行

```bash
python -m bio_clean_agent.interactive.repl
```

---

## 🎯 界面预览

启动后，你会看到：

```
╔══════════════════════════════════════════════════════════════╗
║                        Welcome                                ║
╠══════════════════════════════════════════════════════════════╣
║ 🧬 Bio Clean Agent - Interactive CLI                         ║
║                                                               ║
║ Welcome to the interactive data cleaning assistant!           ║
║                                                               ║
║ Quick Start:                                                  ║
║ - Type your requests in natural language                     ║
║ - Use `/help` to see available commands                      ║
║ - Use `/tools` to list all tools                             ║
║ - Press Ctrl+C to exit                                       ║
║                                                               ║
║ Example requests:                                             ║
║ - "Load data from trial_data.csv"                            ║
║ - "Show me the first 10 rows"                                ║
║ - "Assess data quality"                                       ║
║ - "Remove duplicates and handle missing values"              ║
╚══════════════════════════════════════════════════════════════╝

You:
```

---

## 💬 自然语言交互

### 示例对话 1: 加载和检查数据

```
You: Load data from data/trial_data.csv

🔧 Calling tool: load_data
   Parameters: {"file_path": "data/trial_data.csv"}

┌─ 📂 Data Loaded Successfully ────────────────────────┐
│ Property │ Value                                     │
├──────────┼───────────────────────────────────────────┤
│ File     │ data/trial_data.csv                       │
│ Rows     │ 100                                       │
│ Columns  │ 12                                        │
└──────────┴───────────────────────────────────────────┘

Columns: patient_id, enrollment_date, visit_date, age, sex,
         weight, height, systolic_bp, diastolic_bp,
         heart_rate, temperature, treatment_arm

You: Show me the first 10 rows

🔧 Calling tool: show_data
   Parameters: {"n": 10}

Data Preview (showing 10 of 100 rows)
┌────────────────────────────────────────────────────┐
│ patient_id  age  sex  weight  systolic_bp  ...    │
│ P0001       45   M    72.3    118          ...    │
│ P0002       52   F    68.1    125          ...    │
│ P0003       38   M    81.2    112          ...    │
│ ...                                                │
└────────────────────────────────────────────────────┘

You: Assess data quality

🔧 Calling tool: assess_quality

Overall Quality Score: 87.3% (GOOD)

┌─ 📈 Quality Dimensions ─────────────────────┐
│ Dimension    │ Score  │ Bar                 │
├──────────────┼────────┼─────────────────────┤
│ Completeness │ 92.1%  │ ██████████████████░░│
│ Validity     │ 85.4%  │ █████████████████░░░│
│ Consistency  │ 94.0%  │ ███████████████████░│
│ Uniqueness   │ 77.8%  │ ███████████████░░░░░│
└──────────────┴────────┴─────────────────────┘
```

### 示例对话 2: 数据清洗

```
You: Detect issues

🔧 Calling tool: detect_issues

Detected 5 issues:

┌─ Issue 1 ─────────────────────────────────────────┐
│ Severity: HIGH                                     │
│ Category: duplicates                               │
│ Field: patient_id,visit_date                       │
│ Count: 3                                           │
│                                                    │
│ 3 duplicate patient visits detected                │
│                                                    │
│ Recommendation: Perfect duplicates provide no      │
│ additional information and may indicate database   │
│ errors or repeated data entry                      │
│                                                    │
│ Evidence: duplicate_exact_matches                  │
└────────────────────────────────────────────────────┘

You: Remove duplicates

🔧 Calling tool: remove_duplicates
   Parameters: {"keep": "first"}

✓ Removed 3 duplicate records
   Records affected: 3
   Evidence: duplicate_exact_matches

You: Handle missing values in systolic_bp

🔧 Calling tool: handle_missing
   Parameters: {"column": "systolic_bp", "auto_select": true}

✓ Handled 6 missing values in 'systolic_bp' using median method
   Records affected: 6
   Method: median
   Evidence: missing_median_imputation_robust
```

### 示例对话 3: 导出结果

```
You: Save data to output/cleaned_data.csv

🔧 Calling tool: save_data
   Parameters: {"output_path": "output/cleaned_data.csv"}

✓ Data saved to output/cleaned_data.csv
   File: output/cleaned_data.csv
   Records saved: 97

You: Export audit trail

🔧 Calling tool: export_audit
   Parameters: {"output_path": "output/audit_trail.json"}

✓ Audit trail exported to output/audit_trail.json
   File: output/audit_trail.json
   Audit entries: 8
```

---

## ⚡ 斜杠命令（Slash Commands）

### 系统命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/help` | 显示帮助信息 | `/help` |
| `/tools` | 列出所有可用工具 | `/tools` |
| `/tool <name>` | 显示特定工具的详细信息 | `/tool load_data` |
| `/stats` | 显示会话统计信息 | `/stats` |
| `/status` | 显示当前状态 | `/status` |
| `/history` | 显示对话历史 | `/history` |
| `/clear` | 清屏 | `/clear` |
| `/exit` 或 `/quit` | 退出程序 | `/exit` |

### 使用示例

```
You: /tools

┌─ 📦 Data Loading ──────────────────────────────┐
│ Tool       │ Description                       │
├────────────┼───────────────────────────────────┤
│ load_data  │ Load clinical trial data from CSV │
│            │ or Excel file                     │
└────────────┴───────────────────────────────────┘

┌─ 📦 Data Inspection ───────────────────────────┐
│ Tool          │ Description                    │
├───────────────┼────────────────────────────────┤
│ show_data     │ Display first N rows           │
│ describe_data │ Show statistical summary       │
│ show_columns  │ List columns and types         │
│ show_missing  │ Show missing value statistics  │
└───────────────┴────────────────────────────────┘

...

You: /tool load_data

┌─ Tool: load_data ──────────────────────────────┐
│ Category: data_loading                          │
│ Description: Load clinical trial data from CSV  │
│ or Excel file                                   │
│ Returns: Dictionary with data summary           │
│                                                 │
│ Parameters:                                     │
│                                                 │
│ - file_path (string) ✓                         │
│   Path to data file                             │
│                                                 │
│ - data_type (string)                            │
│   Type of data                                  │
│   Default: clinical_trial                       │
└─────────────────────────────────────────────────┘

You: /stats

┌─ 📊 Session Statistics ────────────────────────┐
│ Metric              │ Value                    │
├─────────────────────┼──────────────────────────┤
│ Session Start       │ 2024-01-15T10:30:00      │
│ Commands Executed   │ 8                        │
│ Current File        │ data/trial_data.csv      │
│ Records             │ 97                       │
│ Columns             │ 12                       │
│ Operations Performed│ 5                        │
└─────────────────────┴──────────────────────────┘
```

---

## 🛠️ 可用工具列表

### 数据加载 (Data Loading)

- **load_data** - 从 CSV/Excel 加载数据

### 数据检查 (Data Inspection)

- **show_data** - 显示前 N 行
- **describe_data** - 统计摘要
- **show_columns** - 列信息
- **show_missing** - 缺失值统计

### 质量评估 (Quality Assessment)

- **assess_quality** - ISO 8000 质量评估
- **detect_issues** - 检测问题（带证据）

### 数据清洗 (Data Cleaning)

- **remove_duplicates** - 删除重复记录
- **handle_missing** - 处理缺失值（证据驱动）

### 验证 (Validation)

- **validate_ranges** - 验证值范围

### 导出 (Export)

- **save_data** - 保存清洗后数据
- **export_audit** - 导出审计追踪
- **export_lineage** - 导出数据血缘

### 系统 (System)

- **show_stats** - 会话统计
- **list_tools** - 列出工具

---

## 🎨 自然语言理解

系统能理解多种表达方式：

### 加载数据

```
✓ "Load data from file.csv"
✓ "Open file.csv"
✓ "Load file.csv"
```

### 查看数据

```
✓ "Show me the data"
✓ "Display first 10 rows"
✓ "View the first 5 rows"
✓ "Show data"
```

### 质量评估

```
✓ "Assess data quality"
✓ "Check quality"
✓ "Quality assessment"
✓ "How's the data quality?"
```

### 清洗操作

```
✓ "Remove duplicates"
✓ "Delete duplicate records"
✓ "Clean duplicates"

✓ "Handle missing values in age"
✓ "Fix missing data in systolic_bp"
✓ "Fill missing values in weight"
```

### 导出

```
✓ "Save data to output.csv"
✓ "Export to cleaned.csv"
✓ "Save cleaned data"

✓ "Export audit trail"
✓ "Save audit to audit.json"
```

---

## 📋 完整使用流程

### 流程 1: 基础数据清洗

```
You: Load data from trial_data.csv
→ 数据加载成功，100 行，12 列

You: Show missing values
→ 显示缺失值统计表

You: Assess quality
→ 质量评分：87.3% (GOOD)

You: Detect issues
→ 检测到 5 个问题（带证据和建议）

You: Remove duplicates
→ 删除 3 条重复记录

You: Handle missing in systolic_bp
→ 使用中位数填充 6 个缺失值

You: Assess quality
→ 质量评分：95.1% (EXCELLENT) ✨

You: Save to cleaned.csv
→ 保存成功

You: Export audit trail
→ 审计追踪已导出
```

### 流程 2: 探索性数据分析

```
You: Load data from dataset.csv
You: Describe the data
You: Show columns
You: Show first 20 rows
You: What columns do I have?
You: Show missing values
You: /stats
```

---

## 🔧 高级用法

### 自定义用户 ID

```bash
python bio-clean-cli.py --user analyst_john

# 审计追踪会记录：user=analyst_john
```

### 批处理模式（计划中）

```bash
# 从文件读取命令
python bio-clean-cli.py --batch commands.txt
```

### 与 LLM 集成（未来功能）

```bash
# 使用 OpenAI GPT-4 进行智能对话
python bio-clean-cli.py --llm openai --model gpt-4

You: Analyze this data and recommend cleaning strategies
AI: Based on the data profile, I recommend...
```

---

## 🎯 与 Claude Code 的相似之处

| 特性 | Claude Code | Bio Clean Agent CLI |
|------|-------------|---------------------|
| **交互方式** | 自然语言对话 | ✅ 自然语言对话 |
| **工具调用** | 自动执行工具 | ✅ 自动执行工具 |
| **漂亮UI** | Rich 终端界面 | ✅ Rich 终端界面 |
| **上下文感知** | 记住对话历史 | ✅ 会话状态管理 |
| **斜杠命令** | /help, /clear 等 | ✅ /help, /tools 等 |
| **实时反馈** | 显示工具执行 | ✅ 显示工具调用 |
| **结果可视化** | 表格、面板 | ✅ 表格、面板、进度条 |

---

## 💡 使用技巧

### 1. 链式操作

```
You: Load data from file.csv, assess quality, and remove duplicates
```

系统会自动分解为：
1. load_data
2. assess_quality
3. remove_duplicates

### 2. 查看工具详情

```
You: /tool handle_missing

# 显示参数、类型、默认值等详细信息
```

### 3. 使用 /status 检查当前状态

```
You: /status

Session Status
────────────────
✓ Data loaded

Data loaded from: trial_data.csv
Records: 97
Columns: 12
Operations performed: 5
Quality Score: 95.1% (EXCELLENT)
```

### 4. 回顾历史

```
You: /history

# 显示最近 10 条对话
```

---

## 🐛 故障排除

### 问题 1: Rich 库未安装

**错误**：
```
ModuleNotFoundError: No module named 'rich'
```

**解决**：
```bash
pip install rich
```

### 问题 2: 数据文件未找到

**错误**：
```
✗ File not found: data.csv
```

**解决**：
```
You: Load data from ./data/data.csv  # 使用相对路径
# 或
You: Load data from /full/path/to/data.csv  # 使用绝对路径
```

### 问题 3: 工具未识别

如果自然语言未识别，使用明确的关键词：

```
✗ "Get the info"  # 太模糊
✓ "Show data"     # 明确

✗ "Fix it"        # 太模糊
✓ "Remove duplicates"  # 明确
```

---

## 🚀 下一步

1. **尝试完整流程**：加载 → 评估 → 清洗 → 导出
2. **探索所有工具**：`/tools` 查看全部
3. **查看审计追踪**：了解每个操作的证据
4. **导出结果**：保存清洗后的数据和报告

---

## 📞 获取帮助

- 命令内帮助：`/help`
- 工具列表：`/tools`
- 特定工具：`/tool <name>`
- 会话状态：`/status`
- 统计信息：`/stats`

享受类似 Claude Code 的交互体验！🎉
