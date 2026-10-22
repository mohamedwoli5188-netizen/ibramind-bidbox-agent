from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = (ROOT / "data").resolve()
MAX_FIXTURE_BYTES = 256 * 1024
MAX_MESSAGE_BYTES = 1024 * 1024

TOOL_SCHEMAS = {
    "load_tender": {"type":"object","properties":{"path":{"type":"string","description":"Bundled synthetic JSON fixture under data/"}},"required":["path"],"additionalProperties":False},
    "build_compliance_matrix": {"type":"object","properties":{"tender":{"type":"object"}},"required":["tender"],"additionalProperties":False},
    "summarize_risks": {"type":"object","properties":{"matrix":{"type":"array"}},"required":["matrix"],"additionalProperties":False},
    "prepare_draft_pack": {"type":"object","properties":{"tender":{"type":"object"},"matrix":{"type":"array"},"risk":{"type":"object"}},"required":["tender","matrix","risk"],"additionalProperties":False}
}
TOOLS = {
    "load_tender": "Load a bundled synthetic JSON tender; arbitrary host file access is prohibited.",
    "build_compliance_matrix": "Match synthetic tender requirements to evidence; no award decision.",
    "summarize_risks": "Summarize missing evidence; no award decision.",
    "prepare_draft_pack": "Prepare a governed draft only; finalization is prohibited."
}

def check_tender(tender):
    if not isinstance(tender, dict) or not isinstance(tender.get("tender_id"), str) or not tender["tender_id"].startswith("SYN-"):
        raise ValueError("Only synthetic SYN-* tender IDs are allowed")
    if not isinstance(tender.get("requirements"), list) or not isinstance(tender.get("supplier_evidence"), list):
        raise ValueError("Invalid tender data")
    if len(tender["requirements"]) > 500 or len(tender["supplier_evidence"]) > 1000:
        raise ValueError("Synthetic fixture too large")
    for req in tender["requirements"]:
        if not isinstance(req, dict) or not isinstance(req.get("id"), str) or not isinstance(req.get("text"), str):
            raise ValueError("Invalid synthetic requirement")
    for ev in tender["supplier_evidence"]:
        if not isinstance(ev, dict) or not isinstance(ev.get("id"), str) or not isinstance(ev.get("source"), str) or not isinstance(ev.get("supports"), list):
            raise ValueError("Invalid synthetic evidence")
    return tender

def load_tender(args):
    requested = args["path"]
    if not isinstance(requested, str) or not requested or len(requested) > 240:
        raise ValueError("Invalid fixture path")
    path = (ROOT / requested).resolve()
    if not path.is_relative_to(DATA_ROOT) or path.suffix.lower() != ".json":
        raise ValueError("Only bundled data/*.json fixtures are permitted")
    if not path.is_file() or path.stat().st_size > MAX_FIXTURE_BYTES:
        raise ValueError("Fixture missing or exceeds size limit")
    return check_tender(json.loads(path.read_text(encoding="utf-8")))

def build_compliance_matrix(args):
    tender = check_tender(args["tender"])
    supported = {}
    for ev in tender["supplier_evidence"]:
        for rid in ev["supports"]:
            supported.setdefault(rid, []).append({"evidence_id": ev["id"], "source": ev["source"]})
    rows = []
    for req in tender["requirements"]:
        evidence = supported.get(req["id"], [])
        rows.append({"requirement_id": req["id"], "requirement": req["text"],
                     "mandatory": bool(req.get("mandatory")), "status": "EVIDENCED" if evidence else "MISSING_EVIDENCE",
                     "evidence": evidence, "human_review_required": True})
    return rows

def summarize_risks(args):
    matrix = args["matrix"]
    if not isinstance(matrix, list) or len(matrix) > 500:
        raise ValueError("Invalid compliance matrix")
    if any(not isinstance(r, dict) or r.get("status") not in ("MISSING_EVIDENCE", "EVIDENCED")
           or not isinstance(r.get("mandatory"), bool) or not isinstance(r.get("requirement_id"), str) for r in matrix):
        raise ValueError("Invalid matrix row")
    missing = [r for r in matrix if r["status"] == "MISSING_EVIDENCE"]
    mandatory = [r for r in missing if r["mandatory"]]
    return {"missing_count": len(missing), "mandatory_missing_count": len(mandatory),
            "risk_level": "HIGH" if mandatory else ("MEDIUM" if missing else "LOW"),
            "unresolved_requirements": [r["requirement_id"] for r in missing], "decision": "NO_AWARD_DECISION_MADE"}

def prepare_draft_pack(args):
    tender = check_tender(args["tender"])
    if not isinstance(args["matrix"], list) or not isinstance(args["risk"], dict):
        raise ValueError("Invalid draft input")
    computed_matrix = build_compliance_matrix({"tender": tender})
    computed_risk = summarize_risks({"matrix": computed_matrix})
    if args["matrix"] != computed_matrix or args["risk"] != computed_risk:
        raise ValueError("Draft evidence must match synthetic source")
    return {"tender_id": tender["tender_id"], "title": tender["title"], "matrix": computed_matrix,
            "risk_summary": computed_risk, "status": "DRAFT_AWAITING_HUMAN_APPROVAL",
            "human_approval": {"required": True, "approved": False, "blocked_action": "FINALIZE_EVALUATION"},
            "provenance": "Bundled synthetic fixture only; human review required"}


HANDLERS = {
    "load_tender": load_tender,
    "build_compliance_matrix": build_compliance_matrix,
    "summarize_risks": summarize_risks,
    "prepare_draft_pack": prepare_draft_pack,
}

def respond(msg):
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
        return {"jsonrpc":"2.0","id":None,"error":{"code":-32600,"message":"Invalid JSON-RPC request"}}
    method, mid = msg.get("method"), msg.get("id")
    if isinstance(method, str) and method.startswith("notifications/") and "id" not in msg:
        return None
    if method == "initialize":
        result = {"protocolVersion":"2025-06-18","capabilities":{"tools":{}},
                  "serverInfo":{"name":"ibramind-bidbox-mcp","version":"0.2.0"}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools":[{"name":n,"description":d,"inputSchema":TOOL_SCHEMAS[n]} for n,d in TOOLS.items()]}
    elif method == "tools/call":
        params = msg.get("params")
        if not isinstance(params, dict) or params.get("name") not in HANDLERS:
            return {"jsonrpc":"2.0","id":mid,"error":{"code":-32602,"message":"Unknown tool or invalid parameters"}}
        name, args = params["name"], params.get("arguments", {})
        schema = TOOL_SCHEMAS[name]
        if not isinstance(args, dict) or set(args)-set(schema["properties"]) or any(k not in args for k in schema["required"]):
            result = {"content":[{"type":"text","text":"Invalid tool arguments"}],"isError":True}
        else:
            try:
                value = HANDLERS[name](args)
                result = {"content":[{"type":"text","text":json.dumps(value)}],"isError":False}
            except (ValueError, KeyError, TypeError, OSError) as exc:
                result = {"content":[{"type":"text","text":"Tool rejected input: "+type(exc).__name__}],"isError":True}
    else:
        return {"jsonrpc":"2.0","id":mid,"error":{"code":-32601,"message":"Method not found"}}
    return {"jsonrpc":"2.0","id":mid,"result":result}

def main():
    for line in sys.stdin.buffer:
        if len(line) > MAX_MESSAGE_BYTES:
            output = {"jsonrpc":"2.0","id":None,"error":{"code":-32600,"message":"Request too large"}}
        else:
            try:
                output = respond(json.loads(line))
            except (ValueError, UnicodeDecodeError):
                output = {"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":"Parse error"}}
        if output is not None:
            print(json.dumps(output), flush=True)

if __name__ == "__main__":
    main()
