# EvidenceTrail | Meta Global AI Developer Hackathon 2026

**Theme:** Build for Your World · **Project:** evidence-first hiring-document review  
**Short pitch:** *AI can interpret a CV. EvidenceTrail makes its evidence inspectable.*

EvidenceTrail helps recruiters compare job criteria against candidate CVs without treating an AI-generated answer as proof. **Meta Muse Spark 1.3** proposes criterion-level interpretations and source quotes. Independent Python checks then locate each quote in the supplied PDF/OCR text, preserve its page provenance, flag explicit scope or timeline discrepancies, and expose a reviewable audit. **A human recruiter makes every hiring decision.**

> Built as a submission project for the [Meta Global AI Developer Hackathon](https://cerebralvalley.ai/e/meta-ai-developer-hackathon). This repository is independently built; it is not an official Meta product or an endorsement. Track and submission status must be confirmed in the organizer's portal.

## Start here — judge walkthrough

| If you have… | Open… | What to look for |
| --- | --- | --- |
| **30 seconds** | [EvidenceTrail's judge guide](https://github.com/farhanjamal2002-blip/-evidencetrail/blob/release/evidencetrail-judge-rc1-oct30/JUDGE_GUIDE.md) | The problem, Meta's role, and our independent source-verification boundary |
| **2 minutes** | [Isolated judge-release recruiter inbox](https://evidencetrail-judge-rc1-2026.onrender.com/demo20) | A 20-applicant *fictional* inbox and saved genuine Muse replay; the public host is still on the older `bd9a0a1` build, so features in draft PR #28 may not appear |
| **5 minutes** | [Release-candidate PR #28](https://github.com/farhanjamal2002-blip/-evidencetrail/pull/28) | The newer, **unmerged** recruiter workflow and validation links |
| **Technical review** | [Original live Meta replay receipt](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40892660190) | Genuine Meta response IDs, the fixed fictional corpus, and citation-verification provenance |

**Important version note:** `main` is an earlier implementation. Cumulative PR #28 is the **unmerged judge release candidate**. Its current head `5c20bd2bdf620c00aa6f66938fc3ee09ca5f6674` passed current-head acceptance, browser smoke, and CI; the public host still reports `bd9a0a1e5a95da4dbeec3e995a9bd3089a984c6a`. The standalone redesign in draft PR #38 is not included. Do not present draft-only behavior as live; match the submitted video, repository commit, and hosted build before submission.

## The problem

A CV analysis can sound convincing without providing a dependable trail to the source document. A hiring reviewer needs to distinguish **what the document explicitly says**, **what is merely related**, **what conflicts**, and **what is not found**—and be able to reopen the evidence instead of trusting a polished AI summary.

## What we built

1. **Criteria-first intake:** compare a role's stated requirements to fictional candidate documents; the release-candidate workflow adds a recruiter-editable criteria checklist and received-order inbox.
2. **Meta-powered interpretation:** Muse Spark reads job requirements and CV claims and proposes structured, source-linked findings. Real analysis requires a server-side API key and explicit consent.
3. **Independent source check:** local extraction/OCR and deterministic page matching verify that a proposed quotation exists in the supplied CV; unsupported source pointers are excluded or flagged, not silently promoted.
4. **Inspect the trail:** see the original Muse claim, local evidence status, page-linked quotation, and verification/audit receipt. Timeline and role-scope checks help reveal specific contradictions without claiming to know real-world truth.
5. **Human review and handoff:** reviewers record decisions and follow-up needs. Exportable HTML/JSON/CSV material preserves the inspectable review; the available export formats depend on the branch.

## What to demonstrate

The fixed **20 fictional CV** replay includes regular PDFs, image-only scans/OCR cases, incompatible claims, related-but-not-direct evidence, and a prompt-injection fixture. The saved replay contains **20 authentic historical Muse responses for 80 role-criterion evaluations**. Its audit recorded **76 page-checked quote proposals and 71 individually retained citations**. **Zero quote proposals were rejected in that particular recording.** Separate calibration runs exercised rejection of invalid source quotations; these results must not be conflated. Source: [saved replay and checks](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40892660190), [judge guide](https://github.com/farhanjamal2002-blip/-evidencetrail/blob/release/evidencetrail-judge-rc1-oct30/JUDGE_GUIDE.md).

A saved Muse replay is **real recorded inference, not a fresh model call**. Mock mode is **local deterministic simulation, not Muse**. We keep both explicitly labeled so the demonstration can be explored without an API key or unintended spending.

## Technical distinction

| Muse Spark 1.3 does | EvidenceTrail's non-LLM code does |
| --- | --- |
| Interprets role language and candidate claims | Extracts page text and OCR data |
| Proposes criterion-level evidence and quotations | Matches quotations to document text/page and rejects invalid anchors |
| Supplies the original semantic label | Preserves raw labels alongside rule-based status changes and auditable exceptions |
| Helps surface passages worth reviewing | Builds inspectable source links, reviewer controls, and portable evidence exports |

The model interprets; the verifier checks citation presence; **the reviewer decides whether a passage is persuasive and what to do next**. A verified quotation proves only that text appears in the supplied document—not that the person has the claimed qualifications.

**Stack:** Python, FastAPI, PyMuPDF, Tesseract/pytesseract, Pillow, PDF.js, browser-side review tools, Meta Model API / Muse Spark 1.3. Production-grade ATS integrations, persistent multi-tenant accounts, live employer messaging, and independently measured real-world hiring accuracy are **not** claims of this hackathon demo.

## Trust and boundaries

- **No scores, ranking, automated rejection, or AI hiring decisions.** The human is accountable for review actions.
- **“Not found” ≠ unqualified.** It means verifiable evidence was not found in the provided material.
- **No factual credential verification.** Document anchoring is not background checking.
- **Consent for live analysis.** Keep Meta credentials server-side; do not put sensitive real CV data into the public fictional demo.
- **No invented benchmark.** Synthetic cases, provider receipts, model response counts, and local test results must retain their exact dates, denominators, and limitations.

## Try the earlier main-branch implementation locally

```bash
python -m pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`. The original main-branch sample preview is hand-authored; live Muse analysis requires explicit consent and server-side configuration. For the **newer recruiter workflow**, review the release-candidate branch and its own [README](https://github.com/farhanjamal2002-blip/-evidencetrail/blob/release/evidencetrail-judge-rc1-oct30/README.md) before running its different engine and settings.

## Submission checklist

The organizer's published deadline is **November 4, 2026 at 9:00 PM US Eastern** (November 5 at 7:30 AM IST). Before submitting, confirm the registered track, final deployment SHA, signed-out demo access, recorded video, authenticity receipts, waiver, and actual portal entry. Do not label this repository as “submitted,” “finalist,” or “winner” without confirmation.

**Project position:** *No black-box hiring verdicts. Just evidence, provenance, and human judgment.*
