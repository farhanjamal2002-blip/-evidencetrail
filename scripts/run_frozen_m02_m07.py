"""Run the frozen RC1 API route on M02 and M07 paired fictional cases.

The script makes exactly one live request per predeclared case variant. It
captures each complete application result and provider response ID, marks each
attempt before sending, and never retries. It does not collect human ratings.
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
OUTPUT_ROOT = RESEARCH_ROOT / "artifacts" / "live-m02-m07-frozen-20261030"
EXPECTED_FROZEN_SHA = "8489e45ae0f87d8421562618bda556c31911372b"
MAX_CALLS = 4
BUDGET_USD = 5.00
STANDARD_RATE_USD_PER_MILLION = {"input": 1.25, "output": 4.25}
PAIR_IDS = ("M02", "M07")

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
    selected = []
    for pair_id in PAIR_IDS:
        pair = rows[pair_id]
        if pair["expected_relation"] != "must_change":
            raise SystemExit(f"{pair_id}: expected relation mismatch; no calls.")
        selected.append(pair)
    if len(selected) * 2 != MAX_CALLS:
        raise SystemExit("Request-count contract mismatch; no model calls made.")
    return selected, sha256(raw)


def make_pdf(case_id: str, cv_text: str) -> bytes:
    import pymupdf as fitz

    document = fitz.open()
    try:
        page = document.new_page(width=612, height=792)
        page.insert_text((48, 48), f"FICTIONAL CV — {case_id}", fontsize=14)
        page.insert_text((48, 72), "Synthetic evaluation document; no real applicant.", fontsize=9)
        rect = fitz.Rect(48, 110, 564, 710)
        remaining = page.insert_textbox(rect, cv_text, fontsize=12, lineheight=1.4)
        if remaining < 0:
            raise ValueError(f"CV text did not fit on the page for {case_id}")
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
    if FROZEN_ROOT.name != "release" and not (FROZEN_ROOT / "app.py").is_file():
        raise SystemExit("Frozen RC1 checkout missing; no model calls made.")
    if not (FROZEN_ROOT / "app.py").is_file():
        raise SystemExit("Frozen RC1 app.py missing; no model calls made.")
    try:
        frozen_sha = os.environ["EVIDENCETRAIL_FROZEN_SHA"]
    except KeyError:
        raise SystemExit("Frozen code SHA missing; no model calls made.")
    if frozen_sha != EXPECTED_FROZEN_SHA:
        raise SystemExit("Frozen code SHA mismatch; no model calls made.")

    pairs, corpus_sha = load_cases()
    if OUTPUT_ROOT.exists():
        raise SystemExit("Attempt/output directory already exists; refusing duplicate paid calls.")
    if os.getenv("EVIDENCETRAIL_PROVIDER", "").strip().casefold() != "muse":
        raise SystemExit("Muse provider not enabled; no model calls made.")
    if os.getenv("EVIDENCETRAIL_ENABLE_MUSE", "").strip().casefold() != "true":
        raise SystemExit("Explicit Muse opt-in missing; no model calls made.")
    if os.getenv("EVIDENCETRAIL_ENABLE_META_VISION", "false").strip().casefold() != "false":
        raise SystemExit("Native vision must remain disabled for this text-only test.")
    if not os.getenv("MODEL_API_KEY", "").strip():
        raise SystemExit("No configured model key; no model calls made.")

    import app

    if app.ANALYSIS_PROVIDER != "muse" or not app.MUSE_PROVIDER_ENABLED:
        raise SystemExit("Frozen app Muse configuration mismatch; no model calls made.")
    if not app.configured_model_api_key():
        raise SystemExit("Frozen app key preflight failed; no model calls made.")

    OUTPUT_ROOT.mkdir(parents=True)
    (OUTPUT_ROOT / "attempt_started.json").write_text(
        json.dumps(
            {
                "frozen_release_sha": EXPECTED_FROZEN_SHA,
                "challenge_sha256": corpus_sha,
                "pair_ids": list(PAIR_IDS),
                "requests_max": MAX_CALLS,
                "requests_planned": MAX_CALLS,
                "automatic_retries": 0,
                "provider": app.ANALYSIS_PROVIDER,
                "model": app.MODEL_ID,
                "reasoning_effort": app.MUSE_REASONING_EFFORT,
                "analysis_prompt_sha256": sha256(app.SYSTEM_PROMPT.encode("utf-8")),
                "native_vision": False,
                "human_ratings": False,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    from fastapi.testclient import TestClient

    outputs: list[dict] = []
    attempts = 0
    estimated_total = 0.0
    stopped_for_budget = False
    started = time.perf_counter()
    with TestClient(app.app) as client:
        for pair in pairs:
            requirement = pair["requirement"]
            job_description = "FICTIONAL ROLE\nRequirement:\n" + requirement
            for role in ("baseline", "variant"):
                case = pair[role]
                case_id = f"{pair['id']}-{role}"
                pdf_bytes = make_pdf(case_id, case["cv_text"])
                input_hash = sha256(pdf_bytes)
                attempt_path = OUTPUT_ROOT / "attempts" / f"{case_id}.attempt"
                attempt_path.parent.mkdir(parents=True, exist_ok=True)
                attempt_path.write_text(
                    f"One request maximum; no retry. Input SHA-256: {input_hash}\n",
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
                    "challenge_sha256": corpus_sha,
                    "input_pdf_sha256": input_hash,
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
                            estimated_total += estimate_usd(input_tokens, output_tokens)
                        findings = payload.get("requirements")
                        if isinstance(findings, list):
                            record["finding_summary"] = [
                                {
                                    "requirement": finding.get("requirement"),
                                    "raw_status": finding.get("raw_status"),
                                    "final_status": finding.get("status"),
                                    "evidence_type": finding.get("evidence_type"),
                                    "evidence": finding.get("evidence"),
                                }
                                for finding in findings
                                if isinstance(finding, dict)
                            ]
                        record["estimated_standard_cost_usd_so_far"] = round(estimated_total, 8)
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
                    # Never retry; continue with the remaining predeclared cases.
                    continue
                outputs.append(record)
                if estimated_total >= BUDGET_USD:
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
    summary = {
        "status": "completed" if len(successful) == MAX_CALLS else "partial_or_failed",
        "frozen_release_sha": EXPECTED_FROZEN_SHA,
        "challenge_sha256": corpus_sha,
        "pair_ids": list(PAIR_IDS),
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
        "estimated_standard_cost_usd": round(estimated_total, 8),
        "cost_estimate_is_not_provider_invoice": True,
        "budget_ceiling_usd": BUDGET_USD,
        "stopped_for_budget": stopped_for_budget,
        "wall_seconds": round(time.perf_counter() - started, 3),
        "limitations": [
            "Two author-labelled fictional pairs; not human-rated and not representative accuracy.",
            "A real provider receipt proves a call occurred, not that its semantic label is correct.",
            "Page/quote verification does not prove real-world truth of a CV statement.",
            "No retries; usage for failed requests may be unknown.",
        ],
        "cases": [
            {
                "case_id": row.get("case_id"),
                "expected_status": row.get("expected_status"),
                "http_status": row.get("http_status"),
                "provider_receipt_present": row.get("provider_receipt_present", False),
                "raw_status": (row.get("finding_summary") or [{}])[0].get("raw_status"),
                "final_status": (row.get("finding_summary") or [{}])[0].get("final_status"),
            }
            for row in outputs
        ],
    }
    write_json(OUTPUT_ROOT / "run.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
