# EvidenceTrail — Hackathon Judge Guide

**Meta Global AI Developer Hackathon · Build for Your World · Indie-track candidate**
**Submission cutoff:** November 4, 2026, 9:00 PM US Eastern = **November 5, 2026, 7:30 AM IST**. Aim to submit on November 4 IST. Track must match the entrant's selected registration.

## 20-second explanation

**EvidenceTrail turns a stack of CVs into source-checkable evidence against a recruiter-approved job checklist.** Meta Muse Spark 1.3 interprets the requirements and proposes cited passages. Our independent PDF verifier checks the exact quotations and pages, adds scope/timeline safeguards, and records both the original model label and the final evidence status. The recruiter reviews the evidence and makes the decision. **No score, ranking, automated hiring decision, or claim that a CV statement is true in the real world.**

## What judges should open

1. **Start with the demo recruiter inbox**: `/demo20` in a running build from branch `feat/recruiter-demo20-muse-inbox`. One fictional job, 4 editable criteria, 20 clearly fictional CVs, including 2 image-only PDFs, a contradictory CV and a prompt-injection CV. Nothing is falsely marked as AI-reviewed when first loaded.
2. **Confirm the role checklist** and inspect the applicants in upload/received order. Search for `ET-018` (injected prompt), `ET-019` (OCR scan), or `ET-005` (related-vs-direct negotiation) to show hard cases.
3. **Run a selected candidate only when Muse is configured, consented, and quota allows**, or open the existing clearly labeled **saved five-CV Muse replay** from the main workbench. A simulation is never presented as a live model result.
4. Open one requirement and its exact CV page citation; show how **verified quote ≠ proven job requirement**, and how a related quote cannot silently become Direct support.
5. Record a *human* Hold decision with a reason, then export the review/evidence. This is a demo browser-state record, not a durable database.

## Actual Meta Muse demonstration receipts — recorded October 29, 2026

These are **distinct controlled runs**, not arbitrary combined statistics:

- [20-applicant workflow: five live Muse test CVs](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40888203979): `ET-001`, `ET-005`, `ET-015`, `ET-018`, `ET-019`. **Five actual Meta API responses / five authentic provider receipts**. **21/21 proposed quotations page-verified**; 20/20 original model-label fields retained; zero verified-Related findings incorrectly accepted as exact requirement support. ET-019 required OCR on page 1. The malicious-instruction ET-018 did not receive a supported criterion. Median **5.94 seconds per CV** for this small, sequential fictional test; not a service-level promise.
- [Frozen five-CV replay with provider receipts](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40867761271): five real requests; 15/15 quotations verified. [Independent receipt audit](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40868066727) confirmed 5/5 authentic saved IDs. This earlier replay was **before** the later semantic hardening; never conflate it with the newer 20-applicant workflow.
- [Hardening comparison](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40876918794): matched five-fictional-CV sets at minimal and medium reasoning. Minimal: 6.3 seconds total; medium: 18.856 seconds. Both 9/10 raw expected labels, 10/10 after deterministic timeline checks, zero related-as-supported after safeguards. Small sample and variable provider latency: no general performance guarantee.

**Muse's actual role:** interpret job and CV meaning, propose requirement-level findings, evidence roles and exact quotes in a structured response. **Our code's role:** independently re-find those quotes in extracted/OCR PDF pages, verify page positions, run deterministic conflict and date safeguards, handle failed calls without fictional receipts, and generate the inspectable report.

## Inspect the implementation and tests

- `app.py`: `call_muse`, `verify_single_pass_proposals_locally`, `enforce_evidence_status_invariants`, `apply_explicit_scope_boundary_guard`, timeline audit and PDF previews.
- `demo20_workflow.py`: fixed fictional 20-applicant dataset, on-demand real PDFs and two image-only scans.
- `static/demo20.html`: recruiter-controlled criteria, received-order inbox, opt-in analysis, page/source evidence and manual decisions.
- `tests/test_demo20_workflow.py`, `tests/test_production_semantics.py`: fixture and fail-closed behavior.
- [Full acceptance build](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40888555124): **143 Python tests, 13 JavaScript tests**, Chromium desktop/mobile UI, invalid uploads and source checks, plus Docker image build. Both jobs passed.

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

**Official event:** https://cerebralvalley.ai/e/meta-ai-developer-hackathon . The organizer's accepted-participant rules and portal control the actual required submission fields, IP/eligibility terms and deadline.

## Suggested judge Q&A

**“Is this just an LLM wrapper?”** No. Muse does the semantic interpretation, while deterministic page anchoring, quote verification, timeline/scope guards, status-audit preservation, and export are separate code. The source check has blocked actual invented/wrong-page citations in prior calibration.

**“Do you rank applicants?”** No. The recruiter can filter by documented evidence and unresolved requirements, but every applicant remains visible and decisions are human-authored.

**“Have you tested live Meta Muse?”** Yes. The action runs above contain real Muse Spark 1.3 calls with authentic response IDs and saved synthetic-only receipts. The default public deployment is not asserted to have a valid Meta key.

**“Is it production-ready?”** Not as a multi-tenant commercial ATS. The hackathon build demonstrates and tests the document-evidence core; security, durable job intake and account isolation are later work.
