#!/usr/bin/env python3
"""Run a controlled live Muse calibration over the fictional public-JD cases.

The script makes exactly two Meta Model API requests per case, only when
``--confirm-live-call`` is supplied. CVs are fictional and built into PDFs in
memory. The report omits full CV text and accepted quotes, but retains rejected
quote snippets with their cited page and rejection reason for calibration.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import textwrap
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CASE_FILE = ROOT / "calibration" / "semantic_cases.json"
LABELS = ("direct", "related", "unsupported", "conflicting")
MIN_ALIGNMENT_SCORE = 0.35


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm-live-call",
        action="store_true",
        help="Authorize two Muse requests per selected fictional CV (six for all cases).",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Check provider configuration and dependencies without calling Muse.",
    )
    parser.add_argument(
        "--case",
        action="append",
        dest="case_ids",
        help="Limit the run to a case ID; repeat to choose multiple cases.",
    )
    args = parser.parse_args()
    if args.confirm_live_call and args.preflight_only:
        parser.error("Choose either --confirm-live-call or --preflight-only.")
    return args


def normalize(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value).casefold()))


def text_similarity(left: Any, right: Any) -> float:
    a, b = normalize(left), normalize(right)
    if not a or not b:
        return 0.0
    sequence = SequenceMatcher(None, a, b).ratio()
    a_tokens, b_tokens = set(a.split()), set(b.split())
    overlap = len(a_tokens & b_tokens) / max(1, len(a_tokens | b_tokens))
    return max(sequence, 0.72 * sequence + 0.28 * overlap)


def align_findings(
    expected: list[dict[str, Any]], returned: list[dict[str, Any]]
) -> tuple[list[tuple[int, int, float]], list[int], list[int]]:
    """Greedily pair each gold criterion with its best unmatched returned item."""
    pairs: list[tuple[float, int, int]] = []
    for gold_index, gold in enumerate(expected):
        gold_text = gold.get("requirement", "")
        for result_index, item in enumerate(returned):
            source = item.get("job_source") if isinstance(item, dict) else None
            source_text = source.get("text", "") if isinstance(source, dict) else ""
            score = max(
                text_similarity(gold_text, item.get("requirement", "")),
                text_similarity(gold_text, source_text),
            )
            pairs.append((score, gold_index, result_index))
    pairs.sort(reverse=True)

    used_gold: set[int] = set()
    used_results: set[int] = set()
    aligned: list[tuple[int, int, float]] = []
    for score, gold_index, result_index in pairs:
        if score < MIN_ALIGNMENT_SCORE:
            break
        if gold_index in used_gold or result_index in used_results:
            continue
        used_gold.add(gold_index)
        used_results.add(result_index)
        aligned.append((gold_index, result_index, score))
    aligned.sort()
    return (
        aligned,
        [index for index in range(len(expected)) if index not in used_gold],
        [index for index in range(len(returned)) if index not in used_results],
    )


def score_case(
    case: dict[str, Any], result: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, int]]:
    expected = case.get("expected", [])
    returned = result.get("requirements", [])
    if not isinstance(expected, list):
        expected = []
    if not isinstance(returned, list):
        returned = []
    strength_labels = ("specific", "stated", "keyword_only", "none", "not_reported")
    strength_distribution = {label: 0 for label in strength_labels}
    for item in returned:
        strength = item.get("evidence_strength") if isinstance(item, dict) else None
        strength = (
            strength
            if isinstance(strength, str) and strength in strength_distribution
            else "not_reported"
        )
        strength_distribution[strength] += 1
    aligned, missing_gold, unmatched_results = align_findings(expected, returned)
    confusion = {gold: {predicted: 0 for predicted in (*LABELS, "unclassified")} for gold in LABELS}
    adjudicated_confusion = {gold: {predicted: 0 for predicted in (*LABELS, "unclassified")} for gold in LABELS}
    correct = 0
    adjudicated_correct = 0
    timeline_adjudicated = 0
    false_transfer = 0
    missed_transfer = 0
    related_overclaim = 0
    ambiguous = 0
    item_labels: list[dict[str, Any]] = []
    for gold_index, result_index, _score in aligned:
        gold_label = expected[gold_index].get("evidence_type")
        item = returned[result_index]
        muse_predicted = item.get("evidence_type")
        predicted = muse_predicted
        if gold_label not in LABELS:
            continue
        if predicted not in LABELS:
            predicted = "unclassified"
        timeline_flags = item.get("timeline_review_flags")
        has_timeline_conflict = isinstance(timeline_flags, list) and bool(timeline_flags)
        adjudicated = item.get("final_evidence_type")
        if adjudicated not in LABELS:
            adjudicated = "conflicting" if has_timeline_conflict else predicted
        if adjudicated not in LABELS:
            adjudicated = "unclassified"
        confusion[gold_label][predicted] += 1
        adjudicated_confusion[gold_label][adjudicated] += 1
        correct += int(gold_label == predicted)
        adjudicated_correct += int(gold_label == adjudicated)
        timeline_adjudicated += int(has_timeline_conflict)
        false_transfer += int(predicted == "related" and gold_label != "related")
        missed_transfer += int(gold_label == "related" and predicted != "related")
        related_overclaim += int(gold_label == "related" and predicted == "direct")
        ambiguous += int(item.get("certainty") == "ambiguous")
        item_labels.append({
            "gold_item": gold_index + 1,
            "result_finding_index": result_index + 1,
            "expected": gold_label,
            "predicted": predicted,
            "adjudicated": adjudicated,
            "adjudication_reason": "timeline_gate" if has_timeline_conflict else None,
            "predicted_strength": item.get("evidence_strength") if item.get("evidence_strength") in strength_distribution else "not_reported",
            "certainty": item.get("certainty") if item.get("certainty") in {"clear", "ambiguous"} else "unclassified",
        })
    for gold_index in missing_gold:
        gold_label = expected[gold_index].get("evidence_type")
        if gold_label in LABELS:
            item_labels.append({
                "gold_item": gold_index + 1,
                "result_finding_index": None,
                "expected": gold_label,
                "predicted": "unclassified",
                "adjudicated": "unclassified",
                "adjudication_reason": None,
                "predicted_strength": "not_reported",
                "certainty": "unclassified",
            })
            adjudicated_confusion[gold_label]["unclassified"] += 1
            missed_transfer += int(gold_label == "related")
    item_labels.sort(key=lambda item: item["gold_item"])

    quote_audit = result.get("quote_audit")
    if not isinstance(quote_audit, dict):
        quote_audit = {}
    verification_audit = result.get("verification_audit")
    if not isinstance(verification_audit, dict):
        verification_audit = {}
    rejected_quote_details: list[dict[str, Any]] = []
    raw_rejections = verification_audit.get("rejected_citations", [])
    if isinstance(raw_rejections, list):
        for record in raw_rejections:
            if not isinstance(record, dict) or not record.get("quote"):
                continue
            raw_page = record.get("cited_page")
            cited_page = (
                raw_page
                if isinstance(raw_page, int) and not isinstance(raw_page, bool) and raw_page > 0
                else None
            )
            rejected_quote_details.append({
                "requirement_id": str(record.get("requirement_id", ""))[:32],
                "requirement": str(record.get("requirement", ""))[:180],
                "quote": str(record.get("quote", ""))[:360],
                "cited_page": cited_page,
                "reason": str(record.get("reason", "unknown"))[:80],
            })
    raw_ocr_pages = result.get("ocr_pages", [])
    if not isinstance(raw_ocr_pages, list):
        raw_ocr_pages = []
    ocr_pages = sorted({
        page for page in raw_ocr_pages
        if isinstance(page, int)
        and not isinstance(page, bool)
        and page > 0
    })
    verified = safe_nonnegative_int(quote_audit.get("verification_verified"))
    proposed = safe_nonnegative_int(quote_audit.get("verification_proposed"))
    expected_timeline = set(case.get("expected_timeline_flags", []))
    timeline_audit = result.get("timeline_audit")
    if not isinstance(timeline_audit, dict):
        timeline_audit = {}
    detected_timeline = {
        str(flag.get("type"))
        for flag in timeline_audit.get("flags", [])
        if isinstance(flag, dict) and isinstance(flag.get("type"), str)
    }
    timeline_true_positive = len(expected_timeline & detected_timeline)
    timeline_false_positive = len(detected_timeline - expected_timeline)
    timeline_false_negative = len(expected_timeline - detected_timeline)
    timeline_gated = [
        item for item in returned
        if isinstance(item, dict)
        and isinstance(item.get("timeline_review_flags"), list)
        and item["timeline_review_flags"]
    ]
    direct_claims_gated = sum(
        item.get("evidence_type") == "direct" and item.get("certainty") == "ambiguous"
        for item in timeline_gated
    )
    return (
        {
            "case_id": case.get("id", "unknown"),
            "industry": case.get("industry", ""),
            "level": case.get("level", ""),
            "cv_variant": case.get("cv_variant", "searchable text PDF"),
            "ocr_used": bool(ocr_pages),
            "ocr_pages": ocr_pages,
            "gold_requirements": len(expected),
            "aligned_findings": len(aligned),
            "missing_gold_requirements": len(missing_gold),
            "unmatched_model_findings": len(unmatched_results),
            "strict_category_accuracy": round(correct / len(expected), 4) if expected else None,
            "deterministic_adjudicated_accuracy": round(adjudicated_correct / len(expected), 4) if expected else None,
            "ambiguous_aligned_findings": ambiguous,
            "false_related_transfers": false_transfer,
            "missed_related_transfers": missed_transfer,
            "related_to_direct_overclaims": related_overclaim,
            "item_labels": item_labels,
            "evidence_strength_distribution": strength_distribution,
            "verification_citations_verified": verified,
            "verification_citations_proposed": proposed,
            "verification_quote_rate": round(verified / proposed, 4) if proposed else None,
            "rejected_quote_details": rejected_quote_details,
            "expected_timeline_flags": sorted(expected_timeline),
            "detected_timeline_flags": sorted(detected_timeline),
            "timeline_flag_precision": round(timeline_true_positive / len(detected_timeline), 4) if detected_timeline else (1.0 if not expected_timeline else None),
            "timeline_flag_recall": round(timeline_true_positive / len(expected_timeline), 4) if expected_timeline else (1.0 if not detected_timeline else None),
            "timeline_review_gated_findings": len(timeline_gated),
            "direct_claims_gated_to_review": direct_claims_gated,
            "timeline_adjudicated_findings": timeline_adjudicated,
            "rejected_quote_details_count": len(rejected_quote_details),
            "adjudicated_item_labels": item_labels,
        },
        {
            "correct": correct,
            "adjudicated_correct": adjudicated_correct,
            "gold": len(expected),
            "aligned": len(aligned),
            "false_related_transfers": false_transfer,
            "missed_related_transfers": missed_transfer,
            "related_overclaims": related_overclaim,
            "ambiguous": ambiguous,
            "verification_verified": verified,
            "verification_proposed": proposed,
            "missing_gold": len(missing_gold),
            "unmatched_findings": len(unmatched_results),
            "timeline_true_positive": timeline_true_positive,
            "timeline_false_positive": timeline_false_positive,
            "timeline_false_negative": timeline_false_negative,
            "timeline_expected": len(expected_timeline),
            "timeline_detected": len(detected_timeline),
            "timeline_review_gated_findings": len(timeline_gated),
            "direct_claims_gated_to_review": direct_claims_gated,
            "timeline_adjudicated_findings": timeline_adjudicated,
            **{
                "evidence_strength_" + label: count
                for label, count in strength_distribution.items()
            },
        },
    )


def safe_nonnegative_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return 0
    return value


def summarize(
    case_reports: list[dict[str, Any]],
    totals: dict[str, int],
    confusion: dict[str, dict[str, int]],
    adjudicated_confusion: dict[str, dict[str, int]],
) -> dict[str, Any]:
    gold = totals["gold"]
    quote_denominator = totals["verification_proposed"]
    related_gold = sum(confusion["related"].values())
    nonrelated_gold = sum(
        sum(confusion[label].values()) for label in LABELS if label != "related"
    )
    return {
        "status": "completed",
        "cases": case_reports,
        "overall": {
            "gold_requirements": gold,
            "aligned_findings": totals["aligned"],
            "strict_category_accuracy": round(totals["correct"] / gold, 4) if gold else None,
            "deterministic_adjudicated_accuracy": round(
                totals["adjudicated_correct"] / gold, 4
            ) if gold else None,
            "coverage": round(totals["aligned"] / gold, 4) if gold else None,
            "false_related_transfers": totals["false_related_transfers"],
            "false_transfer_rate_on_nonrelated_gold": round(
                totals["false_related_transfers"] / nonrelated_gold, 4
            ) if nonrelated_gold else None,
            "missed_related_transfers": totals["missed_related_transfers"],
            "missed_transfer_rate_on_related_gold": round(
                totals["missed_related_transfers"] / related_gold, 4
            ) if related_gold else None,
            "related_to_direct_overclaims": totals["related_overclaims"],
            "ambiguous_findings": totals["ambiguous"],
            "verified_citations": totals["verification_verified"],
            "proposed_citations": quote_denominator,
            "rejected_quote_count": sum(
                int(case.get("rejected_quote_details_count", 0) or 0)
                for case in case_reports
            ),
            "quote_verification_rate": round(
                totals["verification_verified"] / quote_denominator, 4
            ) if quote_denominator else None,
            "missing_gold_requirements": totals["missing_gold"],
            "unmatched_model_findings": totals["unmatched_findings"],
            "timeline_flags_expected": totals["timeline_expected"],
            "timeline_flags_detected": totals["timeline_detected"],
            "timeline_review_gated_findings": totals["timeline_review_gated_findings"],
            "direct_claims_gated_to_review": totals["direct_claims_gated_to_review"],
            "timeline_adjudicated_findings": totals["timeline_adjudicated_findings"],
            "timeline_flag_precision": round(
                totals["timeline_true_positive"] / totals["timeline_detected"], 4
            ) if totals["timeline_detected"] else (1.0 if not totals["timeline_expected"] else None),
            "timeline_flag_recall": round(
                totals["timeline_true_positive"] / totals["timeline_expected"], 4
            ) if totals["timeline_expected"] else (1.0 if not totals["timeline_detected"] else None),
            "timeline_false_positives": totals["timeline_false_positive"],
            "timeline_missed_flags": totals["timeline_false_negative"],
            "provider_reported_input_tokens": totals["provider_reported_input_tokens"],
            "provider_reported_output_tokens": totals["provider_reported_output_tokens"],
            "evidence_strength_distribution": {
                label: totals["evidence_strength_" + label]
                for label in ("specific", "stated", "keyword_only", "none", "not_reported")
            },
        },
        "confusion_matrix": confusion,
        "deterministic_adjudicated_confusion_matrix": adjudicated_confusion,
        "disclosure": "All CVs are fictional; each job description is paraphrased from a linked public posting. Rejected quote snippets are retained with cited page and reason for calibration review. Scores are calibration evidence, not a hiring recommendation.",
    }


def make_case_pdf(case: dict[str, Any]) -> bytes:
    import fitz
    from PIL import Image, ImageDraw, ImageFont

    document = fitz.open()
    pages = case.get("cv_pages", [])
    layouts = case.get("cv_layout", [])
    for index, content in enumerate(pages):
        page = document.new_page(width=612, height=792)
        layout = layouts[index] if index < len(layouts) else "single_column"
        if layout == "scanned_two_column":
            columns = content if isinstance(content, dict) else {"left": str(content), "right": ""}
            image = Image.new("L", (1275, 1650), 255)
            draw = ImageDraw.Draw(image)
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            try:
                font = ImageFont.truetype(font_path, 25)
                heading_font = ImageFont.truetype(font_path, 29)
            except OSError:
                font = ImageFont.load_default()
                heading_font = font

            def draw_column(raw_text: Any, x: int) -> None:
                y = 100
                for paragraph in str(raw_text).splitlines():
                    if not paragraph.strip():
                        y += 20
                        continue
                    is_heading = paragraph.isupper() or paragraph.startswith("FICTIONAL CV")
                    selected_font = heading_font if is_heading else font
                    lines = textwrap.wrap(paragraph, width=38, break_long_words=False) or [""]
                    for line in lines:
                        draw.text((x, y), line, fill=35, font=selected_font)
                        y += 42 if is_heading else 38
                    y += 10

            draw_column(columns.get("left", ""), 80)
            draw_column(columns.get("right", ""), 670)
            image_stream = io.BytesIO()
            image.save(image_stream, format="PNG", optimize=True)
            page.insert_image(page.rect, stream=image_stream.getvalue())
        elif isinstance(content, dict) or layout == "two_column":
            left = content.get("left", "") if isinstance(content, dict) else str(content)
            right = content.get("right", "") if isinstance(content, dict) else ""
            page.insert_textbox(
                fitz.Rect(42, 44, 294, 748), str(left), fontsize=10, lineheight=1.3
            )
            page.insert_textbox(
                fitz.Rect(318, 44, 570, 748), str(right), fontsize=10, lineheight=1.3
            )
        else:
            page.insert_textbox(
                fitz.Rect(48, 48, 564, 744), str(content), fontsize=10, lineheight=1.35
            )
    output = document.tobytes(garbage=4, deflate=True, clean=True)
    document.close()
    return output


def load_cases(case_ids: list[str] | None) -> list[dict[str, Any]]:
    data = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    if case_ids:
        requested = set(case_ids)
        known = {case.get("id") for case in cases}
        unknown = requested - known
        if unknown:
            raise ValueError("Unknown case ID(s): " + ", ".join(sorted(unknown)))
        cases = [case for case in cases if case.get("id") in requested]
    return cases


def main() -> int:
    args = parse_args()
    cases = load_cases(args.case_ids)
    if not cases:
        print(json.dumps({"status": "blocked", "reason": "No calibration cases selected."}, indent=2))
        return 2
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ModuleNotFoundError:
        pass
    provider = os.getenv("EVIDENCETRAIL_PROVIDER", "muse").strip().casefold()
    key_configured = bool(os.getenv("MODEL_API_KEY", "").strip())
    preflight = {
        "provider": provider,
        "model": "muse-spark-1.3",
        "server_key_configured": key_configured,
        "selected_cases": [case.get("id") for case in cases],
        "expected_live_requests": 2 * len(cases),
        "automatic_retries": 0,
        "report_contains_cv_text": False,
        "report_contains_accepted_quote_text": False,
        "report_contains_rejected_quote_text": True,
    }
    if provider != "muse":
        print(json.dumps({"status": "blocked", "reason": "Set EVIDENCETRAIL_PROVIDER=muse.", "live_calls_made": 0, **preflight}, indent=2), file=sys.stderr)
        return 2
    if not key_configured:
        print(json.dumps({"status": "blocked", "reason": "MODEL_API_KEY is not configured in this runtime; no request was made.", "live_calls_made": 0, **preflight}, indent=2), file=sys.stderr)
        return 2
    try:
        from fastapi.testclient import TestClient
        import app
        import fitz  # noqa: F401
    except ModuleNotFoundError as exc:
        print(json.dumps({
            "status": "blocked",
            "reason": "A project dependency is missing.",
            "missing_dependency": exc.name or "unknown",
            "live_calls_made": 0,
        }, indent=2), file=sys.stderr)
        return 2

    report = {
        "provider": app.ANALYSIS_PROVIDER,
        "model": app.MODEL_ID,
        "server_key_configured": key_configured,
        "selected_cases": [case.get("id") for case in cases],
        "expected_live_requests": 2 * len(cases),
        "automatic_retries": 0,
        "report_contains_cv_text": False,
        "report_contains_accepted_quote_text": False,
        "report_contains_rejected_quote_text": True,
    }
    if app.ANALYSIS_PROVIDER != "muse":
        print(json.dumps({"status": "blocked", "reason": "Set EVIDENCETRAIL_PROVIDER=muse.", **report}, indent=2), file=sys.stderr)
        return 2
    if not key_configured:
        print(json.dumps({"status": "blocked", "reason": "MODEL_API_KEY is not configured in this runtime; no request was made.", "live_calls_made": 0, **report}, indent=2), file=sys.stderr)
        return 2
    if args.preflight_only:
        print(json.dumps({"status": "ready_for_review", **report}, indent=2))
        return 0
    if not args.confirm_live_call:
        print(json.dumps({"status": "preflight_passed", "next_step": "Rerun with --confirm-live-call to make the stated number of live requests.", **report}, indent=2))
        return 0

    from fastapi.testclient import TestClient

    case_reports: list[dict[str, Any]] = []
    confusion = {gold: {predicted: 0 for predicted in (*LABELS, "unclassified")} for gold in LABELS}
    adjudicated_confusion = {gold: {predicted: 0 for predicted in (*LABELS, "unclassified")} for gold in LABELS}
    totals = {
        "correct": 0, "adjudicated_correct": 0, "gold": 0, "aligned": 0,
        "false_related_transfers": 0, "missed_related_transfers": 0,
        "related_overclaims": 0, "ambiguous": 0,
        "verification_verified": 0, "verification_proposed": 0,
        "missing_gold": 0, "unmatched_findings": 0,
        "timeline_true_positive": 0, "timeline_false_positive": 0,
        "timeline_false_negative": 0, "timeline_expected": 0,
        "timeline_detected": 0,
        "timeline_review_gated_findings": 0,
        "direct_claims_gated_to_review": 0,
        "timeline_adjudicated_findings": 0,
        "provider_reported_input_tokens": 0,
        "provider_reported_output_tokens": 0,
        "evidence_strength_specific": 0,
        "evidence_strength_stated": 0,
        "evidence_strength_keyword_only": 0,
        "evidence_strength_none": 0,
        "evidence_strength_not_reported": 0,
    }
    failures = 0
    completed_call_count = 0
    with TestClient(app.app) as client:
        for case in cases:
            response = client.post(
                "/api/analyze",
                files={"cv": (str(case["id"]) + ".pdf", make_case_pdf(case), "application/pdf")},
                data={"job_description": case["job_description"], "consent": "true"},
            )
            if response.status_code != 200:
                failures += 1
                case_reports.append({
                    "case_id": case.get("id", "unknown"),
                    "status": "failed",
                    "http_status": response.status_code,
                    "reason": response.json().get("detail", "Analysis failed."),
                })
                continue
            result_payload = response.json()
            report_for_case, case_totals = score_case(case, result_payload)
            usage = result_payload.get("usage")
            usage = usage if isinstance(usage, dict) else {}
            input_tokens = safe_nonnegative_int(usage.get("input_tokens"))
            output_tokens = safe_nonnegative_int(usage.get("output_tokens"))
            report_for_case["provider_reported_input_tokens"] = input_tokens
            report_for_case["provider_reported_output_tokens"] = output_tokens
            case_totals["provider_reported_input_tokens"] = input_tokens
            case_totals["provider_reported_output_tokens"] = output_tokens
            case_reports.append(report_for_case)
            completed_call_count += safe_nonnegative_int(response.json().get("analysis_calls"))
            for key in totals:
                totals[key] += case_totals[key]
            for item_label in report_for_case["item_labels"]:
                gold_label = item_label.get("expected")
                if gold_label not in LABELS:
                    continue
                predicted = item_label.get("predicted")
                if predicted not in LABELS:
                    predicted = "unclassified"
                confusion[gold_label][predicted] += 1
                adjudicated = item_label.get("adjudicated")
                if adjudicated not in LABELS:
                    adjudicated = "unclassified"
                adjudicated_confusion[gold_label][adjudicated] += 1

    result = summarize(case_reports, totals, confusion, adjudicated_confusion)
    result["status"] = "completed_with_case_failures" if failures else "completed"
    result["failed_cases"] = failures
    result["live_requests_expected"] = 2 * len(cases)
    result["live_calls_reported_for_completed_cases"] = completed_call_count
    result["live_calls_for_failed_cases"] = "unknown; no automatic retry was made"
    result["model"] = app.MODEL_ID
    input_tokens = result["overall"]["provider_reported_input_tokens"]
    output_tokens = result["overall"]["provider_reported_output_tokens"]
    result["estimated_standard_token_cost_usd"] = round(
        (input_tokens * 1.25 + output_tokens * 4.25) / 1_000_000, 8
    )
    result["cost_estimate_note"] = (
        "Token-based estimate at the saved Muse Spark Standard rates; not a provider billing record."
    )
    result["automatic_retries"] = 0
    result["report_contains_cv_text"] = False
    result["report_contains_accepted_quote_text"] = False
    result["report_contains_rejected_quote_text"] = True
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
