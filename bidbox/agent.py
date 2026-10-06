from __future__ import annotations
import argparse
import json
import os
import subprocess
import urllib.request
from pathlib import Path

TOOLS = ["load_tender", "build_compliance_matrix", "summarize_risks", "prepare_draft_pack"]

def open_weights_plan(task):
    url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
    prompt = (
        "Plan a public-procurement evidence review. Never award a bidder. "
        "Return JSON with objective and ordered_tools. Allowed tools: "
        + ", ".join(TOOLS) + ". Task: " + task
    )
    body = json.dumps({
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        response = json.loads(r.read().decode())
    return json.loads(response["message"]["content"])

class MCPClient:
    def __init__(self):
        self.proc = subprocess.Popen(
            ["python3", "-m", "bidbox.server"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, bufsize=1
        )
        self.next_id = 1
        self.request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "bidbox-agent", "version": "0.1.0"}
        })
        self.notify("notifications/initialized", {})

    def request(self, method, params):
        mid = self.next_id
        self.next_id += 1
        msg = {"jsonrpc": "2.0", "id": mid, "method": method, "params": params}
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        reply = json.loads(self.proc.stdout.readline())
        if "error" in reply:
            raise RuntimeError(reply["error"]["message"])
        return reply["result"]

    def notify(self, method, params):
        self.proc.stdin.write(json.dumps(
            {"jsonrpc": "2.0", "method": method, "params": params}
        ) + "\n")
        self.proc.stdin.flush()

    def call_tool(self, name, arguments):
        result = self.request("tools/call", {"name": name, "arguments": arguments})
        return json.loads(result["content"][0]["text"])

    def close(self):
        self.proc.terminate()

def run(input_path, output_path, use_model=False):
    log = []
    plan = {"objective": "prepare a cited tender evaluation working file", "ordered_tools": TOOLS}
    if use_model:
        plan = open_weights_plan("Review the synthetic tender and prepare a human-review draft.")
        log.append({"event": "open_weights_model_plan", "plan": plan})

    client = MCPClient()
    try:
        def call(name, arguments):
            value = client.call_tool(name, arguments)
            snapshot = json.loads(json.dumps(value))
            log.append({"event": "mcp_tool_call", "tool": name,
                        "arguments": arguments, "result": snapshot})
            return value

        tender = call("load_tender", {"path": str(Path(input_path).resolve())})
        matrix = call("build_compliance_matrix", {"tender": tender})
        risk = call("summarize_risks", {"matrix": matrix})
        pack = call("prepare_draft_pack", {
            "tender": tender, "matrix": matrix, "risk": risk
        })
    finally:
        client.close()

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
    ap.add_argument("--model", action="store_true")
    a = ap.parse_args()
    pack = run(a.input, a.output, a.model)
    print(json.dumps({
        "tender_id": pack["tender_id"],
        "risk": pack["risk_summary"],
        "status": pack["status"],
        "human_approval": pack["human_approval"]
    }, indent=2))

if __name__ == "__main__":
    main()
