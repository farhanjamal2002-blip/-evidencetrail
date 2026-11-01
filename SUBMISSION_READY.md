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

EvidenceTrail helps recruiters inspect what a CV actually supports against a job checklist. Meta Muse Spark reads extracted, page-labelled CV text and proposes structured findings with quotations. EvidenceTrail independently checks that each quote appears on the cited PDF page, then checks whether the passage credits the applicant for the required work. The interface keeps the original Muse label beside the final status, links evidence to its source, and leaves every decision to a human reviewer. The public demo uses fictional CVs and saved Muse responses; browsing makes no new model calls. In the saved twelve-pair replay, raw Muse labels match nineteen of twenty-four author references; final labels match all twenty-four. All twenty-five proposed quotes were found on their cited pages. These results describe a small fictional set, not accuracy on real CVs. Reviewers can inspect outlined source instructions, record notes, and export evidence without candidate scores, rankings, or automated rejections.

## How we used Meta Muse Spark

Meta Muse Spark 1.3 provides the semantic interpretation: it reads page-labelled text extracted from a CV alongside job requirements and returns structured requirement-level findings, evidence labels, explanations, and proposed quotations. The original PDF bytes are not attached to the model request. EvidenceTrail independently re-finds quotes on their cited pages and applies applicant-attribution and timeline safeguards, retaining the raw Muse label and final status for inspection. A human reviewer checks the evidence and records the decision.

The public judge path replays saved genuine Muse responses, with provider response IDs and source archives linked from the public JSON receipts. It makes no new Muse calls. The saved 12-pair / 24-request fictional replay records 19/24 raw labels and 24/24 final labels matching the author key, with 25/25 proposed quotes found on the cited pages. This small, author-labelled set is not a real-CV accuracy estimate; a provider receipt proves a call occurred, not that its answer is correct.

## Links and final handoff

- [Live demo](https://evidencetrail-judge-rc1-2026.onrender.com/)
- [M02 proof and full 12-pair table](https://evidencetrail-judge-rc1-2026.onrender.com/demo20?view=replay)
- [Public replay summary](https://evidencetrail-judge-rc1-2026.onrender.com/static/replay-artifacts/twelve-pair-summary.json)
- [Source code](https://github.com/farhanjamal2002-blip/-evidencetrail)
- Video URL: pending the entrant's recording and upload; follow [the three-minute script](demo/3_MINUTE_JUDGE_VIDEO.md).
- Before submission, confirm the deployed `/build-info` commit matches both `main` and the judge release branch.

## Entrant's final checklist

- [ ] Record and upload the judge video from the verified deployed build.
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
| Nov 1 | Capture the 75-second demonstration from the verified SHA and a backup local recording |
| Nov 2 | Review the cut, README, judge guide, and receipt references; no feature additions |
| Nov 3 | Signed-out, clean-room demo from submission commit; freeze all feature work |
| Nov 4 | **Submit early India time**, save portal confirmation; no last-minute feature builds |

## Failure fallbacks

- **Muse credentials missing on demo host:** use the saved 20-CV and 12-pair receipts, label them as saved replays, and never fake a live request.
- **Cold start or demo site unavailable:** use locally recorded screen capture with actual provider receipt evidence and runnable GitHub instructions; don't claim a live hosted result.
- **One candidate fails:** leave it in the queue as Failed, show explicit error; don't silently drop, rerun or fabricate success.
- **Time running out:** submission video + GitHub + authentic recorded test are more valuable than a half-built ATS.

Official event: https://cerebralvalley.ai/e/meta-ai-developer-hackathon .
