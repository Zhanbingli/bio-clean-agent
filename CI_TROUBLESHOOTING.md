# GitHub CI/CD Troubleshooting Guide

## 已识别的问题及修复

### 问题 1: CI 不在功能分支上运行 ✅ 已修复

**问题描述**:
原始 CI 配置只在 `main` 和 `develop` 分支上触发，不会在功能分支（如 `claude/**`）上运行。

**修复**:
更新了 `.github/workflows/ci.yml`，添加了对 Claude Code 分支的支持：

```yaml
on:
  push:
    branches:
      - main
      - develop
      - 'claude/**'  # 允许在 Claude Code 分支上运行 CI
```

### 问题 2: 缺少测试依赖 ✅ 已修复

**问题描述**:
- 缺少 `httpx` (FastAPI TestClient 需要)
- 缺少 `pydantic-settings` (配置管理需要)

**修复**:
更新了 `pyproject.toml`，添加了必需的依赖：

```toml
api = [
    ...
    "httpx>=0.24.0",  # Required for TestClient
]
dev = [
    ...
    "httpx>=0.24.0",  # Required for API testing
    "pydantic-settings>=2.0",  # Required for config management
]
```

### 问题 3: 测试文件中的潜在导入错误

**可能的问题**:
一些测试文件导入了可能不存在的模块或类。

**检查清单**:

#### ✅ 需要存在的模块/类：

1. **knowledge/base.py**:
   - `KnowledgeBase` 类
   - `KnowledgeEntry` 类

2. **knowledge/medical_standards.py**:
   - `MedicalStandards` 类
   - `get_vital_signs_range()` 方法
   - `get_lab_value_range()` 方法
   - `validate_vital_sign()` 方法

3. **knowledge/evidence_base.py**:
   - `EvidenceBase` 类
   - `get_strategies()` 方法
   - `get_best_strategy()` 方法

4. **quality/assessment.py**:
   - `QualityAssessment` 类
   - `QualityDimension` 类
   - `QualityScore` 类
   - `assess_data_quality()` 函数

5. **medical/clinical_trials.py**:
   - `ClinicalTrialHandler` 类
   - `load()` 方法
   - `detect_issues()` 方法
   - `assess_quality()` 方法

6. **medical/ehr.py**:
   - `EHRHandler` 类
   - `is_phi_field()` 方法
   - `mask_phi()` 方法
   - `hash_phi_value()` 方法
   - `contains_phi()` 方法

### 如何在本地测试

#### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 安装所有依赖
pip install -e .[all]
```

#### 2. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 只运行单元测试
pytest tests/unit/ -v

# 只运行集成测试
pytest tests/integration/ -v

# 运行特定测试文件
pytest tests/unit/test_agent.py -v

# 生成覆盖率报告
pytest tests/ --cov=src/bio_clean_agent --cov-report=html
```

#### 3. 检查代码质量

```bash
# 格式化代码
black src/ tests/

# Lint检查
ruff check src/

# 类型检查
mypy src/
```

### 常见 CI 失败原因及解决方案

#### 失败原因 1: 导入错误

**错误信息**: `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:
1. 检查模块是否存在于 `src/bio_clean_agent/` 中
2. 检查 `__init__.py` 文件是否存在
3. 确保依赖在 `pyproject.toml` 中声明

#### 失败原因 2: 测试失败

**错误信息**: `AssertionError` 或测试用例失败

**解决方案**:
1. 本地运行失败的测试：`pytest tests/unit/test_xxx.py::TestClass::test_method -v`
2. 检查测试中的断言是否正确
3. 确保被测试的功能已实现

#### 失败原因 3: 类型检查失败

**错误信息**: mypy 报告类型错误

**解决方案**:
1. 添加类型注解
2. 使用 `# type: ignore` 注释（临时）
3. 在 `pyproject.toml` 中配置 mypy 忽略规则

#### 失败原因 4: 覆盖率不足

**错误信息**: Coverage below threshold

**解决方案**:
1. 添加更多测试
2. 删除不必要的代码
3. 调整覆盖率阈值（临时）

### 下一步行动

1. **推送修复**:
   ```bash
   git add .github/workflows/ci.yml pyproject.toml
   git commit -m "fix: CI configuration and test dependencies"
   git push
   ```

2. **监控 CI**:
   - 访问 GitHub Actions 页面
   - 检查工作流运行状态
   - 查看失败的步骤日志

3. **如果仍然失败**:
   - 查看完整的错误日志
   - 在本地复现问题
   - 修复代码
   - 重新提交

### 预期的 CI 行为

✅ **应该成功的检查**:
- Test job (Python 3.10, 3.11, 3.12)
- Build job
- Security scan (continue-on-error: true)

⚠️ **可能失败但不阻塞的检查**:
- mypy type check (continue-on-error: true)
- Bandit security scan (continue-on-error: true)
- Safety check (continue-on-error: true)

❌ **可能失败的原因**:
- 测试导入模块不存在
- 测试断言失败
- 代码格式不符合 Black 标准
- Ruff lint 错误

### 快速修复命令

```bash
# 1. 修复格式问题
make format

# 2. 修复 lint 问题
ruff check --fix src/

# 3. 运行测试查看失败
make test

# 4. 提交修复
git add -A
git commit -m "fix: CI issues"
git push
```

---

**最后更新**: 2025-10-21
**状态**: CI 配置已修复，等待推送
