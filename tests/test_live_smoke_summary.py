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
            "analysis_calls": 1,
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
                "analysis_pass": {
                    "input_tokens": 1800,
                    "output_tokens": 700,
                    "cached_input_tokens": 1200,
                    "reasoning_tokens": 450,
                    "api_latency_ms": 1250,
                    "cv_text_characters": 920,
                    "cv_page_count": 2,
                    "cv_ocr_page_count": 1,
                },
                "local_verification": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "mode": "local_deterministic",
                },
            },
            "performance_ms": {
                "pdf_extract_and_ocr_ms": 240,
                "pdf_ocr_execution_ms": None,
                "muse_api_ms": 18000,
                "muse_prompt_build_ms": 4,
                "local_quote_verification_ms": 3,
            },
            "ocr_pages": [],
        }

        summary, warnings = safe_live_summary(result, "medium")
        serialized = json.dumps(summary)

        self.assertEqual(warnings, [])
        self.assertEqual(summary["status_coverage"], {
            "supported": 2,
            "not_found": 1,
            "conflicting": 1,
        })
        self.assertEqual(summary["reasoning_effort"], "medium")
        self.assertEqual(summary["evidence_type_coverage"]["related"], 1)
        self.assertEqual(summary["usage_by_stage"]["muse_analysis"]["input_tokens"], 1800)
        self.assertEqual(summary["usage_by_stage"]["muse_analysis"]["cached_input_tokens"], 1200)
        self.assertEqual(summary["usage_by_stage"]["muse_analysis"]["reasoning_tokens"], 450)
        self.assertEqual(summary["usage_by_stage"]["muse_analysis"]["api_latency_ms"], 1250)
        self.assertEqual(summary["usage_by_stage"]["muse_analysis"]["cv_text_characters"], 920)
        self.assertEqual(summary["usage_by_stage"]["muse_analysis"]["cv_ocr_page_count"], 1)
        self.assertEqual(summary["performance_ms"]["muse_api_ms"], 18000)
        self.assertIsNone(summary["performance_ms"]["pdf_ocr_execution_ms"])
        self.assertEqual(summary["usage_by_stage"]["local_verification"]["mode"], "local_deterministic")
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
            "analysis_calls": 1,
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
