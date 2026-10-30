# EvidenceTrail — ready-to-paste competition submission draft

**DRAFT, NOT SUBMITTED.** Confirm actual participant portal fields, video length, accepted track, entrant eligibility and hackathon rules. Do not use placeholders as submitted URLs. The repository default branch is currently OLDER than the frozen judge release; link to the actual release branch.

## Project title
EvidenceTrail — Inspectable AI Evidence Review for Hiring

## One-line pitch
Meta Muse interprets CVs; EvidenceTrail checks the source pages, exposes corrections, and lets recruiters resolve uncertainty without AI candidate scores or automatic decisions.

## Theme
Build for Your World.

## Track
**USE THE TRACK ACCEPTED IN THE ORGANIZER PORTAL.** Do not assume Indie or Startup based solely on the source repository or company founder role.

## Short project description
Recruiters receive CVs full of shorthand, overlapping roles, and missing details. A language model can sound confident even when it credits an applicant with work a colleague performed. EvidenceTrail reverses that failure mode. Meta Muse Spark 1.3 produces requirement-level semantic proposals and exact CV quotations. Our local engine rechecks each quote against the actual source PDF page, preserves original and corrected labels, and distinguishes missing, conflicting, and supported document claims. Recruiters can inspect the highlighted page, ask a source-linked clarification, record an explicitly self-attested candidate reply, and export the full audit. EvidenceTrail never ranks candidates or auto-rejects them.

## What was actually built
An inspectable recruiter-facing CV evidence review workflow with an approved criteria rubric, document parsing and on-device/server-local OCR, genuine Meta Muse structured output, source-quote/page verification, scope/timeline safeguards, contradictory claim inspection, no-score human review stages, clarification draft, self-attested reply handoff, and standalone HTML/CSV exports. The judge-facing demo uses 20 fictional CVs and saved authentic Meta responses to avoid charging judges or exposing keys.

## Meta integration and reproducible proof
- **Meta Muse Spark 1.3** interprets CV/job meaning and proposes structured requirement findings with page quotes.
- **Saved authentic response receipts**: 20 genuine Meta responses in the October 29 recorded replay, 76 proposed quotes passed the local page check, 71 individual source citations retained. The sample does **not** contain a rejected quote; semantic scope corrections are visible instead.
- **Distinct newer evaluation**: five fresh fictional CVs yielded 5/5 final labels matching author-created references (raw 3/5), 6/6 source-verified quotes, and genuine provider response IDs. This is not a real-world accuracy estimate.
- **Meta native image experiment**: one opt-in image+OCR call succeeded technically but lost an OCR-supported finding on the single paired test. Vision stays disabled on the public judge demo; do not claim an improvement.

## Competitive differentiation
Conventional AI-assisted hiring tools often present model criteria and recommendations. EvidenceTrail emphasizes independent verification of quotations against source pages, visibility into Muse's original versus corrected evidence label, failure-closed handling of unsupported citations, and human rather than automated employment decisions. This is an evidence layer, not an ATS replacement or independent real-world credential verification.

## Demo links
- **Working anonymous judge demo:** https://evidencetrail-judge-rc1-2026.onrender.com/demo20
- **Deployed commit proof:** https://evidencetrail-judge-rc1-2026.onrender.com/build-info
- **Exact source tree for deployed release:** https://github.com/farhanjamal2002-blip/-evidencetrail/tree/release/evidencetrail-judge-rc1-oct30
- **Pinned release SHA:** `8489e45ae0f87d8421562618bda556c31911372b`
- **Authentic Muse 20-CV receipts:** https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40892660190
- **Real public browser acceptance:** https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/41014520478
- **Capped five-CV Muse scope evaluation:** https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/41016897397
- **Captioned video rehearsal (not the final):** https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/41019499720
- **FINAL PUBLIC VIDEO URL:** [MISSING — record narration, host and verify signed-out]

## Claims not to make
Do not claim results on real applicants, independent hiring fairness compliance, a representative benchmark, 30–50% measured productivity savings, universal protection against injection, or native Meta vision improving accuracy. The recorded demo is genuine historical Muse output, not a model invoked for each judge click.

## Required organizer/entrant verification
- [ ] Accepted track and permitted team/entrant structure confirmed in portal.
- [ ] Official rules, new-code/reused-work requirements, third-party assets and licensing confirmed.
- [ ] Final video produced, duration/format/hosting checked against actual portal requirements.
- [ ] Every submitted link opened while signed out and source commit checked.
- [ ] Entrant submitted the actual portal form before November 4, 2026, 9 PM Eastern (November 5, 7:30 AM IST).
- [ ] Actual submission confirmation saved.