# 🤝 贡献指南

感谢您考虑为 Bio Clean Agent 做出贡献！

## 📋 目录

- [行为准则](#行为准则)
- [开始之前](#开始之前)
- [开发环境设置](#开发环境设置)
- [贡献方式](#贡献方式)
- [代码规范](#代码规范)
- [提交流程](#提交流程)
- [问题报告](#问题报告)

## 行为准则

请友好、尊重和包容。我们致力于为所有人提供一个无骚扰的体验。

## 开始之前

在开始贡献之前，请：

1. 阅读 [README.md](README.md) 了解项目
2. 查看 [docs/](docs/) 目录了解详细文档
3. 浏览现有的 [Issues](../../issues) 和 [Pull Requests](../../pulls)
4. 确保您的想法还没有被实现或讨论

## 开发环境设置

### 1. Fork 和 Clone

```bash
# Fork 项目到您的 GitHub 账户
# 然后 clone 您的 fork

git clone https://github.com/YOUR_USERNAME/bio-clean-agent.git
cd bio-clean-agent
```

### 2. 创建虚拟环境

```bash
# 使用 Makefile（推荐）
make init

# 或手动创建
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
# 安装所有依赖（包括开发依赖）
make install-all

# 或手动安装
pip install -e .[all]
```

### 4. 安装 pre-commit hooks（推荐）

```bash
# 安装 pre-commit
pip install pre-commit

# 安装 git hooks
pre-commit install

# 测试 hooks
pre-commit run --all-files
```

### 5. 验证安装

```bash
# 运行示例程序
make demo

# 或启动 Web 服务器
make web
```

## 贡献方式

### 🐛 报告 Bug

1. 在 [Issues](../../issues) 中搜索是否已有相关报告
2. 如果没有，创建新 Issue，包含：
   - 清晰的标题
   - 详细的问题描述
   - 复现步骤
   - 期望行为和实际行为
   - 环境信息（Python 版本、操作系统等）
   - 相关日志或截图

### ✨ 提议新功能

1. 在 [Issues](../../issues) 中创建 Feature Request
2. 描述功能的用途和价值
3. 如果可能，提供使用示例
4. 等待讨论和反馈

### 💻 提交代码

1. 确保 Issue 存在并获得认可
2. 创建新分支
3. 实现功能或修复
4. 添加测试
5. 更新文档
6. 提交 Pull Request

## 代码规范

### Python 代码风格

我们使用以下工具确保代码质量：

```bash
# 格式化代码
make format

# 代码检查
make lint

# 运行测试
make test
```

### 具体要求

1. **格式化**：使用 [Black](https://black.readthedocs.io/)
   ```bash
   black src/ examples/
   ```

2. **代码检查**：使用 [Ruff](https://docs.astral.sh/ruff/)
   ```bash
   ruff check src/
   ```

3. **类型检查**：使用 [mypy](https://mypy.readthedocs.io/)
   ```bash
   mypy src/
   ```

4. **文档字符串**：使用 Google 风格
   ```python
   def example_function(param1: str, param2: int) -> bool:
       """函数的简短描述。

       更详细的描述（如果需要）。

       Args:
           param1: 第一个参数的描述
           param2: 第二个参数的描述

       Returns:
           返回值的描述

       Raises:
           ValueError: 错误条件的描述
       """
       pass
   ```

### Git 提交信息

使用清晰的提交信息：

```
类型(范围): 简短描述

详细描述（如果需要）

Fixes #123
```

**类型：**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 添加测试
- `chore`: 构建/工具链更新

**示例：**
```
feat(medical): 添加 DICOM 元数据处理支持

实现了对医学影像 DICOM 标签的解析和验证功能。
包括隐私信息自动脱敏处理。

Fixes #42
```

## 提交流程

### 1. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/bug-description
```

### 2. 开发

```bash
# 编写代码
vim src/bio_clean_agent/your_file.py

# 添加测试
vim tests/test_your_feature.py

# 运行测试
make test

# 格式化和检查
make format
make lint
```

### 3. 提交更改

```bash
git add .
git commit -m "feat: 添加新功能"
git push origin feature/your-feature-name
```

### 4. 创建 Pull Request

1. 访问您的 Fork 仓库
2. 点击 "New Pull Request"
3. 填写 PR 描述：
   - 解决的问题
   - 更改内容
   - 测试情况
   - 相关 Issue
4. 等待审查

### 5. 代码审查

- 回应审查意见
- 进行必要的修改
- 更新 PR

### 6. 合并

PR 获得批准后，维护者将合并您的代码。

## 问题报告

### Bug 报告模板

```markdown
**描述**
简短描述遇到的问题。

**复现步骤**
1. 执行 '...'
2. 点击 '...'
3. 看到错误

**期望行为**
描述您期望发生什么。

**实际行为**
描述实际发生了什么。

**环境信息**
- OS: [例如 macOS 14.0]
- Python: [例如 3.11.5]
- 项目版本: [例如 0.3.0]

**日志/截图**
如果适用，添加日志或截图。

**额外信息**
其他相关信息。
```

### 功能请求模板

```markdown
**问题描述**
当前存在什么问题？

**建议方案**
您希望实现什么功能？

**替代方案**
您考虑过的其他方案。

**使用场景**
这个功能的典型使用场景。

**额外信息**
其他相关信息或示例代码。
```

## 开发提示

### 运行测试

```bash
# 运行所有测试
make test

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行特定测试文件
pytest tests/unit/test_agent.py -v

# 运行特定测试
pytest tests/unit/test_agent.py::TestBioCleaningAgent::test_agent_initialization -v

# 生成覆盖率报告
make test-cov

# 查看HTML覆盖率报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### 测试要求

**所有新代码必须包含测试：**

1. **单元测试覆盖率目标**: >80%
2. **集成测试**: 至少一个端到端测试
3. **测试命名**: 清晰描述测试目的
   ```python
   def test_agent_handles_missing_input_files_gracefully():
       """Test that agent gracefully handles missing input files."""
       # Test implementation
   ```
4. **使用标记**: 正确标记测试类型
   ```python
   @pytest.mark.unit
   def test_something():
       pass
   ```

### CI/CD 要求

您的 PR 必须通过所有 CI 检查：

- ✅ 测试通过（Python 3.10, 3.11, 3.12）
- ✅ 代码格式检查（Black）
- ✅ Lint检查（Ruff）
- ✅ 类型检查（mypy）
- ✅ 安全扫描（Bandit, Safety）
- ✅ 测试覆盖率 >80%

### 清理项目

```bash
# 清理临时文件
make clean
```

### 查看项目结构

```bash
# 显示目录树
make tree

# 代码统计
make size
```

### 调试技巧

1. **使用 Rich 库进行调试输出**
   ```python
   from rich import print as rprint
   rprint(f"[bold red]调试信息:[/] {variable}")
   ```

2. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **使用断点**
   ```python
   import pdb; pdb.set_trace()
   ```

## 项目结构

```
src/bio_clean_agent/
├── agent.py              # 核心 Agent 逻辑
├── cli.py                # 命令行界面
├── llm.py                # LLM 集成
├── api/                  # REST API
├── decisions/            # 决策管理
├── knowledge/            # 知识库
├── medical/              # 医疗数据处理
├── observer/             # 进度监控
├── pipelines/            # 数据处理管道
├── planning/             # 智能规划
├── reporting/            # 报告生成
├── web/                  # Web 界面
└── utils/                # 工具函数
```

## 常见问题

### Q: 我应该先创建 Issue 还是直接提交 PR？

A: 对于重大更改，请先创建 Issue 讨论。对于小的 bug 修复或文档改进，可以直接提交 PR。

### Q: 我的 PR 需要多长时间才能得到审查？

A: 我们会尽快审查，通常在 1-3 个工作日内。

### Q: 我可以同时处理多个问题吗？

A: 可以，但建议每个 PR 只解决一个问题，这样更容易审查和合并。

### Q: 测试失败了怎么办？

A: 检查错误信息，修复问题后重新运行测试。如果需要帮助，在 PR 中留言。

## 联系方式

- **Issues**: [GitHub Issues](../../issues)
- **Discussions**: [GitHub Discussions](../../discussions)
- **Email**: [your-email@example.com]

## 致谢

感谢所有贡献者！您的努力使这个项目变得更好。

---

**祝您编码愉快！** 🎉
