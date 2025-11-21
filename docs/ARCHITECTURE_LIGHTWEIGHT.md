# Lightweight Architecture Overview

This project now separates the **core cleaning runtime** from optional surfaces so it stays easy to install and run without pulling extra dependencies.

## Core runtime (always available)
- Agent orchestration: `bio_clean_agent.agent`, `bio_clean_agent.cli`
- Data models: `bio_clean_agent.dataspec`
- Pipelines: sequencing, transcriptomics, metabolomics under `bio_clean_agent.pipelines`
- Utilities: logging, preflight checks, IO, reporting helpers
- LLM planner (simulated/OpenAI) in `bio_clean_agent.llm`

## Optional/extra components
- REST/Web UI: `bio_clean_agent.api` and `bio_clean_agent.web` (FastAPI/uvicorn). Install with `pip install "bio-clean-agent[api]"`.
- Legacy interactive REPL: `bio_clean_agent.interactive` (kept for demos).
- Medical knowledge, observer dashboard, planning/reporting helpers: load on demand only.

All optional modules now fail gracefully with a clear message when dependencies are missing instead of breaking base installs.

## Recommended lightweight usage
```bash
pip install -e .
bio-clean-agent init data/raw.fastq --dataset-type sequencing
bio-clean-agent run configs/example.yaml --dry-run  # use SimulatedToolExecutor
```

To launch the API/Web UI:
```bash
pip install -e ".[api]"
python start_web.py  # or: python -m bio_clean_agent.web.server
```

## Maintenance notes
- `__pycache__` artefacts are removed from `src/` to keep wheels clean.
- FastAPI/uvicorn imports are lazy; importing `bio_clean_agent` no longer requires optional extras.
