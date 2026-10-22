"""Security and protocol regressions for the public synthetic MCP showcase."""
import json
import unittest
from bidbox.server import respond, load_tender, build_compliance_matrix, summarize_risks, prepare_draft_pack

class MCPHardeningTests(unittest.TestCase):
    def invoke(self, name, arguments):
        return respond({"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":name,"arguments":arguments}})

    def test_initialize_and_tool_schemas(self):
        r=respond({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}})
        self.assertEqual(r["result"]["protocolVersion"], "2025-06-18")
        listed=respond({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})["result"]["tools"]
        self.assertEqual(len(listed),4)
        self.assertTrue(all(not t["inputSchema"]["additionalProperties"] for t in listed))

    def test_reject_traversal(self):
        self.assertTrue(self.invoke("load_tender",{"path":"../LICENSE"})["result"]["isError"])

    def test_reject_absolute_outside_path(self):
        self.assertTrue(self.invoke("load_tender",{"path":"/etc/passwd"})["result"]["isError"])

    def test_reject_unknown_tool(self):
        self.assertEqual(self.invoke("FINALIZE_EVALUATION",{})["error"]["code"],-32602)

    def test_reject_extra_tool_arguments(self):
        self.assertTrue(self.invoke("load_tender",{"path":"data/synthetic_tender.json","unsafe":True})["result"]["isError"])

    def test_synthetic_draft_requires_review(self):
        tender=load_tender({"path":"data/synthetic_tender.json"})
        matrix=build_compliance_matrix({"tender":tender})
        risk=summarize_risks({"matrix":matrix})
        draft=prepare_draft_pack({"tender":tender,"matrix":matrix,"risk":risk})
        self.assertEqual(risk["mandatory_missing_count"],1)
        self.assertEqual(draft["status"],"DRAFT_AWAITING_HUMAN_APPROVAL")
        self.assertFalse(draft["human_approval"]["approved"])

    def test_tampered_risk_is_rejected(self):
        tender=load_tender({"path":"data/synthetic_tender.json"})
        matrix=build_compliance_matrix({"tender":tender})
        risk=summarize_risks({"matrix":matrix})
        risk["risk_level"]="LOW"
        with self.assertRaises(ValueError):
            prepare_draft_pack({"tender":tender,"matrix":matrix,"risk":risk})

    def test_invalid_row_rejected(self):
        with self.assertRaises(ValueError):
            summarize_risks({"matrix":[{"status":"MISSING_EVIDENCE"}]})

    def test_invalid_jsonrpc_method(self):
        self.assertEqual(respond({"jsonrpc":"2.0","id":3,"method":"other"})["error"]["code"],-32601)

if __name__=="__main__":
    unittest.main()
