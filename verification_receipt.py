"""EvidenceTrail verification-receipt v1 — source-derived audit presentation.

Never infer a security PASS, PDF coordinate, char offset or unrecorded model
reasoning. Immutable recorded Muse input remains untouched. Exactly zero API
calls and no CV scoring/recommendation.
"""
from __future__ import annotations

from typing import Any


def _status(value: Any) -> str:
    return str(value) if value not in (None, "") else "not_recorded"


def _as_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def build_verification_receipt(payload: dict[str, Any], *, recorded: bool = False) -> dict[str, Any]:
    findings = payload.get("requirements") or []
    if not isinstance(findings, list):
        findings = []
    quote_audit = payload.get("quote_audit") or {}
    verifier = payload.get("verification_audit") or {}
    proposed = _as_int(quote_audit.get("proposed"))
    verified = _as_int(quote_audit.get("verified"))
    excluded = _as_int(quote_audit.get("excluded"))
    source_citations = sum(
        1 for finding in findings if isinstance(finding, dict)
        for citation in (finding.get("evidence") or []) if isinstance(citation, dict)
    )
    # Historical recording has aggregate confirmation; never pretend it
    # contains per-quote character offsets, bbox geometry or confidence.
    audit_consistent = (
        proposed is not None and verified is not None and excluded is not None
        and proposed == verified + excluded
        and verified >= source_citations
    )
    ocr_pages = [
        p for p in (payload.get("ocr_pages") or [])
        if isinstance(p, int) and not isinstance(p, bool) and p > 0
    ]
    ocr_pages = sorted(set(ocr_pages))
    source_pages = sorted({
        citation["page"] for finding in findings if isinstance(finding, dict)
        for citation in (finding.get("evidence") or [])
        if isinstance(citation, dict)
        and isinstance(citation.get("page"), int)
        and not isinstance(citation["page"], bool) and citation["page"] > 0
    })
    criteria = []
    count_overrides = 0
    for index, finding in enumerate(findings, 1):
        if not isinstance(finding, dict):
            continue
        raw = finding.get("raw_status") or finding.get("muse_status")
        final = finding.get("effective_status") or finding.get("status")
        changed = isinstance(raw, str) and isinstance(final, str) and raw != final
        if changed:
            count_overrides += 1
        citations = [
            {
                "page": citation["page"],
                "source_id": citation.get("source_id"),
                "quote": citation.get("quote"),
                "source_verified": True if audit_consistent else None,
                "match_method": None,     # not captured in historic replay
                "char_span": None,        # no offsets recorded
                "bounding_boxes": None,  # PDF geometry is a separate next upgrade
            }
            for citation in (finding.get("evidence") or [])
            if isinstance(citation, dict)
            and isinstance(citation.get("page"), int) and not isinstance(citation["page"], bool)
            and citation["page"] > 0 and isinstance(citation.get("quote"), str)
        ]
        criteria.append({
            "requirement_index": index,
            "requirement": finding.get("requirement"),
            "raw_muse_status": raw if isinstance(raw, str) else None,
            "verified_status": final if isinstance(final, str) else None,
            "review_label": finding.get("review_label"),
            "override_applied": changed,
            "override_reason_code": (
                finding.get("review_reason_code") or finding.get("status_policy")
                if changed else None
            ),
            "verification_explanation": (
                finding.get("review_explanation") if changed else None
            ),
            "quote_citations": citations,
            "timeline_review_flags": finding.get("timeline_review_flags") or [],
        })
    # A count of *raw vs final* changes, not a count of all local review notes.
    # Some semantic annotations can clarify wording without changing status.
    usage = payload.get("usage") or {}
    first_pass = usage.get("analysis_pass") if isinstance(usage, dict) else None
    provider_id = payload.get("receipt") if recorded else (
        first_pass.get("provider_response_id")
        if isinstance(first_pass, dict) else None
    )
    real_muse = payload.get("provider_mode") == "muse"
    timeline = payload.get("timeline_audit")
    if not isinstance(timeline, dict):
        timeline = None
    # These statuses must remain unknown until explicit, source-backed
    # instrumentation exists. The presence of an adversarial fixture is NOT
    # evidence that a specific injection detector fired.
    return {
        "schema": "evidencetrail/verification-receipt/v1",
        "provider": {
            "mode": payload.get("provider_mode"),
            "model": payload.get("model"),
            "response_id": provider_id if isinstance(provider_id, str) else None,
            "real_muse_response": bool(real_muse and provider_id),
            "source": "saved_authentic_replay" if recorded else "new_analysis",
            "additional_model_calls_for_receipt": 0,
        },
        "document": {
            "cv_sha256": payload.get("cv_sha256"),
            "extraction_mode": "tesseract_ocr_used" if ocr_pages else "pdf_text_no_ocr_reported",
            "ocr_pages": ocr_pages,
            "cited_pages": source_pages,
        },
        "quote_grounding": {
            "proposed": proposed,
            "verified": verified,
            "excluded": excluded,
            "citation_count": source_citations,
            "aggregate_source_audit_consistent": audit_consistent,
            "method_detail": "not_recorded",
        },
        "semantic_overrides": {
            "raw_vs_verified_status_changes": count_overrides,
            "unmodified_raw_labels": True,
        },
        "input_guardrails": {
            "prompt_injection_scan": {"status": "not_recorded"},
            "hidden_text_scan": {"status": "not_recorded"},
            "input_sanitization_check": {"status": "not_recorded"},
        },
        "timeline": {
            "status": "recorded" if timeline is not None else "not_recorded",
            "audit": timeline if timeline is not None else None,
        },
        "requirements": criteria,
        "disclaimer": (
            "PDF grounding confirms the supplied document passage, not real-world "
            "truth or a candidate hiring decision. Unknown checks are not passed checks."
        ),
    }
