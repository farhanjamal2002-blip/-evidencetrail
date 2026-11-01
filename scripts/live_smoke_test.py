"""Preflight or run one controlled Muse analysis on fictional sample documents.

The script makes one Meta Model API request only when the server-side key is
configured and ``--confirm-live-call`` is supplied. Its report contains no key,
full CV text, accepted quotes, or full report; rejected quote snippets include
their cited page and failure reason for calibration review.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm-live-call",
        action="store_true",
        help="Authorize exactly one Meta Model API request for the synthetic sample.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Check local dependencies and provider configuration without making requests.",
    )
    args = parser.parse_args()
    if args.confirm_live_call and args.preflight_only:
        parser.error("Choose either --confirm-live-call or --preflight-only.")
    return args


def load_app() -> Any | None:
    try:
        from fastapi.testclient import TestClient  # noqa: F401

        import app

        return app
    except ModuleNotFoundError as exc:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "A project dependency is missing.",
                    "missing_dependency": exc.name or "unknown",
                    "meta_request_made": False,
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return None


def configuration_report(application: Any) -> dict[str, Any]:
    key_configured = bool(application.configured_model_api_key())
    provider = application.ANALYSIS_PROVIDER
    muse_enabled = bool(getattr(application, "MUSE_PROVIDER_ENABLED", False))
    return {
        "provider": provider,
        "model": application.MODEL_ID,
        "reasoning_effort": application.MUSE_REASONING_EFFORT,
        "server_key_configured": key_configured,
        "muse_enabled": muse_enabled,
        "expected_live_requests": 1 if provider == "muse" and muse_enabled and key_configured else 0,
        "automatic_retries": 0,
        "api_storage_requested": False,
        "meta_request_made": False,
        "report_contains_cv_text": False,
        "report_contains_accepted_quote_text": False,
        "report_contains_rejected_quote_text": True,
    }


def make_sample_job_description() -> str:
    return "\n".join(
        [
            "Role: Procurement Automation Lead",
            "Requirements:",
            "1. At least five years of Python experience.",
            "2. Current AWS Solutions Architect Professional certification.",
            "3. At least seven years of procurement experience.",
            "4. Negotiate multi-year supply agreements with GCC manufacturers.",
            "5. At least three years of team leadership experience.",
        ]
    )


def safe_live_summary(
    result: dict[str, Any], reasoning_effort: str = "unknown"
) -> tuple[dict[str, Any], list[str]]:
    """Return a small calibration report and structural warnings, not raw output."""
    warnings: list[str] = []
    requirements = result.get("requirements")
    if not isinstance(requirements, list):
        requirements = []
        warnings.append("The response did not contain a requirements list.")

    allowed_statuses = {"supported", "not_found", "conflicting"}
    allowed_evidence_types = {"direct", "related", "unsupported", "conflicting"}
    requirement_summary: list[dict[str, Any]] = []
    for item in requirements:
        if not isinstance(item, dict):
            warnings.append("A returned requirement had an invalid shape.")
            continue
        status = item.get("status")
        evidence_type = item.get("evidence_type")
        evidence = item.get("evidence")
        if status not in allowed_statuses:
            warnings.append("A requirement had an unrecognized status.")
        if not isinstance(evidence, list):
            evidence = []
            warnings.append("A requirement had an invalid evidence list.")
        if status in {"supported", "conflicting"} and not evidence:
            warnings.append(f"{item.get('id', 'A requirement')} has a non-missing status without verified evidence.")
        if evidence_type not in allowed_evidence_types:
            warnings.append(f"{item.get('id', 'A requirement')} has no recognized evidence type.")
        if evidence_type == "related" and (
            not evidence
            or not isinstance(item.get("transfer_explanation"), str)
            or not item.get("transfer_explanation", "").strip()
            or not isinstance(item.get("unproven_aspects"), list)
            or not item.get("unproven_aspects")
        ):
            warnings.append(f"{item.get('id', 'A requirement')} has incomplete related-evidence details.")
        requirement_summary.append(
            {
                "id": item.get("id"),
                "requirement": item.get("requirement"),
                "status": status,
                "evidence_type": evidence_type,
                "certainty": item.get("certainty"),
                "transfer_explanation_present": bool(item.get("transfer_explanation")),
                "unproven_aspect_count": len(item.get("unproven_aspects", []))
                if isinstance(item.get("unproven_aspects"), list)
                else 0,
                "verified_evidence_count": len(evidence),
                "evidence_pages": sorted(
                    {
                        citation.get("page")
                        for citation in evidence
                        if isinstance(citation, dict)
                        and isinstance(citation.get("page"), int)
                        and not isinstance(citation.get("page"), bool)
                    }
                ),
            }
        )

    evidence_types = {item["evidence_type"] for item in requirement_summary}
    missing_demo_cases = sorted(allowed_evidence_types - evidence_types)
    if missing_demo_cases:
        warnings.append(
            "The live sample did not produce all evidence-type calibration cases: "
            + ", ".join(missing_demo_cases)
            + ". Treat the statuses as model output to review, not a test failure."
        )

    verification = result.get("verification_audit")
    verification = verification if isinstance(verification, dict) else {}
    rejected_quote_details: list[dict[str, Any]] = []
    rejected_records = verification.get("rejected_citations", [])
    if isinstance(rejected_records, list):
        for record in rejected_records:
            if not isinstance(record, dict) or not record.get("quote"):
                continue
            page = record.get("cited_page")
            page = page if isinstance(page, int) and not isinstance(page, bool) and page > 0 else None
            rejected_quote_details.append({
                "requirement_id": str(record.get("requirement_id", ""))[:32],
                "requirement": str(record.get("requirement", ""))[:180],
                "quote": str(record.get("quote", ""))[:360],
                "cited_page": page,
                "reason": str(record.get("reason", "unknown"))[:80],
            })

    usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
    analysis_usage = usage.get("analysis_pass")
    if not isinstance(analysis_usage, dict):
        analysis_usage = {}
    local_verification = usage.get("local_verification")
    if not isinstance(local_verification, dict):
        local_verification = {}
    performance = result.get("performance_ms")
    if not isinstance(performance, dict):
        performance = {}

    quote_audit = result.get("quote_audit")
    if not isinstance(quote_audit, dict):
        quote_audit = {}
        warnings.append("The response did not contain a quote audit.")

    summary = {
        "status": "completed",
        "provider": result.get("provider_mode"),
        "model": result.get("model"),
        "reasoning_effort": reasoning_effort,
        "analysis_calls": result.get("analysis_calls"),
        "requirements": requirement_summary,
        "status_coverage": {
            "supported": sum(item["status"] == "supported" for item in requirement_summary),
            "not_found": sum(item["status"] == "not_found" for item in requirement_summary),
            "conflicting": sum(item["status"] == "conflicting" for item in requirement_summary),
        },
        "evidence_type_coverage": {
            evidence_type: sum(item["evidence_type"] == evidence_type for item in requirement_summary)
            for evidence_type in sorted(allowed_evidence_types)
        },
        "job_item_coverage": safe_coverage(result.get("job_item_coverage")),
        "quote_audit": {
            key: nonnegative_int(
                quote_audit.get(
                    key,
                    quote_audit.get("retrieved_source_spans", 0)
                    if key == "locally_anchored_source_spans"
                    else 0,
                )
            )
            for key in (
                "proposed",
                "verified",
                "excluded",
                "verification_proposed",
                "verification_verified",
                "verification_excluded",
                "ambiguous_requirements",
                "locally_anchored_source_spans",
            )
        },
        "rejected_quote_details": rejected_quote_details,
        "usage_by_stage": {
            "muse_analysis": {
                "input_tokens": nonnegative_int(analysis_usage.get("input_tokens")),
                "output_tokens": nonnegative_int(analysis_usage.get("output_tokens")),
                "cached_input_tokens": nonnegative_int(analysis_usage.get("cached_input_tokens")),
                "reasoning_tokens": nonnegative_int(analysis_usage.get("reasoning_tokens")),
                "api_latency_ms": nonnegative_int(analysis_usage.get("api_latency_ms")),
                "cv_text_characters": nonnegative_int(analysis_usage.get("cv_text_characters")),
                "cv_page_count": nonnegative_int(analysis_usage.get("cv_page_count")),
                "cv_ocr_page_count": nonnegative_int(analysis_usage.get("cv_ocr_page_count")),
            },
            "local_verification": {
                "input_tokens": nonnegative_int(local_verification.get("input_tokens")),
                "output_tokens": nonnegative_int(local_verification.get("output_tokens")),
                "mode": local_verification.get("mode", "unknown"),
            },
        },
        "usage_total": {
            "input_tokens": nonnegative_int(usage.get("input_tokens")),
            "output_tokens": nonnegative_int(usage.get("output_tokens")),
            "cached_input_tokens": nonnegative_int(usage.get("cached_input_tokens")),
            "reasoning_tokens": nonnegative_int(usage.get("reasoning_tokens")),
        },
        "performance_ms": {
            str(key)[:80]: (
                None
                if value is None
                else nonnegative_int(value)
                if isinstance(value, int) and not isinstance(value, bool)
                else None
            )
            for key, value in performance.items()
        },
        "ocr_pages": result.get("ocr_pages", []),
        "warnings": warnings,
    }
    return summary, warnings


def nonnegative_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return 0
    return value


def safe_coverage(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {"matched": 0, "needs_review": 0}
    return {
        "matched": nonnegative_int(value.get("matched")),
        "needs_review": nonnegative_int(value.get("needs_review")),
    }


def main() -> int:
    args = parse_args()
    application = load_app()
    if application is None:
        return 2

    report = configuration_report(application)
    if application.ANALYSIS_PROVIDER != "muse":
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "Set EVIDENCETRAIL_PROVIDER=muse in the server environment.",
                    **report,
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    if not application.MUSE_PROVIDER_ENABLED:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "Set EVIDENCETRAIL_ENABLE_MUSE=true to explicitly enable Muse.",
                    **report,
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    if not report["server_key_configured"]:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "MODEL_API_KEY is not configured in the server environment.",
                    **report,
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    if args.preflight_only:
        print(json.dumps({"status": "ready_for_review", **report}, indent=2))
        return 0
    if not args.confirm_live_call:
        print(
            json.dumps(
                {
                    "status": "preflight_passed",
                    "next_step": "Rerun with --confirm-live-call to make exactly one live request.",
                    **report,
                },
                indent=2,
            )
        )
        return 0

    from fastapi.testclient import TestClient

    pdf_bytes = application.make_demo_pdf()
    smoke_started = time.perf_counter()
    with TestClient(application.app) as client:
        response = client.post(
            "/api/analyze",
            files={"cv": ("evidencetrail-synthetic-cv.pdf", pdf_bytes, "application/pdf")},
            data={
                "job_description": make_sample_job_description(),
                "consent": "true",
            },
        )
    smoke_elapsed_seconds = round(time.perf_counter() - smoke_started, 3)

    if response.status_code != 200:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "http_status": response.status_code,
                    "detail": response.json().get("detail", "Analysis failed."),
                    "meta_request_made": None,
                    "provider_request_receipt": "unknown; failed app responses do not expose it",
                    "expected_live_requests": 1,
                    "automatic_retries": 0,
                    "end_to_end_seconds": smoke_elapsed_seconds,
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    summary, warnings = safe_live_summary(
        response.json(), application.MUSE_REASONING_EFFORT
    )
    summary["end_to_end_seconds"] = smoke_elapsed_seconds
    if summary["provider"] != "muse" or summary["analysis_calls"] != 1:
        warnings.append("The completed response did not report one Muse analysis request.")
        summary["warnings"] = warnings
        summary["status"] = "completed_with_contract_warning"
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 1

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
