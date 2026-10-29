"""Regression checks for explicit CV responsibility limits."""

from __future__ import annotations

import unittest

import app


REQUIREMENT = (
    "Support supplier negotiations, pricing analysis, and commercial contract implementation."
)


def finding_with_quote(
    page: dict[str, object],
    quote: str,
    requirement: str = REQUIREMENT,
) -> dict[str, object]:
    match = app.locate_quote(quote, [page], 1)
    if not match:
        raise AssertionError("Test quote must resolve on the source page.")
    return {
        "id": "R2",
        "requirement": requirement,
        "status": "supported",
        "evidence_type": "direct",
        "evidence_strength": "specific",
        "certainty": "clear",
        "note": "Muse proposed a direct finding.",
        "transfer_explanation": None,
        "unproven_aspects": [],
        "follow_up_question": None,
        "evidence": [{
            "quote": quote,
            "role": "supports",
            "page": 1,
            "boxes": match["boxes"],
            "source_id": "R2-Q1",
            "evidence_type": "direct",
        }],
    }


def synthetic_page(text: str) -> dict[str, object]:
    """Build page words so tests exercise the same quote anchor path as PDFs."""
    words = []
    x = 0.0
    for token in text.split():
        width = max(4.0, len(token) * 4.0)
        words.append(app.word_record(token, x, 0.0, x + width, 10.0, line_id=1))
        x += width + 2.0
    return {"number": 1, "text": text, "words": words}


class ExplicitScopeBoundaryTests(unittest.TestCase):
    def test_adjacent_procurement_tasks_are_downgraded_when_negotiation_is_explicitly_limited(self) -> None:
        support = (
            "Requested bids, compared supplier quotations, tracked service levels and corrective actions, "
            "and coordinated contract renewals."
        )
        limitation = "I did not own supplier negotiations or contract sign-off."
        page = synthetic_page(support + " " + limitation)
        finding = finding_with_quote(page, support)
        page_marks: dict[int, list[dict[str, object]]] = {}

        audit = app.apply_explicit_scope_boundary_guard([finding], [page], page_marks)

        self.assertEqual(finding["evidence_type"], "related")
        self.assertEqual(finding["muse_evidence_type"], "direct")
        self.assertEqual(finding["final_evidence_type"], "related")
        self.assertEqual(finding["certainty"], "ambiguous")
        self.assertEqual(finding["scope_limitations"][0]["quote"], limitation)
        self.assertEqual(finding["scope_limitations"][0]["page"], 1)
        self.assertIn("direct participation in negotiations", finding["unproven_aspects"][-1])
        self.assertIn("who held the negotiation", finding["follow_up_question"])
        self.assertEqual(page_marks[1][0]["role"], "scope_limitation")
        self.assertEqual(audit["direct_to_related_adjustments"], 1)

    def test_single_pass_pipeline_demotes_direct_claim_with_explicit_scope_limit(self) -> None:
        support = (
            "Requested bids, compared supplier quotations, tracked service levels and corrective actions, "
            "and coordinated contract renewals."
        )
        limitation = "I did not own supplier negotiations or contract sign-off."
        page = synthetic_page(support + " " + limitation)
        model_result = {
            "requirements": [{
                "requirement": REQUIREMENT,
                "status": "supported",
                "evidence_type": "direct",
                "evidence_strength": "specific",
                "transfer_explanation": None,
                "unproven_aspects": [],
                "follow_up_question": None,
                "certainty": "clear",
                "reason": "Adjacent procurement activities support the requirement.",
                "evidence": [{"quote": support, "role": "supports", "page_hint": 1}],
            }],
            "application_claims": [],
        }

        findings, page_marks, usage, audit = app.verify_single_pass_proposals_locally(
            model_result, [{
                "id": "R2",
                "requirement": REQUIREMENT,
                "status": "not_found",
                "note": "",
                "evidence": [],
            }], [], [page]
        )

        self.assertEqual(findings[0]["evidence_type"], "related")
        self.assertEqual(findings[0]["muse_evidence_type"], "direct")
        self.assertEqual(findings[0]["proposed_evidence_type"], "direct")
        self.assertEqual(findings[0]["final_evidence_type"], "related")
        self.assertEqual(findings[0]["scope_limitations"][0]["quote"], limitation)
        self.assertEqual(audit["scope_boundary_review"]["direct_to_related_adjustments"], 1)
        self.assertEqual(usage["input_tokens"], 0)
        self.assertEqual(page_marks[1][0]["role"], "related")

    def test_documented_negotiation_support_stays_direct_when_final_ownership_is_denied(self) -> None:
        support = "I joined supplier negotiation calls and documented the negotiation actions."
        limitation = "I did not own final contract sign-off."
        page = synthetic_page(support + " " + limitation)
        finding = finding_with_quote(page, support)
        page_marks: dict[int, list[dict[str, object]]] = {}

        audit = app.apply_explicit_scope_boundary_guard([finding], [page], page_marks)

        self.assertEqual(finding["evidence_type"], "direct")
        self.assertNotIn("scope_limitations", finding)
        self.assertEqual(audit["direct_to_related_adjustments"], 0)

    def test_supported_rather_than_led_is_direct_when_the_job_only_asks_for_support(self) -> None:
        quote = "Supported rather than led supplier negotiations."
        page = synthetic_page(quote)
        finding = finding_with_quote(page, quote)
        audit = app.apply_explicit_scope_boundary_guard([finding], [page], {})

        self.assertEqual(finding["evidence_type"], "direct")
        self.assertEqual(finding["status"], "supported")
        self.assertEqual(audit["direct_to_related_adjustments"], 0)

    def test_no_direct_experience_and_exposure_only_are_limited_to_related(self) -> None:
        support = "Requested bids, compared supplier quotations, and coordinated renewals."
        for limitation in (
            "I have no direct experience with supplier negotiations.",
            "My exposure only to supplier negotiations was through renewal tracking.",
            "I had only exposure to supplier negotiations.",
        ):
            with self.subTest(limitation=limitation):
                page = synthetic_page(support + " " + limitation)
                finding = finding_with_quote(page, support)
                audit = app.apply_explicit_scope_boundary_guard([finding], [page], {})

                self.assertEqual(finding["evidence_type"], "related")
                self.assertEqual(finding["final_evidence_type"], "related")
                self.assertEqual(finding["muse_evidence_type"], "direct")
                self.assertEqual(audit["direct_to_related_adjustments"], 1)

    def test_limitation_quote_alone_does_not_become_related_evidence(self) -> None:
        quote = "I have no direct experience with supplier negotiations."
        page = synthetic_page(quote)
        finding = finding_with_quote(page, quote)
        audit = app.apply_explicit_scope_boundary_guard([finding], [page], {})

        self.assertEqual(finding["status"], "not_found")
        self.assertEqual(finding["evidence_type"], "unsupported")
        self.assertEqual(finding["muse_evidence_type"], "direct")
        self.assertEqual(finding["evidence"][0]["role"], "contradicts")
        self.assertEqual(audit["direct_to_unsupported_adjustments"], 1)

    def test_exposure_only_conflicts_with_a_direct_experience_requirement(self) -> None:
        requirement = "Direct experience with supplier negotiations."
        quote = "My exposure only to supplier negotiations was through renewals."
        page = synthetic_page(quote)
        finding = finding_with_quote(page, quote, requirement)
        audit = app.apply_explicit_scope_boundary_guard([finding], [page], {})

        self.assertEqual(finding["status"], "conflicting")
        self.assertEqual(finding["evidence_type"], "conflicting")
        self.assertEqual(finding["scope_boundary_review"]["final_status"], "conflicting")
        self.assertEqual(audit["direct_to_conflict_adjustments"], 1)

    def test_explicit_denial_conflicts_when_the_job_requires_leadership(self) -> None:
        requirement = "Lead supplier negotiations."
        quote = "Supported rather than led supplier negotiations."
        page = synthetic_page(quote)
        finding = finding_with_quote(page, quote, requirement)
        audit = app.apply_explicit_scope_boundary_guard([finding], [page], {})

        self.assertEqual(finding["status"], "conflicting")
        self.assertEqual(finding["evidence_type"], "conflicting")
        self.assertEqual(finding["muse_evidence_type"], "direct")
        self.assertEqual(finding["scope_boundary_review"]["final_evidence_type"], "conflicting")
        self.assertEqual(audit["direct_to_conflict_adjustments"], 1)

    def test_scope_limit_for_unrelated_action_does_not_change_label(self) -> None:
        page = synthetic_page(
            "I did not own supplier negotiations. I managed the facilities maintenance schedule."
        )
        finding = {
            "id": "R3",
            "requirement": "Manage a facilities maintenance schedule.",
            "status": "supported",
            "evidence_type": "direct",
            "evidence_strength": "specific",
            "certainty": "clear",
            "evidence": [{
                "quote": "I managed the facilities maintenance schedule.",
                "role": "supports",
            }],
        }
        page_marks: dict[int, list[dict[str, object]]] = {}

        audit = app.apply_explicit_scope_boundary_guard([finding], [page], page_marks)

        self.assertEqual(finding["evidence_type"], "direct")
        self.assertEqual(audit["explicit_scope_limitations_detected"], 0)
        self.assertEqual(page_marks, {})


if __name__ == "__main__":
    unittest.main()
