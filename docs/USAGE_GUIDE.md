# Clinical Trials Agent - 使用指南

## 快速开始

### 1. 基础使用 (简单模式)

如果你只需要基本的数据清洗功能:

```python
from bio_clean_agent.medical.clinical_trials import ClinicalTrialHandler

# 创建handler
handler = ClinicalTrialHandler("data/your_clinical_data.csv")

# 加载数据
df = handler.load_data()
print(f"加载了 {len(df)} 条记录")

# 生成数据概况
profile = handler.profile_data()
print(f"缺失值: {profile['missing_values']}")

# 检测问题
issues = handler.detect_issues()
print(f"发现 {len(issues)} 个问题")

# 清理重复数据
removed = handler.clean_duplicates()
print(f"删除了 {removed} 条重复记录")

# 处理缺失值
handler.handle_missing_values("systolic_bp", strategy="median")

# 验证生命体征范围
handler.validate_vital_signs("systolic_bp", 70, 200, action="flag")

# 保存清洗后的数据
handler.save_cleaned_data("outputs/cleaned_data.csv")

# 查看清洗摘要
summary = handler.get_cleaning_summary()
print(summary)
```

### 2. 专业模式 (推荐使用) ⭐

如果你需要完整的专业级功能,包括审计追踪、数据血缘、科学验证等:

```python
from bio_clean_agent.medical.clinical_trials_enhanced import EnhancedClinicalTrialHandler

# 创建增强版handler
handler = EnhancedClinicalTrialHandler(
    data_path="data/your_clinical_data.csv",
    user_id="your_username"  # 用于审计追踪
)

# 加载数据
df = handler.load_data()
print(f"✓ 加载了 {len(df)} 条记录")

# 初始质量评估
initial_quality = handler.assess_data_quality()
print(f"初始质量分数: {initial_quality.overall_score:.2%}")
print(f"质量等级: {initial_quality.data_quality_level}")

# 检测问题(带科学证据)
issues = handler.detect_issues_with_evidence()
for issue in issues:
    print(f"{issue['severity'].value}: {issue['message']}")
    if 'evidence' in issue:
        print(f"  证据: {issue['evidence']}")

# 清理重复数据(带血缘追踪)
removed = handler.clean_duplicates_with_lineage(keep="first")
print(f"✓ 删除了 {removed} 条重复记录")

# 基于证据的缺失值处理(自动选择最佳方法)
affected, method, evidence = handler.handle_missing_values_evidence_based(
    "systolic_bp",
    auto_select=True  # 自动选择最佳策略
)
print(f"✓ 使用 {method} 方法处理了 {affected} 个缺失值")
print(f"  科学依据: {evidence}")

# 最终质量评估
final_quality = handler.assess_data_quality()
improvement = (final_quality.overall_score - initial_quality.overall_score) * 100
print(f"最终质量分数: {final_quality.overall_score:.2%}")
print(f"质量提升: +{improvement:.2f}%")

# 保存所有结果
from pathlib import Path
output_dir = Path("outputs/my_analysis")
output_dir.mkdir(parents=True, exist_ok=True)

# 保存清洗后的数据和元数据
handler.save_cleaned_data(output_dir / "cleaned_data.csv")
print("✓ 已保存清洗后的数据")

# 导出审计追踪(用于合规性)
handler.export_audit_trail(output_dir / "audit_trail.json")
print("✓ 已导出审计追踪")

# 导出数据血缘
handler.export_lineage(output_dir / "data_lineage.json")
print("✓ 已导出数据血缘")

# 生成质量报告
report = handler.generate_quality_report()
print(f"\n质量改善报告:")
print(f"  初始记录数: {report['records_initial']}")
print(f"  最终记录数: {report['records_current']}")
print(f"  删除记录数: {report['records_removed']}")
print(f"  执行操作数: {report['total_operations']}")
print(f"  质量提升: {report['improvement_percentage']:.2f}%")
```

## 完整工作流示例

### 方式一: 运行现成的示例脚本

最简单的方式是直接运行我们提供的示例脚本:

```bash
# 运行完整的专业级清洗流程
python examples/professional_clinical_data_cleaning.py

# 或者运行快速测试
python examples/quick_test.py
```

### 方式二: 集成到你的项目中

创建你自己的清洗脚本:

```python
# my_cleaning_script.py
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bio_clean_agent.medical.clinical_trials_enhanced import (
    EnhancedClinicalTrialHandler
)


def clean_my_data(input_file, output_dir):
    """清洗临床试验数据的自定义函数"""

    # 1. 初始化
    handler = EnhancedClinicalTrialHandler(
        data_path=input_file,
        user_id="data_analyst_001"
    )

    # 2. 加载并评估
    df = handler.load_data()
    initial_quality = handler.assess_data_quality()

    print(f"数据概况:")
    print(f"  记录数: {len(df)}")
    print(f"  字段数: {len(df.columns)}")
    print(f"  初始质量: {initial_quality.overall_score:.2%}")

    # 3. 检测问题
    issues = handler.detect_issues_with_evidence()
    print(f"\n发现 {len(issues)} 个问题:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. [{issue['severity'].value}] {issue['message']}")

    # 4. 数据清洗
    print("\n开始清洗...")

    # 清理重复
    dup_removed = handler.clean_duplicates_with_lineage()
    if dup_removed > 0:
        print(f"  ✓ 删除 {dup_removed} 条重复记录")

    # 处理关键字段的缺失值
    critical_fields = ["systolic_bp", "diastolic_bp", "heart_rate"]
    for field in critical_fields:
        if field in df.columns:
            try:
                affected, method, _ = handler.handle_missing_values_evidence_based(
                    field,
                    auto_select=True
                )
                if affected > 0:
                    print(f"  ✓ {field}: 使用{method}处理了{affected}个缺失值")
            except Exception as e:
                print(f"  ⚠ {field}: {e}")

    # 验证生命体征范围
    vital_ranges = {
        "systolic_bp": (70, 200),
        "diastolic_bp": (40, 130),
        "heart_rate": (40, 150),
        "temperature": (35.0, 42.0),
    }

    for field, (min_val, max_val) in vital_ranges.items():
        if field in df.columns:
            count = handler.validate_vital_signs_with_evidence(
                field, min_val, max_val, action="flag"
            )
            if count > 0:
                print(f"  ⚠ {field}: 标记 {count} 个异常值")

    # 5. 最终评估
    final_quality = handler.assess_data_quality()
    print(f"\n最终质量: {final_quality.overall_score:.2%}")

    # 6. 保存结果
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    handler.save_cleaned_data(output_path / "cleaned_data.csv")
    handler.export_audit_trail(output_path / "audit_trail.json")
    handler.export_lineage(output_path / "data_lineage.json")

    print(f"\n✅ 清洗完成!")
    print(f"输出文件保存在: {output_path}/")

    # 7. 返回报告
    return handler.generate_quality_report()


if __name__ == "__main__":
    # 使用示例
    report = clean_my_data(
        input_file="data/sample_clinical_trial.csv",
        output_dir="outputs/my_analysis"
    )

    print(f"\n质量改善: {report['improvement_percentage']:.2f}%")
```

## 高级用法

### 1. 自定义缺失值处理策略

```python
# 手动指定策略
handler.handle_missing_values_evidence_based(
    column="weight",
    auto_select=False,  # 手动选择
    strategy="median",  # 使用中位数
    reason="Weight data is not normally distributed"
)

# 或使用多重插补
handler.handle_missing_values_evidence_based(
    column="weight",
    auto_select=False,
    strategy="multiple_imputation",
    reason="Multiple imputation for better statistical properties"
)
```

### 2. 回滚功能

```python
# 创建快照
print(f"当前记录数: {len(handler.df)}")

# 执行一些操作
handler.clean_duplicates_with_lineage()
handler.df = handler.df.head(50)  # 假设误删了数据

print(f"误删后记录数: {len(handler.df)}")

# 回滚到之前的状态
success = handler.rollback_to_snapshot("before_remove_duplicates")
if success:
    print(f"回滚成功! 恢复到 {len(handler.df)} 条记录")
```

### 3. ISO 8000 质量评估

```python
from bio_clean_agent.quality.assessment import DataQualityAssessor

# 创建评估器
assessor = DataQualityAssessor(
    reference_ranges={
        "systolic_bp": (90, 180),
        "diastolic_bp": (60, 110),
        "heart_rate": (50, 100),
        "temperature": (35.5, 38.5),
    }
)

# 运行评估
iso_report = assessor.assess(
    handler.df,
    dataset_name="Clinical Trial 001",
    key_fields=["patient_id", "visit_date"],
    date_fields=["enrollment_date", "visit_date"]
)

# 查看结果
print(f"ISO 8000 评估:")
print(f"  总分: {iso_report.overall_score:.2%}")
print(f"  等级: {iso_report.overall_level.value}")
print(f"\n维度分数:")
print(f"  完整性: {iso_report.completeness.score:.2%}")
print(f"  有效性: {iso_report.validity.score:.2%}")
print(f"  一致性: {iso_report.consistency.score:.2%}")
print(f"  唯一性: {iso_report.uniqueness.score:.2%}")
```

### 4. 批量处理多个文件

```python
from pathlib import Path

def batch_clean_files(input_dir, output_dir):
    """批量清洗多个临床试验数据文件"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # 找到所有CSV文件
    csv_files = list(input_path.glob("*.csv"))

    print(f"找到 {len(csv_files)} 个文件")

    results = []
    for csv_file in csv_files:
        print(f"\n处理: {csv_file.name}")

        try:
            # 创建handler
            handler = EnhancedClinicalTrialHandler(
                data_path=csv_file,
                user_id="batch_processor"
            )

            # 加载和清洗
            handler.load_data()
            handler.assess_data_quality()
            handler.detect_issues_with_evidence()
            handler.clean_duplicates_with_lineage()

            # 保存
            file_output = output_path / csv_file.stem
            file_output.mkdir(parents=True, exist_ok=True)
            handler.save_cleaned_data(file_output / f"{csv_file.stem}_cleaned.csv")
            handler.export_audit_trail(file_output / "audit_trail.json")

            # 记录结果
            report = handler.generate_quality_report()
            results.append({
                "file": csv_file.name,
                "status": "success",
                "improvement": report['improvement_percentage']
            })

            print(f"  ✓ 完成 (质量提升: {report['improvement_percentage']:.2f}%)")

        except Exception as e:
            results.append({
                "file": csv_file.name,
                "status": "failed",
                "error": str(e)
            })
            print(f"  ✗ 失败: {e}")

    return results

# 使用
results = batch_clean_files("data/trials/", "outputs/batch_cleaned/")

# 汇总报告
print("\n批处理汇总:")
success_count = sum(1 for r in results if r['status'] == 'success')
print(f"成功: {success_count}/{len(results)}")
```

## 输出文件说明

运行清洗流程后,会生成以下文件:

### 1. `cleaned_data.csv`
清洗后的数据文件,可以直接用于分析

### 2. `cleaned_data_metadata.json`
包含:
- 数据源信息
- 清洗时间戳
- 操作人员
- 质量报告(初始/最终质量分数)
- 操作统计

示例:
```json
{
  "source": "data/sample_clinical_trial.csv",
  "timestamp": "2025-10-20T15:47:17.558953",
  "user": "data_scientist_001",
  "quality_report": {
    "initial_quality": {...},
    "current_quality": {...},
    "improvement_percentage": 0.73
  }
}
```

### 3. `audit_trail.json`
FDA 21 CFR Part 11 合规的审计追踪,记录:
- 每个操作的时间戳
- 操作类型
- 影响的记录数
- 操作参数
- 科学证据引用

### 4. `data_lineage.json`
完整的数据血缘追踪,记录:
- 每个数据点的原始值
- 当前值
- 所有应用的转换
- 转换的时间和原因

## 配置和自定义

### 修改生命体征参考范围

```python
# 在detect_issues_with_evidence()之前自定义
custom_ranges = {
    "systolic_bp": (80, 190),  # 自定义范围
    "diastolic_bp": (45, 125),
    "heart_rate": (45, 140),
    "temperature": (35.5, 40.0),
}

# 使用自定义范围进行验证
for field, (min_val, max_val) in custom_ranges.items():
    handler.validate_vital_signs_with_evidence(
        field, min_val, max_val, action="flag"
    )
```

### 添加自定义验证规则

```python
# 添加自定义业务规则
def custom_validation(df):
    """自定义验证逻辑"""
    issues = []

    # 例: 检查BMI是否合理
    if "weight" in df.columns and "height" in df.columns:
        df["bmi"] = df["weight"] / ((df["height"] / 100) ** 2)
        invalid_bmi = ((df["bmi"] < 15) | (df["bmi"] > 50)).sum()
        if invalid_bmi > 0:
            issues.append({
                "field": "bmi",
                "count": invalid_bmi,
                "message": f"{invalid_bmi} records with unrealistic BMI"
            })

    return issues

# 运行自定义验证
custom_issues = custom_validation(handler.df)
print(f"自定义验证发现 {len(custom_issues)} 个问题")
```

## 最佳实践

### 1. 数据清洗工作流

```python
# 推荐的清洗顺序:
# 1. 加载和初始评估
# 2. 检测问题
# 3. 清理重复数据
# 4. 处理缺失值
# 5. 验证范围
# 6. 最终评估
# 7. 保存和导出
```

### 2. 质量检查点

```python
# 在关键步骤后检查质量
def check_quality(handler, step_name):
    quality = handler.assess_data_quality()
    print(f"{step_name}: {quality.overall_score:.2%}")
    return quality

# 使用
initial = check_quality(handler, "初始状态")
handler.clean_duplicates_with_lineage()
after_dedup = check_quality(handler, "去重后")
# ... 更多步骤
```

### 3. 错误处理

```python
try:
    handler = EnhancedClinicalTrialHandler(
        data_path="data/trial.csv",
        user_id="analyst"
    )
    handler.load_data()
    handler.clean_duplicates_with_lineage()
    # ... 更多操作

except FileNotFoundError:
    print("错误: 数据文件不存在")
except ValueError as e:
    print(f"数据验证错误: {e}")
except Exception as e:
    print(f"意外错误: {e}")
    # 可以选择回滚
    handler.rollback_to_snapshot("initial_load")
```

## 常见问题

### Q1: 如何选择基础版还是增强版?

**基础版 (`ClinicalTrialHandler`)** 适用于:
- 快速简单的数据清洗
- 不需要审计追踪
- 探索性分析

**增强版 (`EnhancedClinicalTrialHandler`)** 适用于:
- 需要监管合规性
- 需要完整的审计追踪
- 生产环境
- 科学研究发表

### Q2: 数据会被修改吗?

不会。原始数据文件不会被修改。所有清洗后的数据保存在新文件中。

### Q3: 如何处理大文件?

```python
# 对于大文件,可以分块处理
import pandas as pd

chunk_size = 10000
handler = EnhancedClinicalTrialHandler(...)

for chunk in pd.read_csv("large_file.csv", chunksize=chunk_size):
    # 处理每个chunk
    pass
```

### Q4: 可以自定义缺失值处理吗?

可以。使用 `auto_select=False` 并指定策略:

```python
handler.handle_missing_values_evidence_based(
    column="weight",
    auto_select=False,
    strategy="median",  # 或 "mean", "mode", "multiple_imputation"
    reason="Custom business rule"
)
```

## 技术支持

如遇问题:
1. 查看 `docs/AGENT_IMPROVEMENTS.md` - 技术细节
2. 查看 `docs/BEFORE_AFTER_COMPARISON.md` - 对比文档
3. 运行 `examples/quick_test.py` 进行测试

---

**祝你使用愉快!** 🎉
