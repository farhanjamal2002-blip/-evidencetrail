"""Zero-paid-call judge evidence and reproducibility preflight.

Produces an auditable inventory of exactly what the frozen fictional replay
can prove. A passing local preflight is NOT proof of public deployment,
eligibility, an official judge score, or real-world recruiting accuracy.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from demo20_workflow import (
    CASES, CRITERIA, JOB, _load_verified_recording, make_cv_pdf,
)

OUTPUT = Path("artifacts/judge-readiness/preflight.json")


def _sha() -> str:
    if os.getenv("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=3
        ).strip()
    except Exception:
        return "unknown"


def report() -> dict:
    issues: list[str] = []
    data = _load_verified_recording()  # Validates fixture/job/rubric hashes.
    rows = data["results"]
    ids = [r["id"] for r in rows]
    if len(CASES) != 20 or len(rows) != 20 or len(set(ids)) != 20:
        issues.append("The published 20-applicant replay is incomplete or duplicated.")
    if any(len(row.get("requirements") or []) != len(CRITERIA) for row in rows):
        issues.append("At least one recorded applicant lacks a complete job rubric.")
    api_calls = sum(int(row.get("analysis_calls") or 0) for row in rows)
    if api_calls != len(rows):
        issues.append("Saved genuine model-call receipts do not total one per CV.")
    if any(row.get("provider_mode") != "muse" or not row.get("receipt") for row in rows):
        issues.append("At least one recorded analysis lacks its genuine Muse receipt.")

    proposed = verified = excluded = retained = 0
    quote_problems: list[str] = []
    for row in rows:
        qa = row.get("quote_audit") or {}
        p, v, x = (qa.get(k) for k in ("proposed", "verified", "excluded"))
        if not all(type(num) is int and num >= 0 for num in (p, v, x)):
            quote_problems.append(row["id"] + ": incomplete quote counters")
            continue
        if p != v + x:
            quote_problems.append(row["id"] + ": proposed does not equal verified plus excluded")
        proposed += p
        verified += v
        excluded += x
        retained += sum(len(q.get("evidence") or []) for q in row["requirements"])
        if row.get("cv_sha256") != hashlib.sha256(make_cv_pdf(row["id"])).hexdigest():
            quote_problems.append(row["id"] + ": actual fictional CV PDF hash mismatch")
    issues.extend(quote_problems)

    by_id = {r["id"]: r for r in rows}
    def changes(ident: str) -> list[dict]:
        return [
            {
                "criterion": i + 1, "raw": q.get("raw_status"),
                "final": q.get("status"),
            }
            for i, q in enumerate(by_id[ident]["requirements"])
            if q.get("raw_status") != q.get("status")
        ]

    if "ET-003" not in by_id or not any(
        c["raw"] == "supported" and c["final"] == "not_found"
        for c in changes("ET-003")
    ):
        issues.append("Demo anchor ET-003 no longer shows authentic Muse-to-local correction.")
    if "ET-015" not in by_id or not any(
        {e.get("role") for e in q.get("evidence") or []}
        >= {"supports", "contradicts"}
        for q in by_id["ET-015"]["requirements"]
    ):
        issues.append("Demo anchor ET-015 has no two-sided CV statements.")
    if not any(item[0] == "ET-019" and item[3].startswith("Scanned") for item in CASES):
        issues.append("Document OCR demo anchor ET-019 is not actually scanned.")
    if "ET-018" not in by_id or any(
        q.get("status") == "supported" for q in by_id["ET-018"]["requirements"]
    ):
        issues.append("Prompt-injection anchor ET-018 unexpectedly has supported results.")
    if verified < retained:
        issues.append("More individual citations retained than source checks verified.")

    return {
        "schema": "evidencetrail/judge-readiness-preflight/v1",
        "git_commit": _sha(),
        "evaluation_kind": "fixed fictional replay, recorded genuine Meta Muse requests",
        "job_sha256": hashlib.sha256(JOB.encode()).hexdigest(),
        "model_calls_when_running_this_preflight": 0,
        "model_receipts_in_historical_record": api_calls,
        "fictional_cv_count": len(rows),
        "requirement_judgments": sum(len(row["requirements"]) for row in rows),
        "quote_counters": {
            "proposed": proposed, "source_checked": verified,
            "excluded_by_page_check": excluded, "retained_individual_citations": retained,
        },
        "demonstrable_anchors": {
            "ET-003": {
                "purpose": "actual saved raw-to-final semantic corrections",
                "corrections": changes("ET-003"),
            },
            "ET-015": {
                "purpose": "opposing first-person CV passages for clarification",
                "no_claim_of_external_truth": True,
            },
            "ET-018": {
                "purpose": "fixture with instruction-injection text and no supported final labels",
                "not_a_general_prompt_injection_resistance_rate": True,
            },
            "ET-019": {
                "purpose": "image-only fictional CV using local OCR",
                "not_proof_of_a_live_image_input_to_muse": True,
            },
        },
        "external_gates_not_proven_here": [
            "final deployed public URL uses this exact git commit",
            "signed-out cold-start and mobile links work",
            "registered track, accepted rules and eligibility are confirmed",
            "final judge video is recorded and accessible",
            "time savings are independently measured",
            "direct Muse image-input API call succeeds with a genuine provider receipt",
            "candidate source claims are independently true",
            "performance or accuracy on a representative real-world population",
        ],
        "errors": issues,
        "local_preflight_passed": not issues,
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result = report()
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "passed": result["local_preflight_passed"],
        "historical_model_receipts": result["model_receipts_in_historical_record"],
        "replay_criteria": result["requirement_judgments"],
        "quote_counts": result["quote_counters"],
        "errors": result["errors"],
        "unverified_external_gates": len(result["external_gates_not_proven_here"]),
    }, indent=2))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
