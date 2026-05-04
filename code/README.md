# Support Triage Agent

A terminal-based multi-domain support triage agent for HackerRank, Claude, and Visa support tickets.

## Architecture

```
main.py        – CLI entry point, reads input CSV, writes output CSV
agent.py       – SupportAgent: orchestrates retrieval + Claude API
corpus.py      – Corpus loader (JSON/TXT/MD files) + BM25-lite retriever
```

### How it works

1. **Corpus Loading** (`corpus.py`): Recursively reads all files in `data/` (JSON articles, text files, markdown). Builds an in-memory TF-IDF index for retrieval — no network, no embeddings, no vector DB required.

2. **Retrieval**: For each ticket, retrieves the top-5 most relevant corpus snippets using BM25-lite scoring, preferring the ticket's domain (hackerrank/claude/visa) with a global fallback.

3. **Triage + Response** (`agent.py`): Sends the ticket + retrieved snippets to `claude-sonnet-4-20250514` with a structured system prompt. The model outputs a strict JSON object:
   - `status` → `replied` | `escalated`
   - `product_area` → domain-specific category
   - `response` → grounded user-facing reply
   - `justification` → internal routing rationale
   - `request_type` → `product_issue` | `feature_request` | `bug` | `invalid`

4. **Safety guards** (pre-LLM, in-code):
   - Hard-reject harmful system commands (delete all files, exploits, etc.)
   - Keyword-based escalation pre-flagging for fraud, security, outages
   - JSON parse fallback → auto-escalate on parse failure

## Requirements

- Python 3.10+
- `anthropic` Python SDK
- `ANTHROPIC_API_KEY` environment variable

## Installation

```bash
cd code/
pip install anthropic
```

## Usage

```bash
# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run on the main support_issues.csv
python main.py

# Run on sample tickets (with expected outputs, for validation)
python main.py --sample

# Process a single ticket (0-indexed) for debugging
python main.py --ticket 0

# Custom paths
python main.py --input ../support_issues/support_issues.csv --output ../support_issues/output.csv
```

Output is written to `support_issues/output.csv`.

## Design decisions

| Decision | Rationale |
|---|---|
| BM25-lite (no embeddings) | Zero extra dependencies, fast, deterministic, works offline |
| Domain-filter retrieval | Improves precision; tickets tagged with a company get domain-specific docs first |
| Structured JSON output | Enables reliable parsing + validation without brittle regex |
| Pre-LLM safety guards | Catches harmful requests before spending API tokens |
| Escalation-first on ambiguity | Safer than hallucinating policies on sensitive issues |
| Retry with exponential backoff | Handles transient rate limits gracefully |

## Environment variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Required. Your Anthropic API key. |
