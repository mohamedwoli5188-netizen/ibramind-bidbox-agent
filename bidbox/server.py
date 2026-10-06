from __future__ import annotations
import json
import sys
from pathlib import Path

TOOLS = {
    "load_tender": "Load a synthetic/open tender package from JSON.",
    "build_compliance_matrix": "Match tender requirements to supplied evidence.",
    "summarize_risks": "Summarize unresolved compliance risk.",
    "prepare_draft_pack": "Prepare a draft evaluation working file."
}

def load_tender(args):
    p = Path(args["path"]).resolve()
    data = json.loads(p.read_text())
    if not str(data.get("tender_id", "")).startswith("SYN-"):
        raise ValueError("Demo safety gate: only SYN-* tender IDs are accepted.")
    return data

def build_compliance_matrix(args):
    tender = args["tender"]
    supported = {}
    for ev in tender.get("supplier_evidence", []):
        for rid in ev.get("supports", []):
            supported.setdefault(rid, []).append(
                {"evidence_id": ev["id"], "source": ev["source"]}
            )
    rows = []
    for req in tender.get("requirements", []):
        evidence = supported.get(req["id"], [])
        rows.append({
            "requirement_id": req["id"],
            "requirement": req["text"],
            "mandatory": bool(req.get("mandatory")),
            "status": "EVIDENCED" if evidence else "MISSING_EVIDENCE",
            "evidence": evidence,
            "human_review_required": True
        })
    return rows

def summarize_risks(args):
    matrix = args["matrix"]
    missing = [r for r in matrix if r["status"] == "MISSING_EVIDENCE"]
    mandatory = [r for r in missing if r["mandatory"]]
    return {
        "missing_count": len(missing),
        "mandatory_missing_count": len(mandatory),
        "risk_level": "HIGH" if mandatory else ("MEDIUM" if missing else "LOW"),
        "unresolved_requirements": [r["requirement_id"] for r in missing],
        "decision": "NO_AWARD_DECISION_MADE"
    }

def prepare_draft_pack(args):
    return {
        "tender_id": args["tender"]["tender_id"],
        "title": args["tender"]["title"],
        "matrix": args["matrix"],
        "risk_summary": args["risk"],
        "status": "DRAFT_AWAITING_HUMAN_APPROVAL",
        "provenance": "Synthetic/open data processed through logged MCP tool calls."
    }

HANDLERS = {
    "load_tender": load_tender,
    "build_compliance_matrix": build_compliance_matrix,
    "summarize_risks": summarize_risks,
    "prepare_draft_pack": prepare_draft_pack,
}

def respond(msg):
    method = msg.get("method")
    mid = msg.get("id")
    if method == "initialize":
        result = {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "ibramind-bidbox-mcp", "version": "0.1.0"}
        }
    elif method == "tools/list":
        result = {
            "tools": [
                {
                    "name": name,
                    "description": desc,
                    "inputSchema": {"type": "object", "additionalProperties": True}
                }
                for name, desc in TOOLS.items()
            ]
        }
    elif method == "tools/call":
        params = msg.get("params", {})
        name = params["name"]
        value = HANDLERS[name](params.get("arguments", {}))
        result = {
            "content": [{"type": "text", "text": json.dumps(value)}],
            "isError": False
        }
    elif method == "notifications/initialized":
        return None
    else:
        raise ValueError("Unsupported MCP method: " + str(method))
    return {"jsonrpc": "2.0", "id": mid, "result": result}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            out = respond(json.loads(line))
            if out is not None:
                print(json.dumps(out), flush=True)
        except Exception as e:
            mid = None
            try:
                mid = json.loads(line).get("id")
            except Exception:
                pass
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": mid,
                "error": {"code": -32000, "message": str(e)}
            }), flush=True)

if __name__ == "__main__":
    main()
