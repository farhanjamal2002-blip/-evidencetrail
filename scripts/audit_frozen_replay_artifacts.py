#!/usr/bin/env python3
"""Audit the committed frozen replay payloads without model/API calls.

Checks challenge fingerprint, manifest scope, provider receipt fields, pair
completeness, raw/final labels, local quote-verification totals, and page-shift
citations. Receipt IDs are audited for consistency and uniqueness; this script
does not independently authenticate Meta's provider logs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "evaluation" / "RESEARCH_METAMORPHIC_PAIRS.json"
RUNS = (
    ROOT / "artifacts" / "live-m02-m07-frozen-20261030",
    ROOT / "artifacts" / "live-remaining-pairs-frozen-20261030",
)
FROZEN_SHA = "8489e45ae0f87d8421562618bda556c31911372b"
EXPECTED_CORPUS_SHA = "43c7168bb15faf0c1355428eff865dd3dda7810f8843c966fcb9ca5b4f06b62b"
PAIR_IDS = tuple(f"M{i:02d}" for i in range(1, 13))
RATES = {"input": 1.25, "output": 4.25}


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read JSON: {path.relative_to(ROOT)}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path.relative_to(ROOT)}")
    return value


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    corpus_bytes = CORPUS.read_bytes()
    corpus_sha = hashlib.sha256(corpus_bytes).hexdigest()
    need(corpus_sha == EXPECTED_CORPUS_SHA, "Frozen challenge fingerprint changed")
    corpus = json.loads(corpus_bytes)
    need(corpus.get("reference_provenance") == "author_labelled_synthetic",
         "Challenge provenance is not the expected synthetic author labels")
    pair_rows = corpus.get("pairs", [])
    need(len(pair_rows) == 12, "Expected exactly 12 frozen pairs")
    pairs = {row["id"]: row for row in pair_rows}
    need(set(pairs) == set(PAIR_IDS), "Pair IDs do not match the frozen set")

    seen_cases: dict[str, dict[str, Any]] = {}
    manifest_summaries = []
    for run_root in RUNS:
        manifest = read_json(run_root / "run.json")
        need(manifest.get("status") == "completed", f"Incomplete run: {run_root.name}")
        need(manifest.get("frozen_release_sha") == FROZEN_SHA, "Frozen release SHA mismatch")
        need(manifest.get("challenge_sha256") == corpus_sha, "Run challenge hash mismatch")
        need(manifest.get("provider") == "muse" and manifest.get("model") == "muse-spark-1.3",
             "Unexpected provider or model")
        need(manifest.get("automatic_retries") == 0, "A run declares retries")
        need(manifest.get("human_ratings") is False, "Unexpected human-rating data")
        pair_ids = manifest.get("pair_ids")
        need(isinstance(pair_ids, list) and pair_ids, "Run pair list is empty")
        need(manifest.get("requests_planned") == len(pair_ids) * 2, "Planned call count mismatch")
        need(manifest.get("requests_attempted") == len(pair_ids) * 2, "Attempt count mismatch")
        need(manifest.get("successful_authentic_receipts") == len(pair_ids) * 2,
             "Manifest receipt count mismatch")

        for case_id in (f"{pair_id}-{role}" for pair_id in pair_ids
                        for role in ("baseline", "variant")):
            need(case_id not in seen_cases, f"Duplicate case across runs: {case_id}")
            record = read_json(run_root / "cases" / f"{case_id}.json")
            need(record.get("case_id") == case_id, f"Case filename/content mismatch: {case_id}")
            pair_id, role = case_id.rsplit("-", 1)
            expected = pairs[pair_id][role]["authored_reference"]
            need(record.get("pair_id") == pair_id and record.get("role") == role,
                 f"Pair/role mismatch: {case_id}")
            need(record.get("expected_status") == expected, f"Gold label mismatch: {case_id}")
            need(record.get("expected_relation") == pairs[pair_id]["expected_relation"],
                 f"Pair relation mismatch: {case_id}")
            need(record.get("challenge_sha256") == corpus_sha, f"Case challenge hash mismatch: {case_id}")
            need(record.get("frozen_release_sha") == FROZEN_SHA, f"Case frozen SHA mismatch: {case_id}")
            need(record.get("automatic_retries") == 0, f"Retry found: {case_id}")
            need(record.get("http_status") == 200, f"HTTP failure: {case_id}")
            need(record.get("provider_receipt_present") is True, f"Receipt missing: {case_id}")
            receipt = record.get("provider_response_id")
            need(isinstance(receipt, str) and receipt.strip(), f"Receipt ID missing: {case_id}")
            payload = record.get("application_result", {})
            usage = payload.get("usage", {}).get("analysis_pass", {})
            need(payload.get("provider_mode") == "muse", f"Payload provider mismatch: {case_id}")
            need(payload.get("model") == "muse-spark-1.3", f"Payload model mismatch: {case_id}")
            need(payload.get("analysis_calls") == 1, f"Expected one provider call: {case_id}")
            need(usage.get("provider_response_id") == receipt, f"Receipt ID mismatch: {case_id}")
            need(isinstance(usage.get("input_tokens"), int), f"Input-token count missing: {case_id}")
            need(isinstance(usage.get("output_tokens"), int), f"Output-token count missing: {case_id}")
            need(isinstance(record.get("quote_audit"), dict), f"Quote audit missing: {case_id}")
            need(isinstance(record.get("verification_audit"), dict), f"Verification audit missing: {case_id}")
            audit = record["quote_audit"]
            need(audit.get("verified", 0) + audit.get("excluded", 0) == audit.get("proposed", 0),
                 f"Quote audit accounting mismatch: {case_id}")
            need(audit.get("verification_verified", 0) + audit.get("verification_excluded", 0)
                 == audit.get("verification_proposed", 0),
                 f"Verification audit accounting mismatch: {case_id}")

            findings = payload.get("requirements")
            need(isinstance(findings, list) and len(findings) == 1,
                 f"Expected one finding: {case_id}")
            finding = findings[0]
            summary = record.get("finding_summary")
            need(isinstance(summary, list) and len(summary) == 1, f"Finding summary missing: {case_id}")
            compact = summary[0]
            need(compact.get("raw_status") == finding.get("raw_status"),
                 f"Raw status summary mismatch: {case_id}")
            need(compact.get("final_status") == finding.get("status"),
                 f"Final status summary mismatch: {case_id}")
            need(compact.get("final_status") == finding.get("effective_status", compact.get("final_status")),
                 f"Effective status mismatch: {case_id}")
            need(record.get("provider_mode") == "muse" and record.get("analysis_calls") == 1,
                 f"Top-level receipt metadata mismatch: {case_id}")
            seen_cases[case_id] = record

        manifest_summaries.append(manifest)

    expected_case_ids = {f"{pair_id}-{role}" for pair_id in PAIR_IDS
                         for role in ("baseline", "variant")}
    need(set(seen_cases) == expected_case_ids, "Missing or unexpected case files")
    receipts = [row["provider_response_id"] for row in seen_cases.values()]
    need(len(set(receipts)) == 24, "Provider response IDs are missing or duplicated")

    raw_matches = 0
    final_matches = 0
    pair_results = []
    quote_proposed = 0
    quote_verified = 0
    quote_excluded = 0
    for pair_id in PAIR_IDS:
        pair = pairs[pair_id]
        records = {role: seen_cases[f"{pair_id}-{role}"] for role in ("baseline", "variant")}
        observed = {}
        for role, record in records.items():
            finding = record["finding_summary"][0]
            raw_matches += finding["raw_status"] == record["expected_status"]
            final_matches += finding["final_status"] == record["expected_status"]
            observed[role] = finding["final_status"]
            quote_proposed += record["quote_audit"]["proposed"]
            quote_verified += record["quote_audit"]["verified"]
            quote_excluded += record["quote_audit"]["excluded"]
        invariant = observed["baseline"] == observed["variant"]
        expected_invariant = pair["expected_relation"] == "invariant"
        pair_results.append({
            "pair_id": pair_id,
            "factor": pair["single_change_factor"],
            "expected_relation": pair["expected_relation"],
            "observed_relation": "invariant" if invariant else "changed",
            "relation_matches_expectation": invariant == expected_invariant,
            "final_labels_match_authored_references": all(
                records[role]["finding_summary"][0]["final_status"]
                == pair[role]["authored_reference"] for role in ("baseline", "variant")
            ),
        })

    m08_pages = {}
    for role in ("baseline", "variant"):
        record = seen_cases[f"M08-{role}"]
        expected_page = record.get("expected_evidence_page")
        pages = record["finding_summary"][0].get("cited_pages") or []
        need(expected_page is not None and pages == [expected_page], f"M08 page shift failed: {role}")
        m08_pages[role] = {"expected": expected_page, "cited": pages}

    total_input = sum(row["application_result"]["usage"]["analysis_pass"]["input_tokens"]
                      for row in seen_cases.values())
    total_output = sum(row["application_result"]["usage"]["analysis_pass"]["output_tokens"]
                       for row in seen_cases.values())
    estimated_cost = (total_input * RATES["input"] + total_output * RATES["output"]) / 1_000_000
    expected_cost = sum(
        float(manifest.get("estimated_standard_cost_usd",
                           manifest.get("new_estimated_standard_cost_usd", 0.0)))
        for manifest in manifest_summaries
    )
    need(abs(estimated_cost - expected_cost) < 0.0000001,
         "Recomputed standard-rate estimate differs from run manifests")
    need(raw_matches == 19 and final_matches == 24, "Observed label counts changed")
    need(quote_proposed == 25 and quote_verified == 25 and quote_excluded == 0,
         "Observed quote audit counts changed")
    need(all(row["relation_matches_expectation"] for row in pair_results),
         "One or more paired relations failed")
    need(abs(estimated_cost - 0.11587275) < 0.0000001, "Combined cost estimate changed")

    report = {
        "status": "PASS — committed replay records are internally consistent",
        "no_model_calls_made": True,
        "frozen_release_sha": FROZEN_SHA,
        "challenge_sha256": corpus_sha,
        "pair_count": 12,
        "case_count": len(seen_cases),
        "unique_provider_response_ids": len(set(receipts)),
        "raw_labels_matching_author_reference": raw_matches,
        "final_labels_matching_author_reference": final_matches,
        "pair_relations_matching_expectation": sum(row["relation_matches_expectation"]
                                                   for row in pair_results),
        "proposed_quotes": quote_proposed,
        "verified_quotes": quote_verified,
        "excluded_quotes": quote_excluded,
        "m08_page_shift": m08_pages,
        "recomputed_standard_rate_cost_usd": round(estimated_cost, 8),
        "cost_estimate_is_not_provider_invoice": True,
        "provider_id_authenticity_independently_verified": False,
        "author_labels_are_independent_ground_truth": False,
        "human_ratings_collected": False,
        "pairs": pair_results,
        "limitations": [
            "Fictional author-labelled pairs do not establish population or real-world résumé accuracy.",
            "A locally verified quote/page does not by itself prove semantic support for the requirement.",
            "Provider IDs are checked for presence, uniqueness, and consistency with the stored application payload; provider authenticity relies on the preserved Actions execution, not this offline audit.",
            "The cost figure is a standard-rate estimate, not a provider invoice.",
        ],
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
