# IBRAMIND BidBox Agent

Challenge-specific Governance / **Bid Box** agent for the African Agentic AI Design Challenge.

## Problem statement
African procurement teams often review tender requirements, BOQs, supplier evidence and technical schedules manually across disconnected files. Mandatory requirements can be missed, evidence can be difficult to trace, and evaluation working files can be inconsistent or slow to assemble.

## Solution overview
IBRAMIND BidBox Agent prepares an auditable tender-evaluation working file from **synthetic/open data**. It matches requirements to evidence, flags unresolved compliance risk, preserves provenance, and blocks finalization until a human reviewer approves it. It **does not award a tender or choose a bidder**.

## Target users
Public-procurement officers, evaluation committees, technical consultants, infrastructure owners, auditors and institutional procurement teams.

## Architecture
Human Reviewer → Agent Planner → MCP Client → BidBox MCP Server → Compliance Matrix → Risk Summary → Draft Evidence Pack → Human Approval Gate.

See `ARCHITECTURE.md` and `docs/architecture.svg.png`.

## Agent architecture
The bounded Python agent executes a multi-step review workflow. An optional open-weights planning path can use a local Ollama-compatible Qwen2.5 model. Tool results become state for subsequent steps and are recorded in an audit log.

## MCP implementation
The repository implements Model Context Protocol (MCP) JSON-RPC over stdio between the agent client and the challenge-specific BidBox server. The server exposes four bounded tools:
- `load_tender`
- `build_compliance_matrix`
- `summarize_risks`
- `prepare_draft_pack`

## MCP tools / servers
`bidbox/server.py` is the BidBox MCP server. `bidbox/agent.py` is the client/orchestrator. The public demo accepts only `SYN-*` tender IDs.

## Human-in-the-loop workflow
`FINALIZE_EVALUATION` is blocked by default. The generated pack records `required: true`, `approved: false`, and `blocked_action: FINALIZE_EVALUATION`. Human reviewers remain accountable for procurement decisions.

## Setup / installation
Requires Python 3.10+ for the default demo. No third-party packages are required.

```bash
git clone https://github.com/mohamedwoli5188-netizen/ibramind-bidbox-agent.git
cd ibramind-bidbox-agent
./run_demo.sh
```

Optional open-weights planning mode expects a local Ollama-compatible endpoint and model.

## Usage
Run `./run_demo.sh`. The script executes the evaluation tests and then generates `outputs/evaluation_pack.json`.

## Technology stack
Python · MCP JSON-RPC stdio tools · synthetic JSON data · unittest · GitHub Pages · optional Ollama/Qwen2.5.

## Technical evidence
`tests/test_demo.py` contains nine evaluation cases: eight passing checks and one intentional expected failure showing that missing mandatory bid-security evidence is surfaced rather than fabricated.

## Limitations
The public challenge demo uses a small synthetic fixture and does not connect to live procurement systems, supplier databases or live tender decisions. It is not a substitute for legal, procurement or engineering judgment.

## Future improvements
Add authenticated institutional connectors, document parsing for open tender PDFs/BOQs, richer evidence provenance, multilingual extraction, benchmark datasets, and stronger open-weights planning/evaluation while preserving the same approval boundary.

## Safety
- Synthetic/open challenge data only.
- No personal supplier data in the public fixture.
- No autonomous award decision.
- Every tool result is recorded in the generated audit log.
- Human approval is mandatory for finalization.

## Live demo
GitHub Pages demo: https://mohamedwoli5188-netizen.github.io/ibramind-bidbox-agent/

## Repository
https://github.com/mohamedwoli5188-netizen/ibramind-bidbox-agent
