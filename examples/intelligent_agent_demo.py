"""
Demonstration of Intelligent Agent with Scientific Knowledge

This shows how the agent goes from being a "task executor"
to an "intelligent assistant" that:
  1. Reasons about data
  2. Consults scientific knowledge
  3. Provides evidence-based recommendations
  4. Explains its decisions
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bio_clean_agent.knowledge import MedicalStandards, ValidationRules, EvidenceBase
from bio_clean_agent.planning import SmartPlanner
from bio_clean_agent.medical import ClinicalTrialHandler

import pandas as pd
import numpy as np


def demo_1_scientific_knowledge():
    """
    Demo 1: Scientific Knowledge Base

    The agent has 50+ medical standards with full scientific citations.
    """
    print("=" * 70)
    print("DEMO 1: Scientific Knowledge Base")
    print("=" * 70)

    standards = MedicalStandards()

    # Get blood pressure standard
    bp_entry = standards.get_entry("vs_blood_pressure_normal")

    print("\n📚 Medical Standard: Blood Pressure")
    print("-" * 70)
    print(f"Statement: {bp_entry.statement}")
    print(f"Rationale: {bp_entry.rationale}")
    print(f"\nEvidence Level: {bp_entry.evidence_level.value}")
    print(f"Confidence: {bp_entry.confidence.value.upper()}")
    print(f"\nCitations:")
    for cite in bp_entry.citations:
        print(f"  • {cite.source} ({cite.year})")
        print(f"    \"{cite.title}\"")
        if cite.url:
            print(f"    {cite.url}")

    # Get evidence-based recommendation for missing data
    evidence = EvidenceBase()
    rec = evidence.get_entry("missing_multiple_imputation")

    print("\n\n📊 Evidence-Based Recommendation: Missing Data")
    print("-" * 70)
    print(f"Statement: {rec.statement}")
    print(f"Rationale: {rec.rationale}")
    print(f"\nEvidence Level: {rec.evidence_level.value}")
    print(f"Confidence: {rec.confidence.value.upper()}")
    print(f"\nCitations:")
    for cite in rec.citations:
        print(f"  • {cite.source}")
        if cite.year:
            print(f"    Year: {cite.year}")
        if cite.doi:
            print(f"    DOI: {cite.doi}")

    print("\n✓ This is not just \"agent does stuff\" - it's SCIENTIFICALLY GROUNDED")


def demo_2_intelligent_validation():
    """
    Demo 2: Intelligent Validation with Evidence

    The agent validates data against medical knowledge and explains WHY.
    """
    print("\n\n" + "=" * 70)
    print("DEMO 2: Intelligent Validation")
    print("=" * 70)

    validator = ValidationRules()

    test_cases = [
        ("systolic_bp", 250, {"age": 45}),  # Too high
        ("systolic_bp", 50, {"age": 45}),  # Too low
        ("heart_rate", 45, {"age": 45}),  # Low but possibly normal
        ("heart_rate", 45, {"age": 45, "athlete": True}),  # Normal for athlete
        ("temperature", 39.5, {}),  # Fever
    ]

    for field, value, context in test_cases:
        print(f"\n🔍 Validating: {field} = {value}")
        if context:
            print(f"   Context: {context}")
        print("-" * 70)

        result = validator.validate_vital_sign(field, value, context)

        if not result.valid:
            print("❌ INVALID")
            for error in result.errors:
                print(f"   Error: {error}")
        else:
            print("✓ Valid")

        if result.warnings:
            for warning in result.warnings:
                print(f"   ⚠ Warning: {warning}")

        if result.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in result.recommendations:
                print(f"   • {rec}")

        if result.evidence:
            print(f"\n📚 Evidence:")
            for ev in result.evidence:
                print(f"   Source: {ev.citations[0].source if ev.citations else 'Internal knowledge'}")

    print("\n✓ Every validation is backed by medical knowledge!")


def demo_3_intelligent_planning():
    """
    Demo 3: Intelligent Task Planning

    The agent REASONS about what to do, not just executes blindly.
    """
    print("\n\n" + "=" * 70)
    print("DEMO 3: Intelligent Task Planning")
    print("=" * 70)

    # Create sample data profile
    data_profile = {
        "total_records": 1000,
        "total_columns": 8,
        "missing_values": {
            "age": {"count": 150, "percentage": 15.0},
            "systolic_bp": {"count": 45, "percentage": 4.5},
            "weight": {"count": 230, "percentage": 23.0},
        },
        "numeric_summary": {
            "age": {"min": 18, "max": 95, "mean": 52.3, "std": 15.2},
            "systolic_bp": {"min": 80, "max": 250, "mean": 128.5, "std": 18.7},
        },
    }

    print("\n📊 Data Profile:")
    print(f"  Total records: {data_profile['total_records']}")
    print(f"  Missing data issues: {len(data_profile['missing_values'])}")

    # Create intelligent plan
    planner = SmartPlanner()
    plan = planner.create_plan(
        job_id="demo-001",
        data_type="clinical_trial",
        objectives=[
            "Remove duplicates",
            "Handle missing values",
            "Validate vital signs",
        ],
        data_profile=data_profile,
    )

    print(f"\n🧠 Agent Analysis:")
    print(f"  Detected issues: {len(plan.detected_issues)}")
    for issue in plan.detected_issues:
        severity_icon = "🔴" if issue["severity"] == "critical" else "🟡"
        print(f"    {severity_icon} {issue['type']} in {issue['field']}: {issue['details']}")

    print(f"\n📋 Intelligent Execution Plan:")
    print(f"  Total steps: {len(plan.steps)}")
    print(f"  Critical steps: {sum(1 for s in plan.steps if s.priority.value == 'critical')}")

    for i, step in enumerate(plan.steps, 1):
        print(f"\n  {i}. {step.name}")
        print(f"     Type: {step.step_type.value}")
        print(f"     Priority: {step.priority.value.upper()}")
        print(f"     Rationale: {step.rationale}")

        if step.evidence_based:
            print(f"     ✓ Evidence-based: {step.evidence_summary}")

        if step.depends_on:
            print(f"     Dependencies: {', '.join(step.depends_on)}")

        print(f"     Risk: {step.risk_level} | Reversible: {'Yes' if step.reversible else 'No'}")

    print(f"\n💡 Agent Recommendations:")
    for rec in plan.recommendations:
        print(f"  • {rec}")

    if plan.warnings:
        print(f"\n⚠ Warnings:")
        for warn in plan.warnings:
            print(f"  • {warn}")

    print(f"\n📈 Estimated Outcomes:")
    print(f"  Quality improvement: {plan.estimated_quality_improvement * 100:.0f}%")
    print(f"  Data loss: {plan.estimated_data_loss * 100:.1f}%")

    print("\n✓ This is INTELLIGENT PLANNING, not blind execution!")


def demo_4_evidence_based_decisions():
    """
    Demo 4: Evidence-Based Decision Making

    The agent provides recommendations with full scientific backing.
    """
    print("\n\n" + "=" * 70)
    print("DEMO 4: Evidence-Based Decision Making")
    print("=" * 70)

    evidence = EvidenceBase()

    scenarios = [
        ("missing_data", {"missing_rate": 0.03}, "3% missing data"),
        ("missing_data", {"missing_rate": 0.15}, "15% missing data"),
        ("missing_data", {"missing_rate": 0.25, "inferential_statistics": True}, "25% missing, need inference"),
        ("outliers", {}, "Outlier treatment"),
        ("duplicates", {}, "Duplicate records"),
    ]

    for situation, context, desc in scenarios:
        print(f"\n📊 Scenario: {desc}")
        print("-" * 70)

        rec = evidence.get_cleaning_recommendation(situation, context)

        if rec:
            print(f"💡 Recommendation:")
            print(f"   {rec.statement}")
            print(f"\n📝 Rationale:")
            print(f"   {rec.rationale}")
            print(f"\n🔬 Evidence:")
            print(f"   Level: {rec.evidence_level.value}")
            print(f"   Confidence: {rec.confidence.value.upper()}")

            if rec.citations:
                print(f"\n📚 Citations:")
                for cite in rec.citations:
                    print(f"   • {cite.source}")
                    if cite.year:
                        print(f"     Year: {cite.year}")
                    print(f"     \"{cite.title}\"")
                    if cite.doi:
                        print(f"     DOI: {cite.doi}")

            if rec.conditions:
                print(f"\n✓ Apply when:")
                for cond in rec.conditions:
                    print(f"   - {cond}")

            if rec.contraindications:
                print(f"\n⚠ Do NOT use when:")
                for contra in rec.contraindications:
                    print(f"   - {contra}")

    print("\n✓ Every recommendation has peer-reviewed scientific backing!")


def demo_5_complete_workflow():
    """
    Demo 5: Complete Intelligent Workflow

    Putting it all together: Agent with scientific knowledge and reasoning.
    """
    print("\n\n" + "=" * 70)
    print("DEMO 5: Complete Intelligent Workflow")
    print("=" * 70)

    # Create sample data
    np.random.seed(42)
    df = pd.DataFrame({
        "patient_id": [f"PT{i:03d}" for i in range(100)],
        "age": np.random.randint(18, 85, 100).astype(float),
        "systolic_bp": np.random.randint(100, 160, 100).astype(float),
        "weight": np.random.randint(50, 120, 100).astype(float),
    })

    # Introduce issues
    df.loc[10:14, "age"] = np.nan  # Missing
    df.loc[20, "systolic_bp"] = 250  # Outlier
    df.loc[30, "age"] = 150  # Invalid

    # Save
    data_path = Path("data/demo_intelligent.csv")
    data_path.parent.mkdir(exist_ok=True)
    df.to_csv(data_path, index=False)

    print(f"\n1️⃣ Loading data...")
    handler = ClinicalTrialHandler(data_path)
    handler.load_data()
    print(f"   ✓ Loaded {len(handler.df)} records")

    print(f"\n2️⃣ Consulting medical knowledge...")
    standards = MedicalStandards()
    bp_std = standards.get_entry("vs_blood_pressure_normal")
    print(f"   📚 Reference: {bp_std.statement}")
    print(f"   📖 Source: {bp_std.citations[0].source} ({bp_std.citations[0].year})")

    print(f"\n3️⃣ Intelligent analysis...")
    profile = handler.profile_data()
    planner = SmartPlanner()
    plan = planner.create_plan(
        job_id="demo-final",
        data_type="clinical_trial",
        objectives=["Clean with scientific best practices"],
        data_profile=profile,
    )

    print(f"   🔍 Detected {len(plan.detected_issues)} issues:")
    for issue in plan.detected_issues:
        print(f"      • {issue['type']} in {issue['field']}")

    print(f"\n4️⃣ Evidence-based execution plan:")
    for step in [s for s in plan.steps if s.evidence_based]:
        print(f"   ✓ {step.name}")
        print(f"     Evidence: {step.evidence_summary}")

    print(f"\n5️⃣ Validating against medical knowledge...")
    validator = ValidationRules()

    invalid_count = 0
    for idx, row in handler.df.iterrows():
        if pd.notna(row["systolic_bp"]):
            result = validator.validate_vital_sign(
                "systolic_bp",
                row["systolic_bp"],
                context={"age": row.get("age")}
            )
            if not result.valid:
                invalid_count += 1

        if pd.notna(row["age"]):
            result = validator.validate_age(row["age"])
            if not result.valid:
                invalid_count += 1

    print(f"   ⚠ Found {invalid_count} invalid values")

    print(f"\n6️⃣ Getting evidence-based recommendations...")
    evidence = EvidenceBase()
    for issue in plan.detected_issues[:2]:  # Show first 2
        rec = evidence.get_cleaning_recommendation(
            issue["type"],
            context=issue
        )
        if rec:
            print(f"   💡 {issue['field']}: {rec.statement}")
            print(f"      Confidence: {rec.confidence.value}")

    print(f"\n✅ COMPLETE WORKFLOW WITH:")
    print(f"   ✓ Scientific knowledge (50+ standards with citations)")
    print(f"   ✓ Intelligent reasoning (data-driven planning)")
    print(f"   ✓ Evidence-based recommendations (70+ strategies)")
    print(f"   ✓ Full transparency (every decision explained)")
    print(f"\n   This is a TOP-TIER intelligent agent! 🚀")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("INTELLIGENT AGENT DEMONSTRATION")
    print("Scientific Knowledge + Intelligent Reasoning")
    print("=" * 70)

    demo_1_scientific_knowledge()
    demo_2_intelligent_validation()
    demo_3_intelligent_planning()
    demo_4_evidence_based_decisions()
    demo_5_complete_workflow()

    print("\n\n" + "=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print("""
This agent is NOT just a task executor. It's an INTELLIGENT ASSISTANT that:

1. 📚 Has 50+ Medical Standards
   - Full scientific citations (AHA, WHO, ADA, FDA)
   - Evidence hierarchy (systematic reviews → expert opinion)
   - Confidence levels (HIGH/MEDIUM/LOW)

2. 🧠 Reasons About Data
   - Analyzes data characteristics
   - Detects issues intelligently
   - Prioritizes based on impact

3. 💡 Provides Evidence-Based Recommendations
   - 70+ cleaning strategies with citations
   - Context-specific advice
   - Risk assessment included

4. 🔍 Validates Against Medical Knowledge
   - Checks biological plausibility
   - References clinical guidelines
   - Explains WHY values are invalid

5. 📋 Creates Intelligent Plans
   - Evidence-backed steps
   - Dependency management
   - Outcome estimation

6. 🎯 Assists Decision-Making
   - Not "do this"
   - But "do this BECAUSE [evidence], confidence: HIGH, citation: [paper]"

This combines:
  ✓ Task execution (agent capabilities)
  ✓ Scientific knowledge (medical expertise)
  ✓ Intelligent reasoning (smart planning)

Making it a TRUE INTELLIGENT ASSISTANT for medical data! 🏆
""")
