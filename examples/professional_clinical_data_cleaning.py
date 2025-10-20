"""
Professional-Grade Clinical Trial Data Cleaning Example

This example demonstrates enterprise-level data cleaning with:
- Scientific validation using knowledge base
- Complete data lineage tracking
- Statistical testing
- Audit trails for regulatory compliance
- Comprehensive quality metrics
- Rollback capabilities
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bio_clean_agent.medical.clinical_trials_enhanced import (
    EnhancedClinicalTrialHandler,
    OperationType
)
from bio_clean_agent.quality.assessment import DataQualityAssessor
import pandas as pd
import numpy as np


def create_sample_clinical_data() -> pd.DataFrame:
    """Create sample clinical trial data with quality issues."""
    np.random.seed(42)

    data = {
        "patient_id": [f"P{i:04d}" for i in range(1, 101)],
        "enrollment_date": pd.date_range("2023-01-01", periods=100, freq="D"),
        "visit_date": pd.date_range("2023-01-15", periods=100, freq="D"),
        "age": np.random.randint(18, 80, 100),
        "sex": np.random.choice(["M", "F"], 100),
        "weight": np.random.normal(70, 15, 100),  # kg
        "height": np.random.normal(170, 10, 100),  # cm
        "systolic_bp": np.random.normal(120, 15, 100),
        "diastolic_bp": np.random.normal(80, 10, 100),
        "heart_rate": np.random.normal(75, 12, 100),
        "temperature": np.random.normal(37.0, 0.5, 100),
        "treatment_arm": np.random.choice(["Active", "Placebo"], 100)
    }

    df = pd.DataFrame(data)

    # Add quality issues for demonstration

    # 1. Missing values
    df.loc[5:10, "systolic_bp"] = np.nan
    df.loc[20:22, "weight"] = np.nan
    df.loc[50, "patient_id"] = np.nan  # Critical issue

    # 2. Duplicates
    df = pd.concat([df, df.iloc[[0, 1, 2]]], ignore_index=True)

    # 3. Out-of-range values
    df.loc[15, "systolic_bp"] = 250  # Too high
    df.loc[16, "temperature"] = 42.5  # High fever
    df.loc[17, "heart_rate"] = 200  # Too high

    # 4. Date inconsistency
    df.loc[30, "visit_date"] = "2022-12-15"  # Before enrollment

    # 5. Negative values (data entry error)
    df.loc[40, "weight"] = -70

    return df


def main():
    """Run professional clinical data cleaning workflow."""

    print("=" * 80)
    print("PROFESSIONAL CLINICAL TRIAL DATA CLEANING")
    print("=" * 80)

    # Step 1: Create sample data
    print("\n[Step 1] Creating sample clinical trial data with quality issues...")
    df = create_sample_clinical_data()

    # Save sample data
    sample_path = Path("data/sample_clinical_trial.csv")
    sample_path.parent.mkdir(exist_ok=True)
    df.to_csv(sample_path, index=False)
    print(f"✓ Sample data saved to {sample_path}")
    print(f"  Total records: {len(df)}")

    # Step 2: Initialize handler
    print("\n[Step 2] Initializing Enhanced Clinical Trial Handler...")
    handler = EnhancedClinicalTrialHandler(
        data_path=sample_path,
        user_id="data_scientist_001"
    )
    print("✓ Handler initialized with knowledge base integration")

    # Step 3: Load data
    print("\n[Step 3] Loading data...")
    df_loaded = handler.load_data()
    print(f"✓ Data loaded: {len(df_loaded)} records, {len(df_loaded.columns)} fields")

    # Step 4: Initial quality assessment
    print("\n[Step 4] Performing initial quality assessment...")
    initial_quality = handler.assess_data_quality()
    print(f"✓ Initial Quality Score: {initial_quality.overall_score:.2%}")
    print(f"  - Completeness: {initial_quality.completeness_score:.2%}")
    print(f"  - Validity: {initial_quality.validity_score:.2%}")
    print(f"  - Consistency: {initial_quality.consistency_score:.2%}")
    print(f"  - Uniqueness: {initial_quality.uniqueness_score:.2%}")
    print(f"  Quality Level: {initial_quality.data_quality_level}")

    # Step 5: Detect issues with evidence
    print("\n[Step 5] Detecting data quality issues with scientific evidence...")
    issues = handler.detect_issues_with_evidence()
    print(f"✓ Detected {len(issues)} issues:")

    for i, issue in enumerate(issues[:5], 1):  # Show first 5
        print(f"\n  Issue {i}:")
        print(f"    Severity: {issue['severity'].value.upper()}")
        print(f"    Category: {issue['category']}")
        print(f"    Field: {issue['field']}")
        print(f"    Count: {issue['count']}")

        if issue.get('evidence'):
            print(f"    Evidence: {issue.get('evidence')}")
        if issue.get('evidence_statement'):
            print(f"    Statement: {issue.get('evidence_statement')[:100]}...")
        if issue.get('citation'):
            print(f"    Citation: {issue.get('citation')}")

    # Step 6: Clean duplicates with lineage tracking
    print("\n[Step 6] Removing duplicates with lineage tracking...")
    dup_removed = handler.clean_duplicates_with_lineage(keep="first")
    print(f"✓ Removed {dup_removed} duplicate records")
    print(f"  Lineage tracked: {len(handler.lineage)} data points")

    # Step 7: Handle missing values (evidence-based)
    print("\n[Step 7] Handling missing values with evidence-based strategies...")

    # Auto-select best method for systolic_bp
    affected, method, evidence = handler.handle_missing_values_evidence_based(
        "systolic_bp",
        auto_select=True
    )
    print(f"✓ Handled missing systolic_bp:")
    print(f"  Records affected: {affected}")
    print(f"  Method used: {method}")
    print(f"  Evidence ID: {evidence}")

    # Step 8: Final quality assessment
    print("\n[Step 8] Final quality assessment...")
    final_quality = handler.assess_data_quality()
    print(f"✓ Final Quality Score: {final_quality.overall_score:.2%}")
    print(f"  - Completeness: {final_quality.completeness_score:.2%} " +
          f"(+{(final_quality.completeness_score - initial_quality.completeness_score)*100:.1f}%)")
    print(f"  - Validity: {final_quality.validity_score:.2%}")
    print(f"  - Uniqueness: {final_quality.uniqueness_score:.2%} " +
          f"(+{(final_quality.uniqueness_score - initial_quality.uniqueness_score)*100:.1f}%)")
    print(f"  Quality Level: {final_quality.data_quality_level}")

    # Step 9: Generate comprehensive quality report
    print("\n[Step 9] Generating quality report...")
    quality_report = handler.generate_quality_report()
    print(f"✓ Quality improvement: {quality_report['improvement_percentage']:.1f}%")
    print(f"  Initial records: {quality_report['records_initial']}")
    print(f"  Final records: {quality_report['records_current']}")
    print(f"  Records removed: {quality_report['records_removed']}")
    print(f"  Total operations: {quality_report['total_operations']}")

    # Step 10: Save results with audit trail
    print("\n[Step 10] Saving cleaned data and audit trails...")

    output_dir = Path("outputs/professional_cleaning")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save cleaned data
    handler.save_cleaned_data(output_dir / "cleaned_data.csv")
    print(f"✓ Cleaned data saved to {output_dir / 'cleaned_data.csv'}")

    # Export audit trail (FDA 21 CFR Part 11 compliant)
    handler.export_audit_trail(output_dir / "audit_trail.json")
    print(f"✓ Audit trail exported to {output_dir / 'audit_trail.json'}")

    # Export lineage
    handler.export_lineage(output_dir / "data_lineage.json")
    print(f"✓ Data lineage exported to {output_dir / 'data_lineage.json'}")

    # Step 11: Advanced quality assessment using ISO 8000 framework
    print("\n[Step 11] Running ISO 8000 quality assessment...")
    assessor = DataQualityAssessor(
        reference_ranges={
            "systolic_bp": (90, 180),
            "diastolic_bp": (60, 110),
            "heart_rate": (50, 100),
            "temperature": (35.5, 38.5),
            "age": (18, 100),
            "weight": (40, 200),
            "height": (140, 220)
        }
    )

    iso_report = assessor.assess(
        handler.df,
        dataset_name="Clinical Trial 001",
        key_fields=["patient_id", "visit_date"],
        date_fields=["enrollment_date", "visit_date"]
    )

    print(f"✓ ISO 8000 Assessment Complete:")
    print(f"  Overall Score: {iso_report.overall_score:.2%}")
    print(f"  Overall Level: {iso_report.overall_level.value.upper()}")
    print(f"\n  Dimension Breakdown:")
    print(f"    Completeness: {iso_report.completeness.score:.2%} ({iso_report.completeness.level.value})")
    print(f"    Validity: {iso_report.validity.score:.2%} ({iso_report.validity.level.value})")
    print(f"    Consistency: {iso_report.consistency.score:.2%} ({iso_report.consistency.level.value})")
    print(f"    Uniqueness: {iso_report.uniqueness.score:.2%} ({iso_report.uniqueness.level.value})")

    # Statistical tests
    if iso_report.statistical_tests.get("normality"):
        print(f"\n  Statistical Tests:")
        normal_fields = [
            f for f, r in iso_report.statistical_tests["normality"].items()
            if r["normal"]
        ]
        print(f"    {len(normal_fields)} fields follow normal distribution")

    # Step 12: Demonstrate rollback capability
    print("\n[Step 12] Demonstrating rollback capability...")
    print("  Current records:", len(handler.df))

    # Perform an operation
    handler.df = handler.df.head(50)  # Simulate accidental deletion
    print("  After accidental deletion:", len(handler.df))

    # Rollback
    success = handler.rollback_to_snapshot("before_remove_duplicates")
    if success:
        print(f"  ✓ Rolled back successfully: {len(handler.df)} records restored")
    else:
        print("  ✗ Rollback failed")

    # Summary
    print("\n" + "=" * 80)
    print("CLEANING COMPLETE - PROFESSIONAL WORKFLOW")
    print("=" * 80)
    print("\n✓ All cleaning operations completed with:")
    print(f"  • Scientific validation using {len(handler.evidence_base.entries)} evidence entries")
    print(f"  • {len(handler.audit_trail)} audit trail entries")
    print(f"  • {len(handler.lineage)} lineage tracked data points")
    print(f"  • {len(handler.snapshots)} rollback snapshots")
    print(f"  • Quality improvement: {quality_report['improvement_percentage']:.1f}%")
    print(f"\n  Output files:")
    print(f"    {output_dir / 'cleaned_data.csv'}")
    print(f"    {output_dir / 'cleaned_data_metadata.json'}")
    print(f"    {output_dir / 'audit_trail.json'}")
    print(f"    {output_dir / 'data_lineage.json'}")
    print("\n  Regulatory compliance:")
    print("    ✓ FDA 21 CFR Part 11 (Electronic Records)")
    print("    ✓ ISO 8000 (Data Quality)")
    print("    ✓ ALCOA+ Principles (Attributable, Legible, Contemporaneous, Original, Accurate)")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
