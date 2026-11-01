# EvidenceTrail — submission draft and final checklist

**Contest:** Meta Global AI Developer Hackathon (worldwide, including India).
**Official project deadline:** Nov 4, 2026, **9 PM US Eastern** = Nov 5, **7:30 AM India**.
**Internal safety deadline:** Nov 4, 2026, **11:59 PM IST**.
**Suggested submission:** Indie Developer / Build for Your World, **only if that matches the entrant's accepted track**. Do not change tracks without checking the portal.

## Title

EvidenceTrail

## Tagline

The quote is real. But who did the work?

## Description (150 words)

EvidenceTrail helps recruiters inspect whether a CV supports a job requirement. Meta Muse Spark proposes structured findings and quotations from extracted, page-labelled text. EvidenceTrail verifies each quote against its cited PDF page, then checks whether the passage documents the applicant doing the required work. Reviewers can inspect source highlights, original Muse labels, final labels, and recorded reasons before adding notes and exporting evidence. The public demo uses fictional CVs and saved Muse responses, with no new model calls. On twelve fictional pairs, raw labels matched nineteen of twenty-four author references; final labels matched all twenty-four. The five changes reclassified conflicting as not found where the source limited applicant responsibility. They were scope clarifications, not five fabricated quotations. All twenty-five proposed quotes were found on their cited pages. This small author-labelled set is not real-CV accuracy. EvidenceTrail provides evidence for human review, without candidate scores, rankings, automated rejections, or hiring decisions.

## How we used Meta Muse Spark

Meta Muse Spark 1.3 provides the semantic interpretation: it reads page-labelled text extracted from a CV alongside job requirements and returns structured requirement-level findings, evidence labels, explanations, and proposed quotations. The original PDF bytes are not attached to the model request. EvidenceTrail independently re-finds quotes on their cited pages and applies applicant-attribution and timeline safeguards, retaining the raw Muse label and final status for inspection. A human reviewer checks the evidence and records the decision.

The public judge path replays saved genuine Muse responses, with provider response IDs and source archives linked from the public JSON receipts. It makes no new Muse calls. The saved 12-pair / 24-request fictional replay records 19/24 raw labels and 24/24 final labels matching the author key, with 25/25 proposed quotes found on the cited pages. All five raw-to-final changes are `conflicting → not_found`, clarifying source scope rather than correcting five false `supported` findings. This small, author-labelled set is not a real-CV accuracy estimate; a provider receipt proves a call occurred, not that its answer is correct.

## Links and final handoff

- [Live demo](https://evidencetrail-judge-rc1-2026.onrender.com/)
- [M02 proof and full 12-pair table](https://evidencetrail-judge-rc1-2026.onrender.com/demo20?view=replay)
- [Per-case quote checks and source context](https://evidencetrail-judge-rc1-2026.onrender.com/static/replay-artifacts/twelve-pair-quote-audit.json)
- [Public replay summary](https://evidencetrail-judge-rc1-2026.onrender.com/static/replay-artifacts/twelve-pair-summary.json)
- [Source code](https://github.com/farhanjamal2002-blip/-evidencetrail)
- Video URL: [finished three-minute judge film](https://evidencetrail-judge-rc1-2026.onrender.com/static/evidencetrail-judge.mp4), with synthesized narration and actual live-site footage. [Transcript and proof map](demo/3_MINUTE_JUDGE_VIDEO.md).
- Before submission, confirm the deployed `/build-info` commit matches both `main` and the judge release branch.

## Entrant's final checklist

- [x] Create the three-minute judge film from the verified live build; publish its narration, captions, and proof map.
- [ ] Attach the video URL or upload the film in the participant portal as required.
- [ ] Check that the video, public repository, and live demo open while signed out.
- [ ] Confirm selected track, eligibility, rules acceptance, and required portal fields.
- [ ] Submit in the participant portal before the deadline and save the confirmation receipt. A merged PR is not an event submission.

## Freeze scope for the sprint

**IN:** criteria → saved fictional replay → separate quote and applicant-attribution checks → human review state/note → source inspection → receipts; reliable replay when offline; fast loading; visibly clear saved Muse results vs simulation.

**OUT until after Nov 4:** actual ATS integration, employer accounts, persistent database, auto-ranking/screening, interview scheduling, multi-tenant scalability, payment processing, new model routing, or expanded benchmark claims. None is required to show the hackathon's core AI innovation.

## Tight schedule (India time)

| Date | Goal and stop condition |
| --- | --- |
| Oct 29 | Lock feature list and judge narrative; commit current receipts/script |
| Oct 30 | Freeze feature/UI scope; make the exact ET-018 geometry and M02 browser smoke pass; no exposed API key |
| Oct 31 | Reproduce the exact screen flow on the final candidate build; fix only release-blocking UI, accessibility, or source-grounding defects |
| Nov 1 | Finish the three-minute judge video and check its claims against saved proof |
| Nov 2 | Review the cut, README, judge guide, and receipt references; no feature additions |
| Nov 3 | Signed-out, clean-room demo from submission commit; freeze all feature work |
| Nov 4 | **Submit early India time**, save portal confirmation; no last-minute feature builds |

## Failure fallbacks

- **Muse credentials missing on demo host:** use the saved 20-CV and 12-pair receipts, label them as saved replays, and never fake a live request.
- **Cold start or demo site unavailable:** use locally recorded screen capture with actual provider receipt evidence and runnable GitHub instructions; don't claim a live hosted result.
- **One candidate fails:** leave it in the queue as Failed, show explicit error; don't silently drop, rerun or fabricate success.
- **Time running out:** submission video + GitHub + authentic recorded test are more valuable than a half-built ATS.

Official event: https://cerebralvalley.ai/e/meta-ai-developer-hackathon .
