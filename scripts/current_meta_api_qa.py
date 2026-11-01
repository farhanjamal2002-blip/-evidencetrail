"""Live Meta Muse QA against the *current* EvidenceTrail branch.

Exactly eight fictional CV analyses, one request each, no model retries.
Preserves genuine receipts, requirement labels, verification counters and latency.
Does NOT update the public saved judge replay or touch real candidate data.
"""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from fastapi.testclient import TestClient

import app
from demo20_workflow import CRITERIA, JOB, make_cv_pdf

OUT = Path("artifacts/current-meta-api-qa")
OUT.mkdir(parents=True, exist_ok=True)
assert app.ANALYSIS_PROVIDER == "muse", "This must use actual Muse, not mock"
assert app.MUSE_PROVIDER_ENABLED, "Muse is not enabled"
assert app.configured_model_api_key(), "Missing server-side Meta key"

# Direct, weak/adjacent skills, non-procurement, keyword-only, contradictory
# employment and responsibilities, malicious PDF instruction and image OCR.
IDS = ["ET-002", "ET-006", "ET-009", "ET-013", "ET-015", "ET-016", "ET-018", "ET-020"]
# Material constraints the fictional CV objectively does NOT establish.
MUST_NOT_SUPPORT = {
    "ET-006": [2, 3, 4],
    "ET-009": [1, 2, 3, 4],
    "ET-013": [1, 2, 3, 4],
    "ET-015": [1, 2, 4],
    "ET-016": [2, 3],
    "ET-018": [1, 2, 3, 4],
    "ET-020": [2, 3],
}
# Evidence a human can verify does occur in the fictional CV. Assess for misses.
EXPECTED_DIRECT = {"ET-002": [1, 2, 3, 4], "ET-016": [4], "ET-020": [4]}
results, failures, warnings = [], [], []
start = time.monotonic()

with TestClient(app.app) as client:
    # Never charge for a CV without the user's explicit consent.
    no_consent = client.post(
        "/api/analyze",
        data={"job_description": JOB, "locked_rubric_json": json.dumps(CRITERIA)},
        files={"cv": ("fictional.pdf", make_cv_pdf("ET-002"), "application/pdf")},
    )
    assert no_consent.status_code == 400, f"Consent gate broken: {no_consent.status_code}"
    print("META_QA_PREFLIGHT=" + json.dumps({"no_consent_status": no_consent.status_code, "expect": 400}), flush=True)

    for cid in IDS:
        # Every marker blocks an accidental same-run second request.
        marker = OUT / f"{cid}.attempt.json"
        assert not marker.exists(), "Refusing duplicate Meta request for " + cid
        marker.write_text(json.dumps({"candidate": cid, "attempted": True, "retries": 0}) + "\n")
        began = time.monotonic()
        try:
            response = client.post(
                "/api/analyze",
                data={"job_description": JOB, "locked_rubric_json": json.dumps(CRITERIA), "consent": "true"},
                files={"cv": (f"{cid}.pdf", make_cv_pdf(cid), "application/pdf")},
            )
            duration = round(time.monotonic() - began, 3)
            row = {"id": cid, "http_status": response.status_code, "elapsed_seconds": duration}
            if response.status_code != 200:
                try: row["error"] = str(response.json().get("detail", "unknown"))[:220]
                except ValueError: row["error"] = "non-json API failure"
                failures.append({"id": cid, "reason": "live HTTP failure", "http": response.status_code})
                results.append(row)
                print("META_QA_CASE=" + json.dumps(row), flush=True)
                continue

            data = response.json()
            fields = data.get("requirements") or []
            usage = data.get("usage") or {}
            receipt = (usage.get("analysis_pass") or {}).get("provider_response_id")
            quote = data.get("quote_audit") or {}
            row.update({
                "provider": data.get("provider_mode"),
                "model": data.get("model"),
                "real_provider_receipt_present": isinstance(receipt, str) and bool(receipt.strip()),
                "provider_receipt": receipt if isinstance(receipt,str) else None,
                "reported_api_calls": data.get("analysis_calls"),
                "requirements": len(fields),
                "raw_status_count": sum(bool(f.get("raw_status") or f.get("muse_status")) for f in fields),
                "effective_status_count": sum(f.get("effective_status") == f.get("status") for f in fields),
                "proposed_quotes": quote.get("proposed", 0),
                "verified_quotes": quote.get("verified", 0),
                "excluded_quotes": quote.get("excluded", 0),
                "ocr_pages": data.get("ocr_pages") or [],
                "outcomes": [
                    {"requirement": i + 1, "status": f.get("status"),
                     "evidence_type": f.get("evidence_type"),
                     "raw_status": f.get("raw_status") or f.get("muse_status"),
                     "evidence_count": len(f.get("evidence") or [])}
                    for i,f in enumerate(fields)
                ],
            })
            if row["provider"] != "muse" or not row["real_provider_receipt_present"] or row["reported_api_calls"] != 1:
                failures.append({"id": cid, "reason": "provider authenticity or call count"})
            if len(fields) != len(CRITERIA) or row["raw_status_count"] != 4 or row["effective_status_count"] != 4:
                failures.append({"id": cid, "reason": "incomplete requirement or status audit"})
            if row["verified_quotes"] > row["proposed_quotes"]:
                failures.append({"id": cid, "reason": "impossible quote verification counts"})
            for k,f in enumerate(fields, 1):
                if f.get("status") == "supported" and f.get("evidence_type") != "direct":
                    failures.append({"id": cid, "requirement": k, "reason": "non-direct quote was allowed to prove a criterion"})
                if k in MUST_NOT_SUPPORT.get(cid, []) and f.get("status") == "supported":
                    failures.append({"id": cid, "requirement": k, "reason": "false support on human-known fictional negative"})
                if k in EXPECTED_DIRECT.get(cid, []) and f.get("status") != "supported":
                    warnings.append({"id": cid, "requirement": k, "reason": "potential missed direct experience"})
            if cid == "ET-020" and 1 not in row["ocr_pages"]:
                failures.append({"id": cid, "reason": "scanned CV was processed without OCR"})
            results.append(row)
            # Hide complete receipt from CI stdout while retain authentic ID in artifact.
            public_row = {k:v for k,v in row.items() if k!="provider_receipt"}
            print("META_QA_CASE=" + json.dumps(public_row), flush=True)
        except Exception as exc:
            failures.append({"id": cid, "reason": "exception", "type": type(exc).__name__})
            results.append({"id": cid, "exception_type": type(exc).__name__})
            print("META_QA_CASE=" + json.dumps({"id":cid,"exception_type":type(exc).__name__}),flush=True)

durations = [r["elapsed_seconds"] for r in results if r.get("http_status") == 200]
durations_sorted = sorted(durations)
summary = {
    "live_meta_model_calls": sum(r.get("reported_api_calls") or 0 for r in results),
    "fictional_cases": len(IDS),
    "successes": len(durations),
    "authentic_receipts": sum(bool(r.get("real_provider_receipt_present")) for r in results),
    "consent_without_opt_in_http": no_consent.status_code,
    "quote_proposed": sum(r.get("proposed_quotes") or 0 for r in results),
    "quote_verified": sum(r.get("verified_quotes") or 0 for r in results),
    "quote_excluded": sum(r.get("excluded_quotes") or 0 for r in results),
    "raw_status_fields": sum(r.get("raw_status_count") or 0 for r in results),
    "median_seconds_per_cv": statistics.median(durations) if durations else None,
    "p95_seconds_per_cv": durations_sorted[min(len(durations_sorted)-1, int(len(durations_sorted)*0.95))] if durations else None,
    "test_wall_seconds": round(time.monotonic()-start,3),
    "hard_failures": failures,
    "quality_warnings": warnings,
    "disclosure": "Real Meta Model API calls on eight fictional PDFs; no retries, not a production SLA or real hiring evaluation.",
}
(OUT/"report.json").write_text(json.dumps({"summary":summary, "cases":results},ensure_ascii=False,indent=2)+"\n")
print("META_QA_SUMMARY="+json.dumps(summary),flush=True)
if failures:
    raise SystemExit(1)
