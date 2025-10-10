# Task-Oriented Medical Data Cleaning Agent

## Why Not a Chatbot?

This agent **deliberately avoids the chatbot paradigm** for medical data cleaning. Here's why:

### Problems with Chatbot Approach

❌ **Inefficient Communication**
```
User: "I have some medical data to clean"
Bot: "Great! What kind of medical data?"
User: "Clinical trial data"
Bot: "What issues are you experiencing?"
User: "I don't know, that's why I need help"
Bot: "Let me analyze... I found missing values. What should I do?"
User: "What are my options?"
... (10 more messages)
```

❌ **Wrong Mental Model**
- Users want to **delegate tasks**, not have conversations
- Medical data cleaning is a **process**, not a dialogue
- Results should be **visual and actionable**, not text responses

❌ **Cognitive Overhead**
- Users must constantly engage and respond
- Can't multitask while agent works
- Unclear progress and completion status

### Task-Oriented Approach

✅ **Submit and Observe**
```python
# 1. Submit task (structured, clear)
job = JobRequest(
    data_type=DataType.CLINICAL_TRIAL,
    input_paths=["data.csv"],
    objectives=[
        "Remove duplicates",
        "Handle missing values",
        "Validate vital signs"
    ]
)

# 2. Watch progress (no conversation needed)
watch_job(job.job_id)  # Real-time dashboard

# 3. Get results (visual report)
# → Interactive HTML report generated automatically
```

✅ **Right Mental Model**
- Task submission interface (like GitHub Actions, not ChatGPT)
- Real-time observer dashboard (like CI/CD pipelines)
- Structured decision points (not Q&A)
- Interactive reports (HTML, not text dumps)

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│           User Interface Layer                   │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐  ┌────────────┐  ┌─────────┐ │
│  │ Task Submit  │  │  Observer  │  │  Report │ │
│  │ API/CLI      │  │  Dashboard │  │  Viewer │ │
│  └──────────────┘  └────────────┘  └─────────┘ │
│                                                  │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│           Orchestration Layer                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  • Job Manager (queue, status, lifecycle)       │
│  • Event Stream (real-time updates)             │
│  • Decision Manager (structured approvals)      │
│                                                  │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│         Medical Data Handlers                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  • Clinical Trials  • EHR/EMR  • Imaging Meta   │
│  • Genomics  • Transcriptomics  • General       │
│                                                  │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│              Output Layer                        │
├─────────────────────────────────────────────────┤
│                                                  │
│  • Cleaned Data  • Quality Report (HTML)        │
│  • Action Log    • Recommendations              │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Task Submission API (`src/bio_clean_agent/api/`)

**Non-conversational job submission:**

```python
from bio_clean_agent.api import JobRequest, DataType

job = JobRequest(
    data_type=DataType.CLINICAL_TRIAL,
    input_paths=["trial_data.csv"],
    output_dir="outputs/trial_001",

    # Clear objectives (not vague questions)
    objectives=[
        "Remove duplicate patient visits",
        "Validate vital sign ranges",
        "Handle missing demographics"
    ],

    # Parameters
    parameters={
        "quality_threshold": 0.95,
    },

    # Auto-approval for minor decisions
    auto_approve=False,
)

job_id = job_manager.submit(job)
# → Returns immediately, execution happens asynchronously
```

**Key Features:**
- Structured task specification
- Asynchronous execution
- Status tracking via API
- No conversation required

---

### 2. Observer Dashboard (`src/bio_clean_agent/observer/`)

**Real-time monitoring WITHOUT chatting:**

```python
from bio_clean_agent.observer import watch_job

# Launch observer dashboard
watch_job(job_id)
```

**What you see:**
```
┌────────────────────────────────────────────┐
│ Bio Clean Agent - Observer Dashboard       │
├────────────────────────────────────────────┤
│ Job: abc-123-def                           │
│ Status: RUNNING                            │
│ Current Step: handle_missing_values        │
│                                            │
│ Metrics:                                   │
│   Records Processed: 1,250                 │
│   Records Cleaned:   1,180                 │
│   Issues Found:      47                    │
│   Elapsed Time:      00:02:15              │
│                                            │
│ Progress:                                  │
│ ⣾ Validate data schema      ████████ 100%  │
│ ⣾ Handle missing values     ████░░░░  60%  │
│ ○ Check for duplicates      ░░░░░░░░   0%  │
│ ○ Generate report           ░░░░░░░░   0%  │
│                                            │
│ Recent Events:                             │
│ 10:23:45 step.progress  60% complete       │
│ 10:23:32 issue.detected 15 missing vals    │
│ 10:23:15 step.started   handle_missing...  │
│ 10:23:10 data.profiled  1250 records       │
└────────────────────────────────────────────┘
```

**Unlike a chatbot:**
- No need to ask "how's it going?"
- See everything in real-time
- Can walk away and come back
- Visual progress tracking

---

### 3. Decision Point System (`src/bio_clean_agent/decisions/`)

**Structured decisions, NOT chatbot Q&A:**

#### ❌ Chatbot Approach
```
Bot: "I found some missing values in the age column"
User: "Ok, what should we do?"
Bot: "We could drop them or fill them"
User: "Which is better?"
Bot: "It depends on your use case"
User: "What are the trade-offs?"
... (continues indefinitely)
```

#### ✅ Task-Oriented Approach
```
┌─────────────────────────────────────────────────┐
│ ⚠  DECISION REQUIRED                             │
│                                                  │
│ Step: handle_missing_values                     │
│                                                  │
│ Column 'age' has 150 missing values (15%).      │
│ How should we handle this?                       │
│                                                  │
│ Options:                                         │
│ #  Option               Impact           Rec.    │
│ 1  Drop rows           Remove 150 rows           │
│ 2  Impute with median  Preserves data     ✓     │
│ 3  Keep as missing     Manual review             │
│                                                  │
│ Select option [1-3]: 2                           │
└─────────────────────────────────────────────────┘
```

**Decision Strategies:**

```python
from bio_clean_agent.decisions import (
    DecisionManager,
    AutoApproveStrategy,      # Auto-approve using defaults
    InteractiveStrategy,      # Structured prompts
    LLMAssistedStrategy,      # AI recommendation
)

# Different strategies for different scenarios
decision_manager = DecisionManager(
    strategy=AutoApproveStrategy()  # For batch processing
)

# Or use interactive for important decisions
decision_manager.set_strategy(InteractiveStrategy())
```

---

### 4. Medical Data Handlers (`src/bio_clean_agent/medical/`)

**Specialized handlers for medical data types:**

#### Clinical Trials
```python
from bio_clean_agent.medical import ClinicalTrialHandler

handler = ClinicalTrialHandler("trial_data.csv")
handler.load_data()

# Automatic issue detection
issues = handler.detect_issues()
# → Detects: duplicates, missing IDs, invalid vital signs, date inconsistencies

# Specialized cleaning
handler.clean_duplicates(keep="first")
handler.handle_missing_values("age", strategy="median")
handler.validate_vital_signs("systolic_bp", min_val=70, max_val=200)

# Save and report
handler.save_cleaned_data("cleaned_data.csv")
summary = handler.get_cleaning_summary()
```

#### EHR/EMR Data
```python
from bio_clean_agent.medical import EHRHandler

handler = EHRHandler("ehr_data.csv")
handler.load_data()

# Detect PHI that needs redaction
phi_fields = handler.detect_phi_fields()
# → ['patient_name', 'address', 'phone', 'mrn']

# Redact PHI
handler.redact_phi(fields=phi_fields)

# Validate medical codes
icd_validation = handler.validate_icd10_codes("diagnosis_code")
```

#### Imaging Metadata
```python
from bio_clean_agent.medical import ImagingMetadataHandler

handler = ImagingMetadataHandler("imaging_meta.csv")
modality_check = handler.validate_modality()
scan_issues = handler.check_scan_parameters()
```

---

### 5. Interactive HTML Reports (`src/bio_clean_agent/reporting/`)

**Visual, interactive reports instead of text dumps:**

```python
from bio_clean_agent.reporting import HTMLReportGenerator

generator = HTMLReportGenerator()
generator.generate(
    job_id="trial-001",
    data_type="clinical_trial",
    profile=profile,
    issues=issues,
    cleaning_summary=summary,
    output_path="report.html"
)
```

**Report includes:**
- 📊 Data quality metrics
- 🔍 Issues detected with severity levels
- ⚙️ Cleaning operations timeline
- 📈 Interactive charts (Chart.js)
- 💡 Actionable recommendations
- ✅ Before/after comparisons

**Open in browser → Interactive exploration**, not reading chat logs!

---

## Usage Examples

### Example 1: Quick Batch Cleaning

```python
# Submit task
job = JobRequest(
    data_type=DataType.CLINICAL_TRIAL,
    input_paths=["data.csv"],
    objectives=["Clean data for analysis"],
    auto_approve=True,  # No interruptions
)

job_id = job_manager.submit(job)

# Wait for completion (or check later)
while job_manager.get_status(job_id)["status"] != "completed":
    time.sleep(1)

# Get report
report_path = job_manager.get_status(job_id)["report_path"]
```

### Example 2: Interactive Cleaning with Decisions

```python
# Submit with interactive decisions
job = JobRequest(
    data_type=DataType.CLINICAL_TRIAL,
    input_paths=["data.csv"],
    objectives=["Careful cleaning with user approval"],
    auto_approve=False,
)

job_id = job_manager.submit(job)

# Watch in real-time
watch_job(job_id)  # Dashboard shows progress + decision prompts
```

### Example 3: API Integration

```bash
# Start API server
bio-clean-agent serve --port 8000

# Submit via REST API
curl -X POST http://localhost:8000/jobs \\
  -H "Content-Type: application/json" \\
  -d '{
    "data_type": "clinical_trial",
    "input_paths": ["data.csv"],
    "objectives": ["Remove duplicates", "Handle missing values"]
  }'

# Check status
curl http://localhost:8000/jobs/{job_id}

# Get report when done
curl http://localhost:8000/jobs/{job_id}/report
```

---

## Comparison Table

| Aspect | Chatbot Approach | Task-Oriented (This) |
|--------|-----------------|---------------------|
| **Task Input** | Conversational description | Structured specification |
| **Execution** | Interactive, requires presence | Asynchronous, fire-and-forget |
| **Progress** | Ask "how's it going?" | Real-time dashboard |
| **Decisions** | Back-and-forth Q&A | Structured prompts with options |
| **Results** | Text messages | Interactive HTML reports |
| **Mental Model** | Talking to assistant | Submitting to service |
| **Efficiency** | Many messages | Single task submission |
| **Multitasking** | Must stay engaged | Observe or leave |
| **Reproducibility** | Hard to repeat exact conversation | Task config is reusable |

---

## When to Use Each Approach

### Use Chatbot When:
- ❓ User is exploring and doesn't know what they need
- 💭 Task is genuinely ambiguous and requires discussion
- 🎓 Educational context (learning about the data)

### Use Task-Oriented When:
- ✅ Task is clear and repeatable
- ⚡ Efficiency matters
- 🔄 Multiple similar jobs need processing
- 📊 Results need to be visual and actionable
- 👥 Team collaboration (shared task definitions)

**For medical data cleaning: Task-oriented is almost always better!**

---

## Installation

```bash
# Basic installation
pip install -e .

# With API server
pip install -e .[api]  # Includes FastAPI, uvicorn

# Full installation
pip install -e .[api,seq,openai]
```

---

## CLI Commands

```bash
# Submit a job
bio-clean-agent submit \\
  --data-type clinical_trial \\
  --input data.csv \\
  --objectives "Remove duplicates,Handle missing values" \\
  --output-dir outputs/

# Watch a job
bio-clean-agent watch <job-id>

# List jobs
bio-clean-agent jobs --status running

# Start API server
bio-clean-agent serve --port 8000
```

---

## Design Principles

1. **Tasks, not conversations** - Users submit structured tasks, not chat messages
2. **Observe, don't interrogate** - Real-time visibility without constant questions
3. **Decide, don't discuss** - Structured decisions at key points, not open-ended Q&A
4. **Visual, not textual** - Interactive reports, not message dumps
5. **Async by default** - Fire-and-forget execution, check status when needed
6. **Reproducible** - Task definitions can be saved and reused

---

## Future Enhancements

- [ ] Web-based dashboard (React)
- [ ] Slack/email notifications for decisions
- [ ] Job scheduling and automation
- [ ] Team workspaces for shared tasks
- [ ] Advanced analytics on cleaning patterns
- [ ] Integration with data catalogs
- [ ] Compliance audit trails (HIPAA, GDPR)

---

## Contributing

See `CONTRIBUTING.md` for guidelines on adding new data handlers, decision strategies, or report formats.

---

## License

MIT License - see `LICENSE` file for details.
