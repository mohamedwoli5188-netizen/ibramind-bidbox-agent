import json
import unittest
from pathlib import Path

class BidBoxAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(Path("data/synthetic_tender.json").read_text())

    def test_01_synthetic_only(self):
        self.assertTrue(self.data["tender_id"].startswith("SYN-"))

    def test_02_four_requirements(self):
        self.assertEqual(len(self.data["requirements"]), 4)

    def test_03_bid_security_missing(self):
        self.assertFalse(any("R1" in e["supports"] for e in self.data["supplier_evidence"]))

    def test_04_registration_evidenced(self):
        self.assertTrue(any("R2" in e["supports"] for e in self.data["supplier_evidence"]))

    def test_05_method_evidenced(self):
        self.assertTrue(any("R3" in e["supports"] for e in self.data["supplier_evidence"]))

    def test_06_experience_evidenced(self):
        self.assertTrue(any("R4" in e["supports"] for e in self.data["supplier_evidence"]))

    def test_07_no_personal_data(self):
        self.assertNotIn("@", json.dumps(self.data))

    def test_08_no_live_award(self):
        self.assertNotIn("winner", json.dumps(self.data).lower())

    @unittest.expectedFailure
    def test_09_known_unresolved_failure(self):
        self.assertTrue(
            any("R1" in e["supports"] for e in self.data["supplier_evidence"]),
            "Known failure retained: mandatory bid-security evidence is intentionally missing."
        )

if __name__ == "__main__":
    unittest.main()
