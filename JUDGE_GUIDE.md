# EvidenceTrail — Hackathon Judge Guide

**Meta Global AI Developer Hackathon · Build for Your World · Indie-track candidate**
**Submission cutoff:** November 4, 2026, 9:00 PM US Eastern = **November 5, 2026, 7:30 AM IST**. Aim to submit on November 4 IST. Track must match the entrant's selected registration.

## 20-second explanation

**EvidenceTrail turns a stack of CVs into source-checkable evidence against a recruiter-approved job checklist.** Meta Muse Spark 1.3 interprets the requirements and proposes cited passages. Our independent PDF verifier checks the exact quotations and pages, adds scope/timeline safeguards, and records both the original model label and the final evidence status. The recruiter reviews the evidence and makes the decision. **No score, ranking, automated hiring decision, or claim that a CV statement is true in the real world.**

## What judges should open

1. **Start with the [isolated judge-release recruiter inbox](https://evidencetrail-judge-rc1-2026.onrender.com/demo20)** (version fingerprint at [`/build-info`](https://evidencetrail-judge-rc1-2026.onrender.com/build-info); check matching release commit before judging). One fictional job, 4 editable criteria, 20 clearly fictional CVs, including 2 image-only PDFs, a contradictory CV and a prompt-injection CV. Clicking the replay control loads the genuine 20-CV recorded Muse results, distinctly labeled as a **saved replay**, not new inference.
2. **Open Replay benchmark.** Compare the M02 baseline and actor swap. Point to the separate **Quote on the page?** and **Does it credit the applicant?** checks, then the struck-through raw Muse label, final evidence status, and one-line reason. Keep the caveat visible: the 12-pair set is small and fictional; 25/25 quote checks is the full-replay count, not an M02 score.

3. **Inspect the saved M02 receipts.** Open the public case audit and workflow records. The replay uses stored provider responses and makes no new Muse call.

4. **Use the dark ET-018 next card.** Open ET-018 in the inbox and choose **View outlined source instruction**. Both instruction-like lines are outlined from exact PyMuPDF geometry and labeled **Treated as content**. The text is part of the fictional CV and is not followed by the app.

5. **Show the independent reviewer panel.** It has **Not reviewed**, **Reviewed**, and **Follow-up needed**, with a note field. This records the recruiter's review state; it does not modify the evidence label. The record stays in browser memory unless exported.

6. If there is time, open **ET-019** to show the scanned-PDF page-only OCR path. EvidenceTrail does not invent word-level coordinates for an image-only source.



**Release provenance — current draft snapshot:** PR #28 head `5c20bd2bdf620c00aa6f66938fc3ee09ca5f6674` passed [20-CV mock acceptance 41080741919](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/41080741919), [judge-browser smoke 41080742057](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/41080742057), and [CI 41080742170](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/41080742170). PR #28 remains draft and is not deployed. [Public parity run 41080729614](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/41080729614) reports the public host is still on SHA `bd9a0a1e5a95da4dbeec3e995a9bd3089a984c6a`. Check `/build-info` against the reviewed release SHA before directing judges to the hosted build. The separate eight-screen prototype in [draft PR #38](https://github.com/farhanjamal2002-blip/-evidencetrail/pull/38) is not part of PR #28.

## Source quote geometry benchmark — October 29, 2026

The [zero-API PDF geometry benchmark](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40914988326) checked every retained quote against the **20 original fictional PDF files**:

- **62/71** retained verified citations mapped to precise PyMuPDF source rectangles, all via direct \`search_for()\`; normalized word fallback was implemented but not needed on this dataset.
- **9/71** citation texts belong to scanned documents and correctly display the verified **PDF page without fabricated word boxes**.
- **0/71** retained citations remain unlocated or invalid.
- Historical source verification was **76**, but five verified quotations were not persisted individually in the saved replay: ET-010 (one) and ET-017 (four). We cannot create geometry for unretained text and do **not** claim 76 exact highlights.
- Raw Meta receipts, original quote text, per-requirement status and any human decisions are preserved, with **zero new Meta model calls** to browse geometry.
- [Full quote-snap acceptance](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40915423957): backend Python, source geometry, JS, Docker and real Chromium desktop/mobile PDF-click flows passed. A native **Open original PDF** link remains available.

## Actual Meta Muse demonstration receipts — recorded October 29, 2026

These are **distinct controlled runs**, not arbitrary combined statistics:

- [**One-time recorded 20-CV Muse replay**](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40892660190): **20/20 genuine Muse responses**, all 20 with authentic Meta response IDs, **76 locally verified PDF quotations**, original Muse labels preserved for **80/80 criteria**, and no missing recordings. The exact source PDF and job checklist hashes are verified before the saved data is published. Viewing the public replay uses ZERO new model calls. A first recording attempt was rejected because randomly generated PDF trailer IDs made source hashes unstable; the generator was corrected and the full replay re-run before publication. This is a fictional QA dataset, not a general accuracy/latency claim.


- [20-applicant workflow: five live Muse test CVs](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40888203979): `ET-001`, `ET-005`, `ET-015`, `ET-018`, `ET-019`. **Five actual Meta API responses / five authentic provider receipts**. **21/21 proposed quotations page-verified**; 20/20 original model-label fields retained; zero verified-Related findings incorrectly accepted as exact requirement support. ET-019 required OCR on page 1. The malicious-instruction ET-018 did not receive a supported criterion. Median **5.94 seconds per CV** for this small, sequential fictional test; not a service-level promise.
- [Frozen five-CV replay with provider receipts](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40867761271): five real requests; 15/15 quotations verified. [Independent receipt audit](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40868066727) confirmed 5/5 authentic saved IDs. This earlier replay was **before** the later semantic hardening; never conflate it with the newer 20-applicant workflow.
- [Hardening comparison](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40876918794): matched five-fictional-CV sets at minimal and medium reasoning. Minimal: 6.3 seconds total; medium: 18.856 seconds. Both 9/10 raw expected labels, 10/10 after deterministic timeline checks, zero related-as-supported after safeguards. Small sample and variable provider latency: no general performance guarantee.

**Muse's actual role:** interpret job and CV meaning, propose requirement-level findings, evidence roles and exact quotes in a structured response. **Our code's role:** independently re-find those quotes in extracted/OCR PDF pages, verify page positions, run deterministic conflict and date safeguards, handle failed calls without fictional receipts, and generate the inspectable report.

## Inspect the implementation and tests

- `app.py`: `call_muse`, `verify_single_pass_proposals_locally`, `enforce_evidence_status_invariants`, `apply_explicit_scope_boundary_guard`, timeline audit and PDF previews.
- `demo20_workflow.py`: fixed fictional 20-applicant dataset, on-demand deterministically fingerprinted PDFs, two image-only scans, and an authenticity-checking saved Muse replay endpoint.
- `data/demo20_muse_replay.json`: the genuine 20-fictional-applicant source-verified Muse outputs and provider receipts. It is NOT a fabricated or live response.
- `static/demo20.html`: recruiter-controlled criteria, received-order inbox, opt-in analysis, page/source evidence and manual decisions.
- `tests/test_demo20_workflow.py`, `tests/test_production_semantics.py`: fixture and fail-closed behavior.
- [Full 20-CV replay acceptance](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40893215283) adds genuine-receipt/fixture hash checks and a browser proof that **opening all 20 saved results sends no new Muse requests**.
- [Previous full acceptance build](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40888555124): **143 Python tests, 13 JavaScript tests**, Chromium desktop/mobile UI, invalid uploads and source checks, plus Docker image build. Both jobs passed.

## Run locally (without Meta credits)

```bash
python -m pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/demo20`. Default mode is clearly labeled **mock**; all twenty fictional CVs and most UI actions work without any Meta key. Mock is only a deterministic demonstration and must not be described as Muse analysis.

For a live Muse demonstration, place `MODEL_API_KEY` on the **server only**, set `EVIDENCETRAIL_PROVIDER=muse` and `EVIDENCETRAIL_ENABLE_MUSE=true`, then **explicitly consent** and click a selected fictional candidate. Never commit credentials, never send real CVs to a demo provider without permission, and do not expose an unauthenticated public API with unlimited paid analysis.

## Boundaries and disclosure

This hackathon demo **does not** yet offer real ATS webhooks, durable queues for 20 incoming CVs, employer authentication, multi-tenancy, persistent review records, interviewer scheduling, or a production hiring deployment. The existing route processes at most five uploads per batch; the 20-applicant inbox can send a small explicit subset to that route. It does not automatically sort applicants by worth or recommend a hiring decision.

**“Not found” means not supported by the supplied document; it is not proof that a person lacks a qualification.** Real employment uses require privacy, legal and fairness evaluation beyond this demo.

**Hosting:** The isolated free [judge-release demo](https://evidencetrail-judge-rc1-2026.onrender.com/demo20) intentionally disables paid Muse to prevent anonymous API use. The recorded real Muse runs above provide model provenance, while `/build-info` proves the exact current deployment SHA when available. The older `evidencetrail.onrender.com` and `evidencetrail-meta-hackathon-demo.onrender.com` are separate deployments. Free hosting may cold-start.

**Official event:** https://cerebralvalley.ai/e/meta-ai-developer-hackathon . The organizer's accepted-participant rules and portal control the actual required submission fields, IP/eligibility terms and deadline.

## Suggested judge Q&A

**“Is this just an LLM wrapper?”** No. Muse does the semantic interpretation, while deterministic page anchoring, quote verification, timeline/scope guards, status-audit preservation, and export are separate code. The source check has blocked actual invented/wrong-page citations in prior calibration.

**“Do you rank applicants?”** No. The recruiter can filter by documented evidence and unresolved requirements, but every applicant remains visible and decisions are human-authored.

**“Have you tested live Meta Muse?”** Yes. The action runs above contain real Muse Spark 1.3 calls with authentic response IDs and saved synthetic-only receipts. The default public deployment is not asserted to have a valid Meta key.

**“Is it production-ready?”** Not as a multi-tenant commercial ATS. The hackathon build demonstrates and tests the document-evidence core; security, durable job intake and account isolation are later work.
