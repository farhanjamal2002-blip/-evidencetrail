import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "static" / "replay-artifacts" / "twelve-pair-summary.json"
DEMO = ROOT / "static" / "demo20.html"


class TwelvePairSummaryTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(SUMMARY.read_text())

    def test_counts_match_published_replay_result(self):
        cases = [c for p in self.data["pairs"] for c in (p["baseline"], p["variant"])]
        self.assertEqual(len(self.data["pairs"]), 12)
        self.assertEqual(len(cases), 24)
        raw = sum(c["raw_muse"] == c["expected"] for c in cases)
        final = sum(c["final"] == c["expected"] for c in cases)
        self.assertEqual((raw, final), (19, 24))
        self.assertEqual(self.data["raw_muse_matches_reference"], raw)
        self.assertEqual(self.data["final_matches_reference"], final)

    def test_every_case_has_a_provider_receipt(self):
        for p in self.data["pairs"]:
            for c in (p["baseline"], p["variant"]):
                self.assertTrue(c["provider_response_id"].startswith("chatcmpl-"), c["case_id"])
                self.assertEqual(c["model"], "muse-spark-1.3")

    def test_m02_matches_the_public_case_audit(self):
        audit = json.loads((ROOT / "static/replay-artifacts/m02-case-audit.json").read_text())
        m02 = next(p for p in self.data["pairs"] if p["pair_id"] == "M02")
        by_id = {c["case_id"]: c for c in audit["cases"]}
        for c in (m02["baseline"], m02["variant"]):
            self.assertEqual(c["provider_response_id"], by_id[c["case_id"]]["provider_response_id"])

    def test_demo_table_rows_match_summary(self):
        html = DEMO.read_text()
        table = html[html.index('<table class="pair-table">'):html.index("</table>", html.index('<table class="pair-table">'))]
        self.assertEqual(len(re.findall(r"<tr(?: class=\"pair-changed\")?><td", table)), 24)
        changed = sum(c["raw_muse"] != c["final"] for p in self.data["pairs"] for c in (p["baseline"], p["variant"]))
        self.assertEqual(table.count('class="pair-changed"'), changed)


if __name__ == "__main__":
    unittest.main()
