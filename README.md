# IBRAMIND BidBox Agent

Challenge-specific governance agent for the African Agentic AI Design Challenge - Bid Box Challenge.

It prepares an auditable tender-evaluation working file from synthetic/open data using MCP tool calls, while keeping the final procurement judgment with a human reviewer.

## One-command demo

    ./run_demo.sh

Optional open-weights planning path using Ollama and Qwen2.5 0.5B:

    OLLAMA_MODEL=qwen2.5:0.5b ./run_demo.sh --model

## Workflow

Tender package -> requirement/evidence matrix -> unresolved-risk summary -> draft working file -> human approval gate.

It does not award a tender or choose a bidder.

## Challenge safeguards

- Public challenge data is synthetic/open only.
- Every MCP tool call is written into the output audit log.
- FINALIZE_EVALUATION is blocked pending human approval.
- No live tender in progress is included.
- No personal supplier data is included.
- This repository is challenge-period work isolated from the existing IBRAMIND platform.

## Files

- bidbox/server.py - MCP server and tools
- bidbox/agent.py - bounded agent workflow and optional open-weights planner
- data/synthetic_tender.json - safe fixture
- ARCHITECTURE.md - architecture description
- docs/architecture.svg - submission diagram
- EVALS.md - 8+ eval tasks and one unresolved failure
