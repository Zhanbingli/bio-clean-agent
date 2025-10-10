# 🌐 Web Interface User Guide

## 🎯 超简单！3步开始使用

### 第1步：启动Web界面

```bash
# 方法1：使用启动脚本（推荐）
python start_web.py

# 方法2：直接运行
python -m bio_clean_agent.web.server
```

### 第2步：打开浏览器

访问：**http://localhost:8080**

### 第3步：上传数据文件

1. 点击上传区域
2. 选择你的CSV或Excel文件
3. 等待智能分析完成（几秒钟）
4. 查看结果和建议！

**就这么简单！** 🎉

---

## 📱 界面功能

### 主页面

```
┌─────────────────────────────────────────┐
│  🧬 Bio Clean Agent                     │
│  Intelligent Medical Data Cleaning      │
├─────────────────────────────────────────┤
│                                         │
│        📊 点击上传数据文件                 │
│        Supports CSV, Excel             │
│                                         │
├─────────────────────────────────────────┤
│  📚 50+ Medical Standards              │
│  🧠 Intelligent Planning               │
│  🔬 Scientific Validation              │
└─────────────────────────────────────────┘
```

### 上传后看到什么

**1. 数据概览**
- 总记录数
- 列数
- 发现的问题数量

**2. 智能计划**
- 总步骤数
- 证据支持的步骤数
- 预期质量提升
- 预期数据损失

**3. Top建议**
- 具体问题
- 建议的解决方法
- 科学依据（置信度、证据级别）

---

## 🔧 API端点（开发者）

如果你想用代码调用：

### 上传文件
```bash
curl -X POST http://localhost:8080/upload \
  -F "file=@data.csv"
```

### 分析数据
```bash
curl -X POST "http://localhost:8080/analyze?file_id=YOUR_FILE_ID"
```

### 查看医学标准
```bash
curl http://localhost:8080/knowledge/standards
```

### 健康检查
```bash
curl http://localhost:8080/health
```

---

## 🎨 界面特点

### ✅ 简洁设计
- 渐变紫色主题（现代感）
- 大按钮，易点击
- 清晰的信息层级

### ✅ 实时反馈
- 上传进度显示
- 分析动画
- 即时结果展示

### ✅ 科学可信
- 每个建议都有证据支持
- 显示置信度和证据级别
- 引用来源（AHA, WHO, ADA等）

---

## 📖 使用示例

### 示例1：临床试验数据清洗

```
1. 上传 trial_data.csv
2. 系统自动分析：
   ✓ 检测到1,250条记录
   ✓ 发现15%的age列缺失
   ✓ 发现3个血压异常值

3. 智能建议：
   💡 年龄缺失值：使用中位数填充
      理由：中位数对异常值更稳健
      证据：Systematic Review
      置信度：HIGH

   💡 血压异常值：验证测量技术
      可能是数据录入错误
      引用：AHA 2017 Guidelines
```

### 示例2：查看医学标准

访问：http://localhost:8080/knowledge/standards

看到：
```json
{
  "total": 50,
  "standards": [
    {
      "id": "vs_blood_pressure_normal",
      "statement": "Normal adult systolic BP: 90-120 mmHg",
      "confidence": "high",
      "evidence_level": "systematic_review",
      "citations": [{
        "source": "American Heart Association",
        "year": 2017
      }]
    }
  ]
}
```

---

## ⚙️ 配置选项

### 修改端口

编辑 `start_web.py`：

```python
run_server(host="127.0.0.1", port=9000)  # 改为9000端口
```

### 允许外部访问

如果想让局域网内其他设备访问：

```python
run_server(host="0.0.0.0", port=8080)
```

然后访问：http://YOUR_IP:8080

---

## 🐛 常见问题

### Q1: 端口被占用

**错误信息：** `OSError: [Errno 48] Address already in use`

**解决方法：**
```bash
# 方法1：换个端口
python start_web.py --port 9000

# 方法2：杀掉占用端口的进程
lsof -ti:8080 | xargs kill -9
```

### Q2: 找不到模块

**错误信息：** `ModuleNotFoundError: No module named 'fastapi'`

**解决方法：**
```bash
pip install -e .[api]
# 或
pip install fastapi uvicorn pandas numpy
```

### Q3: 上传文件失败

**可能原因：**
- 文件格式不支持（只支持CSV和Excel）
- 文件太大（>100MB可能很慢）
- 文件编码问题

**解决方法：**
- 确保是CSV或XLSX格式
- 尝试小一点的数据样本
- 用UTF-8编码保存CSV

### Q4: 分析很慢

**正常情况：**
- <1000行：几秒钟
- 1000-10000行：10-30秒
- >10000行：可能1-2分钟

**优化建议：**
- 先用小样本测试（前1000行）
- 考虑使用后台任务（即将推出）

---

## 🚀 高级功能（即将推出）

### 🔜 实时进度

WebSocket连接，实时看到：
- 当前执行步骤
- 完成百分比
- 实时日志

### 🔜 批量处理

一次上传多个文件，批量清洗

### 🔜 历史记录

查看之前处理过的所有任务

### 🔜 自定义规则

添加你自己的验证规则和清洗策略

### 🔜 下载报告

下载完整的HTML报告（包含图表）

---

## 💻 系统要求

### 最低要求
- Python 3.10+
- 2GB RAM
- 任何现代浏览器（Chrome、Firefox、Safari、Edge）

### 推荐配置
- Python 3.11+
- 4GB+ RAM
- Chrome浏览器（最佳兼容性）

### 支持的操作系统
- ✅ macOS
- ✅ Windows
- ✅ Linux

---

## 📊 性能基准

| 数据大小 | 上传时间 | 分析时间 | 总时间 |
|---------|---------|---------|--------|
| 100行 | <1秒 | 1-2秒 | ~2秒 |
| 1,000行 | 1-2秒 | 3-5秒 | ~5秒 |
| 10,000行 | 2-5秒 | 10-20秒 | ~25秒 |
| 100,000行 | 5-10秒 | 30-60秒 | ~1分钟 |

*测试环境：MacBook Pro M1, 16GB RAM*

---

## 🔐 隐私和安全

### 数据安全
- ✅ 所有数据存储在**本地**
- ✅ 不会上传到云端
- ✅ 不会发送到外部服务器
- ✅ 关闭服务器后可手动删除uploads文件夹

### 注意事项
- 如果包含敏感医疗数据（PHI），确保：
  - 只在本地运行（不要设置host="0.0.0.0"）
  - 使用完毕后删除uploads文件夹
  - 遵守HIPAA等法规要求

---

## 📞 支持

### 遇到问题？

1. **查看日志**
   - 终端中的错误信息
   - 浏览器控制台（F12）

2. **GitHub Issues**
   - 报告bug
   - 请求新功能

3. **文档**
   - [README.md](README.md) - 项目概述
   - [ADVANCED_CAPABILITIES.md](ADVANCED_CAPABILITIES.md) - 高级功能
   - [QUICKSTART.md](QUICKSTART.md) - 快速开始

---

## ✨ 总结

**启动Web界面就3步：**

```bash
# 1. 启动
python start_web.py

# 2. 打开浏览器
# http://localhost:8080

# 3. 上传文件，查看智能分析！
```

**不需要懂代码，不需要配置，开箱即用！** 🎉

---

## 🎁 特别提示

### 第一次使用？

运行这个命令自动安装所有依赖：

```bash
pip install -e .[api]
python start_web.py
```

然后就可以用浏览器访问了，就像使用任何网站一样！

**享受智能数据清洗的乐趣吧！** 🚀
