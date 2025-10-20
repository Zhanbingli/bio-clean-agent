# 🚀 Bio Clean Agent - 交互式 AI Agent (Claude Code 风格)

> 专业级医疗数据清洗 AI Agent，现在支持类似 Claude Code 的交互式命令行界面！

## ✨ 新功能亮点

### 🎮 交互式 CLI
```bash
# 启动交互式界面（类似 Claude Code）
python bio-clean-cli.py
```

**你将得到**：
- 💬 **自然语言对话**：用人类语言与 Agent 交互
- 🛠️ **智能工具调用**：自动选择和执行正确的工具
- 🎨 **漂亮的终端 UI**：使用 Rich 库的精美界面
- 📊 **实时可视化**：表格、进度条、彩色输出
- 🔄 **上下文感知**：Agent 记住整个对话

---

## 📦 快速开始

### 1. 安装依赖

```bash
cd /Users/lizhanbing12/ai-agent

# 安装基础依赖
pip install pandas numpy scipy rich

# 或安装完整版本
pip install -e .[all]
```

### 2. 启动交互式界面

```bash
# 方式 1: 直接运行
python bio-clean-cli.py

# 方式 2: 指定用户
python bio-clean-cli.py --user your_name

# 方式 3: 作为模块
python -m bio_clean_agent.interactive.repl
```

### 3. 开始对话！

```
You: Load data from data/trial_data.csv

You: Show me the first 10 rows

You: Assess data quality

You: Remove duplicates

You: Save to cleaned.csv
```

---

## 💡 使用示例

### 场景 1: 快速数据清洗

```
You: Load data from trial_data.csv
→ ✓ Loaded 100 records, 12 columns

You: Assess quality
→ Quality Score: 87.3% (GOOD)
→ Completeness: 92.1%
→ Validity: 85.4%
→ Consistency: 94.0%
→ Uniqueness: 77.8%

You: Detect issues
→ Found 5 issues:
  1. [HIGH] 3 duplicate patient visits
  2. [MEDIUM] 6 missing systolic_bp values
  3. [MEDIUM] 1 out-of-range temperature
  ...

You: Remove duplicates
→ ✓ Removed 3 duplicate records

You: Handle missing in systolic_bp
→ ✓ Handled 6 missing values using median method
→ Evidence: missing_median_imputation_robust

You: Save to cleaned.csv
→ ✓ Data saved: 97 records
```

### 场景 2: 探索性数据分析

```
You: Load data from dataset.csv

You: Show columns
→ Columns Information:
  patient_id    (object)  100 non-null
  age           (int64)    98 non-null
  systolic_bp   (float64)  94 non-null
  ...

You: Describe the data
→ Statistical Summary:
       age  systolic_bp  ...
  mean  52.3  120.5      ...
  std   15.2   14.8      ...
  ...

You: Show missing values
→ Missing Values:
  systolic_bp:  6 (6.0%)
  weight:       3 (3.0%)
```

---

## 🛠️ 可用工具

### 📂 数据加载
- `load_data` - 加载 CSV/Excel 文件

### 🔍 数据检查
- `show_data` - 显示数据预览
- `describe_data` - 统计摘要
- `show_columns` - 列信息
- `show_missing` - 缺失值分析

### 📊 质量评估
- `assess_quality` - ISO 8000 质量评估
- `detect_issues` - 检测问题（带科学证据）

### 🧹 数据清洗
- `remove_duplicates` - 删除重复记录（带血缘追踪）
- `handle_missing` - 智能处理缺失值（证据驱动）

### ✅ 验证
- `validate_ranges` - 验证医学参考范围

### 💾 导出
- `save_data` - 保存清洗数据
- `export_audit` - 导出审计追踪（FDA 21 CFR Part 11 合规）
- `export_lineage` - 导出数据血缘

---

## ⌨️ 斜杠命令

| 命令 | 功能 |
|------|------|
| `/help` | 显示帮助 |
| `/tools` | 列出所有工具 |
| `/tool <name>` | 显示工具详情 |
| `/stats` | 会话统计 |
| `/status` | 当前状态 |
| `/history` | 对话历史 |
| `/clear` | 清屏 |
| `/exit` | 退出 |

---

## 🎨 界面展示

### 欢迎界面

```
╔══════════════════════════════════════════════════════╗
║              🧬 Bio Clean Agent                       ║
║           Interactive CLI (Claude Code Style)         ║
╠══════════════════════════════════════════════════════╣
║ Welcome to the interactive data cleaning assistant!  ║
║                                                       ║
║ Quick Start:                                          ║
║ - Type requests in natural language                   ║
║ - Use /help for commands                              ║
║ - Press Ctrl+C to exit                                ║
╚══════════════════════════════════════════════════════╝
```

### 质量评估结果

```
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

### 问题检测

```
┌─ Issue 1 ─────────────────────────────────┐
│ Severity: HIGH                             │
│ Category: duplicates                       │
│ Field: patient_id,visit_date               │
│ Count: 3                                   │
│                                            │
│ Recommendation: Remove duplicate records   │
│ Evidence: duplicate_exact_matches          │
│ Citation: FDA (2018)                       │
└────────────────────────────────────────────┘
```

---

## 🏗️ 架构设计

### 组件层次

```
交互层 (Interactive Layer)
├── REPL (repl.py) - 主界面
│   ├── Rich UI 渲染
│   ├── 命令解析
│   └── 结果展示
│
├── Session (session.py) - 会话管理
│   ├── 状态维护
│   ├── 工具执行
│   └── 历史记录
│
└── Tools (tools.py) - 工具注册表
    ├── 工具定义
    ├── 参数验证
    └── 执行路由
            ↓
核心引擎层
├── EnhancedClinicalTrialHandler
│   ├── 数据血缘追踪
│   ├── 审计追踪
│   └── 快照回滚
│
├── DataQualityAssessor
│   └── ISO 8000 评估
│
└── KnowledgeBase
    ├── 医学标准 (50+)
    ├── 证据库 (70+)
    └── 验证规则
```

### 工具调用流程

```
用户输入
    ↓
自然语言解析 (parse_intent)
    ↓
工具选择
    ↓
参数提取
    ↓
Session.execute_tool()
    ↓
Handler 执行实际操作
    ↓
结果格式化
    ↓
Rich UI 展示
```

---

## 📚 完整文档

### 用户指南
- [交互式 CLI 使用指南](docs/INTERACTIVE_CLI_GUIDE.md) - 详细使用说明
- [专业优化总结](docs/PROFESSIONAL_OPTIMIZATION.md) - 企业级功能
- [快速入门](docs/QUICK_START_PROFESSIONAL.md) - 5 分钟上手

### 开发者文档
- [高级功能](docs/ADVANCED_CAPABILITIES.md) - 知识库和证据系统
- [任务导向设计](docs/TASK_ORIENTED_DESIGN.md) - 架构理念

---

## 🌟 核心特性

### 1. 自然语言交互
```
✓ "Load data from file.csv"
✓ "Show me the first 10 rows"
✓ "Remove duplicates"
✓ "Handle missing values in age"
```

### 2. 智能工具调用
- 自动解析意图
- 自动提取参数
- 自动选择最佳方法

### 3. 证据驱动清洗
- 50+ 医学标准（AHA, WHO, FDA）
- 70+ 证据支持的策略
- 每个操作都有文献引用

### 4. 完整追溯能力
- 数据血缘追踪
- FDA 21 CFR Part 11 审计追踪
- 快照回滚功能

### 5. 漂亮的 UI
- Rich 库精美界面
- 彩色输出
- 表格、面板、进度条
- 实时反馈

---

## 🔄 与其他模式对比

### CLI 交互模式（新）vs Web UI vs REST API

| 特性 | CLI 交互 | Web UI | REST API |
|------|---------|--------|----------|
| **启动** | `python bio-clean-cli.py` | `python start_web.py` | `bio-clean-agent serve` |
| **界面** | 终端对话 | 浏览器图形界面 | 编程调用 |
| **交互方式** | 自然语言 | 点击/表单 | JSON 请求 |
| **适用场景** | 快速探索、脚本化 | 非技术用户 | 系统集成 |
| **实时反馈** | ✅ 即时 | ✅ WebSocket | ⚠️ 轮询 |
| **上手难度** | 简单 | 最简单 | 需编程 |

---

## 🎯 使用场景

### 场景 1: 数据科学家日常工作
```bash
# 早上到办公室
python bio-clean-cli.py --user analyst_jane

You: Load data from today's_trial_data.csv
You: Assess quality
You: Detect issues
You: Remove duplicates and handle missing
You: Save to cleaned/today.csv
You: Export audit trail
```

### 场景 2: 快速数据探索
```
You: Load data from new_dataset.csv
You: Show first 20 rows
You: Describe the data
You: What columns do I have?
You: Show missing values
You: /stats
```

### 场景 3: 监管合规审计
```
You: Load data from audit_dataset.csv
You: Detect issues
You: Remove duplicates
You: Export audit trail to audit_2024.json
You: Export lineage to lineage_2024.json

# 审计追踪包含：
# - 每个操作的时间戳
# - 操作者 ID
# - 科学证据引用
# - 参数和影响记录数
```

---

## 🚀 运行完整示例

```bash
# 1. 创建测试数据
python -c "
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'patient_id': [f'P{i:03d}' for i in range(1, 21)],
    'age': np.random.randint(18, 80, 20),
    'systolic_bp': np.random.normal(120, 15, 20),
})
df.loc[0, 'systolic_bp'] = None  # 缺失值
df = pd.concat([df, df.iloc[[0]]])  # 重复
df.to_csv('test_data.csv', index=False)
print('✓ Test data created')
"

# 2. 启动交互式 CLI
python bio-clean-cli.py

# 3. 执行清洗
You: Load data from test_data.csv
You: Assess quality
You: Detect issues
You: Remove duplicates
You: Handle missing in systolic_bp
You: Save to cleaned_test.csv
You: /stats
You: /exit
```

---

## 💻 系统要求

- Python 3.10+
- pandas >= 2.0
- numpy
- scipy
- rich (可选，用于漂亮的 UI)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 🎉 总结

你现在拥有了：

1. ✅ **交互式 CLI**：类似 Claude Code 的对话体验
2. ✅ **智能工具系统**：15+ 专业数据清洗工具
3. ✅ **证据驱动**：50+ 医学标准，70+ 证据条目
4. ✅ **完整追溯**：数据血缘、审计追踪、快照回滚
5. ✅ **监管合规**：FDA 21 CFR Part 11, ISO 8000, ALCOA+
6. ✅ **漂亮界面**：Rich 终端 UI，彩色输出
7. ✅ **易于使用**：自然语言交互，一键启动

**开始享受专业级 AI Agent 带来的高效数据清洗体验！** 🚀

---

## 📞 获取帮助

- **交互式帮助**：在 CLI 中输入 `/help`
- **工具列表**：`/tools`
- **文档**：查看 `docs/` 目录
- **示例**：查看 `examples/` 目录

Happy cleaning! 🧹✨
