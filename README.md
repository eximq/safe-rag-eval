# SafeRAG Eval

Evaluation framework for hallucination and unauthorized action risk in RAG/agent LLM systems.

## Overview

This project provides a comprehensive evaluation harness to assess:
- **Hallucination risk** in RAG systems
- **Unauthorized action risk** from agentic tool use
- **Prompt injection resistance** in retrieved documents

The framework uses RAGAS metrics, custom scenarios, mock tool sandboxes, and policy-based evaluation to measure safety and reliability of LLM applications.

## Features

- ✅ RAG hallucination evaluation using RAGAS
- ✅ Unauthorized tool action detection
- ✅ Prompt injection attack scenarios
- ✅ Policy-based safety checks
- ✅ Support for multiple LLM providers (local + API)
- ✅ Automated reporting with metrics

## Project Structure

```text
safe-rag-eval/
├── src/
│   ├── runner/          # Test scenario runner
│   ├── tools/           # Mock tool implementations
│   ├── sandbox/         # Tool execution sandbox
│   ├── evaluation/      # Metrics and judges
│   └── utils/           # Helper functions
├── configs/
│   ├── scenarios/       # Test scenario definitions
│   └── policies/        # Safety policies
├── data/
│   ├── documents/       # RAG documents
│   ├── attacks/         # Attack scenarios
│   └── golden_answers/  # Expected outputs
├── tests/               # Unit tests
├── notebooks/           # Exploration notebooks
└── reports/             # Evaluation reports
```

## Setup

**Clone repository**
```bash
git clone https://github.com/eximq/safe-rag-eval.git
cd safe-rag-eval
```

**Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows (Git Bash): source .venv/Scripts/activate
```

**Install dependencies**
```bash
pip install -r requirements.txt
```

## Quick Start

**Run evaluation**
```bash
python -m src.runner.evaluate --config configs/scenarios/basic.yaml
```

**Generate report**
```bash
python -m src.evaluation.report --output reports/results.json
```

## Supported Models

The project works with any OpenAI-compatible LLM provider. Tested with:

- **Groq**: `qwen/qwen3.8-27b` (recommended), `openai/gpt-oss-20b`
- **OpenAI**: `gpt-4o-mini` (requires API key)

To change the model, update `GROQ_MODEL` or `OPENAI_MODEL` in your `.env` file.

## Metrics

The framework evaluates:

- **Hallucination Rate:** Percentage of responses not grounded in context
- **Unauthorized Action Rate:** Percentage of policy-violating tool calls
- **Prompt Injection ASR:** Attack Success Rate for injection attempts
- **Safety Score:** Composite safety metric

## Status

🚧 **Work in Progress** - Actively being developed

## License

MIT License - see LICENSE file
