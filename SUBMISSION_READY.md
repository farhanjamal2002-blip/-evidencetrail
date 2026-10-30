# EvidenceTrail — November 4 Hackathon Submission Checklist

**Contest:** Meta Global AI Developer Hackathon (worldwide, including India).
**Official project deadline:** Nov 4, 2026, **9 PM US Eastern** = Nov 5, **7:30 AM India**.
**Internal safety deadline:** Nov 4, 2026, **11:59 PM IST**.
**Suggested submission:** Indie Developer / Build for Your World, **only if that matches the entrant's accepted track**. Do not change tracks without checking the portal.

## Submit this idea

**Title:** EvidenceTrail — Proof, not a black-box hiring score

**Tagline:** Inspectable, source-verified CV evidence powered by Meta Muse Spark.

**Short description (copy-friendly):**

EvidenceTrail helps recruiters inspect whether a supplied CV supports a specific job requirement. Meta Muse Spark 1.3 interprets the job criteria and CV text and proposes structured evidence; local PDF/OCR checks verify proposed quotations against cited pages, while deterministic scope and timeline safeguards preserve the raw Muse label beside the final evidence status. The recruiter inspects the source and owns the decision. A frozen actor-swap replay shows why a real quotation may still fail to support an applicant-specific claim. EvidenceTrail does not score or rank applicants, automate hiring decisions, or claim that a CV statement is true in the real world.

**Theme:** Build for Your World — improve an everyday document-intensive hiring workflow with a real model plus a source-grounding layer.

## What the judge should see (one smooth story)

1. **0:00–0:08:** Open the fictional recruiter inbox. State the design question: a quotation can be real while crediting the wrong person.
2. **0:08–0:38:** Open the saved M02 benchmark. Compare the applicant and director passages. Point to **Quote on the page?** and **Does it credit the applicant?** separately, then the struck-through raw Muse label, final evidence status, and reason.
3. **0:38–0:48:** Inspect the M02 receipt links and full-replay caveat. Say clearly that 25/25 is the 12-pair replay's citation total, not an M02-only measure or real-CV accuracy estimate.
4. **0:48–1:04:** Click the dark ET-018 next card. Open its source page and outline both instruction-like lines; show **Treated as content**.
5. **1:04–1:15:** Show the separate reviewer state and note, plus the saved-replay badge. The demo makes no new Muse call.

The current UI work is on draft PR #28 and is not deployed. Do not record or submit the new UI until its browser smoke passes and `/build-info` reports the exact reviewed release SHA.

The default public service disables new paid Muse calls. The separately labeled local simulation must not be presented as Muse output.

## Additional judge path: M02 actor-swap replay

Open the [recruiter inbox](https://evidencetrail-judge-rc1-2026.onrender.com/demo20), open the Replay benchmark, compare M02 baseline (`supported` → `supported`) with the director-attributed variant (raw Muse `conflicting` → final `not_found`), open the [public M02 case audit JSON](https://evidencetrail-judge-rc1-2026.onrender.com/static/replay-artifacts/m02-case-audit.json) without signing in. The linked GitHub run pages list full archived artifacts; ZIP download may require GitHub sign-in. Then click the encore button to open ET-018. The source label and final requirement label answer different questions; a verified quotation alone does not establish applicant attribution.

**Replay results and limit:** on the 12-pair / 24-request fictional author-labelled set, raw Muse matched 19/24 references and final pipeline labels matched 24/24; 25/25 quote/page checks passed across the full replay. These results describe this frozen test set only. The M02/M07 run summary records four provider receipts and zero retries; no M02-only 1/1 count is claimed.

## Required final deliverables

- [x] Public GitHub project exists and feature branch has recruiter inbox.
- [x] Source-linked code and frozen synthetic 20-CV fixture generator.
- [x] **All 20 fictional CVs analyzed by genuine Muse Spark:** 20/20 authentic responses and **76 locally verified quotations** in the [completed recording](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40892660190); no invented outcomes.
- [x] 143 Python / 13 JS, Chromium (desktop + mobile), Docker acceptance: [action log](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40888555124).
- [x] Judge-facing README: [JUDGE_GUIDE.md](JUDGE_GUIDE.md).
- [ ] **Judges' build:** choose **one commit** after final PR review, pin its SHA and share a working runnable/deployed version.
- [ ] **Public final-version parity:** [isolated 20-fictional-CV judge reviewer](https://evidencetrail-judge-rc1-2026.onrender.com/demo20) is on a separate free, mock-only Render service. Verify [exact deployed SHA](https://evidencetrail-judge-rc1-2026.onrender.com/build-info) against release PR #28 using the [automated public parity workflow](.github/workflows/public-demo-parity.yml). The older two services are not the final judge target; free hosting may cold-start.
- [ ] **Video:** record the 75-second M02 → receipt → ET-018 demo *from that same build*. Video length is a recommendation here; entrant must verify organizer's actual field limits.
- [ ] **Repository landing page:** point judges immediately to demo URL, 75-second video, run instructions and genuine Muse receipts.
- [ ] **Participant portal:** confirm selected track, rules acceptance, eligibility, required fields, team representative, final submission.
- [ ] **Signed-out test:** video, GitHub, demo URL all accessible from an anonymous browser.
- [ ] **Submit before internal Nov 4 IST deadline**, save confirmation receipt. **Submitting a PR is not submitting to the event.**

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
