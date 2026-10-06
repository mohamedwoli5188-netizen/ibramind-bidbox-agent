from __future__ import annotations
import argparse
import asyncio
import json
import os
from pathlib import Path
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TOOL_SEQUENCE = ["load_tender", "build_compliance_matrix", "summarize_risks", "prepare_draft_pack"]

async def model_plan(task: str) -> dict:
    """Use an open-weights model through local Ollama when available."""
    url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
    prompt = (
        "You are planning a public-procurement evidence review. Never award a bidder. "
        "Return JSON with keys objective and ordered_tools. Only use these tools: "
        + ", ".join(TOOL_SEQUENCE) + ". Task: " + task
    )
    async with httpx.AsyncClient(timeout=45) as client:
        r = await client.post(url, json={
            "model": model,
            "stream": False,
            "format": "json",
            "messages": [{"role": "user", "content": prompt}],
        })
        r.raise_for_status()
        return json.loads(r.json()["message"]["content"])

async def run(input_path: str, output_path: str, use_model: bool) -> dict:
    log = []
    plan = {"objective": "prepare a cited tender evaluation working file", "ordered_tools": TOOL_SEQUENCE}
    if use_model:
        plan = await model_plan("Review the synthetic tender package and prepare a human-review draft.")
        log.append({"event": "open_weights_model_plan", "plan": plan})

    server = StdioServerParameters(command="python3", args=["-m", "bidbox.server"])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            async def call(name, args):
                res = await session.call_tool(name, args)
                payload = json.loads(res.content[0].text)
                log.append({"event": "mcp_tool_call", "tool": name, "args": args, "result": payload})
                return payload

            tender = await call("load_tender", {"path": str(Path(input_path).resolve())})
            matrix = await call("build_compliance_matrix", {"tender": tender})
            risk = await call("summarize_risks", {"matrix": matrix})
            pack = await call("prepare_draft_pack", {"tender": tender, "matrix": matrix, "risk": risk})

    pack["agent_plan"] = plan
    pack["audit_log"] = log
    pack["human_approval"] = {
        "required": True,
        "approved": False,
        "blocked_action": "FINALIZE_EVALUATION"
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(pack, indent=2))
    return pack

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/synthetic_tender.json")
    ap.add_argument("--output", default="outputs/evaluation_pack.json")
    ap.add_argument("--model", action="store_true", help="Plan with local open-weights Ollama model.")
    a = ap.parse_args()
    pack = asyncio.run(run(a.input, a.output, a.model))
    print(json.dumps({
        "tender_id": pack["tender_id"],
        "risk": pack["risk_summary"],
        "status": pack["status"],
        "human_approval": pack["human_approval"]
    }, indent=2))

if __name__ == "__main__":
    main()
