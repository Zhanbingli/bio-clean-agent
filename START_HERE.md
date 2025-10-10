# 🚀 如何使用 Bio Clean Agent

## 超级简单！只需2步

### 第1步：安装

```bash
pip install -e .[api]
```

这会安装所有需要的包（FastAPI、uvicorn等）。

### 第2步：启动Web界面

```bash
python start_web.py
```

**就这样！** 🎉

然后在浏览器打开：**http://localhost:8080**

---

## 或者，使用命令行

如果你更喜欢命令行而不是Web界面：

```bash
# 运行示例
python examples/intelligent_agent_demo.py

# 或者运行任务导向工作流
python examples/task_oriented_workflow.py
```

---

## 故障排除

### 问题："pip install失败"

**解决：** 确保Python版本 >= 3.10

```bash
python --version  # 应该显示 3.10 或更高
```

### 问题："端口8080已被占用"

**解决：** 换个端口

编辑 `start_web.py` 第96行：

```python
run_server(host="127.0.0.1", port=9000)  # 改成9000或其他端口
```

### 问题："找不到模块"

**解决：** 重新安装

```bash
pip uninstall bio-clean-agent
pip install -e .[api]
```

---

## 我应该用哪个？

### 用Web界面，如果你：
- ✅ 不想写代码
- ✅ 喜欢图形界面
- ✅ 只是想快速清洗数据

### 用命令行/Python，如果你：
- ✅ 需要自动化
- ✅ 要集成到你的workflow
- ✅ 需要更高级的定制

---

## 快速测试

### 测试Web界面是否工作

```bash
# 启动服务器
python start_web.py

# 在另一个终端测试
curl http://localhost:8080/health
```

应该看到：
```json
{
  "status": "healthy",
  "version": "0.3.0",
  "features": ["scientific_knowledge", "intelligent_planning", "evidence_based"]
}
```

---

## 完整文档

- **[WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md)** - Web界面完整指南
- **[QUICKSTART.md](QUICKSTART.md)** - Python API快速开始
- **[ADVANCED_CAPABILITIES.md](ADVANCED_CAPABILITIES.md)** - 高级功能说明

---

## 需要帮助？

看不懂这些？没关系！

**最简单的方式：**

1. 打开终端
2. 运行：`pip install -e .[api]`
3. 运行：`python start_web.py`
4. 在浏览器打开：http://localhost:8080
5. 拖拽你的CSV文件到页面上
6. 看结果！

**就是这么简单！** 不需要懂代码 🎉

---

## 视频教程（即将推出）

我们正在制作视频教程，敬请期待！

---

**有任何问题？欢迎提issue！**
