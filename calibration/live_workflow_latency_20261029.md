# Live Muse workflow and bottleneck report — 2026-10-29

## Run performed

This is a fresh live run through the current one-request-per-CV analysis path, not the frozen replay.

- **Fixture:** one public-job-derived GlobalFoundries supplier-operations JD and five fictional CV PDFs from `unified_demo_v2`.
- **Route:** `POST /api/analyze-batch`, which runs the same `analyze()` pipeline used by the browser's per-candidate `/api/analyze` requests.
- **Model:** Muse Spark 1.3, medium reasoning, five concurrent slots.
- **Requests:** five successful analysis calls, no automatic retries, no failed candidates.
- **End-to-end server batch:** 30.689 seconds.
- **Token estimate:** $0.09864975 at the saved Standard rates. This is an estimate, not a provider billing record.
- **Inputs:** fictional candidate profiles only; the JD is disclosed in the fixture.
- A no-generation `GET /models` connectivity check returned HTTP 200 before the batch.

The attempt, metric summary, and full fictional replay are retained as separate files. The replay contains the fictional result payloads needed to inspect evidence; the metrics omit CV text and accepted quote text.

## Measured latency

| Candidate | Muse API | Whole candidate pipeline | Non-Muse time | PDF/OCR | Page preview |
|---|---:|---:|---:|---:|---:|
| C1 | 22.573 s | 22.722 s | 149 ms | 15 ms | 12 ms |
| C2 | 29.450 s | 29.588 s | 138 ms | 15 ms | 0 ms |
| C3 | 30.505 s | 30.659 s | 154 ms | 15 ms | 16 ms |
| C4 | 25.232 s | 25.387 s | 155 ms | 15 ms | 10 ms |
| C5, image-only scan | 26.139 s | 26.965 s | 826 ms | 799 ms | 20 ms |

Across the five calls, Muse latency had a **26.139-second median**, **26.780-second mean**, and **30.505-second maximum**. The median share of a candidate's server pipeline spent waiting for Muse was **99.39%**. The batch finished about 30 ms after its slowest candidate pipeline.

The model reported 10,794 input tokens, 20,037 output tokens, and 17,811 reasoning tokens. Prompt construction took 0–1 ms; response decoding and schema validation rounded to 0 ms in this trace. Client setup was at most 84 ms. Local quote checks and timeline/review rules took 1–11 ms. The scan's OCR execution was 783 ms, within 799 ms total extraction. These local stages are not the main batch delay.

The browser already schedules up to five candidate workers and adds each completed result as it arrives. This run measures the server analysis route, not browser paint, upload latency on a recruiter's network, or perceived usability on a deployed service.

## Semantic and grounding outcome

| Candidate | Expected-label result | What happened |
|---|---:|---|
| C1: specific evidence | 2/2 labels; 2/2 strength labels | Both direct findings matched. |
| C2: keyword-heavy profile | 1/2 labels; 0/2 strength labels | Muse missed one expected Related finding and returned `none` for both strength labels. |
| C3: facilities career switcher | 1/2 labels; 2/2 strength labels | One Related finding was correct; a second expected Related finding was labeled Direct despite the CV explicitly limiting the candidate's negotiation ownership. |
| C4: overlapping dates | 0/2 Muse labels; 1/2 after the timeline gate | The timeline detector found the planted overlap and overrode Muse's Direct label to Conflict to clarify. Muse also missed a separate expected Direct finding. |
| C5: scanned two-column CV | 2/2 labels; 2/2 strength labels | OCR ran on page 1; both findings and all four proposed quotes passed local verification. |

Overall, Muse matched **6/10** expected evidence labels; the deterministic timeline gate raised that to **7/10**. Strength labels matched **6/10**. The verifier accepted **14/14 proposed quotes** and blocked none in this run. The planted timeline conflict was found (**1/1**), but that single case is not a broad accuracy claim.

A prior same-day medium/five-slot summary for these same five case IDs recorded 27.87 seconds and 8/10 raw label matches. The older summary does not retain a prompt hash, so treat the difference as a repeatability/versioning warning, not a controlled measure of model variance. Do not blend the old and new results.

## Bottlenecks and next actions

1. **Semantic boundary is the product risk.** The C3 Direct label contradicts explicit CV wording that the candidate did not own negotiations. The quote verifier proves a quote exists; it does not prove the quote supports the model's interpretation. Keep decisions human-controlled. Tighten the Direct-versus-Related prompt around ownership, authority, and execution, then score the overclaim case separately from underclaims.
2. **Muse generation is the latency bottleneck.** Five-way concurrency is already in use. Test lower reasoning effort and a shorter output contract only as matched runs on the same frozen inputs, recording prompt hash, response size, latency, and label outcomes. Do not claim the speed tradeoff is safe until the semantic score holds.
3. **OCR is a secondary cost.** The scan adds about 0.8 seconds, less than 3% of its 26.965-second pipeline. Preserve the OCR path; further OCR tuning is lower priority than Muse latency and semantic reliability.
4. **Browser timing is still unmeasured.** Add client-side timestamps for upload start, each candidate's first result, all-results completion, and render completion before making a recruiter-time or end-user-latency claim.

**Current baseline:** 30.689 seconds for five candidates, 6/10 raw labels, 7/10 after one deterministic timeline override, 14/14 proposed quotes verified, one Related-to-Direct overclaim, and an estimated $0.09865 token cost.
