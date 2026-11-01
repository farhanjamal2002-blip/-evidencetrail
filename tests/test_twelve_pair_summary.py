import json
import html
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

    def test_quote_audit_totals_and_source_context_match_existing_receipts(self):
        audit = json.loads((ROOT / "static/replay-artifacts/twelve-pair-quote-audit.json").read_text(encoding="utf-8"))
        cases = {c["case_id"]: c for p in self.data["pairs"] for c in (p["baseline"], p["variant"])}
        self.assertEqual({r["case_id"] for r in audit["cases"]}, set(cases))
        self.assertEqual(len(audit["cases"]), 24)
        citations = []
        for row in audit["cases"]:
            self.assertEqual(row["provider_response_id"], cases[row["case_id"]]["provider_response_id"])
            self.assertEqual(len(row["verified_citations"]), row["quote_grounding"]["verified"])
            self.assertTrue(all(q["source_verified"] and q["page"] >= 1 for q in row["verified_citations"]))
            citations.extend(row["verified_citations"])
        self.assertEqual(len(citations), 25)
        self.assertEqual(audit["quote_grounding_totals"], {"proposed": 25, "verified": 25, "excluded": 0})
        changed = [(c["raw_muse"], c["final"]) for c in cases.values() if c["raw_muse"] != c["final"]]
        self.assertEqual(changed, [("conflicting", "not_found")] * 5)

    def test_table_exposes_requirements_and_additional_verified_context(self):
        document = DEMO.read_text(encoding="utf-8")
        audit = json.loads((ROOT / "static/replay-artifacts/twelve-pair-quote-audit.json").read_text(encoding="utf-8"))
        self.assertEqual(document.count('class="pair-requirement"'), 24)
        for pair in self.data["pairs"]:
            self.assertIn("Requirement: " + html.escape(pair["requirement"]), document)
        for row in audit["cases"]:
            if len(row["verified_citations"]) > 1:
                for citation in row["verified_citations"]:
                    self.assertIn(html.escape(citation["quote"]), document)


if __name__ == "__main__":
    unittest.main()
