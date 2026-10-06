# IBRAMIND BidBox Agent - Architecture

This challenge build is isolated from the pre-existing IBRAMIND platform.

## Flow

1. Human reviewer supplies an open or synthetic tender package.
2. Agent planner creates a bounded review plan.
3. MCP client invokes the IBRAMIND BidBox MCP server.
4. MCP tools load the package, build a compliance matrix, summarize unresolved risk, and prepare a draft evidence pack.
5. Every call and result is appended to an audit log.
6. A finalization gate remains blocked until a human reviewer approves it.
7. The agent never awards or selects a bidder.

## Components

- Agent/orchestration: Python async state machine, open source in this repo.
- Open-weights model path: Ollama with Qwen2.5 0.5B.
- MCP: official Python MCP SDK with stdio client/server.
- Tools: tender loading, evidence matching, risk summary, draft-pack preparation.
- Data: synthetic JSON only for the public demo.
- Human-in-the-loop: explicit FINALIZE_EVALUATION approval block.
- Evidence: tool-by-tool audit log in the generated output.

See docs/architecture.svg for the submission diagram.
