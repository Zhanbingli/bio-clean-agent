# Bio Clean Agent

AI-powered clinical data cleaning and quality assessment tool built with TypeScript.

## Features

- **ISO 8000 Data Quality Assessment** - Comprehensive quality scoring across 6 dimensions: completeness, validity, consistency, uniqueness, timeliness, and accuracy
- **Evidence-Based Issue Detection** - Identifies data quality issues with medical knowledge-backed analysis
- **Smart Duplicate Removal** - Deduplication with full audit trail and lineage tracking
- **Missing Value Handling** - Evidence-based imputation strategies for clinical data fields
- **FDA 21 CFR Part 11 Audit Trail** - Immutable operation records for regulatory compliance
- **LLM-Powered Interactive REPL** - Conversational data cleaning assistant via Vercel AI SDK
- **Real-Time Job Monitoring** - WebSocket-based progress tracking for long-running pipelines

## Architecture

Turborepo monorepo with 4 packages:

```
packages/
  core/   @bio-clean/core   - Schemas, knowledge base, processing engine, quality assessor
  api/    @bio-clean/api    - NestJS REST API + WebSocket gateway
  web/    @bio-clean/web    - Next.js dashboard with real-time monitoring
  cli/    @bio-clean/cli    - Command-line tool with LLM interactive mode
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Node.js + TypeScript |
| Backend | NestJS |
| Frontend | Next.js 15 + React 19 + Tailwind CSS + shadcn/ui |
| Validation | Zod |
| Statistics | simple-statistics |
| LLM | Vercel AI SDK (@ai-sdk/openai) |
| WebSocket | Socket.io |
| CLI | Commander.js + chalk + ora |
| Testing | Vitest |
| Monorepo | Turborepo + pnpm |

## Quick Start

### Prerequisites

- Node.js >= 18
- pnpm >= 9

### Install & Build

```bash
pnpm install
pnpm build
```

### Run CLI

```bash
# Run the full cleaning pipeline
cd packages/cli
pnpm dev -- run data/sample.csv --type clinical --output ./output

# Interactive LLM mode (requires OPENAI_API_KEY or DEEPSEEK_API_KEY)
pnpm dev -- interactive

# Setup wizard
pnpm dev -- wizard
```

### Start API Server

```bash
cd packages/api
pnpm dev
# API runs on http://localhost:3000
```

### Start Web Dashboard

```bash
cd packages/web
pnpm dev
# Dashboard runs on http://localhost:3001
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /upload | Upload CSV data file |
| POST | /analyze | Run quality analysis |
| POST | /jobs | Create cleaning job |
| GET | /jobs | List all jobs |
| GET | /jobs/:id | Get job details |
| PUT | /jobs/:id/decisions/:did | Resolve decision point |
| DELETE | /jobs/:id | Cancel job |
| GET | /knowledge/standards | Browse medical standards |
| WS | /ws/:clientId | Real-time job updates |

## Environment Variables

```bash
# LLM Provider (choose one)
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...

# API Server
PORT=3000
ALLOWED_ORIGINS=http://localhost:3001

# Optional
API_KEY=your-api-key      # Protect API endpoints
LOG_LEVEL=info
```

## Project Structure

```
packages/core/src/
  schemas/        Zod schemas for datasets, jobs, quality reports, audit entries
  knowledge/      Medical standards, evidence-based strategies, validation rules
  quality/        ISO 8000 data quality assessor
  processing/     Clinical trial data handler and cleaning pipeline
  planning/       Smart execution planner
  decisions/      Decision strategies (auto-approve, notify, LLM-assisted)
  events/         Event stream for real-time progress
  agent.ts        Main orchestrator
```

## License

MIT
