"""Regression checks for inconsistent Muse requirement and citation labels."""

from __future__ import annotations

import unittest
import os

os.environ["EVIDENCETRAIL_PROVIDER"] = "mock"
os.environ["MAX_ANALYSES_PER_HOUR_PER_IP"] = "1000"
os.environ["MAX_ANALYSES_PER_PROCESS"] = "1000"

import app


REQUIREMENT = "Support supplier negotiations, pricing analysis, and contract implementation."


def source_page(text: str) -> dict[str, object]:
    words = []
    x = 0.0
    for token in text.split():
        width = max(4.0, len(token) * 4.0)
        words.append(app.word_record(token, x, 0.0, x + width, 10.0, line_id=1))
        x += width + 2.0
    return {"number": 1, "text": text, "words": words}


def verify(
    *, model_type: str, model_status: str, support_quote: str | None,
    conflict_quote: str,
) -> tuple[list[dict[str, object]], dict[int, list[dict[str, object]]], dict[str, object]]:
    parts = [quote for quote in (support_quote, conflict_quote) if quote]
    page = source_page(" ".join(parts))
    source_by_id: dict[str, dict[str, object]] = {}
    evidence = []
    allowed = {"R1": set()}
    for index, quote in enumerate(parts, start=1):
        source_id = f"R1-Q{index}"
        match = app.locate_quote(quote, [page], 1)
        assert match is not None
        source_by_id[source_id] = {
            "id": source_id,
            "page": 1,
            "text": quote,
            "context": quote,
        }
        allowed["R1"].add(source_id)
        evidence.append({
            "source_id": source_id,
            "quote": quote,
            "role": "supports" if quote == support_quote else "contradicts",
        })

    finding = {
        "id": "R1",
        "requirement": REQUIREMENT,
        "status": "not_found",
        "evidence_type": "unsupported",
        "evidence_strength": "none",
        "certainty": "ambiguous",
        "note": "",
        "evidence": [],
    }
    review = {
        "requirement_id": "R1",
        "status": model_status,
        "evidence_type": model_type,
        "evidence_strength": "specific",
        "transfer_explanation": "Price analysis may transfer to supplier negotiations.",
        "unproven_aspects": ["candidate's personal negotiation role"],
        "follow_up_question": "Which negotiation tasks did you personally perform?",
        "certainty": "clear",
        "reason": "The CV describes price analysis and assigns negotiation leadership elsewhere.",
        "evidence": evidence,
    }
    results, marks, audit = app.apply_verification_reviews(
        [finding], {"reviews": [review]}, source_by_id, allowed, [page]
    )
    return results, marks, audit


class EvidenceConflictGateTests(unittest.TestCase):
    def test_related_plus_nonmatching_conflict_citation_becomes_ambiguous_related(self) -> None:
        support = "Prepared price comparisons and purchase-order reports."
        attributed = "Category manager led contract negotiations."
        results, marks, audit = verify(
            model_type="related",
            model_status="supported",
            support_quote=support,
            conflict_quote=attributed,
        )

        finding = results[0]
        self.assertEqual(finding["status"], "supported")
        self.assertEqual(finding["evidence_type"], "related")
        self.assertEqual(finding["final_evidence_type"], "related")
        self.assertEqual(finding["certainty"], "ambiguous")
        self.assertEqual(finding["evidence"][1]["display_role"], "scope_context")
        self.assertEqual([item["role"] for item in marks[1]], ["related", "scope_limitation"])
        self.assertEqual(audit["evidence_conflict_review_findings"], 1)
        graph = app.build_evidence_graph(results)
        self.assertIn("scope_context", [edge["relation"] for edge in graph["edges"]])

    def test_direct_claim_with_mixed_citation_roles_is_downgraded_to_related(self) -> None:
        results, _marks, _audit = verify(
            model_type="direct",
            model_status="supported",
            support_quote="Prepared price comparisons and purchase-order reports.",
            conflict_quote="Category manager led contract negotiations.",
        )

        finding = results[0]
        self.assertEqual(finding["proposed_evidence_type"], "direct")
        self.assertEqual(
            finding["evidence_conflict_review"]["muse_evidence_type"], "direct"
        )
        self.assertEqual(finding["evidence_type"], "related")
        self.assertEqual(finding["final_evidence_type"], "related")
        self.assertEqual(finding["certainty"], "ambiguous")

    def test_consistent_explicit_conflict_remains_conflicting(self) -> None:
        quote = "I do not hold a current PMP certification."
        results, _marks, _audit = verify(
            model_type="conflicting",
            model_status="conflicting",
            support_quote=None,
            conflict_quote=quote,
        )

        self.assertEqual(results[0]["status"], "conflicting")
        self.assertEqual(results[0]["evidence_type"], "conflicting")
        self.assertEqual(results[0]["evidence"][0]["role"], "contradicts")


if __name__ == "__main__":
    unittest.main()
