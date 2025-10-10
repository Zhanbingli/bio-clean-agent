# 🚀 Quick Start: Medical Data Cleaning Agent

Get started with the task-oriented medical data cleaning agent in 5 minutes.

---

## Installation

```bash
# Clone or navigate to project
cd ai-agent

# Install with API support
pip install -e .[api]
```

---

## Your First Cleaning Job

### Step 1: Prepare Your Data

Put your medical data CSV file in the `data/` directory:

```bash
data/
  └── my_trial_data.csv
```

### Step 2: Create a Simple Cleaning Script

Create `clean_my_data.py`:

```python
from pathlib import Path
from bio_clean_agent.medical import ClinicalTrialHandler
from bio_clean_agent.reporting import HTMLReportGenerator

# 1. Load your data
handler = ClinicalTrialHandler("data/my_trial_data.csv")
handler.load_data()
print(f"✓ Loaded {len(handler.df)} records")

# 2. Profile and detect issues
profile = handler.profile_data()
issues = handler.detect_issues()
print(f"✓ Found {len(issues)} issues")

# 3. Clean the data
removed_dups = handler.clean_duplicates(keep="first")
print(f"✓ Removed {removed_dups} duplicates")

if "age" in handler.df.columns:
    handler.handle_missing_values("age", strategy="median")
    print("✓ Handled missing values in age")

handler.validate_vital_signs("systolic_bp", min_val=70, max_val=200, action="flag")
print("✓ Validated vital signs")

# 4. Save results
output_dir = Path("outputs/my_cleaning_job")
output_dir.mkdir(parents=True, exist_ok=True)

handler.save_cleaned_data(output_dir / "cleaned_data.csv")
print(f"✓ Saved cleaned data")

# 5. Generate report
generator = HTMLReportGenerator()
generator.generate(
    job_id="my-first-job",
    data_type="clinical_trial",
    profile=profile,
    issues=issues,
    cleaning_summary=handler.get_cleaning_summary(),
    output_path=output_dir / "report.html"
)
print(f"✓ Generated report: {output_dir / 'report.html'}")
print("\n🎉 Done! Open the HTML report in your browser.")
```

### Step 3: Run It

```bash
python clean_my_data.py
```

### Step 4: Review Results

```bash
# Open the interactive report
open outputs/my_cleaning_job/report.html
```

---

## Example Output

```
✓ Loaded 1250 records
✓ Found 8 issues
✓ Removed 12 duplicates
✓ Handled missing values in age
✓ Validated vital signs
✓ Saved cleaned data
✓ Generated report: outputs/my_cleaning_job/report.html

🎉 Done! Open the HTML report in your browser.
```

The HTML report shows:
- 📊 Data quality metrics
- 🔍 Issues detected with severity
- ⚙️ Cleaning operations performed
- 📈 Interactive charts
- 💡 Recommendations for next steps

---

## Run the Demo Workflow

Try the complete example:

```bash
python examples/task_oriented_workflow.py
```

This demonstrates:
1. Creating sample clinical trial data with issues
2. Automated issue detection
3. Structured cleaning operations
4. Interactive report generation

---

## Using the API (Advanced)

### Start the API Server

```bash
# Install API dependencies first
pip install -e .[api]

# Start server
python -c "from bio_clean_agent.api import run_api_server; run_api_server()"
```

Server runs at `http://localhost:8000`

### Submit a Job via API

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "clinical_trial",
    "input_paths": ["data/my_trial_data.csv"],
    "output_dir": "outputs/api_job_001",
    "objectives": [
      "Remove duplicate records",
      "Handle missing values",
      "Validate vital signs"
    ],
    "auto_approve": false
  }'
```

Response:
```json
{
  "job_id": "abc-123-def",
  "status": "submitted"
}
```

### Check Job Status

```bash
curl http://localhost:8000/jobs/abc-123-def
```

Response:
```json
{
  "job_id": "abc-123-def",
  "status": "running",
  "current_step": "handle_missing_values",
  "steps": [...],
  "metrics": {
    "records_processed": 845,
    "records_cleaned": 820,
    "issues_found": 25
  }
}
```

---

## Interactive Dashboard (Advanced)

Watch job execution in real-time:

```python
from bio_clean_agent.observer import watch_job

# Assuming you have a job_id
watch_job("abc-123-def")
```

You'll see a live terminal dashboard:

```
┌────────────────────────────────────┐
│ Job: abc-123-def                   │
│ Status: RUNNING                    │
│ Current Step: validate_vital_signs │
├────────────────────────────────────┤
│ Metrics:                           │
│   Records Processed: 1,250         │
│   Records Cleaned:   1,180         │
│   Issues Found:      47            │
│                                    │
│ Progress:                          │
│ ✓ Load data           ████████ 100%│
│ ✓ Profile data        ████████ 100%│
│ ⣾ Clean duplicates    ████████ 100%│
│ ⣾ Handle missing      ████░░░░  75%│
│ ○ Validate vitals     ░░░░░░░░   0%│
│                                    │
│ Recent Events:                     │
│ 10:23:45 step.progress             │
│ 10:23:32 issue.detected            │
│ 10:23:15 step.started              │
└────────────────────────────────────┘
```

Press `Ctrl+C` to exit (job continues in background).

---

## Common Use Cases

### Use Case 1: Clean Multiple Files

```python
from bio_clean_agent.medical import ClinicalTrialHandler

files = [
    "trial_001.csv",
    "trial_002.csv",
    "trial_003.csv"
]

for file in files:
    handler = ClinicalTrialHandler(f"data/{file}")
    handler.load_data()
    handler.clean_duplicates()
    handler.save_cleaned_data(f"outputs/cleaned_{file}")
    print(f"✓ Cleaned {file}")
```

### Use Case 2: EHR Data with PHI Redaction

```python
from bio_clean_agent.medical import EHRHandler

handler = EHRHandler("data/ehr_data.csv")
handler.load_data()

# Detect and redact PHI
phi_fields = handler.detect_phi_fields()
print(f"Found PHI fields: {phi_fields}")

handler.redact_phi(fields=phi_fields)

# Validate medical codes
icd_validation = handler.validate_icd10_codes("diagnosis_code")
print(f"Valid ICD-10 codes: {icd_validation['valid']}")

handler.save_cleaned_data("outputs/ehr_cleaned.csv")
```

### Use Case 3: Imaging Metadata Validation

```python
from bio_clean_agent.medical import ImagingMetadataHandler

handler = ImagingMetadataHandler("data/dicom_metadata.csv")
handler.load_data()

# Validate modality
modality_check = handler.validate_modality()
print(f"Valid modalities: {modality_check['valid']}")

# Check scan parameters
issues = handler.check_scan_parameters()
for issue in issues:
    print(f"Issue: {issue['field']} - {issue['issue']}")
```

---

## Next Steps

### Learn More

1. **Read the design philosophy:** [TASK_ORIENTED_DESIGN.md](TASK_ORIENTED_DESIGN.md)
2. **See detailed comparison:** [docs/comparison.md](docs/comparison.md)
3. **Check implementation details:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

### Customize

1. **Add your own data handler:**
   - Create `src/bio_clean_agent/medical/my_handler.py`
   - Inherit from base handler
   - Implement `load_data()`, `detect_issues()`, `clean_*()` methods

2. **Create custom decision strategies:**
   - See `src/bio_clean_agent/decisions/strategies.py`
   - Implement `DecisionStrategy` interface
   - Use in `DecisionManager`

3. **Customize reports:**
   - Modify `src/bio_clean_agent/reporting/html_generator.py`
   - Add new sections or visualizations
   - Include domain-specific metrics

---

## Troubleshooting

### "Module not found" errors

```bash
# Make sure you installed with -e flag
pip install -e .

# Or reinstall
pip uninstall bio-clean-agent
pip install -e .[api]
```

### "FastAPI not found" when using API

```bash
# Install API dependencies
pip install -e .[api]
```

### Data not loading

```python
# Check file path
from pathlib import Path
print(Path("data/my_file.csv").exists())

# Check file format
import pandas as pd
df = pd.read_csv("data/my_file.csv")
print(df.head())
```

---

## Get Help

- **GitHub Issues:** [Report bugs or request features](https://github.com/your-repo/issues)
- **Documentation:** See `README.md` and `TASK_ORIENTED_DESIGN.md`
- **Examples:** Check `examples/` directory

---

## Summary

You've learned how to:
- ✅ Install the agent
- ✅ Clean medical data with Python
- ✅ Generate interactive reports
- ✅ Use the REST API
- ✅ Watch jobs in real-time

**Remember:** This is NOT a chatbot. You submit tasks, observe execution, and review visual results.

**Happy cleaning! 🧬**
