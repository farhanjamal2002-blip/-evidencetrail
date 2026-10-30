"""Run the ten remaining frozen metamorphic pairs through RC1's real API route.

Twenty fictional variants, one Muse request each, no retries. M02 and M07 were
already run and are deliberately excluded. Outputs preserve full app results
and authentic provider response IDs; no human ratings are collected.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import time

RESEARCH_ROOT = Path(__file__).resolve().parents[1]
FROZEN_ROOT = Path(os.environ.get("EVIDENCETRAIL_FROZEN_ROOT", "")).resolve()
CORPUS_PATH = RESEARCH_ROOT / "evaluation" / "RESEARCH_METAMORPHIC_PAIRS.json"
OUTPUT_ROOT = RESEARCH_ROOT / "artifacts" / "live-remaining-pairs-frozen-20261030"
EXPECTED_FROZEN_SHA = "8489e45ae0f87d8421562618bda556c31911372b"
PAIR_IDS = ("M01", "M03", "M04", "M05", "M06", "M08", "M09", "M10", "M11", "M12")
MAX_CALLS = len(PAIR_IDS) * 2
BUDGET_USD = 5.00
PRIOR_ESTIMATED_COST_USD = 0.0201655
STANDARD_RATE_USD_PER_MILLION = {"input": 1.25, "output": 4.25}

sys.path.insert(0, str(FROZEN_ROOT))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_cases() -> tuple[list[dict], str]:
    raw = CORPUS_PATH.read_bytes()
    corpus = json.loads(raw)
    if corpus.get("reference_provenance") != "author_labelled_synthetic":
        raise SystemExit("Wrong corpus provenance; no model calls made.")
    rows = {item.get("id"): item for item in corpus.get("pairs", [])}
    if set(PAIR_IDS) - set(rows):
        raise SystemExit("Required frozen pair missing; no model calls made.")
    if set(PAIR_IDS) & {"M02", "M07"}:
        raise SystemExit("Previously run pair selected; no model calls made.")
    selected = []
    for pair_id in PAIR_IDS:
        pair = rows[pair_id]
        if pair.get("expected_relation") not in {"invariant", "must_change"}:
            raise SystemExit(f"{pair_id}: invalid frozen relation; no calls.")
        for role in ("baseline", "variant"):
            case = pair[role]
            if case.get("authored_reference") not in {"supported", "not_found", "conflicting"}:
                raise SystemExit(f"{pair_id}-{role}: invalid frozen label; no calls.")
            if not isinstance(case.get("cv_text"), str) or not case["cv_text"].strip():
                raise SystemExit(f"{pair_id}-{role}: missing source text; no calls.")
        selected.append(pair)
    if len(selected) * 2 != MAX_CALLS:
        raise SystemExit("Request-count contract mismatch; no model calls made.")
    return selected, sha256(raw)


def make_pdf(case_id: str, case: dict) -> bytes:
    import pymupdf as fitz

    total_pages = case.get("total_pages", 1)
    evidence_page = case.get("evidence_page", 1)
    if not isinstance(total_pages, int) or total_pages < 1:
        raise ValueError(f"Invalid total_pages for {case_id}")
    if not isinstance(evidence_page, int) or not 1 <= evidence_page <= total_pages:
        raise ValueError(f"Invalid evidence_page for {case_id}")

    document = fitz.open()
    try:
        for page_number in range(1, total_pages + 1):
            page = document.new_page(width=612, height=792)
            page.insert_text((48, 44), f"FICTIONAL CV — {case_id} — page {page_number}", fontsize=11)
            if page_number == 1:
                page.insert_text((48, 68), "Synthetic evaluation document; no real applicant.", fontsize=9)
            if page_number == evidence_page:
                rect = fitz.Rect(48, 110, 564, 710)
                remaining = page.insert_textbox(
                    rect, case["cv_text"], fontsize=12, lineheight=1.4
                )
                if remaining < 0:
                    raise ValueError(f"CV text did not fit on {case_id} page {page_number}")
        return document.tobytes(garbage=4, deflate=True, clean=True)
    finally:
        document.close()


def estimate_usd(input_tokens: int, output_tokens: int) -> float:
    rates = STANDARD_RATE_USD_PER_MILLION
    return round(
        (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000,
        8,
    )


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    if not (FROZEN_ROOT / "app.py").is_file():
        raise SystemExit("Frozen RC1 app.py missing; no model calls made.")
    if os.getenv("EVIDENCETRAIL_FROZEN_SHA") != EXPECTED_FROZEN_SHA:
        raise SystemExit("Frozen code SHA mismatch; no model calls made.")

    pairs, corpus_sha = load_cases()
    if OUTPUT_ROOT.exists():
        raise SystemExit("Attempt/output directory already exists; refusing duplicate paid calls.")
    if os.getenv("EVIDENCETRAIL_PROVIDER", "").strip().casefold() != "muse":
        raise SystemExit("Muse provider not enabled; no model calls made.")
    if os.getenv("EVIDENCETRAIL_ENABLE_MUSE", "").strip().casefold() != "true":
        raise SystemExit("Explicit Muse opt-in missing; no model calls made.")
    if os.getenv("EVIDENCETRAIL_ENABLE_META_VISION", "false").strip().casefold() != "false":
        raise SystemExit("Native vision must remain disabled.")
    if not os.getenv("MODEL_API_KEY", "").strip():
        raise SystemExit("No configured model key; no model calls made.")

    import app

    if app.ANALYSIS_PROVIDER != "muse" or not app.MUSE_PROVIDER_ENABLED:
        raise SystemExit("Frozen app Muse configuration mismatch; no model calls made.")
    if not app.configured_model_api_key():
        raise SystemExit("Frozen app key preflight failed; no model calls made.")

    OUTPUT_ROOT.mkdir(parents=True)
    attempt_manifest = {
        "frozen_release_sha": EXPECTED_FROZEN_SHA,
        "challenge_sha256": corpus_sha,
        "pair_ids": list(PAIR_IDS),
        "previously_run_pairs_excluded": ["M02", "M07"],
        "requests_planned": MAX_CALLS,
        "automatic_retries": 0,
        "provider": app.ANALYSIS_PROVIDER,
        "model": app.MODEL_ID,
        "reasoning_effort": app.MUSE_REASONING_EFFORT,
        "analysis_prompt_sha256": sha256(app.SYSTEM_PROMPT.encode("utf-8")),
        "native_vision": False,
        "human_ratings": False,
        "prior_estimated_cost_usd": PRIOR_ESTIMATED_COST_USD,
        "budget_ceiling_usd": BUDGET_USD,
    }
    write_json(OUTPUT_ROOT / "attempt_started.json", attempt_manifest)

    from fastapi.testclient import TestClient

    outputs: list[dict] = []
    attempts = 0
    new_estimated_cost = 0.0
    stopped_for_budget = False
    started = time.perf_counter()
    with TestClient(app.app) as client:
        for pair in pairs:
            requirement = pair["requirement"]
            job_description = "FICTIONAL ROLE\nRequirement:\n" + requirement
            for role in ("baseline", "variant"):
                case = pair[role]
                case_id = f"{pair['id']}-{role}"
                pdf_bytes = make_pdf(case_id, case)
                pdf_hash = sha256(pdf_bytes)
                expected_page = case.get("evidence_page")
                total_pages = case.get("total_pages", 1)
                attempt_path = OUTPUT_ROOT / "attempts" / f"{case_id}.attempt"
                attempt_path.parent.mkdir(parents=True, exist_ok=True)
                attempt_path.write_text(
                    f"Exactly one request maximum; no retry. PDF SHA-256: {pdf_hash}\n",
                    encoding="utf-8",
                )
                attempts += 1
                record = {
                    "case_id": case_id,
                    "pair_id": pair["id"],
                    "role": role,
                    "single_change_factor": pair["single_change_factor"],
                    "expected_status": case["authored_reference"],
                    "expected_relation": pair["expected_relation"],
                    "expected_evidence_page": expected_page,
                    "expected_total_pages": total_pages,
                    "challenge_sha256": corpus_sha,
                    "input_pdf_sha256": pdf_hash,
                    "frozen_release_sha": EXPECTED_FROZEN_SHA,
                    "request_ordinal": attempts,
                    "automatic_retries": 0,
                    "native_vision": False,
                }
                case_started = time.perf_counter()
                try:
                    response = client.post(
                        "/api/analyze",
                        data={
                            "job_description": job_description,
                            "locked_rubric_json": json.dumps([requirement]),
                            "consent": "true",
                            "visual_review": "false",
                        },
                        files={"cv": (case_id + ".pdf", pdf_bytes, "application/pdf")},
                    )
                    record["http_status"] = response.status_code
                    record["elapsed_seconds"] = round(time.perf_counter() - case_started, 3)
                    if response.status_code == 200:
                        payload = response.json()
                        record["application_result"] = payload
                        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
                        analysis = usage.get("analysis_pass") if isinstance(usage.get("analysis_pass"), dict) else {}
                        record["provider_response_id"] = analysis.get("provider_response_id")
                        record["provider_receipt_present"] = bool(
                            isinstance(record["provider_response_id"], str)
                            and record["provider_response_id"].strip()
                        )
                        record["provider_mode"] = payload.get("provider_mode")
                        record["model"] = payload.get("model")
                        record["analysis_calls"] = payload.get("analysis_calls")
                        input_tokens = analysis.get("input_tokens", 0)
                        output_tokens = analysis.get("output_tokens", 0)
                        if isinstance(input_tokens, int) and isinstance(output_tokens, int):
                            new_estimated_cost += estimate_usd(input_tokens, output_tokens)
                        findings = payload.get("requirements")
                        if isinstance(findings, list):
                            summaries = []
                            for finding in findings:
                                if not isinstance(finding, dict):
                                    continue
                                citations = finding.get("evidence") or []
                                cited_pages = sorted({
                                    item.get("page") for item in citations
                                    if isinstance(item, dict) and isinstance(item.get("page"), int)
                                })
                                summaries.append({
                                    "requirement": finding.get("requirement"),
                                    "raw_status": finding.get("raw_status"),
                                    "final_status": finding.get("status"),
                                    "evidence_type": finding.get("evidence_type"),
                                    "cited_pages": cited_pages,
                                    "page_matches_expected": (
                                        cited_pages == [expected_page]
                                        if expected_page is not None else None
                                    ),
                                    "evidence": citations,
                                })
                            record["finding_summary"] = summaries
                        record["quote_audit"] = payload.get("quote_audit")
                        record["verification_audit"] = payload.get("verification_audit")
                        record["ocr_pages"] = payload.get("ocr_pages")
                        record["estimated_standard_cost_usd_total"] = round(
                            PRIOR_ESTIMATED_COST_USD + new_estimated_cost, 8
                        )
                    else:
                        try:
                            record["error_response"] = response.json()
                        except Exception:
                            record["error_response"] = {"detail": response.text[:2000]}
                        record["provider_receipt_present"] = False
                        record["call_cost_unknown"] = True
                    write_json(OUTPUT_ROOT / "cases" / f"{case_id}.json", record)
                except Exception as exc:
                    record["error_type"] = type(exc).__name__
                    record["provider_receipt_present"] = False
                    record["call_cost_unknown"] = True
                    record["elapsed_seconds"] = round(time.perf_counter() - case_started, 3)
                    write_json(OUTPUT_ROOT / "cases" / f"{case_id}.json", record)
                    outputs.append(record)
                    continue
                outputs.append(record)
                if PRIOR_ESTIMATED_COST_USD + new_estimated_cost >= BUDGET_USD:
                    stopped_for_budget = attempts < MAX_CALLS
                    if stopped_for_budget:
                        break
            if stopped_for_budget:
                break

    successful = [
        row for row in outputs
        if row.get("http_status") == 200 and row.get("provider_receipt_present")
        and row.get("provider_mode") == "muse" and row.get("analysis_calls") == 1
    ]
    by_pair = []
    for pair in pairs:
        records = {row.get("role"): row for row in outputs if row.get("pair_id") == pair["id"]}
        statuses = {}
        for role in ("baseline", "variant"):
            row = records.get(role, {})
            summaries = row.get("finding_summary") or []
            statuses[role] = {
                "expected": row.get("expected_status"),
                "raw": summaries[0].get("raw_status") if summaries else None,
                "final": summaries[0].get("final_status") if summaries else None,
                "final_matches_author_reference": (
                    summaries[0].get("final_status") == row.get("expected_status")
                    if summaries and row.get("expected_status") is not None else False
                ),
            }
        expected_invariant = pair["expected_relation"] == "invariant"
        observed_invariant = (
            statuses["baseline"]["final"] == statuses["variant"]["final"]
            if statuses["baseline"]["final"] is not None and statuses["variant"]["final"] is not None
            else None
        )
        by_pair.append({
            "pair_id": pair["id"],
            "factor": pair["single_change_factor"],
            "expected_relation": pair["expected_relation"],
            "observed_relation": (
                "invariant" if observed_invariant else "changed"
                if observed_invariant is not None else None
            ),
            "relation_matches_expectation": (
                observed_invariant == expected_invariant
                if observed_invariant is not None else False
            ),
            "variants": statuses,
        })

    summary = {
        "status": "completed" if len(successful) == MAX_CALLS else "partial_or_failed",
        "frozen_release_sha": EXPECTED_FROZEN_SHA,
        "challenge_sha256": corpus_sha,
        "pair_ids": list(PAIR_IDS),
        "previously_run_pairs_excluded": ["M02", "M07"],
        "pair_count": len(pairs),
        "case_count": len(outputs),
        "requests_planned": MAX_CALLS,
        "requests_attempted": attempts,
        "successful_authentic_receipts": len(successful),
        "all_failures_retained": True,
        "automatic_retries": 0,
        "native_vision": False,
        "human_ratings": False,
        "provider": app.ANALYSIS_PROVIDER,
        "model": app.MODEL_ID,
        "reasoning_effort": app.MUSE_REASONING_EFFORT,
        "analysis_prompt_sha256": sha256(app.SYSTEM_PROMPT.encode("utf-8")),
        "new_estimated_standard_cost_usd": round(new_estimated_cost, 8),
        "prior_estimated_standard_cost_usd": PRIOR_ESTIMATED_COST_USD,
        "combined_estimated_standard_cost_usd": round(
            PRIOR_ESTIMATED_COST_USD + new_estimated_cost, 8
        ),
        "cost_estimate_is_not_provider_invoice": True,
        "budget_ceiling_usd": BUDGET_USD,
        "stopped_for_budget": stopped_for_budget,
        "wall_seconds": round(time.perf_counter() - started, 3),
        "cases": [
            {
                "case_id": row.get("case_id"),
                "expected_status": row.get("expected_status"),
                "http_status": row.get("http_status"),
                "provider_receipt_present": row.get("provider_receipt_present", False),
                "raw_status": (row.get("finding_summary") or [{}])[0].get("raw_status"),
                "final_status": (row.get("finding_summary") or [{}])[0].get("final_status"),
                "expected_evidence_page": row.get("expected_evidence_page"),
                "cited_pages": (row.get("finding_summary") or [{}])[0].get("cited_pages"),
                "page_matches_expected": (row.get("finding_summary") or [{}])[0].get("page_matches_expected"),
            }
            for row in outputs
        ],
        "pairs": by_pair,
        "limitations": [
            "Author-labelled fictional tests only; not independent or representative accuracy.",
            "A genuine provider receipt proves a call occurred, not that its semantic label is correct.",
            "Page/quote verification does not prove real-world truth of a CV statement.",
            "No retries; usage for failed requests may be unknown.",
            "M08 moves the same sentence to page 1 versus page 3 in a controlled three-page PDF.",
        ],
    }
    write_json(OUTPUT_ROOT / "run.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
