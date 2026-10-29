# Latency fixes and integrated live calibration — 2026-10-29

## What changed

- Added conservative local extraction of explicit employment date ranges. A Muse omission no longer prevents the deterministic timeline audit from finding a documented overlap. Extracted dates remain page-anchored and are labelled as local extraction in the UI.
- Changed scanned-page OCR segmentation from Tesseract PSM 6 to PSM 3. On the prepared image-only two-column CV, the local anchor check improved from 6/8 to 8/8 phrases; the latest live run verified all four proposed quotes from that scan. The latest scan OCR stage took 887 ms.
- Tightened the minimum-years prompt rule for job requirements that list alternative domains with “or”. A substantiated listed domain can satisfy the semantic domain test; date arithmetic remains local.
- Corrected the unified demo's C2 test data. The old profile included actual purchase-order and supplier-records work, making “unsupported / keyword only” an ambiguous gold label. The original v2 fixture and results remain unchanged. V3 removes that duty line and tests a true skills-list-only profile.
- Added `--fixture` and `--run-suffix` to the unified demo runner. New runs can use a revised fixture and receive separate metrics, replay, attempt, and PDF-asset paths without overwriting prior evidence. Run records now include the fixture hash, system-prompt hash, model, and reasoning setting.

## Latest live run

The v3 fixture contains one shared public-job-derived JD and five fictional CVs. The live route used Muse Spark 1.3 at medium reasoning with five concurrent requests. It completed all five requests in 28.392 seconds, with no retries. The saved token-based Standard-rate estimate is **$0.10055225**, not provider billing telemetry.

| Measure | Result |
|---|---:|
| Muse evidence labels | 9/10 |
| Labels after deterministic timeline gate | 10/10 |
| Evidence-strength labels | 10/10 |
| Proposed quotes locally verified | 15/15 |
| Related-to-Direct overclaims | 0 |
| Planted timeline overlaps detected | 1/1; no false positives |
| Candidate analyses completed | 5/5 |

The sole raw label miss was the planted date overlap: Muse called it Direct, and local date math changed the final state to Conflict to clarify. That is the intended division of work. Both C3 career-switcher findings remained Related and were marked ambiguous for recruiter review. C2 was labelled unsupported / keyword only on both requirements, with no supporting citations. C5 used OCR and returned four locally verified quotes. This run produced no blocked quote; the previously recorded scanned-CV verifier catch remains a separate, labelled example.

## Where the latency is

| Candidate | Muse request | Full candidate pipeline | Extraction/OCR | Other local work |
|---|---:|---:|---:|---:|
| C1 | 13.920 s | 14.068 s | 16 ms | 132 ms |
| C2 | 15.056 s | 15.186 s | 16 ms | 114 ms |
| C3 | 28.213 s | 28.359 s | 16 ms | 130 ms |
| C4 | 22.204 s | 22.360 s | 94 ms | 62 ms |
| C5, image-only scan | 21.387 s | 22.328 s | 907 ms, including 887 ms OCR | 34 ms |

Muse consumed about 98.5% of the combined per-candidate pipeline time. The five requests overlap; total batch wall time is close to the slowest request, not the sum of all five. Five-way concurrency is already enabled. PDF processing, quote verification, timeline math, and previews are no longer material waits on ordinary CVs. OCR adds under one second on this prepared scan.

Lower reasoning effort previously reduced latency, but the broader fixed-set comparison had weaker semantic results and one Related-to-Direct overclaim. Medium remains the default. The remaining 14–28 second per-candidate generation wait is on Muse's side of the API boundary; lowering it further with the measured settings trades away reliability. The UI already posts candidate requests concurrently and adds results as each one completes, so a recruiter can open early results before the slowest CV finishes.

## Verification

- 117 Python unit tests passed.
- 9 JavaScript tests passed.
- JavaScript syntax, Python compilation, and `git diff --check` passed.
- The offline stress scenarios passed, including malformed PDFs, hostile content, and forged quote rejection; they made no live model requests.
- The run uses only fictional CVs. Metrics omit CV text and accepted quotes. The replay contains the fictional evidence needed for demo inspection.

This is a small prepared calibration set. It verifies the intended demo path and deterministic gates; it is not a general accuracy or recruiter-time-savings claim. Browser paint time, deployment-network latency, and broader real-user results remain unmeasured.
