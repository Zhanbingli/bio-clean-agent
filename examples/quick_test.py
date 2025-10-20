"""
Quick test script to verify the fixed clinical trials agent.

This demonstrates that the JSON serialization bug has been fixed.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bio_clean_agent.medical.clinical_trials_enhanced import EnhancedClinicalTrialHandler


def main():
    """Quick test of the fixed agent."""
    print("=" * 60)
    print("QUICK TEST - Fixed Clinical Trials Agent")
    print("=" * 60)

    # Initialize handler
    print("\n1. Initializing handler...")
    handler = EnhancedClinicalTrialHandler(
        data_path="data/sample_clinical_trial.csv",
        user_id="test_user"
    )
    print("   ✓ Handler initialized")

    # Load data
    print("\n2. Loading data...")
    df = handler.load_data()
    print(f"   ✓ Loaded {len(df)} records")

    # Assess quality
    print("\n3. Assessing quality...")
    quality = handler.assess_data_quality()
    print(f"   ✓ Quality score: {quality.overall_score:.2%}")

    # Detect issues
    print("\n4. Detecting issues...")
    issues = handler.detect_issues_with_evidence()
    print(f"   ✓ Found {len(issues)} issues")

    # Clean duplicates
    print("\n5. Cleaning duplicates...")
    removed = handler.clean_duplicates_with_lineage()
    print(f"   ✓ Removed {removed} duplicates")

    # Test JSON serialization (the key fix)
    print("\n6. Testing JSON export (critical test)...")
    try:
        output_dir = Path("outputs/quick_test")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save cleaned data with metadata
        handler.save_cleaned_data(output_dir / "test_data.csv")
        print("   ✓ Saved cleaned data and metadata")

        # Export audit trail
        handler.export_audit_trail(output_dir / "test_audit.json")
        print("   ✓ Exported audit trail")

        # Export lineage
        handler.export_lineage(output_dir / "test_lineage.json")
        print("   ✓ Exported data lineage")

        # Generate quality report
        report = handler.generate_quality_report()
        print(f"   ✓ Generated quality report (improvement: {report['improvement_percentage']:.2f}%)")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe JSON serialization bug has been fixed!")
        print("All export methods work correctly.")
        print(f"\nOutput files saved to: {output_dir}/")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    main()
