# 🧬 Bio Clean Agent

An intelligent AI-powered agent for cleaning and processing biological and medical data. **This is NOT a chatbot** - it's a task-oriented system with **scientific knowledge** and **intelligent reasoning**.

> **New in v0.3:** 🧠 **Scientific Knowledge Base** + **Intelligent Planning**
> The agent now has 50+ medical standards with citations and 70+ evidence-based cleaning strategies.
> See [ADVANCED_CAPABILITIES.md](ADVANCED_CAPABILITIES.md) for the complete guide.

## ✨ Features

### Core Capabilities
- 🎯 **Task-Oriented Design** - Submit structured jobs, not chatbot conversations
- 📊 **Real-time Observer Dashboard** - Watch progress without constant interaction
- 🔔 **Structured Decision Points** - Clear choices at critical moments, no Q&A
- 📈 **Interactive HTML Reports** - Visual, actionable insights instead of text dumps
- 🏥 **Medical Data Handlers** - Specialized support for clinical trials, EHR, imaging metadata

### Data Types Supported
- 🧬 **Genomics** - Sequencing, transcriptomics, metabolomics datasets
- 🏥 **Clinical Trials** - Patient data, vital signs, visit records
- 📋 **EHR/EMR** - Electronic health records with PHI handling
- 🔬 **Imaging Metadata** - DICOM tags and scan parameters

### Technical Features
- 🔌 **REST API** - Submit jobs programmatically
- ⚡ **Async Execution** - Fire-and-forget task processing
- 🤖 **AI-Powered Planning** - Optional LLM-assisted decision recommendations
- 📝 **Audit Trails** - Complete logging of all cleaning operations
- 🎯 **Type-Safe** - Built with Pydantic for robust validation

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install -e .

# With API server (recommended for medical data)
pip install -e .[api]

# Full installation
pip install -e .[api,openai,seq]
```

### Usage Modes

#### 1. **Task-Oriented Workflow** (Recommended for Medical Data)

```python
from bio_clean_agent.api import JobRequest, DataType, get_job_manager
from bio_clean_agent.observer import watch_job

# Submit a cleaning job (no chatting!)
job = JobRequest(
    data_type=DataType.CLINICAL_TRIAL,
    input_paths=["data/trial_data.csv"],
    objectives=[
        "Remove duplicate patient visits",
        "Handle missing values in vital signs",
        "Validate date consistency"
    ],
    output_dir="outputs/trial_001",
    auto_approve=False  # Get prompted for decisions
)

job_id = get_job_manager().submit(job)

# Watch progress in real-time
watch_job(job_id)

# Or check status later via API
# GET /jobs/{job_id}
```

See [examples/task_oriented_workflow.py](examples/task_oriented_workflow.py) for complete examples.

#### 2. **REST API Server**

```bash
# Start the API server
bio-clean-agent serve --port 8000

# Submit jobs via HTTP
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "clinical_trial",
    "input_paths": ["data.csv"],
    "objectives": ["Clean and validate data"]
  }'
```

#### 3. **Legacy Chat Mode** (For Genomics Pipelines)

```bash
# Interactive chat for genomics data
bio-clean-agent chat --dataset-config examples/configs/example.yaml --dry-run
```

## 🎯 Task-Oriented vs Chatbot

| Aspect | Task-Oriented (NEW) | Chatbot (Legacy) |
|--------|---------------------|------------------|
| **Use Case** | Medical data, production workflows | Exploratory genomics |
| **Input** | Structured JobRequest | Natural language chat |
| **Execution** | Async, fire-and-forget | Interactive, requires presence |
| **Progress** | Real-time dashboard | Ask bot "how's it going?" |
| **Decisions** | Structured prompts with options | Back-and-forth Q&A |
| **Output** | Interactive HTML report | Text messages |
| **Efficiency** | Submit once, observe | Many message exchanges |

**For medical data cleaning, use the task-oriented API!**

See [TASK_ORIENTED_DESIGN.md](TASK_ORIENTED_DESIGN.md) for detailed comparison and rationale.

## 📁 Project Structure

```
src/bio_clean_agent/
  ├── agent.py              # Core agent orchestration
  ├── cli.py                # CLI commands
  ├── llm.py                # LLM integration (OpenAI, Simulated)
  ├── wizard.py             # Configuration wizard
  │
  ├── api/                  # NEW: Task-oriented API
  │   ├── jobs.py           # Job management, status tracking
  │   └── endpoints.py      # REST API endpoints (FastAPI)
  │
  ├── observer/             # NEW: Real-time monitoring
  │   ├── dashboard.py      # Terminal dashboard (Rich)
  │   └── events.py         # Event stream for progress tracking
  │
  ├── decisions/            # NEW: Structured decision system
  │   ├── manager.py        # Decision orchestration
  │   └── strategies.py     # Auto, interactive, LLM-assisted
  │
  ├── medical/              # NEW: Medical data handlers
  │   ├── clinical_trials.py # Clinical trial data cleaning
  │   ├── ehr.py            # EHR/EMR with PHI handling
  │   └── imaging.py        # Medical imaging metadata
  │
  ├── reporting/            # NEW: Interactive reports
  │   └── html_generator.py # Self-contained HTML reports
  │
  ├── dataspec/
  │   └── models.py         # Dataset schemas (Pydantic)
  │
  ├── pipelines/            # Genomics pipelines
  │   ├── base.py           # Pipeline base classes
  │   ├── sequencing.py     # Sequencing pipeline
  │   ├── transcriptomics.py
  │   └── metabolomics.py
  │
  ├── ui/                   # Legacy chat UI
  │   └── session.py        # Interactive chat session
  │
  └── utils/
      ├── logging.py
      ├── preflight.py      # Data validation
      └── reporting.py      # Report generation
```

## 🔧 Configuration

Example YAML configuration:

```yaml
dataset:
  dataset_id: my_dataset
  dataset_type: sequencing
  raw_paths:
    - data/sample_R1.fastq.gz
    - data/sample_R2.fastq.gz
  read_type: paired

output_dir: outputs/my_dataset

parameters:
  quality_threshold: 20
  adapter_sequence: AGATCGGAAGAGC...

report_dir: reports
```

## 🛠️ Extending

- **Add Pipelines**: Inherit from `Pipeline` and define steps
- **Custom Tools**: Override the `ToolExecutor` interface
- **New Data Types**: Add schemas in `dataspec/models.py`
- **LLM Providers**: Register new providers in `llm.py`

## 📝 License

MIT
