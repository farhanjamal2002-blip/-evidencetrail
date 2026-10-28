# EvidenceTrail final Muse calibration — 28 Oct 2026

## Run control

- Model: `muse-spark-1.3`, Standard mode
- Frozen set: 5 fictional CV fixtures, 4 unique public job sources, 18 prewritten findings
- Live calls: **10 expected, 10 reported**; 0 retries; 0 failed cases
- Reported usage: **37,535 input tokens; 41,322 output tokens**
- Estimated Standard token cost: **$0.22253725** before cached-input discounts; this is a token-based estimate, not a billing record
- Offline suite: **65 tests passed**; Python and JavaScript syntax checks passed

## Final batch results

| CV fixture | Category accuracy | Quote/page check | Notes |
|---|---:|---:|---|
| India public procurement manager | 3/4 | 3/4 | One proposed citation was rejected by local verification. |
| UAE contract and supplier manager | 3/4 | 7/7 | Duration finding was gated to human review. |
| Semiconductor supplier operations manager | 4/4 | 3/3 | All prewritten labels matched. |
| NHS procurement director, searchable PDF | 3/3 | 3/3 | Hard credential stayed Unsupported; adjacent experience stayed Related. |
| NHS procurement director, image-only scan | 3/3 | 3/3 | OCR ran on page 1; all expected categories matched. |
| **Total** | **16/18 (88.9%)** | **19/20 (95.0%)** | **One citation excluded; no fabricated citation was counted as verified.** |

Across the set, false related transfers, missed related findings, and related-to-direct overclaims were all **0**. The timeline solver detected **2/2** expected flags and both duration findings were sent to human review.

## Honest read of the remaining issues

The two strict category mismatches are the same duration cases seen earlier. Muse calls each Direct with ambiguous certainty; the deterministic timeline gate routes each to Needs review. The CVs do not say that their dated job lists are exhaustive, so the conflict gold labels still need independent human review. They have not been changed to improve the score.

One citation in the India case did not pass the exact local page/quote check. EvidenceTrail excluded it. The evaluation report stores the count, not the rejected quote or rejection detail, so no quote text is retained in this artifact.

## Across all live batches

Four batches used **20 reported Muse calls**. They contain 10 case evaluations of the same 5 fictional CV fixtures and 36 labeled finding observations. Aggregate strict accuracy is **32/36 (88.9%)**; exact quote/page checks are **41/42 (97.6%)**. The scan was included twice as the same image-only CV fixture. This is calibration evidence for a small fixed set, not a production accuracy claim.

Estimated Standard token cost across all four batches is **$0.486832**. If the last reported $149.77 balance was immediately before these batches, estimated remaining balance is about **$149.28**, before any cached-input discount or other account activity. Check the provider dashboard for the actual debit.

## Completion decision

The five-case live calibration and local verification checks are complete for this checkpoint. Keep the timeline review gate and the local quote rejection behavior. The demo can show the scan result and hard-credential boundary with their real measured traces; it should show the 19/20 quote check and the two Needs review duration cases plainly.

Detailed final batch: `live_semantic_results_20261028_final.json`. All-batch record: `live_semantic_results_20261028_all_runs.json`.
