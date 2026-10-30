# EvidenceTrail — final-round red-team audit
_Date: 2026-10-30. Scope: Meta Global AI Developer Hackathon judge-facing edition._

## Objective
Maximize *verifiable* judge confidence, not feature count or an imagined 94/100.
The organizers describe Indie as creativity/ambition/working functionality and
Startup as execution/production resilience. The official 2026 event closes
Nov 4 9 PM Eastern = Nov 5 7:30 AM India. Confirm the registered track in the
participant portal before using either track's framing.
Official: https://cerebralvalley.ai/e/meta-ai-developer-hackathon

The project is a hiring-document **evidence review** tool. It never establishes
external truth, ranks candidates, or makes the employment decision.

## Red-team findings, ordered by potential submission damage

| Rank | Threat / hidden weakness | Current evidence and honest limitation | Fix / no-go gate |
|---|---|---|---|
| P0-1 | Judge reaches stale or broken product | The final work is on draft PR #27, itself depending on draft PR #21, #18, #9, #6, #3; the historical public demo may serve another SHA | Freeze SHA, build/deploy it deliberately, record release commit in public README, verify signed-out desktop/mobile after cold start; no submission link otherwise |
| P0-2 | Video claims a hallucinated quote was blocked in current replay | Pinned 20-CV replay has **zero excluded quote spans**, although it demonstrates several raw-to-final semantic corrections | Use ET-003 (actual supported→not_found status changes) and ET-015 (actual two-sided statements). Quote *no* fake blocked spans |
| P0-3 | Judges cannot tell what Muse does | Generic “AI reads CVs” sounds like existing ATS functionality | Make genuine response ID, structured semantic proposal, quote/page verifier, raw/final status audit and recruiter-controlled resolution visible within first 30 sec |
| P0-4 | “80/80” interpreted as real-world performance | The benchmark and new holdout are author-made synthetic cases; raw Muse labels were much weaker; 80/80 is final pipeline accuracy on constructed scenarios | Show exact denominators, reference-label origin, error taxonomy and examples; never claim population accuracy or human-adjudicated superiority |
| P0-5 | Submission mechanics/eligibility | Code cannot check accepted portal track/rules, team or attribution terms, final submitted URLs, or successful portal confirmation | Confirm accepted track, entry ownership, rules, prize eligibility, disclosure of synthetic data and any team members in portal; capture confirmation |
| P0-6 | Video link or public Render cold start | Browser CI is **local** and does not prove public accessibility; anonymous paid Muse disabled intentionally | Signed-out external cold-start check of exact URL; use saved authentic replay, downloadable backup video, no credentials |
| P1-1 | Multimodal benefit unproven | PDF→OCR and opt-in image_url are implemented, but no authenticated native Meta vision result compared against OCR-only | Consent + key + hard request cap: one or two paired fictional scanned CV calls, capture response IDs/latency/quote validity; drop vision from video if worse |
| P1-2 | “Recruiters save 50%” is untested | Existing synthetic classification tests only measure evidence labels, not human task time | Small randomized timed manual-vs-assisted reviewer trial; log errors and median/p90. If no external reviewers, say unmeasured and don't invent impact |
| P1-3 | Reviewer over-trust and false omissions | Source text presence != semantically correct support; not_found != applicant lacks skill; selective attention could hide applicants | Audit false-supported, missed-supported and abstained/needs-clarification separately. Keep every candidate visible; no auto reject, no automatic score |
| P1-4 | Fairness/criteria risks | Role prerequisites may include proxies or unreasonable restrictions; avoiding scores isn't automatic regulatory compliance | Reviewer-approved job-related criteria, criterion warning/audit, accommodation path and ability to opt out of AI; do not market legal compliance |
| P1-5 | CV PII and model consent | Public demo has only fictional CVs; production intake can include sensitive personal data and source traces | Ensure explicit model consent, server-only key, minimize retention, no uploading real applicants in judge demo; publish clear privacy disclosure |
| P1-6 | Injection and unsafe export | One injection fixture ET-018 is not a full attack benchmark. Third-party CV text remains untrusted | Add hidden/typographic injection + table/OCR variants offline; avoid interpreting CV commands as instructions. Sanitize HTML and CSV exports |
| P1-7 | Multilingual and complex layouts | Existing 20-person replay mostly single-page, English, with two image-only cases. Layout geometry on scans is page-only | New *untouched* PDFs: RTL/multilingual, tables/two-column, low resolution, dates spanning jobs, quotes within footnotes; fail closed to page-only |
| P1-8 | Human reply incorrectly becomes 'verified' | Reply is entered by recruiter, not an authenticated external fact | Keep badge 'candidate self-attested / not independently verified', timestamp, original CV untouched and human decision required |
| P1-9 | Speed, load and cost regression | Small Muse samples give seconds-level timings, not SLA; vision may inflate tokens. No production concurrency benchmark verified | Record p50/p90 in controlled run, cold-start vs warm; cache stable prompt prefix, default to OCR-only, use no paid calls in CI |
| P2-1 | Accessibility | Local Chromium happy path is not a WCAG audit | Keyboard-only path, mobile 375px, 200% zoom, focus state/labels, contrast and screen-reader announcement audit; fix blockers only |
| P2-2 | Demo overflows into competing products | ATS integrations, scheduling, agent email, scoring and team accounts add surface area without core innovation | Keep them in roadmap, not first-minute video; submission flow is Muse → checked source → correction → clarification → human review → export |
| P2-3 | Commercialization and differentiation | Ashby and Gem already have criterion-based AI review. “No scores” alone isn't unique | Demonstrate a genuine source-grounded correction and audit provenance; articulate what is inspectable that a generic AI review does not expose |

## Source references
- Meta/Cerebral Valley official event: https://cerebralvalley.ai/e/meta-ai-developer-hackathon
- Meta model capabilities: https://dev.meta.ai/docs/models
- Meta image input (including base64): https://dev.meta.ai/docs/image-understanding
- Meta prompt caching: https://dev.meta.ai/docs/prompt-caching
- Prior Meta LlamaCon winners, including OrgLens and Geo-ML: https://ai.meta.com/blog/llamacon-hackathon/
- Ashby AI application review (criteria validation and filters): https://docs.ashbyhq.com/ai-assisted-application-review
- Gem application review: https://help.gem.com/external/application-review
- NIST GenAI risk management profile: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- OWASP indirect prompt injection: https://genai.owasp.org/llm-top-10/
- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/
- EU AI Act Employment scope: https://ai-act-service-desk.ec.europa.eu/en/employment-0

## Concrete proof package for judging
1. One immutable source SHA / Docker image / public URL mapping.
2. Judge preflight artifact from scripts/judge_readiness_gate.py, with real model receipts and unproven gates enumerated.
3. A **live or saved but authentic** Meta Muse recording; original provider request ID, model id, and quote/source verification receipt (no fabricated status).
4. ET-003 as real semantic correction; ET-015 as two-sided discrepancy; ET-019 as honest scanned source; ET-018 as a *single* injection fixture, not proof of complete attack robustness.
5. Human clarification and self-attested reply in existing 20-CV inbox; exported standalone pack.
6. One fresh multi-page unseen adversarial set and documented failure breakdown. Include failures rather than only successes.
7. Timed human-pilot CSV, if independently gathered; no impact estimate is passed off as measured outcome.
8. Video 75–90 seconds; show the core correction by 0:30; judge-clickable anonymous replay link and fallback video.

## Release sequence and stop conditions
- **Oct 30:** no new features outside P0; prove preflight, fix only actual CI failures, capture release candidate SHA and deployment strategy. Never claim that local CI proves public availability.
- **Oct 31:** controlled native Meta image test and unseen adversarial cases; forbid unlimited or public paid API access.
- **Nov 1:** independent recruiting usability/time study with explicit limitations.
- **Nov 2:** first final video, accessibility corrections and external signed-out review.
- **Nov 3:** freeze exact build and verified links, submission fields, track and consent disclosures.
- **Nov 4 (IST):** submit early, save portal confirmation. Stop changing the release without emergency need.

## Rule for every proposed new feature
Ship it only if it (a) concretely increases observed evidence integrity, (b) reduces a real reviewer step/time, or (c) makes a true Meta-specific breakthrough visible to a judge, **and** passes the existing zero-paid-call regression and privacy gates. Else defer to the commercial Recruiter OS roadmap.
