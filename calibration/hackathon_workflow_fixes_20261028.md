# Hackathon workflow fixes — 28 Oct 2026

## What changed

- Batch reviews now submit CVs independently and add each result as it finishes. Pending and failed CVs remain visible in upload order; failed files can be retried individually. A live retry makes one Muse request. A late response is discarded if the recruiter starts another review.
- The requirement matrix now warns when independent candidate analyses return different requirement lists. Blank cells remain “not returned,” never “candidate lacks this skill.”
- Before a multi-CV run, the recruiter can edit the detected numbered/bulleted items, remove criteria, or add their own, then choose to apply that checklist to every CV. The same list is included in each candidate request. Deterministic alignment preserves locked wording, drops model-created extras, and leaves omissions visible for review. Failed-CV retries reuse the list. Recruiters can turn off the shared checklist and use separate extraction per CV.
- The live Muse path now makes one structured request per CV. Muse returns semantic labels and candidate quotes together; local code verifies each quote against the PDF and computes date conflicts. This removes the former sequential model adjudication call while keeping citation failure and timeline checks deterministic.
- The Muse request now sends page-labelled text extracted locally from the PDF, not the PDF bytes. The serializer uses the existing layout-aware word stream to keep detected regions/columns separate and marks OCR pages for cautious model interpretation. Exact quote and page checks still use the local PDF word boxes. The schema now caps evidence at two passages per requirement and per candidate-statement claim to reduce redundant generation.
- Live usage telemetry now includes the extracted CV text character count, page count, and OCR page count alongside provider-reported input/output tokens and API latency. These inputs support a measured comparison on the next approved Muse run; this change itself has not yet been benchmarked live.
- Offline packet-shape check on the five unified v2 PDFs produced 390–794 page-labelled CV text characters per candidate from files sized 1,042–33,016 bytes; the scanned two-column CV used OCR on one page. This compares characters to file bytes only. It is not a token, cost, or response-time measurement.
- Batch UI requests run concurrently up to the configured server limit (two by default) and update as each CV finishes. One slow candidate no longer holds completed CVs off screen. The standalone batch API still preserves upload order.
- Identical CV + job + rubric results may be reused in the current browser tab for 15 minutes. The bounded cache is in memory, includes the analysis contract version, and does not persist data on the server. No live timing measurement has yet been made for this revised path.
- Hold and Do not advance require a job-related reason. Selecting “Other” also requires a short note. Incomplete choices are not recorded as decisions. The reason is included in the shortlist audit JSON and the recruiter hand-off.
- Hold and Do not advance now also require one or more exact checklist criteria. The selection is carried into the audit JSON and hand-off with the criterion wording and evidence label. Advance clears these links. This closes the gap between a generic reason and the role requirement that informed the recruiter.
- An explicitly requested Muse provider with `EVIDENCETRAIL_ENABLE_MUSE=false` now fails closed before reading the uploaded PDF. The page labels the disabled state, and the smoke-check script reports that no live request is expected. Default local mode remains explicit and makes no Muse call.
- A copied `.env.example` placeholder is treated as a missing model key. The home-page status, single-CV route, batch route, and live smoke preflight agree; the client-side disabled-submit message also distinguishes an opt-out from a missing key.

## Why

The batch is the recruiter's comparison unit. Losing a wholly failed batch, silently comparing different requirement lists, or recording an unexplained rejection makes that workflow less useful. These changes keep the reviewer in control and make the output clearer without adding a model pass.

## Verification

- Python unit suite: **97 passed** (`.venv/bin/python -m unittest discover -s tests`).
- JavaScript tests: **13 passed**.
- JavaScript syntax checks: passed.
- Offline stress suite: all scenarios passed, including the guarded fake Muse path and hostile-response checks; it made **zero Meta API requests**.
- `git diff --check`: passed.
- A browser interaction smoke could not start because this runtime has Playwright but no Chromium executable. No browser was installed or downloaded.
- Muse/provider configuration tests now distinguish three states: default local simulation, Muse explicitly requested but disabled, and Muse explicitly enabled but missing a key. Each failure occurs before uploaded-file processing or API client creation.
- The recruiter-curated checklist is included in each per-CV request. The current live path reports one Muse request per CV; local quote/page verification and timeline math add no model requests. The new one-pass semantic contract has not yet had a live calibration run.
- The text-first Muse request contract and two-column text serializer pass the fake-client tests. The full Python suite also covers hostile quote rejection through the configured Muse-shaped app path. No live Muse request was made during this optimization pass.
- A no-network slow-provider probe injected 350 ms into the fake API call; the app reported 350 ms API latency and 351 ms end-to-end, with zero retries. This validates timing instrumentation only, not Muse's real latency.
- Live bridge check: the only registered Desktop Commander device, FARHAN-KHAN, is offline (last seen 134 hours ago). The Muse preflight with explicit process-local enable flags reports ready and `meta_request_made=false`; the repository's `.env` remains in local/mock mode. No direct Meta request was attempted.
- A separate Muse Wonder code review used code only, no CVs. Two requests returned no usable critique because the completion cap was consumed by reasoning. The second reported 8,277 input and 1,800 output tokens (1,798 reasoning tokens); the token estimate is about **$0.07** at the saved Wonder rates, not a billing record. The first request's usage was not captured, so it is unknown. Neither response is treated as a code finding.

## Remaining product limitation

The recruiter can edit and lock a plain list of criteria, but the interface does not yet classify each as must-have/preferred or ask Muse to propose structured criteria from unformatted prose. Custom checklist items are labeled as recruiter-provided in the evidence trail; they are never presented as verbatim JD text. The recruiter can add those criteria manually or leave the shared checklist off and use per-CV extraction.
