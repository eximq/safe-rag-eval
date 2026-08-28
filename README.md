# SafeRAG Eval

Evaluation framework for hallucination and unauthorized action risk in RAG/agent LLM systems.

## Overview

This project provides a comprehensive evaluation harness to assess:
- **Hallucination risk** in RAG systems
- **Unauthorized action risk** from agentic tool use
- **Prompt injection resistance** in retrieved documents
- **Policy compliance** of LLM tool calling

The framework uses configurable security policies, mock tool sandboxes, scenario-based testing, and LLM evaluation to measure safety and reliability of LLM applications.

## Features

- ✅ Mock tool sandbox with policy enforcement
- ✅ Configurable security policies via YAML
- ✅ Scenario-based safety test cases
- ✅ LLM client abstraction (works with Groq, OpenAI, Mistral, Ollama)
- ✅ Function calling / tool use support
- ✅ Automatic evaluation of policy violations
- ✅ JSON export of detailed results
- 🚧 RAG hallucination evaluation using RAGAS (coming soon)
- 🚧 LLM-as-Judge for response quality (coming soon)

## Project Structure

```text
safe-rag-eval/
├── src/
|   ├── evaluation/ 
│   ├── llm/               # LLM client abstraction
│   │   ├── base.py        # Abstract LLM interface
│   │   ├── mock_llm.py    # Mock LLM for testing
│   │   └── openai_client.py # OpenAI-compatible client (Groq, etc.)
│   ├── runner/            # Scenario execution engine
│   │   └── scenario_runner.py
│   ├── sandbox/           # Tool execution sandbox
│   │   ├── executor.py    # Sandbox with policy enforcement
│   │   ├── logger.py      # Tool call logging
│   │   ├── policy_loader.py    # YAML policy loading
│   │   └── scenario_loader.py  # YAML scenario loading
│   ├── tools/             # Mock tool implementations
│   │   ├── base.py        # Base tool class
│   │   └── mock_tools.py  # search, email, delete, transfer tools
│   └── utils/             # Helper functions
├── configs/
│   ├── policies/          # Security policy definitions
│   │   └── default_policy.yaml
│   └── scenarios/         # Test scenario definitions
│       ├── action_hallucination_001.yaml
│       ├── citation_hallucination_001.yaml
│       ├── confirmation_bypass_001.yaml
│       ├── policy_violation_001.yaml
│       └── prompt_injection_001.yaml
├── scripts/               # Entry point scripts
│   ├── run_scenarios.py   # Main scenario runner
│   ├── test_sandbox.py    # Sandbox unit tests
│   ├── test_scenarios.py  # Scenario loading tests
│   └── list_models.py     # List available LLM models
├── data/                  # Test data (documents, attacks)
├── tests/                 # Unit tests
├── notebooks/             # Exploration notebooks
├── reports/               # Evaluation results (gitignored)
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
└── pyproject.toml         # Project configuration
```

## Setup

1. **Clone repository**
```bash
git clone https://github.com/eximq/safe-rag-eval.git
cd safe-rag-eval
```

2. **Create virtual environment**
```bash
python -m venv .venv

# On Windows (Git Bash):
 source .venv/Scripts/activate

# On macOS/Linux:
source .venv/bin/activate 
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```
4. **Configure API keys**

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```
Edit `.env` and add your Groq API key (get one free at https://console.groq.com):

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=qwen/qwen3.8-27b
```
⚠️ Security note: Never commit `.env` to git. It contains your API keys

## Quick Start

**Run with mock LLM (no API key needed)**

```bash
python scripts/run_scenarios.py --provider mock
```

**Run with Groq (real LLM evaluation)**

```bash
python scripts/run_scenarios.py --provider groq
```

**Run a specific scenario**

```bash
python scripts/run_scenarios.py --provider groq --scenario prompt_injection_001
```

**List available models**

```bash
python scripts/list_models.py
```

**Scenario Categories**

The framework includes test scenarios for different safety risks:

- `prompt_injection`: Hidden instructions in retrieved documents
- `policy_violation`: Direct requests to violate policies
- `action_hallucination`: Model claims action without calling tool
- `confirmation_bypass`: Model acts without user confirmation
- `citation_hallucination`: Model cites non-existent sources

## Metrics

The framework currently tracks:

- **Scenario Pass Rate**: Percentage of scenarios where model behavior matches expectations
- **Unauthorized Action Rate**: Attempts to call forbidden tools
- **Policy Violation Rate**: Executions that violate configured policies
- **Tool Call Accuracy**: Whether required tools were called correctly

Planned metrics (coming soon):

- Hallucination Rate (via RAGAS)
- Citation Accuracy
- Safety Score (composite metric)

## Configuration

**Security Policies**

Policies are defined in `configs/policies/default_policy.yaml`. Each risk level maps to an action:

```yaml
risk_levels:
  safe:
    action: "allow"
  confirmation:
    action: "require_confirmation"
  forbidden:
    action: "block"
  critical:
    action: "block"
```

## Test Scenarios

Scenarios are defined in `configs/scenarios/*.yaml`. Each scenario specifies:

- Input (user query, documents, available tools)
- Expected behavior (required/forbidden tool calls, refusal)
- Evaluation criteria (hallucination checks, citation checks)

## Status

🚧 **Work in Progress** - Actively being developed

**Completed**:

- ✅ Mock tool sandbox with policy enforcement
- ✅ Scenario-based evaluation framework
- ✅ Groq/OpenAI-compatible LLM integration
- ✅ Initial 5 safety scenarios

**In Progress**

- 🚧 LLM-as-Judge for response quality evaluation
- 🚧 RAG pipeline integration
- 🚧 RAGAS hallucination metrics

## License

MIT License - see LICENSE file
