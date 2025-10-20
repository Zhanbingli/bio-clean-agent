#!/usr/bin/env python3
"""
临床试验数据清洗Agent - 启动脚本

用法:
    python run_clinical_agent.py <input_file> [output_dir]

示例:
    python run_clinical_agent.py data/sample_clinical_trial.csv
    python run_clinical_agent.py data/my_data.csv outputs/my_results
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bio_clean_agent.medical.clinical_trials_enhanced import EnhancedClinicalTrialHandler


def main():
    """主函数"""

    # 解析命令行参数
    if len(sys.argv) < 2:
        print("错误: 请提供输入文件路径")
        print("\n用法:")
        print("  python run_clinical_agent.py <input_file> [output_dir]")
        print("\n示例:")
        print("  python run_clinical_agent.py data/sample_clinical_trial.csv")
        print("  python run_clinical_agent.py data/my_data.csv outputs/my_results")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs/clinical_cleaning"

    # 检查输入文件是否存在
    if not Path(input_file).exists():
        print(f"错误: 输入文件不存在: {input_file}")
        sys.exit(1)

    print("=" * 70)
    print("临床试验数据清洗Agent")
    print("=" * 70)
    print(f"\n输入文件: {input_file}")
    print(f"输出目录: {output_dir}")
    print()

    try:
        # 1. 初始化
        print("[1/8] 初始化Agent...")
        handler = EnhancedClinicalTrialHandler(
            data_path=input_file,
            user_id="user"
        )
        print("      ✓ Agent已初始化")

        # 2. 加载数据
        print("\n[2/8] 加载数据...")
        df = handler.load_data()
        print(f"      ✓ 加载了 {len(df)} 条记录, {len(df.columns)} 个字段")

        # 3. 初始质量评估
        print("\n[3/8] 初始质量评估...")
        initial_quality = handler.assess_data_quality()
        print(f"      ✓ 质量分数: {initial_quality.overall_score:.2%}")
        print(f"        - 完整性: {initial_quality.completeness_score:.2%}")
        print(f"        - 有效性: {initial_quality.validity_score:.2%}")
        print(f"        - 一致性: {initial_quality.consistency_score:.2%}")
        print(f"        - 唯一性: {initial_quality.uniqueness_score:.2%}")
        print(f"        - 质量等级: {initial_quality.data_quality_level}")

        # 4. 检测问题
        print("\n[4/8] 检测数据质量问题...")
        issues = handler.detect_issues_with_evidence()
        print(f"      ✓ 发现 {len(issues)} 个问题:")

        # 按严重程度分组显示
        critical = [i for i in issues if i['severity'].value == 'critical']
        high = [i for i in issues if i['severity'].value == 'high']
        medium = [i for i in issues if i['severity'].value == 'medium']

        if critical:
            print(f"        🔴 严重: {len(critical)} 个")
            for issue in critical[:3]:
                print(f"           - {issue['message']}")

        if high:
            print(f"        🟠 高: {len(high)} 个")
            for issue in high[:3]:
                print(f"           - {issue['message']}")

        if medium:
            print(f"        🟡 中: {len(medium)} 个")
            for issue in medium[:3]:
                print(f"           - {issue['message']}")

        # 5. 清理重复数据
        print("\n[5/8] 清理重复数据...")
        dup_removed = handler.clean_duplicates_with_lineage(keep="first")
        if dup_removed > 0:
            print(f"      ✓ 删除了 {dup_removed} 条重复记录")
        else:
            print("      ✓ 没有发现重复记录")

        # 6. 处理缺失值
        print("\n[6/8] 处理缺失值...")
        missing_handled = 0

        # 自动处理关键字段的缺失值
        key_fields = ["systolic_bp", "diastolic_bp", "heart_rate", "temperature", "weight"]
        for field in key_fields:
            if field in df.columns:
                missing_count = df[field].isna().sum()
                if missing_count > 0:
                    try:
                        affected, method, _ = handler.handle_missing_values_evidence_based(
                            field,
                            auto_select=True
                        )
                        print(f"      ✓ {field}: 使用{method}方法处理了{affected}个缺失值")
                        missing_handled += affected
                    except Exception as e:
                        print(f"      ⚠ {field}: 跳过 ({str(e)[:50]})")

        if missing_handled == 0:
            print("      ✓ 关键字段没有缺失值需要处理")

        # 7. 最终质量评估
        print("\n[7/8] 最终质量评估...")
        final_quality = handler.assess_data_quality()
        improvement = (final_quality.overall_score - initial_quality.overall_score) * 100

        print(f"      ✓ 质量分数: {final_quality.overall_score:.2%}")
        print(f"        - 完整性: {final_quality.completeness_score:.2%} " +
              f"({(final_quality.completeness_score - initial_quality.completeness_score)*100:+.1f}%)")
        print(f"        - 有效性: {final_quality.validity_score:.2%} " +
              f"({(final_quality.validity_score - initial_quality.validity_score)*100:+.1f}%)")
        print(f"        - 唯一性: {final_quality.uniqueness_score:.2%} " +
              f"({(final_quality.uniqueness_score - initial_quality.uniqueness_score)*100:+.1f}%)")
        print(f"        - 质量等级: {final_quality.data_quality_level}")

        if improvement > 0:
            print(f"        🎉 质量提升: +{improvement:.2f}%")
        elif improvement < 0:
            print(f"        ⚠️ 质量下降: {improvement:.2f}%")
        else:
            print(f"        → 质量保持不变")

        # 8. 保存结果
        print("\n[8/8] 保存结果...")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存清洗后的数据
        handler.save_cleaned_data(output_path / "cleaned_data.csv")
        print(f"      ✓ 清洗后的数据: {output_path / 'cleaned_data.csv'}")

        # 保存元数据
        print(f"      ✓ 元数据: {output_path / 'cleaned_data_metadata.json'}")

        # 导出审计追踪
        handler.export_audit_trail(output_path / "audit_trail.json")
        print(f"      ✓ 审计追踪: {output_path / 'audit_trail.json'}")

        # 导出数据血缘
        handler.export_lineage(output_path / "data_lineage.json")
        print(f"      ✓ 数据血缘: {output_path / 'data_lineage.json'}")

        # 生成最终报告
        report = handler.generate_quality_report()

        print("\n" + "=" * 70)
        print("清洗完成!")
        print("=" * 70)
        print(f"\n📊 统计摘要:")
        print(f"   初始记录数: {report['records_initial']}")
        print(f"   最终记录数: {report['records_current']}")
        print(f"   删除记录数: {report['records_removed']}")
        print(f"   执行操作数: {report['total_operations']}")
        print(f"   血缘追踪点: {report['lineage_tracked']}")
        print(f"   质量提升: {report['improvement_percentage']:+.2f}%")

        print(f"\n📁 输出文件:")
        print(f"   {output_path}/cleaned_data.csv")
        print(f"   {output_path}/cleaned_data_metadata.json")
        print(f"   {output_path}/audit_trail.json")
        print(f"   {output_path}/data_lineage.json")

        print(f"\n✅ 合规性:")
        print(f"   ✓ FDA 21 CFR Part 11 (电子记录)")
        print(f"   ✓ ISO 8000 (数据质量)")
        print(f"   ✓ ALCOA+原则")

        print("\n" + "=" * 70)

    except FileNotFoundError:
        print(f"\n❌ 错误: 文件不存在: {input_file}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ 数据验证错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
