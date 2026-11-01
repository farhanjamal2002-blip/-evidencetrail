"""Deterministic, fail-closed interpretation of *verified* CV evidence.

A CV's explicit task limitation does not by itself mean the CV contains
internally contradictory claims. This stage NEVER creates or deletes citations,
never changes the raw Muse label, and never establishes positive qualifications.

The function consumes already locally verified quote roles and retains the
underlying audit. Only evidence that has survived PDF-source grounding may be
supplied here. Empty/malformed citations are not treated as verified evidence.
"""
from __future__ import annotations

import re
from typing import Any

ABSENCE_ONLY = re.compile(
    r"\b(?:no|not|without|none)\b.{0,100}"
    r"\b(?:evidence|listed|mentioned|documented|shown|described|reported)\b"
    r"|\b(?:not|never)\s+(?:listed|mentioned|documented|shown|described|reported)\b",
    re.IGNORECASE,
)


def clarify_verified_findings(findings: list[dict[str, Any]]) -> dict[str, int]:
    """Separate one-sided scope limitations from multiple documented claims.

    One or several scope-limiting citations are evidence against satisfying a
    specific requirement, not proof that the CV contradicts itself. Two-sided
    evidence is necessary before preserving a non-timeline discrepancy. Keep the original Muse proposal in raw_status,
    mark only possible multi-claim discrepancies for human clarification, and
    fail closed (no positive status can be created).

    Mutates findings in-place only after local quote verification and timeline
    adjudication. Safe to run again; results are idempotent.
    """
    counters = {
        "single_scope_limits_clarified": 0,
        "multi_scope_limits_clarified": 0,
        "document_absences_clarified": 0,
        "multi_quote_discrepancies_retained": 0,
        "related_context_labeled": 0,
        "unchanged": 0,
    }
    for finding in findings:
        if not isinstance(finding, dict):
            counters["unchanged"] += 1
            continue
        status = str(finding.get("status", "not_found"))
        evidence_type = str(finding.get("evidence_type", "unsupported"))
        citations = [
            quote for quote in (finding.get("evidence") or [])
            if isinstance(quote, dict) and str(quote.get("quote", "")).strip()
            and isinstance(quote.get("page"), int)
            and not isinstance(quote.get("page"), bool) and quote["page"] >= 1
            and quote.get("role") in {"supports", "contradicts"}
        ]
        support = [q for q in citations if q["role"] == "supports"]
        limiting = [q for q in citations if q["role"] == "contradicts"]
        has_timeline_issue = bool(finding.get("timeline_review_flags"))

        if status == "conflicting" and limiting and not support and not has_timeline_issue and len(citations) == len(limiting):
            document_absence = all(ABSENCE_ONLY.search(str(q["quote"])) for q in limiting)
            code = "document_absence_not_contradiction" if document_absence else "explicit_scope_limit_not_contradiction"
            finding["status"] = "not_found"
            finding["effective_status"] = "not_found"
            finding["evidence_type"] = "unsupported"
            finding["certainty"] = "ambiguous"
            finding["review_reason_code"] = code
            finding["review_label"] = (
                "Not documented in this CV" if document_absence
                else "Scope not established"
            )
            finding["review_explanation"] = (
                "The CV reports that evidence is absent; no verified positive claim opposes it."
                if document_absence else
                "The cited statements limit the documented role or task; no independently verified positive claim opposes them."
            )
            finding["note"] = (
                str(finding.get("note", "")).strip()
                + " Local clarification: this source is a limitation on the requirement, "
                "not verified proof of self-contradictory CV claims."
            ).strip()
            finding["status_policy"] = "unpaired_limiting_quotes_cannot_establish_cv_self_contradiction"
            for item in limiting:
                item["display_role"] = "scope_context"
                item["evidence_type"] = "unsupported"
            scope = finding.get("scope_boundary_review")
            if isinstance(scope, dict):
                scope["final_status"] = "not_found"
            counters[
                "document_absences_clarified" if document_absence else
                "single_scope_limits_clarified" if len(limiting) == 1 else
                "multi_scope_limits_clarified"
            ] += 1
        elif status == "conflicting":
            finding["review_reason_code"] = "multi_claim_or_timeline_discrepancy"
            finding["review_label"] = "Discrepancy to clarify"
            finding["review_explanation"] = (
                "Multiple cited statements or an independently checked timeline flag require human clarification. "
                "This does not establish that the CV claim is false."
            )
            counters["multi_quote_discrepancies_retained"] += 1
        elif status == "not_found" and evidence_type == "related":
            finding["review_reason_code"] = "related_evidence_exact_criterion_unproven"
            finding["review_label"] = "Related evidence — exact requirement unproven"
            finding["review_explanation"] = (
                "Concrete transferable work is quoted, but the specific qualification has not been established."
            )
            counters["related_context_labeled"] += 1
        else:
            counters["unchanged"] += 1
    return counters


def reconcile_scope_context_page_marks(
    findings: list[dict[str, Any]], page_marks: dict[int, list[dict[str, Any]]]
) -> int:
    """Keep PDF highlight colors aligned with post-verification status changes.

    A demoted conflict retains its original quote, page and raw role for audit.
    However, the reader-facing highlight must be a scope limitation, not a red
    self-contradiction. Only exact requirement + source IDs are rewritten.
    """
    changed = 0
    for finding in findings:
        if not isinstance(finding, dict) or finding.get("review_reason_code") not in {
            "explicit_scope_limit_not_contradiction",
            "document_absence_not_contradiction",
        }:
            continue
        requirement_id = str(finding.get("id", ""))
        for citation in finding.get("evidence") or []:
            if not isinstance(citation, dict) or citation.get("display_role") != "scope_context":
                continue
            page = citation.get("page")
            source_id = citation.get("source_id")
            if not isinstance(page, int) or isinstance(page, bool) or page < 1 or not source_id:
                continue
            for mark in page_marks.get(page, []):
                if (
                    isinstance(mark, dict)
                    and mark.get("requirement_id") == requirement_id
                    and mark.get("source_id") == source_id
                    and mark.get("role") != "scope_limitation"
                ):
                    mark["role"] = "scope_limitation"
                    changed += 1
    return changed
