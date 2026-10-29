#!/usr/bin/env python3
"""Run one bounded, two-candidate Muse comparison for the strength ladder demo.

The script makes at most two provider requests: one Muse analysis per fictional
CV. It never retries. The saved result omits full CV text and accepted quotes,
but retains any rejected quote snippet with its page and failure reason.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FIXTURE = ROOT / "calibration" / "strength_ladder_demo.json"
OUTPUT = ROOT / "calibration" / "live_strength_ladder_demo_20261028.json"
LABELS = {"direct", "related", "unsupported", "conflicting"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--confirm-live-call", action="store_true")
    args = parser.parse_args()
    if args.preflight_only and args.confirm_live_call:
        parser.error("Choose either --preflight-only or --confirm-live-call.")
    return args


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    fixture = load_fixture()
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ModuleNotFoundError:
        pass

    provider = os.getenv("EVIDENCETRAIL_PROVIDER", "muse").strip().casefold()
    key_configured = bool(os.getenv("MODEL_API_KEY", "").strip())
    try:
        import app
        from fastapi.testclient import TestClient
        from scripts.evaluate_semantic_cases import make_case_pdf, score_case
    except ModuleNotFoundError as exc:
        print(json.dumps({
            "status": "blocked",
            "reason": "A project dependency is missing; no model request was made.",
            "missing_dependency": exc.name or "unknown",
            "live_calls_made": 0,
        }, indent=2))
        return 2

    preflight = {
        "provider": provider,
        "model": "muse-spark-1.3",
        "server_key_configured": key_configured,
        "candidate_count": len(fixture["candidates"]),
        "expected_live_requests": len(fixture["candidates"]),
        "automatic_retries": 0,
        "report_contains_cv_text": False,
        "report_contains_accepted_quote_text": False,
        "report_contains_rejected_quote_text": True,
    }
    if app.ANALYSIS_PROVIDER != "muse" or provider != "muse":
        print(json.dumps({"status": "blocked", "reason": "The configured provider is not Muse; no request was made.", "live_calls_made": 0, **preflight}, indent=2))
        return 2
    if not key_configured:
        print(json.dumps({"status": "blocked", "reason": "MODEL_API_KEY is not configured; no request was made.", "live_calls_made": 0, **preflight}, indent=2))
        return 2
    if args.preflight_only or not args.confirm_live_call:
        print(json.dumps({
            "status": "ready_for_review" if args.preflight_only else "preflight_passed",
            **preflight,
            **({} if args.preflight_only else {"next_step": "Rerun with --confirm-live-call to make exactly the listed requests."}),
        }, indent=2))
        return 0

    job_requirement = fixture["job_description"].split("Requirement: ", 1)[1].strip()
    files = [
        (
            "cvs",
            (str(candidate["id"]) + ".pdf", make_case_pdf(candidate), "application/pdf"),
        )
        for candidate in fixture["candidates"]
    ]
    candidate_reports: list[dict[str, Any]] = []
    total_input_tokens = 0
    total_output_tokens = 0
    reported_calls = 0
    failures = 0
    with TestClient(app.app) as client:
        response = client.post(
            "/api/analyze-batch",
            files=files,
            data={"job_description": fixture["job_description"], "consent": "true"},
        )
    if response.status_code != 200:
        output = {
            "status": "failed",
            "http_status": response.status_code,
            "expected_live_requests": preflight["expected_live_requests"],
            "live_calls_reported": "unknown",
            "automatic_retries": 0,
            "no_retry_note": "The batch request was not retried. Check provider usage before another live run.",
        }
        OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(output, indent=2))
        return 1

    response_payload = response.json()
    result_by_id = {
        str(item.get("filename", "")).removesuffix(".pdf"): item
        for item in response_payload.get("results", [])
        if isinstance(item, dict)
    }
    for candidate in fixture["candidates"]:
        entry = result_by_id.get(candidate["id"], {})
        result = entry.get("result") if isinstance(entry, dict) else None
        if not isinstance(result, dict):
            failures += 1
            candidate_reports.append({
                "candidate_id": candidate["id"],
                "status": "failed",
                "expected_evidence_type": candidate["expected_evidence_type"],
                "expected_evidence_strength": candidate["expected_evidence_strength"],
            })
            continue

        expected = [{
            "requirement": job_requirement,
            "evidence_type": candidate["expected_evidence_type"],
        }]
        score, _totals = score_case({"id": candidate["id"], "expected": expected}, result)
        matched_label = next((
            item for item in score["item_labels"]
            if item.get("expected") == candidate["expected_evidence_type"]
        ), {})
        returned_findings = result.get("requirements", [])
        returned_findings = returned_findings if isinstance(returned_findings, list) else []
        finding_index = matched_label.get("result_finding_index")
        requirement = (
            returned_findings[finding_index - 1]
            if isinstance(finding_index, int)
            and 0 < finding_index <= len(returned_findings)
            and isinstance(returned_findings[finding_index - 1], dict)
            else {}
        )
        verification = result.get("verification_audit", {})
        verification = verification if isinstance(verification, dict) else {}
        rejected = [
            item for item in verification.get("rejected_citations", [])
            if isinstance(item, dict) and str(item.get("requirement_id", "")) == str(requirement.get("id", ""))
        ]
        evidence = requirement.get("evidence", []) if isinstance(requirement, dict) else []
        evidence = evidence if isinstance(evidence, list) else []
        rejected_details = []
        for record in rejected:
            if not record.get("quote"):
                continue
            page = record.get("cited_page")
            page = page if isinstance(page, int) and not isinstance(page, bool) and page > 0 else None
            rejected_details.append({
                "requirement_id": str(record.get("requirement_id", ""))[:32],
                "requirement": str(record.get("requirement", ""))[:180],
                "quote": str(record.get("quote", ""))[:360],
                "cited_page": page,
                "reason": str(record.get("reason", "unknown"))[:80],
            })
        usage = result.get("usage", {})
        usage = usage if isinstance(usage, dict) else {}
        total_input_tokens += max(0, int(usage.get("input_tokens", 0) or 0))
        total_output_tokens += max(0, int(usage.get("output_tokens", 0) or 0))
        reported_calls += max(0, int(result.get("analysis_calls", 0) or 0))
        actual_strength = str(matched_label.get("predicted_strength", "not_reported"))
        actual_type = str(matched_label.get("predicted", "unclassified"))
        adjudicated_type = str(matched_label.get("adjudicated", actual_type))
        candidate_reports.append({
            "candidate_id": candidate["id"],
            "status": "completed",
            "expected_evidence_type": candidate["expected_evidence_type"],
            "actual_evidence_type": actual_type if actual_type in LABELS else "unclassified",
            "adjudicated_evidence_type": adjudicated_type if adjudicated_type in LABELS else "unclassified",
            "expected_evidence_strength": candidate["expected_evidence_strength"],
            "actual_evidence_strength": actual_strength,
            "expected_label_matched": actual_type == candidate["expected_evidence_type"],
            "expected_strength_matched": actual_strength == candidate["expected_evidence_strength"],
            "matched_requirement_verified_quote_count": len(evidence),
            "matched_requirement_rejected_quote_count": len(rejected),
            "rejected_quote_details": rejected_details,
            "strength_distribution": score["evidence_strength_distribution"],
            "provider_reported_input_tokens": max(0, int(usage.get("input_tokens", 0) or 0)),
            "provider_reported_output_tokens": max(0, int(usage.get("output_tokens", 0) or 0)),
        })

    cost = (total_input_tokens * 1.25 + total_output_tokens * 4.25) / 1_000_000
    output = {
        "status": "completed_with_candidate_failures" if failures else "completed",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_label": "two_candidate_strength_ladder_demo",
        "provider": "muse",
        "model": app.MODEL_ID,
        "candidate_count": len(fixture["candidates"]),
        "expected_live_requests": preflight["expected_live_requests"],
        "live_calls_reported": reported_calls,
        "automatic_retries": 0,
        "failed_candidates": failures,
        "candidates": candidate_reports,
        "overall": {
            "expected_strength_labels_matched": sum(item.get("expected_strength_matched", False) for item in candidate_reports),
            "expected_category_labels_matched": sum(item.get("expected_label_matched", False) for item in candidate_reports),
            "matched_requirement_verified_quotes": sum(item.get("matched_requirement_verified_quote_count", 0) for item in candidate_reports),
            "matched_requirement_rejected_quotes": sum(item.get("matched_requirement_rejected_quote_count", 0) for item in candidate_reports),
            "provider_reported_input_tokens": total_input_tokens,
            "provider_reported_output_tokens": total_output_tokens,
            "estimated_standard_token_cost_usd": round(cost, 8),
            "cost_note": "Token-based estimate at the saved Muse Spark Standard rates; not a provider billing record.",
        },
        "fixture": FIXTURE.name,
        "observation_scope": "Strength distributions cover all returned findings. Category, strength match, and quote counts refer to the returned finding aligned to the prewritten focal requirement.",
        "disclosure": "Both CVs are fictional; the requirement is from the linked public job posting. Results are one small demonstration run, not an accuracy estimate.",
        "report_contains_cv_text": False,
        "report_contains_accepted_quote_text": False,
        "report_contains_rejected_quote_text": True,
    }
    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
