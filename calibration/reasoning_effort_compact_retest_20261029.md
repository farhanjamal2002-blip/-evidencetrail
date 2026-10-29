# Compact prompt and Muse reasoning retest — 2026-10-29

## Decision

Set Muse Spark 1.3's default reasoning effort to `minimal`; retain `medium`, `low`, `high`, and `xhigh` as explicit environment overrides. This is a latency and cost setting for the same model, not a model downgrade.

The decision is based on repeated live runs with the same compact prompt and fixed fictional cases. It does not establish general accuracy. A recruiter still reviews uncertain or conflicting evidence, and the `medium` override remains available for a deliberate comparison.

## Matched public-JD calibration

Each run used the same five fictional CVs, five public-job-derived JDs, and 18 prewritten evidence labels. The compact prompt hash and evaluator were held constant. Each run made five Spark 1.3 requests sequentially, with no retries.

| Effort | Run time | Raw Muse labels | Final labels after local gates | False Related transfers | Missed Related | Related → Direct overclaims | Verified citations | Standard-rate token estimate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Minimal, run 1 | 39.096 s | 15/18 | 17/18 | 0 | 1 | 0 | 23/23 | $0.04236 |
| Minimal, repeat | 34.942 s | 15/18 | 17/18 | 0 | 1 | 0 | 25/25 | $0.04896 |
| Medium, matched control | 94.465 s | 13/18 | 15/18 | 1 | 2 | 0 | 24/24 | $0.11833 |

Across the two minimal runs, elapsed time averaged 37.019 seconds and the token-cost estimate averaged $0.04566. Compared with the single matched medium run, those are about 61% lower. The final label result repeated at 17/18 in both minimal runs. All runs detected both expected timeline flags, with no false-positive timeline flags.

The remaining mismatch is a conservative missed Related label on the India public-procurement case. The two minimal runs produced no false Related transfer and no Related-to-Direct overclaim. These are measurements on this small fixed set, not a general model-accuracy claim. Token costs are estimates at the saved Standard rates, not billing records.

## Five-CV app-route check with the new default

After changing the fallback setting, the unified fictional demo was run through the local application route without setting `MUSE_REASONING_EFFORT` in the command environment. The preflight confirmed the default was `minimal`; the live run then made exactly five Spark 1.3 requests and no retries.

| Measure | Result |
|---|---:|
| Batch elapsed time | 18.656 s |
| Raw Muse evidence labels | 9/10 |
| Labels after timeline and scope gates | 10/10 |
| Strength labels | 10/10 |
| Proposed CV citations locally verified | 15/15 |
| Timeline flags detected | 1/1, no false positives |
| Estimated Standard-rate token cost | $0.049057 |
| Image-only scan OCR | 976 ms |

The batch replay's slowest Muse request took 17.589 seconds. The image-only CV's OCR and extraction took 993 ms total, of which 976 ms was Tesseract. OCR is therefore not the batch critical path, and lowering OCR resolution or weakening segmentation would risk the scan evidence without materially improving completion time. The prior PSM 3 change is retained because it improved anchor recall on the prepared two-column scan.

No proposed CV citation failed page verification. Muse also emitted one quote-like absence statement (“No semiconductor or outsourced assembly experience is listed.”); local evidence policy rejected it because an absence statement is not a candidate passage or conflict. This is not the separate historical amber-catch example; that remains a separately labelled scan audit.

## Changes made

- The application fallback, `.env.example`, and README now use `minimal` for Muse Spark reasoning effort.
- The request-contract test now checks that an unset value resolves to `minimal`.
- Set `MUSE_REASONING_EFFORT=medium` to restore the measured control profile.
- Added HTTP gzip compression for responses of at least 1,000 bytes. Serializing the five saved per-candidate responses measured 427,918 bytes uncompressed; gzip reduced them to 165,062 bytes (61.4% smaller). This is a local compression measurement, not a measured browser-network transfer.

The local extraction, quote-verification, timeline, and report stages already take milliseconds on text CVs; OCR takes about one second on the prepared scan. Gzip reduces the response bytes sent to the browser. Live Muse generation remains the measurable latency bottleneck. The app already runs candidate calls concurrently and renders completed candidates progressively; further local CPU tuning is not expected to materially shorten the five-CV batch.

## Artifacts

- Public-JD minimal run 1: [metrics](semantic_cases_live_20261029_compact_minimal.json) and [attempt ledger](semantic_cases_live_20261029_compact_minimal_attempt.json)
- Public-JD minimal repeat: [metrics](semantic_cases_live_20261029_compact_minimal_repeat.json) and [attempt ledger](semantic_cases_live_20261029_compact_minimal_repeat_attempt.json)
- Matched medium control: [metrics](semantic_cases_live_20261029_compact_medium.json) and [attempt ledger](semantic_cases_live_20261029_compact_medium_attempt.json)
- Default minimal five-CV app route: [metrics](unified_demo_metrics_default_minimal_20261029.json), [replay](unified_demo_replay_default_minimal_20261029.json), and [attempt ledger](unified_demo_attempt_default_minimal_20261029.json)

## Verification after the changes

- 122 Python unit tests passed, including the gzip response check and evidence-conflict gate tests.
- 13 JavaScript tests passed.
- Offline stress checks passed for the mock workflow, fake Muse response, hostile citation, malformed PDFs, and request limits; the stress run used no network or model credits.
- Python compilation, JavaScript syntax, and `git diff --check` passed.
- No extra Muse request was made for the gzip-only change; it does not affect model prompts or analysis semantics.
