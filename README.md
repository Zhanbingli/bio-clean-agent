# 🧬 Bio Clean Agent

An intelligent AI-powered agent for cleaning and processing biological data. The agent uses natural language understanding to plan and execute data cleaning pipelines for sequencing, transcriptomics, and metabolomics datasets.

## ✨ Features

- 🤖 **AI-Powered Planning** - Natural language interface to describe data cleaning goals
- 🔄 **Multiple Data Types** - Support for sequencing, transcriptomics, and metabolomics datasets
- 📊 **Interactive TUI** - Modern Rich-based terminal UI with beautiful formatting
- 🔌 **Pluggable LLM Support** - Works with OpenAI GPT models or simulated mode (no API key needed)
- ⚡ **Dry-Run Mode** - Test pipelines without executing external tools
- 📝 **Auto-Generated Reports** - Comprehensive quality reports for all cleaning operations
- 🎯 **Type-Safe** - Built with Pydantic for robust data validation

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install -e .

# With OpenAI support (optional)
pip install -e .[openai]
```

### Basic Usage

1. **Interactive Chat Mode** (Recommended)
   ```bash
   # Start with simulated planner (no API key needed)
   bio-clean-agent chat --dataset-config examples/configs/example.yaml --dry-run

   # With OpenAI GPT (requires API key)
   export OPENAI_API_KEY="your-api-key"
   bio-clean-agent chat --model openai --dataset-config examples/configs/example.yaml
   ```

2. **Direct Pipeline Execution**
   ```bash
   # Run a pipeline with dry-run mode
   bio-clean-agent run examples/configs/example.yaml --dry-run

   # View available models
   bio-clean-agent models
   ```

3. **Create New Dataset Configuration**
   ```bash
   bio-clean-agent init path/to/your/dataset
   ```
   The wizard will guide you through creating a configuration file.

## 💬 Interactive Chat Commands

Once in chat mode, you can use these commands:

- `/help` - Show all available commands
- `/models` - List available AI models
- `/model <key>` - Switch to a different model
- `/auto [on|off]` - Toggle automatic pipeline execution
- `/plan` - Show the last generated plan
- `/execute` - Execute the current plan
- `/exit` or `/quit` - Exit the session

## 📁 Project Structure

```
src/bio_clean_agent/
  ├── agent.py              # Core agent orchestration
  ├── cli.py                # CLI commands
  ├── llm.py                # LLM integration (OpenAI, Simulated)
  ├── wizard.py             # Configuration wizard
  ├── dataspec/
  │   └── models.py         # Dataset schemas (Pydantic)
  ├── pipelines/
  │   ├── base.py           # Pipeline base classes
  │   ├── sequencing.py     # Sequencing pipeline
  │   ├── transcriptomics.py
  │   └── metabolomics.py
  ├── ui/
  │   └── session.py        # Interactive chat session
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
