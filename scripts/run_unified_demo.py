#!/usr/bin/env python3
"""Preflight or run the single-job, five-CV fictional EvidenceTrail demo.

The live path submits one batch to the local application. The application makes
one Muse request per CV, then verifies quotes and dates locally. No retries are
enabled in the Meta client or runner.
The replay artifact intentionally contains only fictional CV results and is
kept separate from the expected-label calibration report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "calibration" / "unified_supplier_operations_demo_20261028_v2.json"
ASSET_DIR = ROOT / "calibration" / "unified_demo_assets_v2"
METRICS_FILE = ROOT / "calibration" / "unified_demo_metrics_20261028_v2.json"
REPLAY_FILE = ROOT / "calibration" / "unified_demo_replay_20261028_v2.json"
ATTEMPT_FILE = ROOT / "calibration" / "unified_demo_attempt_20261028_v2.json"
RUN_SUFFIX_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
sys.path.insert(0, str(ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--preflight-only", action="store_true")
    group.add_argument("--confirm-live-call", action="store_true")
    parser.add_argument(
        "--fixture",
        help="Calibration fixture JSON under calibration/ (defaults to the frozen v2 fixture).",
    )
    parser.add_argument(
        "--run-suffix",
        help=(
            "Write this run to separate immutable calibration artifacts, for example "
            "hardened_medium_20261029. Letters, digits, underscores, and hyphens only."
        ),
    )
    return parser.parse_args()


def artifact_paths(run_suffix: str | None) -> tuple[Path, Path, Path]:
    """Return metrics, replay, and attempt paths without overwriting prior runs."""
    if run_suffix is None:
        return METRICS_FILE, REPLAY_FILE, ATTEMPT_FILE
    if not RUN_SUFFIX_RE.fullmatch(run_suffix):
        raise ValueError("Run suffix must use 1–64 letters, digits, underscores, or hyphens.")
    return tuple(
        ROOT / "calibration" / f"unified_demo_{kind}_{run_suffix}.json"
        for kind in ("metrics", "replay", "attempt")
    )


def resolve_fixture_path(value: str | None) -> Path:
    if not value:
        return FIXTURE
    path = Path(value)
    path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    calibration_root = (ROOT / "calibration").resolve()
    if path == calibration_root or calibration_root not in path.parents:
        raise ValueError("The fixture path must point to a file under calibration/.")
    if path.suffix.casefold() != ".json":
        raise ValueError("The fixture must be a JSON file.")
    return path


def load_fixture(fixture_path: Path = FIXTURE) -> dict[str, Any]:
    value = json.loads(fixture_path.read_text(encoding="utf-8"))
    candidates = value.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 5:
        raise ValueError("The unified demo fixture must contain exactly five CVs.")
    job = value.get("job_description")
    if not isinstance(job, str) or not job.strip():
        raise ValueError("The unified demo needs one nonempty job description.")
    for candidate in candidates:
        if not isinstance(candidate, dict) or "FICTIONAL CV" not in str(candidate.get("cv_pages")):
            raise ValueError("Every unified demo profile must be explicitly fictional.")
        if not isinstance(candidate.get("expected"), list) or not candidate["expected"]:
            raise ValueError("Every CV needs prewritten expected findings.")
    return value


def build_assets(
    fixture: dict[str, Any], asset_dir: Path = ASSET_DIR
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    import pymupdf as fitz
    import app
    from scripts.evaluate_semantic_cases import make_case_pdf

    asset_dir.mkdir(parents=True, exist_ok=True)
    candidate_rows: list[dict[str, Any]] = []
    asset_checks: list[dict[str, Any]] = []
    for index, candidate in enumerate(fixture["candidates"], start=1):
        pdf = make_case_pdf(candidate)
        filename = f"{candidate['id']}.pdf"
        output_path = asset_dir / filename
        output_path.write_bytes(pdf)
        extracted = app.extract_pdf(pdf)
        document = fitz.open(stream=pdf, filetype="pdf")
        native_text_length = sum(len(page.get_text().strip()) for page in document)
        image_count = sum(len(page.get_images(full=True)) for page in document)
        document.close()
        ocr_pages = [page["number"] for page in extracted if page.get("ocr_used")]
        scanned = candidate.get("cv_variant") == "image-only two-column scan"
        if scanned and (native_text_length or not ocr_pages or not image_count):
            raise ValueError(
                f"{filename} must be an image-only PDF that exercises OCR; preflight stopped."
            )
        if not scanned and not any(str(page.get("text", "")).strip() for page in extracted):
            raise ValueError(f"{filename} has no extractable text; preflight stopped.")
        candidate_rows.append({
            "candidate_id": f"C{index}",
            "fixture_id": candidate["id"],
            "display_name": candidate.get("display_name", f"Candidate {index}"),
            "filename": filename,
            "path": str(output_path.relative_to(ROOT)),
            "bytes": len(pdf),
        })
        asset_checks.append({
            "candidate_id": candidate["id"],
            "native_text_characters": native_text_length,
            "image_count": image_count,
            "ocr_pages": ocr_pages,
            "is_image_only_scan": scanned,
        })
    return candidate_rows, asset_checks


def strength_matches(case: dict[str, Any], result: dict[str, Any]) -> list[dict[str, Any]]:
    from scripts.evaluate_semantic_cases import align_findings

    expected = case.get("expected", [])
    returned = result.get("requirements", [])
    if not isinstance(expected, list):
        expected = []
    if not isinstance(returned, list):
        returned = []
    aligned, missing, _unmatched = align_findings(expected, returned)
    rows: list[dict[str, Any]] = []
    aligned_gold = {gold_index for gold_index, _result_index, _score in aligned}
    result_for_gold = {gold_index: result_index for gold_index, result_index, _score in aligned}
    for gold_index, item in enumerate(expected):
        wanted = item.get("evidence_strength")
        if wanted not in {"specific", "stated", "keyword_only", "none"}:
            continue
        result_index = result_for_gold.get(gold_index)
        predicted = (
            returned[result_index].get("evidence_strength")
            if result_index is not None and isinstance(returned[result_index], dict)
            else "not_reported"
        )
        rows.append({
            "gold_item": gold_index + 1,
            "expected": wanted,
            "predicted": predicted,
            "matched": predicted == wanted,
            "finding_index": result_index + 1 if result_index is not None else None,
        })
    return rows


def main() -> int:
    args = parse_args()
    try:
        metrics_file, replay_file, attempt_file = artifact_paths(args.run_suffix)
        fixture_path = resolve_fixture_path(args.fixture)
    except ValueError as exc:
        print(json.dumps({
            "status": "blocked",
            "reason": str(exc),
            "live_calls_made": 0,
        }, indent=2))
        return 2
    fixture = load_fixture(fixture_path)
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
        from scripts.evaluate_semantic_cases import score_case
    except ModuleNotFoundError as exc:
        print(json.dumps({
            "status": "blocked",
            "reason": "A project dependency is missing; no Muse request was made.",
            "missing_dependency": exc.name or "unknown",
            "live_calls_made": 0,
        }, indent=2))
        return 2

    asset_dir = (
        ROOT / "calibration" / f"unified_demo_assets_{args.run_suffix}"
        if args.run_suffix
        else ASSET_DIR
    )
    candidate_rows, asset_checks = build_assets(fixture, asset_dir)
    fixture_sha256 = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    system_prompt_sha256 = hashlib.sha256(app.SYSTEM_PROMPT.encode("utf-8")).hexdigest()
    preflight = {
        "demo_id": fixture["demo_id"],
        "rubric_version": fixture["rubric_version"],
        "provider": provider,
        "model": app.MODEL_ID,
        "reasoning_effort": app.MUSE_REASONING_EFFORT,
        "system_prompt_sha256": system_prompt_sha256,
        "fixture_sha256": fixture_sha256,
        "server_key_configured": key_configured,
        "candidate_count": len(candidate_rows),
        "one_shared_job_description": True,
        "expected_live_requests": len(candidate_rows),
        "automatic_retries": 0,
        "asset_checks": asset_checks,
        "pdf_assets": candidate_rows,
        "fixture": str(fixture_path.relative_to(ROOT)),
        "metrics_output": str(metrics_file.relative_to(ROOT)),
        "replay_output": str(replay_file.relative_to(ROOT)),
        "attempt_log": str(attempt_file.relative_to(ROOT)),
        "prior_attempt_record_exists": attempt_file.exists(),
        "no_model_requests_made": True,
    }
    if provider != "muse" or app.ANALYSIS_PROVIDER != "muse":
        print(json.dumps({"status": "blocked", "reason": "Configured provider is not Muse; no request was made.", **preflight}, indent=2))
        return 2
    if not key_configured:
        print(json.dumps({"status": "blocked", "reason": "MODEL_API_KEY is not configured; no request was made.", **preflight}, indent=2))
        return 2
    if args.confirm_live_call and attempt_file.exists():
        print(json.dumps({
            "status": "blocked_prior_attempt",
            "reason": "A live-run attempt is already recorded. No new Muse request was made. Check provider usage before deliberately clearing the attempt record.",
            "live_calls_made": 0,
            **preflight,
        }, indent=2))
        return 2
    if args.preflight_only or not args.confirm_live_call:
        print(json.dumps({"status": "ready_for_review", **preflight}, indent=2))
        return 0

    files = [
        (
            "cvs",
            (row["filename"], (ROOT / row["path"]).read_bytes(), "application/pdf"),
        )
        for row in candidate_rows
    ]
    attempt = {
        "demo_id": fixture["demo_id"],
        "rubric_version": fixture["rubric_version"],
        "status": "running",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider": "muse",
        "model": app.MODEL_ID,
        "reasoning_effort": app.MUSE_REASONING_EFFORT,
        "system_prompt_sha256": system_prompt_sha256,
        "fixture_sha256": fixture_sha256,
        "expected_live_requests": preflight["expected_live_requests"],
        "automatic_retries": 0,
        "retry_policy": "No request is automatically retried.",
        "live_calls_reported": None,
        "warning": "A started run may incur provider usage even if the client does not receive a final report.",
    }
    attempt_file.write_text(json.dumps(attempt, indent=2) + "\n", encoding="utf-8")
    started = time.monotonic()
    try:
        with TestClient(app.app) as client:
            response = client.post(
                "/api/analyze-batch",
                files=files,
                data={"job_description": fixture["job_description"], "consent": "true"},
            )
    except KeyboardInterrupt:
        attempt.update({
            "status": "interrupted",
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "live_calls_reported": "unknown",
            "note": "The client was interrupted before receiving the batch response. Check provider usage before authorizing another run.",
        })
        attempt_file.write_text(json.dumps(attempt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(attempt, indent=2))
        return 130
    except Exception as exc:
        attempt.update({
            "status": "transport_or_runtime_error",
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "live_calls_reported": "unknown",
            "error_type": type(exc).__name__,
            "note": "No retry was made. Check provider usage before authorizing another run.",
        })
        attempt_file.write_text(json.dumps(attempt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(attempt, indent=2))
        return 1
    elapsed = round(time.monotonic() - started, 3)

    if response.status_code != 200:
        failure = {
            "status": "failed",
            "http_status": response.status_code,
            "detail": response.json().get("detail", "Batch analysis failed."),
            "expected_live_requests": preflight["expected_live_requests"],
            "live_calls_reported": "unknown",
            "automatic_retries": 0,
            "elapsed_seconds": elapsed,
            "retry_policy": "No retry was made. Check provider usage before any new live run.",
        }
        metrics_file.write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        attempt.update({
            "status": "http_failure",
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": elapsed,
            "live_calls_reported": "unknown",
            "http_status": response.status_code,
            "note": "No retry was made. Check provider usage before authorizing another run.",
        })
        attempt_file.write_text(json.dumps(attempt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(failure, indent=2))
        return 1

    batch = response.json()
    entries = batch.get("results", []) if isinstance(batch, dict) else []
    results_by_filename = {
        str(item.get("filename", "")): item
        for item in entries
        if isinstance(item, dict)
    }
    candidate_reports: list[dict[str, Any]] = []
    replay_entries: list[dict[str, Any]] = []
    totals = {
        "expected_labels": 0,
        "muse_label_matches": 0,
        "adjudicated_label_matches": 0,
        "expected_strength_labels": 0,
        "strength_matches": 0,
        "verified_quotes": 0,
        "proposed_quotes": 0,
        "related_to_direct_overclaims": 0,
        "expected_timeline_flags": 0,
        "detected_timeline_flags": 0,
        "timeline_true_positives": 0,
        "timeline_false_positives": 0,
        "timeline_false_negatives": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "reported_analysis_calls": 0,
        "failed_candidates": 0,
    }
    for case, row in zip(fixture["candidates"], candidate_rows):
        entry = results_by_filename.get(row["filename"], {})
        result = entry.get("result") if isinstance(entry, dict) else None
        if not isinstance(result, dict):
            totals["failed_candidates"] += 1
            candidate_reports.append({
                "candidate_id": row["candidate_id"],
                "fixture_id": case["id"],
                "status": "failed",
                "error": entry.get("error", {}) if isinstance(entry, dict) else {},
            })
            continue

        labels, case_totals = score_case(case, result)
        strengths = strength_matches(case, result)
        case_report = {
            "candidate_id": row["candidate_id"],
            "fixture_id": case["id"],
            "display_name": row["display_name"],
            "status": "completed",
            **labels,
            "strength_label_checks": strengths,
            "strength_matches": sum(item["matched"] for item in strengths),
            "expected_strength_labels": len(strengths),
        }
        candidate_reports.append(case_report)
        replay_entries.append({
            "candidate_id": row["candidate_id"],
            "filename": row["filename"],
            "fixture_id": case["id"],
            "result": result,
        })
        totals["expected_labels"] += case_totals["gold"]
        totals["muse_label_matches"] += case_totals["correct"]
        totals["adjudicated_label_matches"] += case_totals["adjudicated_correct"]
        totals["expected_strength_labels"] += len(strengths)
        totals["strength_matches"] += sum(item["matched"] for item in strengths)
        totals["verified_quotes"] += case_totals["verification_verified"]
        totals["proposed_quotes"] += case_totals["verification_proposed"]
        totals["related_to_direct_overclaims"] += case_totals["related_overclaims"]
        totals["expected_timeline_flags"] += case_totals["timeline_expected"]
        totals["detected_timeline_flags"] += case_totals["timeline_detected"]
        totals["timeline_true_positives"] += case_totals["timeline_true_positive"]
        totals["timeline_false_positives"] += case_totals["timeline_false_positive"]
        totals["timeline_false_negatives"] += case_totals["timeline_false_negative"]
        totals["input_tokens"] += int(result.get("usage", {}).get("input_tokens", 0) or 0)
        totals["output_tokens"] += int(result.get("usage", {}).get("output_tokens", 0) or 0)
        totals["reported_analysis_calls"] += int(result.get("analysis_calls", 0) or 0)

    expected_labels = totals["expected_labels"]
    proposed_quotes = totals["proposed_quotes"]
    expected_strengths = totals["expected_strength_labels"]
    input_tokens = totals["input_tokens"]
    output_tokens = totals["output_tokens"]
    metrics = {
        "status": "completed_with_candidate_failures" if totals["failed_candidates"] else "completed",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_label": fixture["demo_id"],
        "provider": "muse",
        "model": app.MODEL_ID,
        "reasoning_effort": app.MUSE_REASONING_EFFORT,
        "system_prompt_sha256": system_prompt_sha256,
        "fixture_sha256": fixture_sha256,
        "rubric_version": fixture["rubric_version"],
        "candidate_count": len(candidate_rows),
        "expected_live_requests": preflight["expected_live_requests"],
        "live_calls_reported": totals["reported_analysis_calls"],
        "automatic_retries": 0,
        "elapsed_seconds": elapsed,
        "candidates": candidate_reports,
        "overall": {
            "expected_evidence_labels": expected_labels,
            "muse_label_matches": totals["muse_label_matches"],
            "muse_label_accuracy": round(totals["muse_label_matches"] / expected_labels, 4) if expected_labels else None,
            "timeline_adjudicated_label_matches": totals["adjudicated_label_matches"],
            "timeline_adjudicated_label_accuracy": round(totals["adjudicated_label_matches"] / expected_labels, 4) if expected_labels else None,
            "expected_strength_labels": expected_strengths,
            "strength_label_matches": totals["strength_matches"],
            "strength_label_accuracy": round(totals["strength_matches"] / expected_strengths, 4) if expected_strengths else None,
            "verified_quotes": totals["verified_quotes"],
            "proposed_quotes": proposed_quotes,
            "blocked_quotes": max(0, proposed_quotes - totals["verified_quotes"]),
            "quote_verification_rate": round(totals["verified_quotes"] / proposed_quotes, 4) if proposed_quotes else None,
            "related_to_direct_overclaims": totals["related_to_direct_overclaims"],
            "expected_timeline_flags": totals["expected_timeline_flags"],
            "detected_timeline_flags": totals["detected_timeline_flags"],
            "timeline_true_positives": totals["timeline_true_positives"],
            "timeline_false_positives": totals["timeline_false_positives"],
            "timeline_false_negatives": totals["timeline_false_negatives"],
            "provider_reported_input_tokens": input_tokens,
            "provider_reported_output_tokens": output_tokens,
            "estimated_standard_token_cost_usd": round((input_tokens * 1.25 + output_tokens * 4.25) / 1_000_000, 8),
            "cost_note": "Token-based estimate at the saved Muse Spark Standard rates; not a provider billing record.",
        },
        "disclosure": fixture["disclosure"],
        "report_contains_cv_text": False,
        "report_contains_accepted_quote_text": False,
        "report_contains_rejected_quote_text": True,
    }
    attempt.update({
        "status": metrics["status"],
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed,
        "live_calls_reported": totals["reported_analysis_calls"],
        "failed_candidates": totals["failed_candidates"],
        "estimated_standard_token_cost_usd": metrics["overall"]["estimated_standard_token_cost_usd"],
    })
    attempt_file.write_text(json.dumps(attempt, indent=2) + "\n", encoding="utf-8")
    metrics["overall"]["rejected_quote_details"] = [
        detail
        for item in candidate_reports
        for detail in item.get("rejected_quote_details", [])
    ]
    metrics_file.write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    replay = {
        "schema_version": 1,
        "run_label": fixture["demo_id"],
        "run_at_utc": metrics["run_at_utc"],
        "rubric_version": fixture["rubric_version"],
        "provider_mode": "muse",
        "model": app.MODEL_ID,
        "reasoning_effort": app.MUSE_REASONING_EFFORT,
        "system_prompt_sha256": system_prompt_sha256,
        "fixture_sha256": fixture_sha256,
        "job_description": fixture["job_description"],
        "job_source": fixture["job_source"],
        "candidate_count": batch.get("candidate_count", len(candidate_rows)),
        "completed_count": batch.get("completed_count", len(replay_entries)),
        "analysis_calls": batch.get("analysis_calls", totals["reported_analysis_calls"]),
        "automated_ranking": False,
        "elapsed_seconds": elapsed,
        "assets_directory": str(asset_dir.relative_to(ROOT)),
        "results": replay_entries,
        "disclosure": "Frozen Muse results on five fictional CV PDFs. Replaying this file makes no model call. These results are a small demo calibration, not a hiring recommendation or general accuracy estimate.",
    }
    replay_file.write_text(json.dumps(replay, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    return 1 if totals["failed_candidates"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
