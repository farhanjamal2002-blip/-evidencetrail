"""Offline checks for the public-JD, fictional-CV calibration harness."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.evaluate_semantic_cases import align_findings, make_case_pdf, score_case
from app import attach_timeline_review_flags, build_report, extract_pdf
import fitz


ROOT = Path(__file__).resolve().parents[1]


class SemanticCalibrationTests(unittest.TestCase):
    def test_public_case_set_has_diverse_jobs_and_only_fictional_candidates(self) -> None:
        fixture = json.loads((ROOT / "calibration" / "semantic_cases.json").read_text())
        cases = fixture["cases"]
        self.assertGreaterEqual(len(cases), 3)
        self.assertGreaterEqual(len({case["industry"] for case in cases}), 3)
        self.assertTrue(all("FICTIONAL CV" in str(case["cv_pages"]) for case in cases))
        self.assertTrue(all(case["job_source"]["url"].startswith("https://") for case in cases))

    def test_credential_boundary_case_keeps_adjacent_work_separate_from_mcips(self) -> None:
        fixture = json.loads((ROOT / "calibration" / "semantic_cases.json").read_text())
        case = next(
            case for case in fixture["cases"]
            if case["id"] == "nhs_procurement_director_credential_boundary"
        )
        labels = {item["requirement"]: item["evidence_type"] for item in case["expected"]}
        self.assertEqual(labels["MCIPS professional qualification."], "unsupported")
        self.assertEqual(labels["MBA or MSc or other higher degree or equivalent."], "direct")
        self.assertEqual(
            labels["Expert knowledge of procurement, UK and EU legislation and regulations."],
            "related",
        )

    def test_strength_ladder_demo_pairs_keyword_filler_with_specific_work_example(self) -> None:
        fixture = json.loads((ROOT / "calibration" / "strength_ladder_demo.json").read_text())
        self.assertEqual(len(fixture["candidates"]), 2)
        self.assertEqual(
            [item["expected_evidence_strength"] for item in fixture["candidates"]],
            ["keyword_only", "specific"],
        )
        filler = fixture["candidates"][0]["cv_pages"][0]
        self.assertIn(
            "Results-driven contracts professional with a proven track record of delivering value through strategic procurement excellence.",
            filler,
        )
        for candidate in fixture["candidates"]:
            extracted = extract_pdf(make_case_pdf(candidate))
            self.assertTrue(extracted[0]["text"].strip())

    def test_scanned_two_column_case_runs_ocr_and_reports_ocr_pages(self) -> None:
        fixture = json.loads((ROOT / "calibration" / "semantic_cases.json").read_text())
        case = next(
            case for case in fixture["cases"]
            if case["id"] == "scanned_cv_procurement_credential_boundary"
        )
        pdf = make_case_pdf(case)
        document = fitz.open(stream=pdf, filetype="pdf")
        self.assertEqual(document[0].get_text().strip(), "")
        self.assertEqual(len(document[0].get_images(full=True)), 1)
        document.close()

        pages = extract_pdf(pdf)
        self.assertTrue(pages[0]["ocr_used"])
        normalized_ocr = " ".join(pages[0]["text"].casefold().split())
        self.assertIn("no mcips", normalized_ocr)
        self.assertIn("qualification is listed", normalized_ocr)
        report, _totals = score_case(case, {"requirements": [], "ocr_pages": [1]})
        self.assertTrue(report["ocr_used"])
        self.assertEqual(report["ocr_pages"], [1])

    def test_scoring_counts_false_transfer_missed_transfer_and_overclaim(self) -> None:
        case = {
            "id": "fixture",
            "industry": "test",
            "level": "test",
            "expected": [
                {"requirement": "Manage supplier recovery plans", "evidence_type": "related"},
                {"requirement": "Current public procurement license", "evidence_type": "unsupported"},
                {"requirement": "Minimum eight years in role", "evidence_type": "related"},
            ],
        }
        result = {
            "requirements": [
                {
                    "requirement": "Manage supplier recovery plans",
                    "job_source": {"text": "Manage supplier recovery plans"},
                    "evidence_type": "direct",
                    "evidence_strength": "specific",
                    "certainty": "clear",
                },
                {
                    "requirement": "Current public procurement license",
                    "job_source": {"text": "Current public procurement license"},
                    "evidence_type": "related",
                    "evidence_strength": "keyword_only",
                    "certainty": "ambiguous",
                },
                {
                    "requirement": "Minimum eight years in role",
                    "job_source": {"text": "Minimum eight years in role"},
                    "evidence_type": "unsupported",
                    "evidence_strength": "none",
                    "certainty": "ambiguous",
                },
            ],
            "quote_audit": {"verification_verified": 2, "verification_proposed": 3},
            "verification_audit": {
                "rejected_citations": [{
                    "requirement_id": "R1",
                    "requirement": "Manage supplier recovery plans",
                    "quote": "Managed supplier contracts for three years.",
                    "cited_page": 2,
                    "reason": "quote_not_found_on_cited_page",
                }],
            },
        }
        report, _totals = score_case(case, result)
        self.assertEqual(report["related_to_direct_overclaims"], 1)
        self.assertEqual(report["false_related_transfers"], 1)
        self.assertEqual(report["missed_related_transfers"], 2)
        self.assertEqual(report["verification_quote_rate"], 0.6667)
        self.assertEqual(report["rejected_quote_details"], [{
            "requirement_id": "R1",
            "requirement": "Manage supplier recovery plans",
            "quote": "Managed supplier contracts for three years.",
            "cited_page": 2,
            "reason": "quote_not_found_on_cited_page",
        }])
        self.assertEqual(
            report["evidence_strength_distribution"],
            {"specific": 1, "stated": 0, "keyword_only": 1, "none": 1, "not_reported": 0},
        )

    def test_requirement_alignment_marks_omitted_gold_item(self) -> None:
        expected = [
            {"requirement": "Python background"},
            {"requirement": "Current safety certification"},
        ]
        returned = [
            {
                "requirement": "Python background",
                "job_source": {"text": "Python background"},
            }
        ]
        aligned, missing, unmatched = align_findings(expected, returned)
        self.assertEqual(len(aligned), 1)
        self.assertEqual(missing, [1])
        self.assertEqual(unmatched, [])

    def test_timeline_flags_are_scored_separately_from_semantic_labels(self) -> None:
        case = {
            "id": "timeline",
            "expected": [],
            "expected_timeline_flags": ["employment_date_overlap"],
        }
        result = {
            "requirements": [],
            "timeline_audit": {
                "flags": [{"type": "employment_date_overlap"}],
            },
        }
        report, totals = score_case(case, result)
        self.assertEqual(report["timeline_flag_precision"], 1.0)
        self.assertEqual(report["timeline_flag_recall"], 1.0)
        self.assertEqual(totals["timeline_false_positive"], 0)

    def test_timeline_gate_preserves_muse_label_and_adjudicates_conflict(self) -> None:
        finding = {
            "id": "R1",
            "requirement": "Minimum 10 years of procurement and contract management experience.",
            "evidence_type": "direct",
            "certainty": "clear",
            "note": "Muse found direct experience.",
        }
        audit = {
            "flags": [{
                "type": "claimed_tenure_exceeds_dated_evidence",
                "topic": "procurement contract management",
                "claimed_months": 144,
                "documented_months": 96,
                "claim_page": 1,
                "review_note": "Claim exceeds dated evidence.",
            }],
            "episodes": [],
        }

        linked = attach_timeline_review_flags([finding], audit)

        self.assertEqual(len(linked), 1)
        self.assertEqual(finding["evidence_type"], "direct")
        self.assertEqual(finding["muse_evidence_type"], "direct")
        self.assertEqual(finding["final_review_label"], "conflict_to_clarify")
        self.assertEqual(finding["final_evidence_type"], "conflicting")
        self.assertEqual(finding["certainty"], "ambiguous")
        case = {
            "id": "timeline-gate",
            "expected": [{
                "requirement": finding["requirement"],
                "evidence_type": "conflicting",
            }],
        }
        report, _totals = score_case(case, {"requirements": [finding]})
        self.assertEqual(report["strict_category_accuracy"], 0.0)
        self.assertEqual(report["deterministic_adjudicated_accuracy"], 1.0)
        self.assertEqual(report["item_labels"][0]["predicted"], "direct")
        self.assertEqual(report["item_labels"][0]["adjudicated"], "conflicting")

    def test_relevant_timeline_overlap_overrides_the_matching_duration_criterion(self) -> None:
        finding = {
            "id": "R1",
            "requirement": "At least 5 years of procurement experience.",
            "evidence_type": "direct",
            "certainty": "clear",
        }
        audit = {
            "episodes": [{
                "id": "E1",
                "experience_areas": ["procurement"],
            }],
            "flags": [{
                "type": "employment_date_overlap",
                "episodes": ["E1"],
                "roles": ["Procurement Lead", "Procurement Advisor"],
                "overlap_months": 8,
                "review_note": "These dated roles overlap.",
            }],
        }

        attach_timeline_review_flags([finding], audit)

        self.assertEqual(finding["final_review_label"], "conflict_to_clarify")
        self.assertEqual(finding["timeline_review_flags"][0]["type"], "employment_date_overlap")

    def test_html_report_shows_timeline_label_and_preserved_muse_category(self) -> None:
        finding = {
            "id": "R1",
            "requirement": "Minimum 10 years of procurement experience.",
            "status": "supported",
            "evidence_type": "direct",
            "muse_evidence_type": "direct",
            "final_evidence_type": "conflicting",
            "final_review_label": "conflict_to_clarify",
            "certainty": "ambiguous",
            "note": "Clarify the dated experience.",
            "evidence": [],
            "timeline_review_flags": [{"type": "claimed_tenure_exceeds_dated_evidence"}],
        }
        report = build_report(
            findings=[finding],
            previews={},
            cv_hash="cv",
            job_hash="job",
            omitted_requirement_audit=[],
            proposed_quotes=0,
            excluded_quotes=0,
            verification_audit={
                "proposed": 1,
                "verified": 0,
                "excluded": 1,
                "rejected_citations": [{
                    "requirement_id": "R1",
                    "requirement": finding["requirement"],
                    "source_id": "R1-Q1",
                    "cited_page": 1,
                    "quote": "Minimum 10 years of procurement experience.",
                    "reason": "quote_not_found_on_cited_page",
                }],
            },
            evidence_graph={"requirements": []},
            created_at="2026-10-28T00:00:00+00:00",
        )

        self.assertIn("Conflict to clarify", report)
        self.assertIn("Muse: Direct · Timeline check: conflict", report)
        self.assertIn("cited page 1", report)
        self.assertIn("Minimum 10 years of procurement experience.", report)
        self.assertIn("Quote could not be located on the cited PDF page", report)

    def test_fixture_pdf_builder_preserves_pages_and_two_column_text(self) -> None:
        fixture = json.loads((ROOT / "calibration" / "semantic_cases.json").read_text())
        case = fixture["cases"][2]
        document = fitz.open(stream=make_case_pdf(case), filetype="pdf")
        self.assertEqual(document.page_count, 2)
        extracted = "\n".join(page.get_text() for page in document)
        self.assertIn("Supplier Operations Lead", extracted)
        self.assertIn("Category manager led contract negotiations", extracted)
        self.assertIn("No semiconductor", extracted)
        document.close()


if __name__ == "__main__":
    unittest.main()
