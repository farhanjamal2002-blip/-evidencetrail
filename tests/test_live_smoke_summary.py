"""No-network checks for the live smoke script's sanitized report builder."""

from __future__ import annotations

import json
import unittest

from scripts.live_smoke_test import safe_live_summary


class LiveSmokeSummaryTests(unittest.TestCase):
    def test_report_shows_calibration_and_retains_rejected_quotes_only(self) -> None:
        result = {
            "provider_mode": "muse",
            "model": "muse-spark-1.3",
            "analysis_calls": 2,
            "requirements": [
                {
                    "id": "R1",
                    "requirement": "At least five years of Python experience",
                    "status": "supported",
                    "evidence_type": "direct",
                    "certainty": "clear",
                    "evidence": [{"quote": "private fictional quote", "page": 1}],
                },
                {
                    "id": "R2",
                    "requirement": "Current certification",
                    "status": "not_found",
                    "evidence_type": "unsupported",
                    "certainty": "clear",
                    "evidence": [],
                },
                {
                    "id": "R3",
                    "requirement": "Seven years procurement experience",
                    "status": "conflicting",
                    "evidence_type": "conflicting",
                    "certainty": "ambiguous",
                    "evidence": [{"quote": "another private quote", "page": 2}],
                },
                {
                    "id": "R4",
                    "requirement": "Negotiate regional supply agreements",
                    "status": "supported",
                    "evidence_type": "related",
                    "certainty": "clear",
                    "transfer_explanation": "Supplier pricing experience may transfer.",
                    "unproven_aspects": ["multi-year agreement ownership"],
                    "evidence": [{"quote": "a third private quote", "page": 2}],
                },
            ],
            "job_item_coverage": {"matched": 4, "needs_review": 0},
            "quote_audit": {
                "proposed": 4,
                "verified": 3,
                "excluded": 1,
                "verification_proposed": 3,
                "verification_verified": 3,
                "verification_excluded": 0,
                "ambiguous_requirements": 1,
                "retrieved_source_spans": 8,
            },
            "verification_audit": {
                "rejected_citations": [{
                    "requirement_id": "R2",
                    "requirement": "Current certification",
                    "quote": "The OCR proposal crossed two scan columns.",
                    "cited_page": 1,
                    "reason": "quote_not_found_on_cited_page",
                }],
            },
            "usage": {
                "input_tokens": 1800,
                "output_tokens": 700,
                "first_pass": {"input_tokens": 1000, "output_tokens": 400},
                "verification_pass": {"input_tokens": 800, "output_tokens": 300},
            },
            "ocr_pages": [],
        }

        summary, warnings = safe_live_summary(result)
        serialized = json.dumps(summary)

        self.assertEqual(warnings, [])
        self.assertEqual(summary["status_coverage"], {
            "supported": 2,
            "not_found": 1,
            "conflicting": 1,
        })
        self.assertEqual(summary["evidence_type_coverage"]["related"], 1)
        self.assertEqual(summary["usage_by_pass"]["verification_pass"]["input_tokens"], 800)
        self.assertEqual(summary["quote_audit"]["verification_excluded"], 0)
        self.assertEqual(summary["rejected_quote_details"], [{
            "requirement_id": "R2",
            "requirement": "Current certification",
            "quote": "The OCR proposal crossed two scan columns.",
            "cited_page": 1,
            "reason": "quote_not_found_on_cited_page",
        }])
        self.assertNotIn("private fictional quote", serialized)
        self.assertNotIn("another private quote", serialized)
        self.assertNotIn("a third private quote", serialized)

    def test_summary_warns_on_status_without_citation_and_missing_cases(self) -> None:
        result = {
            "provider_mode": "muse",
            "model": "muse-spark-1.3",
            "analysis_calls": 2,
            "requirements": [
                {
                    "id": "R1",
                    "requirement": "Five years Python",
                    "status": "supported",
                    "evidence_type": "direct",
                    "certainty": "clear",
                    "evidence": [],
                }
            ],
        }

        summary, warnings = safe_live_summary(result)

        self.assertEqual(summary["status_coverage"]["supported"], 1)
        self.assertTrue(any("without verified evidence" in warning for warning in warnings))
        self.assertTrue(any("did not produce all evidence-type calibration cases" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()
