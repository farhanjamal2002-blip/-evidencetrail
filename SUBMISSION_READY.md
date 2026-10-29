# EvidenceTrail — November 4 Hackathon Submission Checklist

**Contest:** Meta Global AI Developer Hackathon (worldwide, including India).
**Official project deadline:** Nov 4, 2026, **9 PM US Eastern** = Nov 5, **7:30 AM India**.
**Internal safety deadline:** Nov 4, 2026, **11:59 PM IST**.
**Suggested submission:** Indie Developer / Build for Your World, **only if that matches the entrant's accepted track**. Do not change tracks without checking the portal.

## Submit this idea

**Title:** EvidenceTrail — Proof, not a black-box hiring score

**Tagline:** Inspectable, source-verified CV evidence powered by Meta Muse Spark.

**Short description (copy-friendly):**

Recruiters often receive dozens of CVs but cannot quickly tell which claims actually support a job requirement. EvidenceTrail combines Meta Muse Spark 1.3's semantic interpretation with independent PDF-page quotation verification, date/scope checks, and a human-controlled evidence inbox. A recruiter sets objective criteria for one job, inspects 20 clearly fictional applicants, selects a candidate for consented Muse analysis, reviews exact supported/related/missing/conflicting passages on the original CV page, and exports a traceable review record. The AI does not score or rank applicants or make hiring decisions. Two fictional scanned PDFs and an embedded prompt-injection example demonstrate OCR and robustness.

**Theme:** Build for Your World — improve an everyday document-intensive hiring workflow with a real model plus a source-grounding layer.

## What the judge should see (one smooth story)

1. **0:00–0:20**: 100 CVs create a real review burden; percentages hide why. Show EvidenceTrail's 20 **fictional** received-order CVs.
2. **0:20–0:42**: Employer writes a procurement job and confirms four criteria. Show search/filters; nothing starts as “AI analyzed.”
3. **0:42–1:10**: Select `ET-005` and show **related experience is not proof** of direct negotiations. The raw Muse label is preserved; the final status is grounded.
4. **1:10–1:30**: Open `ET-019`: scanned CV → OCR → exact page-verified quote. Then `ET-018`: malicious instructions on CV did not yield a supported qualification.
5. **1:30–1:50**: Human recruiter records Hold with a reason, opens the original PDF, exports an evidence pack.
6. **1:50–2:00**: Real Meta receipt: five genuine Muse calls, 21/21 page-verified quotes, median 5.94 seconds/CV in this **specific small test**. No score, no automatic hiring.

If live Muse is unavailable on the public service, explicitly use the *saved* authentic run as the model evidence and demonstrate the inbox UI in clearly labelled simulation mode; **never** present local simulation as a live model run.

## Required final deliverables

- [x] Public GitHub project exists and feature branch has recruiter inbox.
- [x] Source-linked code and frozen synthetic 20-CV fixture generator.
- [x] Real Muse integration exercised and authentic provider IDs captured on five fictional cases: [action log](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40888203979).
- [x] 143 Python / 13 JS, Chromium (desktop + mobile), Docker acceptance: [action log](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40888555124).
- [x] Judge-facing README: [JUDGE_GUIDE.md](JUDGE_GUIDE.md).
- [ ] **Judges' build:** choose **one commit** after final PR review, pin its SHA and share a working runnable/deployed version.
- [ ] **Public demo URL:** deploy the same commit, verify it without sign-in and without exposing the paid Muse API to unlimited anonymous usage. Current `https://evidencetrail.onrender.com` still deploys older main and cannot be claimed as the 20-CV build until verified.
- [ ] **Video:** record a tight 2-minute demo *from that same build*. Video length is a recommendation here; entrant must verify organizer's actual field limits.
- [ ] **Repository landing page:** point judges immediately to demo URL, 2-minute video, run instructions and genuine Muse receipts.
- [ ] **Participant portal:** confirm selected track, rules acceptance, eligibility, required fields, team representative, final submission.
- [ ] **Signed-out test:** video, GitHub, demo URL all accessible from an anonymous browser.
- [ ] **Submit before internal Nov 4 IST deadline**, save confirmation receipt. **Submitting a PR is not submitting to the event.**

## Freeze scope for the sprint

**IN:** criteria → 20 fictional applicants → verified evidence → human Hold/Advance → original PDF → standalone export; reliable replay when offline; fast loading; visibly clear Muse vs simulation; real authenticated receipt evidence.

**OUT until after Nov 4:** actual ATS integration, employer accounts, persistent database, auto-ranking/screening, interview scheduling, multi-tenant scalability, payment processing, 100k CV stress campaigns. None is required to show the hackathon's core AI innovation.

## Tight schedule (India time)

| Date | Goal and stop condition |
| --- | --- |
| Oct 29 | Lock feature list and judge narrative; commit current receipts/script |
| Oct 30 | One stable public demo build; anonymized fictional data; no exposed API key |
| Oct 31 | Reproduce the exact screen flow; fix only crashes or quote/consent defects |
| Nov 1 | Capture original 2-minute demonstration and a backup local recording |
| Nov 2 | Record a single updated cut if needed; complete judge README and receipt references |
| Nov 3 | Signed-out, clean-room demo from submission commit; freeze all feature work |
| Nov 4 | **Submit early India time**, save portal confirmation; no last-minute feature builds |

## Failure fallbacks

- **Muse credentials missing on demo host:** use saved real five-CV test receipts and label simulation truthfully; never fake a live request.
- **Cold start or demo site unavailable:** use locally recorded screen capture with actual provider receipt evidence and runnable GitHub instructions; don't claim a live hosted result.
- **One candidate fails:** leave it in the queue as Failed, show explicit error; don't silently drop, rerun or fabricate success.
- **Time running out:** submission video + GitHub + authentic recorded test are more valuable than a half-built ATS.

Official event: https://cerebralvalley.ai/e/meta-ai-developer-hackathon .
