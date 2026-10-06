from __future__ import annotations
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("IBRAMIND BidBox MCP")

@mcp.tool()
def load_tender(path: str) -> dict:
    """Load a synthetic/open tender package from JSON."""
    p = Path(path).resolve()
    data = json.loads(p.read_text())
    if not str(data.get("tender_id", "")).startswith("SYN-"):
        raise ValueError("Demo safety gate: only SYN-* tender IDs are accepted.")
    return data

@mcp.tool()
def build_compliance_matrix(tender: dict) -> list[dict]:
    """Match stated tender requirements to supplied evidence without awarding a bidder."""
    supported = {}
    for ev in tender.get("supplier_evidence", []):
        for rid in ev.get("supports", []):
            supported.setdefault(rid, []).append({"evidence_id": ev["id"], "source": ev["source"]})
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

@mcp.tool()
def summarize_risks(matrix: list[dict]) -> dict:
    """Summarize unresolved compliance risk for human reviewers."""
    missing = [r for r in matrix if r["status"] == "MISSING_EVIDENCE"]
    mandatory_missing = [r for r in missing if r["mandatory"]]
    return {
        "missing_count": len(missing),
        "mandatory_missing_count": len(mandatory_missing),
        "risk_level": "HIGH" if mandatory_missing else ("MEDIUM" if missing else "LOW"),
        "unresolved_requirements": [r["requirement_id"] for r in missing],
        "decision": "NO_AWARD_DECISION_MADE"
    }

@mcp.tool()
def prepare_draft_pack(tender: dict, matrix: list[dict], risk: dict) -> dict:
    """Prepare a draft working file. Finalization remains blocked pending human approval."""
    return {
        "tender_id": tender["tender_id"],
        "title": tender["title"],
        "matrix": matrix,
        "risk_summary": risk,
        "status": "DRAFT_AWAITING_HUMAN_APPROVAL",
        "provenance": "Generated from synthetic/open challenge data via logged MCP tool calls."
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
