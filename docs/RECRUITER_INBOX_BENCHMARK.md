# EvidenceTrail recruiter inbox — product benchmark and build plan
**2026-10-29 | Implementation branch:** `feat/recruiter-demo20-muse-inbox`

## What leading products already do (official sources)
- **Ashby:** per-job recruiter-editable, validated, objective resume criteria, AI review by criterion, review filters, app-level opt out, human decision. https://docs.ashbyhq.com/ai-assisted-application-review
- **Greenhouse:** recruiter-calibrated requirements, AI match categories, review/edit before saving, no automatic hiring decision. https://support.greenhouse.io/hc/en-us/articles/41131886674075-Talent-Matching-FAQ
- **Gem:** applicant review workbench, optional AI prioritization by job, filterable queue, recruiter action. Its percentage score is a product choice, not evidence of accuracy. https://help.gem.com/external/ai-powered-app-review
- **Meta Muse:** structured output, reasoning effort, caching, batch/streaming through Meta Model API. Benchmark observed quality, latency and provider-reported token usage rather than assuming optimization works. https://dev.meta.ai/docs/overview

## Differentiation: inspectability, not an opaque AI leaderboard
Every candidate must remain discoverable. The recruiter sees a source-verified criterion, original PDF page, exact quote, the distinction between **direct** and **related**, missing/conflicting material, and the model-vs-local decision audit. A related quote NEVER silently proves an exact requirement. No candidate scores, demographic inferences, or automatic advances/rejections. "Not found" means "not documented in the supplied CV", not "candidate lacks ability".

## User journey shipped in this branch (fictional demo only)
1. Open `/demo20` from the EvidenceTrail landing page. Job and four objective procurement criteria are filled from a **fictional** fixture.
2. Edit/confirm job criteria before analysis. `POST /api/role-audit` does a free local preflight; the recruiter has control over the rubric. Human edits invalidate the original fixture's expected labels.
3. Click "Load 20 fictional CVs" to view 20 applicants immediately in received order. The dataset contains 2 generated image-only PDFs, overlapping-date cases, career switches, no evidence, and prompt injection.
4. Search applications and filter by completion or **actual verified** evidence states. Unprocessed CVs are never pretended to be model-reviewed.
5. Explicit opt-in for **one CV** or **up to five** separate calls to the existing `/api/analyze` endpoint, with at most 2 requests from the browser concurrently. Consent is required; no auto-run, retry loop, or hidden API spend.
6. Muse (if configured) interprets page-labelled text under the recruiter-locked rubric; EvidenceTrail locally verifies quotes and dates. Only real returned results are presented as Muse evidence.
7. Inspect a source PDF; record Advance/Hold/Do not advance in local browser state; export a review JSON or the app's source-checked HTML report. No interview module.

## Truthfulness and boundaries
- The 20 fictional fixtures have human-written **reference test labels** for QA, hidden under explicit disclosure. They are not model predictions, scores, or applicant recommendations.
- The app's deployment without a Muse key remains a **fictional inbox preview**, not an AI evaluation.
- Existing analysis currently accepts up to 5 CVs per batch. This inbox can display 20 but it is **not** a durable 20-applicant production queue; uploaded files and decisions are not stored across sessions, authentication and multi-tenancy are not implemented.
- Analyses may be blocked by the server's per-IP five-analyzes-per-hour setting. Do not change a global quota just to make the demo appear to process 20.
- Real employment screening in a jurisdiction may require data-protection, disclosure, fairness and audit controls. Do not connect a real ATS or real CVs until those are ready.

## Next production gate (measurable)
1. **Durable intake:** permissioned ATS webhook/upload adapter, tenant-scoped `job_id` + `application_id`, idempotency key by (job, CV SHA256, rubric version, model/prompt version), asynchronous queue and backpressure. Track queued/processing/failed/stale/complete independently.
2. **Tenant privacy:** authentication, no public CV URLs, consent record, encrypted storage, request-scoped temp cleanup, per-tenant deletions, PII minimization and access logs.
3. **Real processing:** low-cost local extraction first, deduplicate identical files, one structured Muse request per CV; deterministic quote/page verification and semantic overclaim gates; no invented response IDs; bounded provider backoff only for confirmed safe retry conditions.
4. **Time-to-value:** measure warm/cold p50/p95/p99 time to first verified candidate; 5 and 20 CV batch wall times; scanned OCR p95; user-visible progressive results; queue 429 and provider 503 recoverability.
5. **Quality:** fixed 20 fictional CVs plus diverse independent industry cases. Report overclaims separately from misses; **no fabricated citations**, reference expected labels never shown as model output. Repeated model runs and a human reviewer must adjudicate disagreements.
6. **Recruiter UX:** keyboard controls, bulk filters/saved views, clear "not documented" wording, confirmation on decisions, persistent human audit and export. Validate with real recruiters before a commercial claim.
7. **Rollout:** controlled staging with secrets; end-to-end on actual intended CPU/RAM, load and privacy tests, rollback gate and production observation. No unreviewed `main` deploy.

## Scorecard to compare against existing ATS
Track recruiter **minutes per evidence review**, number of manual document opens per resolved criterion, time to first verified result, p95 latency at fixed cost, verified-quote rate, overclaim rate, saved reasons, accessibility and explicit opt out. Do not claim superiority without comparative measurements.

## Demo script
Create one fictional job → confirm four criteria → load 20 fictional CVs → open scan / injection cases → show received-order review queue and evidence filters → run one deliberately authorized Muse analysis on a fictional CV if Meta key configured → click a page-verified quote → make a human Hold decision → export.
