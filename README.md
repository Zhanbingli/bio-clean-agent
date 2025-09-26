# Bio Clean Agent

An AI-assisted agent framework that plans and executes data cleaning tasks for sequencing, transcriptomics, and metabolomics datasets. The agent interprets high-level requests, chooses the appropriate cleaning pipeline, and orchestrates tool execution while keeping track of metadata and producing a summarized quality report.

## Features
- Dataset metadata schemas with validation for sequencing, transcriptomics, and metabolomics.
- Modular cleaning pipelines with well-defined steps and hooks for external tooling.
- Agent planner with preflight checks that maps user intents to pipeline runs and compiles human-readable summaries.
- Pluggable LLM registry with auto-selection, conversation history, and JSON-repair for robust planning.
- Rich-powered interactive UI with model switching, auto-execution toggles, and resilient command handling.
- Typer CLI for quick experimentation, including dry-run simulation of external tools and planner-driven chat flows.
- Guided onboarding with `bio-clean-agent init` and a VS Code helper extension for new users.

## Getting Started
1. Install dependencies (editable mode recommended):
   ```bash
   pip install -e .[llm]  # include `[llm]` to enable Qwen integration
   ```
2. Run the example scenario:
   ```bash
   python examples/run_agent.py examples/configs/sequencing.yaml --dry-run
   ```
   (Use `--dry-run` to skip executing external binaries during exploration.)

3. Start the interactive planner:
   ```bash
   bio-clean-agent models  # list available planner backends
   bio-clean-agent chat --model qwen --model-path path/to/Qwen3 \
       --dataset-config examples/configs/sequencing.yaml --dry-run
   ```
   Inside the chat type `/help` to discover commands such as `/model`, `/auto`, `/plan`, and `/execute` for a smoother session.

4. Scaffold a dataset config via the wizard:
   ```bash
   bio-clean-agent init path/to/dataset
   ```
   The wizard guesses the dataset type, suggests parameters, and writes a ready-to-use YAML configuration.

5. Want a GUI entry point? Install the helper extension under `tools/vscode/bio-clean-agent-helper` and run
   **Bio Clean Agent: Create Dataset Config** from the VS Code Command Palette.

## Structure
```
src/bio_clean_agent/
  agent.py              # Agent orchestration and planning logic
  cli.py                # Typer CLI entry point
  llm.py                # Qwen integration and planner utilities
  dataspec/
    models.py           # Dataset metadata schemas
  pipelines/
    base.py             # Pipeline abstractions
    sequencing.py       # Sequencing data cleaning pipeline
    transcriptomics.py  # Transcriptomics cleaning pipeline
    metabolomics.py     # Metabolomics cleaning pipeline
  ui/
    session.py          # Rich-powered interactive chat session
  utils/
    logging.py          # Logging helpers
    preflight.py        # Dataset preflight validation
    reporting.py        # Report generation helpers
examples/
  run_agent.py          # Example usage script
  configs/              # Sample configuration files (YAML)
```

## Extending
- Add new pipelines by inheriting from `Pipeline` and defining ordered steps.
- Register the pipeline with the agent via `agent.register_pipeline()` with matching `dataset_type`.
- Provide tool adapters for your environment by overriding the `ToolExecutor` interface.

## License
MIT
