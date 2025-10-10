"""
Example: Task-Oriented Medical Data Cleaning Workflow

This demonstrates the NON-CHATBOT approach to data cleaning.
Instead of conversational interaction, users submit structured tasks
and observe execution in real-time.
"""

from pathlib import Path
import sys

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bio_clean_agent.api.jobs import JobRequest, DataType, JobPriority, get_job_manager
from bio_clean_agent.observer.dashboard import watch_job
from bio_clean_agent.observer.events import get_event_stream, Event, EventType
from bio_clean_agent.decisions import DecisionManager, InteractiveStrategy
from bio_clean_agent.medical.clinical_trials import ClinicalTrialHandler
from bio_clean_agent.reporting.html_generator import HTMLReportGenerator


def example_1_submit_job():
    """
    Example 1: Submit a job via API (no chatting!)

    User provides:
    - Data files
    - Objectives (structured list, not conversation)
    - Parameters
    - Auto-approval settings

    No need for back-and-forth dialogue.
    """
    print("=" * 60)
    print("Example 1: Task-Oriented Job Submission")
    print("=" * 60)

    # Create a job request (structured, not conversational)
    job_request = JobRequest(
        data_type=DataType.CLINICAL_TRIAL,
        input_paths=["data/clinical_trial_data.csv"],
        output_dir="outputs/trial_001",

        # Clear objectives instead of chatbot queries
        objectives=[
            "Remove duplicate patient visits",
            "Handle missing values in vital signs",
            "Validate date consistency",
            "Generate quality report",
        ],

        # Optional parameters
        parameters={
            "quality_threshold": 0.95,
            "allow_missing_inputs": False,
        },

        # Auto-approve minor decisions
        auto_approve=False,

        # Notification preferences
        notify_on_decision=True,
        notify_on_completion=True,
    )

    # Submit job
    job_manager = get_job_manager()
    job_id = job_manager.submit(job_request)

    print(f"\n✓ Job submitted: {job_id}")
    print(f"  Data type: {job_request.data_type}")
    print(f"  Objectives: {len(job_request.objectives)}")
    print(f"\nYou can now:")
    print(f"  1. Watch progress: watch_job('{job_id}')")
    print(f"  2. Check status via API: GET /jobs/{job_id}")
    print(f"  3. Go do other work while agent executes")

    return job_id


def example_2_observer_mode():
    """
    Example 2: Observer Dashboard (Real-time monitoring, not chatting)

    User watches the agent work in real-time:
    - See current step
    - View progress bars
    - Monitor events
    - NO conversation needed

    This is like watching a CI/CD pipeline, not chatting with ChatGPT.
    """
    print("\n" + "=" * 60)
    print("Example 2: Observer Dashboard")
    print("=" * 60)

    print("\nInstead of chatbot conversation:")
    print("  User: 'How's it going?'")
    print("  Bot: 'I'm processing step 2...'")
    print("  User: 'What's step 2?'")
    print("  Bot: 'Handling missing values...'")
    print()
    print("You get a REAL-TIME DASHBOARD:")
    print("┌────────────────────────────────────┐")
    print("│ Job: abc-123                       │")
    print("│ Status: RUNNING                    │")
    print("│ Current Step: handle_missing_values│")
    print("├────────────────────────────────────┤")
    print("│ Progress:                          │")
    print("│ ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░ 60%          │")
    print("│                                    │")
    print("│ Recent Events:                     │")
    print("│ 10:23:15 step.started              │")
    print("│ 10:23:16 issue.detected            │")
    print("│ 10:23:18 decision.required         │")
    print("└────────────────────────────────────┘")

    # In real usage:
    # watch_job(job_id)


def example_3_decision_points():
    """
    Example 3: Structured Decision Points (Not chatbot Q&A)

    Instead of:
      Bot: "I found missing values. What do you think we should do?"
      User: "Hmm, maybe fill them?"
      Bot: "Fill with what?"
      User: "I don't know, what are my options?"

    You get:
      ┌─────────────────────────────────────────────┐
      │ ⚠ DECISION REQUIRED                          │
      │                                              │
      │ Column 'age' has 150 missing values (15%).  │
      │ How should we handle this?                   │
      │                                              │
      │ Options:                                     │
      │ 1. Drop rows              (lose 15% data)    │
      │ 2. Impute with median     [RECOMMENDED]      │
      │ 3. Keep as missing        (preserve data)    │
      │                                              │
      │ Select option: _                             │
      └─────────────────────────────────────────────┘
    """
    print("\n" + "=" * 60)
    print("Example 3: Structured Decision Points")
    print("=" * 60)

    decision_manager = DecisionManager(
        strategy=InteractiveStrategy()
    )

    print("\nWhen agent encounters ambiguity, it presents")
    print("a STRUCTURED decision (not a chat message):")

    # This would be called by the agent during execution
    choice = decision_manager.request_decision(
        job_id="example-123",
        step_name="handle_missing_values",
        question="Column 'age' has 150 missing values (15%). How should we handle this?",
        options=[
            {
                "id": "drop",
                "label": "Drop rows with missing values",
                "impact": "May lose 15% of data",
                "recommended": False,
            },
            {
                "id": "impute_median",
                "label": "Impute with median value",
                "impact": "Preserves all rows, robust to outliers",
                "recommended": True,
            },
            {
                "id": "keep_missing",
                "label": "Keep as missing (NaN)",
                "impact": "Preserve data integrity",
                "recommended": False,
            },
        ],
        metadata={
            "column": "age",
            "missing_count": 150,
            "total_count": 1000,
        },
        default_option="impute_median",
    )

    print(f"\n✓ Decision made: {choice.get('label')}")


def example_4_full_workflow():
    """
    Example 4: Complete Workflow (Task → Execute → Observe → Report)

    This shows the complete non-chatbot experience.
    """
    print("\n" + "=" * 60)
    print("Example 4: Complete Task-Oriented Workflow")
    print("=" * 60)

    # Create sample data for demonstration
    sample_data_path = Path("data/sample_clinical_trial.csv")
    sample_data_path.parent.mkdir(exist_ok=True)

    if not sample_data_path.exists():
        import pandas as pd
        import numpy as np

        # Create sample clinical trial data with issues
        np.random.seed(42)
        df = pd.DataFrame({
            "patient_id": [f"PT{i:03d}" for i in range(100)],
            "visit_date": pd.date_range("2024-01-01", periods=100),
            "treatment_arm": np.random.choice(["Treatment", "Control"], 100),
            "age": np.random.randint(18, 80, 100).astype(float),  # Use float to allow NaN
            "systolic_bp": np.random.randint(100, 160, 100).astype(float),
            "diastolic_bp": np.random.randint(60, 100, 100).astype(float),
        })

        # Introduce issues
        df.loc[10:14, "age"] = np.nan  # Missing values
        df.loc[20, "systolic_bp"] = 250  # Outlier
        df.loc[50:51, "patient_id"] = df.loc[48, "patient_id"]  # Duplicates
        df.to_csv(sample_data_path, index=False)
        print(f"✓ Created sample data: {sample_data_path}")

    # Step 1: Load and profile data
    print("\nStep 1: Load and Profile Data")
    print("-" * 40)
    handler = ClinicalTrialHandler(sample_data_path)
    handler.load_data()
    profile = handler.profile_data()

    print(f"  Total records: {profile['total_records']}")
    print(f"  Total columns: {profile['total_columns']}")
    print(f"  Missing values in {len(profile['missing_values'])} columns")

    # Step 2: Detect issues
    print("\nStep 2: Detect Issues")
    print("-" * 40)
    issues = handler.detect_issues()
    for issue in issues:
        print(f"  [{issue['severity'].upper()}] {issue['message']}")

    # Step 3: Clean data (no chatting, just execute)
    print("\nStep 3: Execute Cleaning")
    print("-" * 40)

    # Remove duplicates
    removed = handler.clean_duplicates(keep="first")
    print(f"  ✓ Removed {removed} duplicate records")

    # Handle missing values
    if "age" in [issue["field"] for issue in issues if issue["category"] == "missing_required"]:
        handled = handler.handle_missing_values("age", strategy="median")
        print(f"  ✓ Handled {handled} missing values in 'age'")

    # Validate vital signs
    vital_issues = handler.validate_vital_signs(
        "systolic_bp",
        min_val=70,
        max_val=200,
        action="flag"
    )
    print(f"  ✓ Flagged {vital_issues} out-of-range vital signs")

    # Step 4: Save cleaned data
    print("\nStep 4: Save Results")
    print("-" * 40)
    output_path = Path("outputs/sample_clinical_trial_cleaned.csv")
    handler.save_cleaned_data(output_path)
    print(f"  ✓ Saved cleaned data: {output_path}")

    # Step 5: Generate interactive report
    print("\nStep 5: Generate Interactive Report")
    print("-" * 40)
    report_generator = HTMLReportGenerator()
    report_path = Path("outputs/sample_clinical_trial_report.html")

    cleaning_summary = handler.get_cleaning_summary()

    report_generator.generate(
        job_id="example-job-001",
        data_type="clinical_trial",
        profile=profile,
        issues=issues,
        cleaning_summary=cleaning_summary,
        output_path=report_path,
    )
    print(f"  ✓ Generated report: {report_path}")
    print(f"  Open in browser to see interactive visualization!")

    print("\n" + "=" * 60)
    print("Workflow Complete!")
    print("=" * 60)
    print("\nNotice: NO chatbot conversation was needed!")
    print("  - Task was clearly specified upfront")
    print("  - Agent executed autonomously")
    print("  - Results are actionable and visual")
    print("\nThis is MUCH more efficient than:")
    print("  User: 'Can you clean my data?'")
    print("  Bot: 'Sure! What kind of data?'")
    print("  User: 'Clinical trial data'")
    print("  Bot: 'Great! What issues should I look for?'")
    print("  User: 'Um... missing values?'")
    print("  ... (10 more messages) ...")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TASK-ORIENTED MEDICAL DATA CLEANING")
    print("Non-Chatbot Agent Workflow Examples")
    print("=" * 60)

    # Run examples
    # example_1_submit_job()
    # example_2_observer_mode()
    # example_3_decision_points()
    example_4_full_workflow()

    print("\n✨ All examples completed!")
    print("\nKey Takeaways:")
    print("  1. Tasks are submitted, not chatted about")
    print("  2. Execution is observed, not conversed with")
    print("  3. Decisions are structured, not Q&A")
    print("  4. Results are visual and actionable")
    print("\nThis is how agents SHOULD work for data tasks.")
