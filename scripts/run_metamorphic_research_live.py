"""One-shot end-to-end Muse run for the frozen 12-pair metamorphic corpus.

No retries: every variant gets one durable attempt marker before /api/analyze.
Raw API outputs, receipt IDs, and a compact JSONL evaluator input are retained.
This is author-labelled synthetic data; outputs do not establish real-world accuracy.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "evaluation" / "RESEARCH_METAMORPHIC_PAIRS.json"
OUT = ROOT / "artifacts" / "academic-methods" / "metamorphic_live_run"
PREDICTIONS = OUT / "predictions.jsonl"
EXPECTED_APP_BLOB = "a39ffb15b3215659961793b14849c845355bf626"
EXPECTED_CORPUS_SHA256 = "43c7168bb15faf0c1355428eff865dd3dda7810f8843c966fcb9ca5b4f06b62b"
EXPECTED_RUNTIME_GIT_BLOBS = {
    "app.py": "a39ffb15b3215659961793b14849c845355bf626",
    "demo20_workflow.py": "b044ab59518d38a2394a99f82661226df023f288",
    "muse_protocol.py": "d2c9c87d9f89d4812c632c169165513b1bd1476e",
    "role_audit.py": "1b6336c72a60208c002714190f7d9adc9e61ba22",
    "timeline_audit.py": "83364cab5fad9f7e2bab48f1b5cc4c4ade7314ba",
    "semantic_review.py": "417ea128a6e6315c761ea03ee61c2417fc090263",
    "multimodal_intake.py": "d809be166d7e5f05462fef9e2e0caa5cfb89e2aa",
    "verification_receipt.py": "9f2dd512fcc9bd2884c4f1e71c129a93862f1f66",
}

# Refuse mock mode and keep process accounting bounded to this frozen corpus.
os.environ["EVIDENCETRAIL_PROVIDER"] = "muse"
os.environ["EVIDENCETRAIL_ENABLE_MUSE"] = "true"
os.environ["MAX_ANALYSES_PER_PROCESS"] = "24"
os.environ["MAX_ANALYSES_PER_HOUR_PER_IP"] = "100"

import fitz
from fastapi.testclient import TestClient

sys.path.insert(0, str(ROOT))
import app  # noqa: E402
from scripts.metamorphic_research_metrics import evaluate, load_corpus  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def pdf_for(pair: dict, text: str) -> bytes:
    page_count = int(pair.get("total_pages", 1))
    target_page = int(pair.get("evidence_page", 1))
    if page_count < 1 or page_count > 5 or target_page < 1 or target_page > page_count:
        raise ValueError(f"Invalid page metadata for {pair['id']}")
    doc = fitz.open()
    for page_no in range(1, page_count + 1):
        page = doc.new_page(width=612, height=792)
        body = text if page_no == target_page else f"Page {page_no}"
        placed = page.insert_textbox(
            fitz.Rect(54, 54, 558, 738), body,
            fontsize=11, fontname="helv", lineheight=1.3,
        )
        if placed < 0:
            doc.close()
            raise ValueError(f"CV text overflow for {pair['id']} page {page_no}")
    result = doc.tobytes()
    doc.close()
    return result


def normalize_quote(value: str) -> str:
    return " ".join(re.findall(r"\w+", value.casefold(), flags=re.UNICODE))


def cited_evidence(result: dict, source_text: str, fallback_page: int) -> tuple[int, bool]:
    evidence = result.get("evidence") or []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        quote = item.get("quote") or item.get("text") or ""
        page = item.get("page") or item.get("page_number") or item.get("page_index") or 0
        try:
            page_num = int(page)
        except (TypeError, ValueError):
            page_num = 0
        located = bool(quote) and normalize_quote(str(quote)) in normalize_quote(source_text)
        if page_num > 0 or located:
            return page_num or (fallback_page if located else 0), located
    return 0, False


def main() -> int:
    if not CORPUS.is_file() or digest(CORPUS) != EXPECTED_CORPUS_SHA256:
        raise SystemExit("Frozen metamorphic corpus fingerprint mismatch; no calls made.")
    runtime_mismatches = [
        path for path, expected in EXPECTED_RUNTIME_GIT_BLOBS.items()
        if git_blob_sha(ROOT / path) != expected
    ]
    if runtime_mismatches:
        raise SystemExit(
            "Frozen EvidenceTrail runtime fingerprint mismatch: "
            + ", ".join(runtime_mismatches) + "; no calls made."
        )
    if app.ANALYSIS_PROVIDER != "muse" or not app.MUSE_PROVIDER_ENABLED:
        raise SystemExit("Muse provider preflight failed; no calls made.")
    if not app.configured_model_api_key():
        raise SystemExit("MODEL_API_KEY is missing; no calls made.")
    if OUT.exists():
        raise SystemExit(f"Run directory already exists ({OUT}); refusing duplicate/retry run.")
    pairs, corpus_sha = load_corpus(CORPUS)
    if len(pairs) != 12 or corpus_sha != EXPECTED_CORPUS_SHA256:
        raise SystemExit("Frozen corpus validation failed; no calls made.")

    OUT.mkdir(parents=True)
    manifest = {
        "source_app_sha256": digest(ROOT / "app.py"),
        "source_app_git_blob": EXPECTED_APP_BLOB,
        "runtime_git_blobs": EXPECTED_RUNTIME_GIT_BLOBS,
        "challenge_sha256": corpus_sha,
        "pairs": len(pairs),
        "planned_requests": 24,
        "retry_policy": "none",
        "reference_provenance": "author_labelled_synthetic",
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    attempted = 0
    predictions = []
    with TestClient(app.app) as client:
        for pair in pairs:
            job = "POSITION: Evidence review\nAPPROVED REQUIREMENTS:\n- " + pair["requirement"]
            for role in ("baseline", "variant"):
                item = pair[role]
                key = f"{pair['id']}_{role}"
                marker = OUT / f"{key}.attempt"
                if marker.exists():
                    raise SystemExit(f"Duplicate attempt marker for {key}; stopping without retry.")
                marker.write_text("single request reserved; no retry\n", encoding="utf-8")
                attempted += 1
                started = time.monotonic()
                record = {
                    "pair_id": pair["id"], "role": role,
                    "requirement": pair["requirement"],
                    "source_text": item["cv_text"],
                    "author_label": item["authored_reference"],
                    "corpus_sha256": corpus_sha,
                    "attempt_number": 1,
                }
                try:
                    response = client.post(
                        "/api/analyze",
                        data={
                            "job_description": job,
                            "locked_rubric_json": json.dumps([pair["requirement"]]),
                            "consent": "true",
                        },
                        files={"cv": (f"{key}.pdf", pdf_for(pair, item["cv_text"]), "application/pdf")},
                    )
                    record["http_status"] = response.status_code
                    record["elapsed_seconds"] = round(time.monotonic() - started, 3)
                    if response.status_code == 200:
                        payload = response.json()
                        requirements = payload.get("requirements") or []
                        requirement = next(
                            (x for x in requirements
                             if x.get("requirement") == pair["requirement"]),
                            requirements[0] if requirements else {},
                        )
                        usage = ((payload.get("usage") or {}).get("analysis_pass") or {})
                        status = requirement.get("status")
                        if status not in {"supported", "not_found", "conflicting"}:
                            record["error"] = "missing_or_invalid_requirement_status"
                        else:
                            page, located = cited_evidence(
                                requirement, item["cv_text"],
                                int(pair.get("evidence_page", 1)),
                            )
                            record.update({
                                "provider_mode": payload.get("provider_mode"),
                                "provider_response_id": usage.get("provider_response_id"),
                                "analysis_calls": payload.get("analysis_calls"),
                                "predicted_status": status,
                                "cited_page": page,
                                "source_quote_located": located,
                                "usage": usage,
                                "full_response": payload,
                            })
                            if (record["provider_mode"] == "muse"
                                    and record["provider_response_id"]
                                    and record["analysis_calls"] == 1):
                                predictions.append({
                                    "pair_id": pair["id"], "role": role,
                                    "provider_mode": "muse",
                                    "provider_response_id": record["provider_response_id"],
                                    "corpus_sha256": corpus_sha,
                                    "predicted_status": status,
                                    "source_quote_located": located,
                                    "cited_page": page,
                                    "analysis_calls": 1,
                                })
                    else:
                        record["response_body"] = response.text[:4000]
                except Exception as exc:
                    # Keep failure type only; never serialize environment or request headers.
                    record["error_type"] = type(exc).__name__
                    record["elapsed_seconds"] = round(time.monotonic() - started, 3)
                (OUT / f"{key}.json").write_text(
                    json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )
                print(json.dumps({
                    "pair_id": pair["id"], "role": role,
                    "http_status": record.get("http_status"),
                    "receipt_present": bool(record.get("provider_response_id")),
                    "error": record.get("error") or record.get("error_type"),
                }), flush=True)

    PREDICTIONS.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in predictions),
        encoding="utf-8",
    )
    report = evaluate(predictions, pairs, corpus_sha)
    report["attempted_requests"] = attempted
    report["successful_receipt_records"] = len(predictions)
    report["raw_output_files"] = attempted
    report["source_app_git_blob"] = EXPECTED_APP_BLOB
    report["run_manifest"] = manifest
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "attempted_requests": attempted,
        "successful_receipt_records": len(predictions),
        "completed_pairs": report.get("completed_pairs", report.get("pairs", 0)),
        "status": report.get("status"),
    }), flush=True)
    return 0 if attempted == 24 and len(predictions) == 24 else 1


if __name__ == "__main__":
    raise SystemExit(main())
