# Mock recruiter-flow Muse run — 2026-10-29

## What was exercised

I simulated the browser's user path using the actual app routes and five fictional v3 CV PDFs: homepage, v3 input manifest, local JD preflight, PDF retrieval, consented Muse analysis, and the client-side recruiter decision validator. Analysis used five concurrent individual `POST /api/analyze` requests, matching the browser's per-CV request path. Muse was enabled only for this run, at the app's `minimal` reasoning setting, with no retries.

The environment has no Chromium executable, so this is an ASGI/browser-equivalent route run, **not** a visual browser test. It does not measure browser rendering, interaction delays, or the Render deployment.

## Measured flow

| Step | Result |
|---|---:|
| Homepage response | 200 · 65 ms |
| v3 five-CV manifest | 200 · 5 ms |
| Local JD preflight | 200 · 6 ms · 0 Muse calls |
| Five prepared PDFs retrieved | all valid · 17 ms |
| First candidate result | 10.953 s |
| All five candidate results | 11.957 s |
| Successful Muse requests | 5/5 · 1 per CV · 0 retries |
| Request errors | 0 |

## Per-candidate timing and source checks

| CV | Total request | Muse API | PDF/OCR | Preview | Verified / proposed citations | OCR |
|---|---:|---:|---:|---:|---:|---|
| C1 | 10.952 s | 10.758 s | 114 ms | 10 ms | 4/4 | No |
| C2 | 11.949 s | 11.775 s | 113 ms | 0 ms | 0/0; keyword-only profile | No |
| C3 | 11.452 s | 11.266 s | 113 ms | 12 ms | 4/4 | No |
| C4 | 11.007 s | 10.806 s | 110 ms | 17 ms | 3/3 | No |
| C5 | 11.730 s | 10.664 s | 1.025 s | 27 ms | 4/4 | Yes · 1 page |

All 15 proposed CV citations were locally verified. The date audit found one timeline flag on C4. The OCR scan remained below the Muse call time; skipping or lowering OCR would save little and could weaken two-column quote anchoring.

All five response bodies were gzip encoded. Their reported compressed content lengths summed to 164,566 bytes; decoded JSON totaled 424,553 bytes, about 61% smaller after compression. These are app response measurements, not a measurement over the Render network path.

The five requests reported 13,032 input, 6,115 output, and 3,708 reasoning tokens. The token-based Standard-rate estimate is **$0.04227875**, excluding any cached-input discount; this is not provider billing telemetry.

## Recruiter action simulation

The JavaScript decision helper was exercised with the returned candidate requirement IDs:

- Advance without a reason was accepted.
- Hold without a reason or linked criterion was blocked.
- Hold with a job-related scope reason and one linked criterion was accepted.

The browser UI was not available, so no visible matrix click, PDF viewer interaction, or download was claimed as completed. The normal JS suite covers the decision controls and shortlist/export logic. Browser paint and the actual in-page decision/export sequence remain unmeasured.

## Remaining bottlenecks and production boundary

1. **Muse generation is still the main wait:** about 10.7–11.8 seconds per candidate in this run. Five-way concurrency produced a 12-second batch locally.
2. **Render batch latency is unverified and likely slower:** `render.yaml` limits analyses to one, and the browser reads that limit and schedules one candidate at a time. Summing this run's five per-request times gives a rough **55–57 second** five-CV estimate at concurrency one, but that is an extrapolation, not a Render measurement; network and cold-start effects are unknown. Direct API clients that ignore the advertised cap receive HTTP 429 rather than being queued.
3. **Browser behavior is not visually verified here:** Chromium is missing in this environment. The route and client-side decision logic were checked separately, but browser paint and PDF.js interaction were not measured.
4. **The scan's OCR takes about one second:** it is small beside the Muse request and remains enabled to preserve scan recall.
5. **This is fictional calibration only:** it does not measure recruiter time saved or validate behavior on real candidate CVs.

The run used fictional CVs only. It created no persistent recruiter decisions and made no KUL or Render deployment calls.

Machine-readable telemetry: [mock user-flow metrics](mock_user_muse_api_flow_20261029.json).
