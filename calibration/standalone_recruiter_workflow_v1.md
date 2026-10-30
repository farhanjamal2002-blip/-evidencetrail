# EvidenceTrail standalone recruiter workflow — v1

> **Current run mode:** Local workflow simulation. New reviews use deterministic heuristics, make no model calls, and do not evaluate paraphrases or transferable experience. They are not hiring assessments. The Muse adapter is parked behind explicit opt-in flags. The saved Muse replay is historical model output and makes no new request.

## Product boundary

EvidenceTrail is a focused application-review tool for one job and up to five CVs. KUL/ATS integration, interview scheduling, outbound messages, persistent candidate records, and automated candidate ranking are outside this build. Recruiter notes and decisions stay in the browser until downloaded.

The familiar pieces—job criteria, candidate stages, review reasons, and interview handoff—are standard ATS workflow patterns. EvidenceTrail's product focus is the evidence-to-action chain: each requirement points to source material and verification state, and a Hold or Do not advance must link to the exact requirement(s) supporting that recruiter action. This is a focused product distinction, not a claim that other hiring products lack citations, criteria, or review controls.

## Product position against current ATS workflows

This is not a new ATS stage system. Ashby already documents AI review against per-job criteria, per-criterion status/reasoning, filtering, and optional criteria-based sorting. Greenhouse documents application-review advance/reject actions and configurable rejection reasons; Lever documents configurable stages and interview feedback workflows. We adopt those familiar controls because recruiters already know them.

EvidenceTrail's demo should show a narrower job: resolve a single CV claim into (a) what the role asks, (b) what the source page actually says, (c) whether the quote and page survived deterministic checks, (d) what remains unknown or conflicts, and (e) which exact criterion informed the recruiter's action. A missing citation means “not evidenced in this document,” not “candidate lacks the skill.” No match score, auto-reject, or candidate ranking is part of this workflow. This positions EvidenceTrail as an evidence-resolution layer that could sit inside KUL, rather than claiming it replaces KUL or that familiar ATS controls are original inventions.

## Recruiter path

### 1. Set one job and one checklist

1. Paste the job description.
2. Optionally run **Prepare role checklist**. This local preflight pulls numbered and bulleted job criteria, identifies priority only when the job post states it explicitly, and provides reviewer prompts. It makes no Muse request.
3. Edit the checklist: remove irrelevant or duplicate items and add anything the local extraction missed. If the job post is free-form, add the criteria manually.
4. Keep **Use this checklist for each CV** on for a fair side-by-side review. Turn it off only when the recruiter deliberately wants Muse to extract each CV's criteria independently. Independent extraction can yield different rows across candidates.

The same checklist is supported for one CV and for batches. The recruiter, not Muse, owns the final criteria. A changed job description invalidates the prepared checklist so stale criteria cannot be silently reused.

### 2. Add applications and consent

Upload one CV or up to five PDFs in the order the recruiter wants to review them. Searchable PDFs and scanned PDFs are accepted. For one CV only, a candidate statement can optionally be checked separately from job-fit evidence.

The recruiter confirms consent before analysis. In the current local mode, the job text and CVs are processed by local code and are not sent to a model. If the Muse adapter is deliberately enabled in server configuration, the app extracts page-aware CV text locally, then sends that text, the job text, and any optional candidate statement to Meta Model API only after consent. The original PDFs remain in the app's request flow for source verification and viewing; they are not attached to the Muse request. The app does not write them to a durable application store.

### 3. Muse proposes; local checks gate what appears as evidence

In the current local simulation, deterministic rules exercise extraction, retrieval, text/page checks, timeline arithmetic, reviewer actions, and exports. They do not make semantic judgments. When Muse is explicitly enabled, one structured Muse Spark request per CV returns requirement labels, candidate evidence, strength, gaps, follow-up questions, and timeline proposals together. EvidenceTrail checks every proposed quote against the original PDF page and runs deterministic overlap/duration checks locally. A failed quote is excluded from evidence and sent to human review. A timeline flag can request clarification; it cannot reject a candidate. The request includes the locally extracted page-labelled text, with detected text regions kept separate; it does not ask Muse to parse the original PDF again.

The browser sends one CV per request, runs up to the server's configured concurrency, and adds each completed candidate to the review as it finishes. Failed candidates can be retried individually without reprocessing successful candidates. The browser may reuse the same result for 15 minutes when the exact CV, job description, and checklist match; this cache is in-memory in the current tab and never sent to the server. No live Muse timing has yet been measured for this one-request path.

### 4. Review evidence in recruiter language

Each requirement uses one plain status:

- **Direct:** the CV describes the requested work or qualification.
- **Related:** a concrete adjacent task may transfer; the exact gap remains visible.
- **Not mentioned:** no usable passage was found in this CV; this says nothing about what the person can do.
- **Conflict to clarify:** explicit source details disagree or deterministic date math found an overlap.
- **Needs a closer look:** OCR, citation, or interpretation is too uncertain for a stronger claim.

Strength is separate: **Specific**, **Stated**, **Keyword only**, or **None**. Keyword-only language is not displayed as proof. Every displayed quote opens the original CV page. In a batch, candidate columns remain in upload order; the requirement matrix compares evidence but never calculates a candidate score or rank.

### 5. Make and record the human decision

The recruiter can mark a finding reviewed, add a note, and accept or reject related evidence for this job. An accepted transfer remains labelled **Related**; the override records the recruiter's judgment and does not change the original classification.

The candidate-level choices are:

- **Advance / invite:** prepares an editable invitation draft; it does not send or schedule it.
- **Hold:** requires a job-related reason.
- **Do not advance:** requires a job-related reason.

For Hold and Do not advance, the recruiter must also select at least one exact criterion from the shared checklist. The action stays a human decision; the link records which role need informed it and does not change the CV evidence label. Advance does not require a linked criterion.

No missing, conflicting, or unverified evidence automatically changes a candidate's status.

### 6. Export the hand-off

Download the per-candidate evidence pack or batch audit. It includes the rubric used, evidence statuses, verified and excluded citation counts, source pages, timeline flags, recruiter overrides, notes, decision, reason, and the exact criteria linked to Hold or Do not advance. Treat the exported CV images as candidate data and share them only with the intended reviewers.

## What this workflow saves

- Less repeated CV searching: the reviewer opens a cited page instead of hunting for the line again.
- Less inconsistency across a small shortlist: the same role checklist can be applied to every CV.
- Less unsupported model output in the review: failed quotes are blocked and date arithmetic is deterministic.
- Less recruiter rework: missing information and the next clarification question are shown together.

The current local simulation does not claim a measured reduction in review time. Validate recruiter time and missed-evidence rates before making a time-savings claim. Historical saved Muse results can be inspected in replay mode, but are not new live analysis.

## Handoff-by-handoff failure review

| Handoff | Failure that would damage trust or waste recruiter time | Current handling | Remaining limitation |
|---|---|---|---|
| Job text → checklist | A criterion is missed, duplicated, or silently changed. | The local checklist is editable, duplicate wording is flagged, and a shared batch rubric is aligned back to its locked wording. Missing or extra model entries are audited. | It only automatically detects listed items. Free-form prose and must-have/preferred meaning still need recruiter review. |
| PDF upload → extracted pages | A corrupt, oversized, scanned, or awkwardly laid-out CV causes a batch failure or scrambled evidence. | File/page caps, OCR, page-level text blocks, processing errors, per-CV failure isolation, upload-order results, and retry of only failed CVs. | OCR and reading order can still be wrong; reviewers must inspect scan-derived passages. Browser QA is not complete. |
| Muse proposal → evidence finding | A plausible but invented citation, unsupported source ID, generic keyword, or overconfident paraphrase appears as proof. | Muse is currently disabled for new analysis. In the Muse path, strict response validation, allowed-source checks, exact quote/page verification, and strength suppression gate the findings; failed citations are excluded. | The local demo path is heuristic and not semantic. Quote presence proves source text, not truth. Live model reliability still needs continued calibration. |
| Dates → timeline status | LLM date arithmetic double-counts years or misses incompatible timelines. | Supported date ranges are normalized locally; overlaps and tenure unions are computed deterministically; ambiguous date formats stay for review. | Real CVs often omit months or mix full-time, contract, and part-time work; the tool cannot infer those facts safely. |
| One CV → batch comparison | Different criteria make the matrix misleading, or a failed CV looks like a missing candidate skill. | Shared rubric mode applies the same requirement list; independent mode warns when rows differ; failed and unreturned cells are not labeled unsupported. | The matrix is upload-order only and intentionally provides no shortlist ranking. |
| Evidence → recruiter action | A generic reason is disconnected from the job need, or an incomplete decision is exported. | Hold and Do not advance require a reason plus one or more exact linked criteria; Advance clears those links; invalid choices are not recorded. The links appear in both exports. | Recruiter interpretation and consistency are not validated. This is not a legal review or fairness audit. |
| Decision → handoff | A manager receives a decision without its evidence, reason, or open question. | The report includes decision, timestamp, linked criteria, evidence statuses, citation audit, timeline flags, note, and interview-invitation draft. | Exports are manual downloads; there is no workflow sync, permissioning, or delivery confirmation. |
| Application review → rest of hiring | A draft message is mistaken for contact, or the tool appears to have completed interviews/offers. | Invite is editable and clearly marked unsent; interview scheduling and offer outcomes are outside this build. | No end-to-end hiring workflow integration exists yet. KUL integration is post-hackathon work. |

## Distinct product position

Do not pitch the familiar ATS pieces as inventions. Ashby already documents criterion-level evaluations, reasoning, and filters; Greenhouse documents advance/reject review with reasons; Lever documents pipelines and interview feedback. EvidenceTrail should be shown as a small evidence-resolution layer that makes the chain from role need to source text to deterministic checks to human action inspectable. Its design is intentionally non-ranking. The differentiator is the whole auditable path, not a badge, matrix, or a claim that no competitor has citations.

## Current limits

- Five PDFs maximum per run; no ATS import or durable candidate store.
- The default local mode makes no model requests and cannot assess semantic fit. If explicitly enabled, the current live path makes one Muse request per CV; quote/page verification and timeline arithmetic run locally. Batch results appear as each candidate completes, with bounded concurrency and a short-lived in-tab result cache. Muse's response time still depends on the API and CV size.
- Quote verification proves that text occurs on a cited page, not that the claim is true.
- Timeline checks only support date formats the local parser can safely interpret; uncertain formats stay for human review.
- This is a hackathon/pilot workflow, not a production hiring system with user access controls, retention policy enforcement, audit administration, or a validated bias program.
- Muse is disabled for new calls in the present local configuration. The saved live replay is useful for demo inspection but cannot satisfy a requirement to demonstrate a new live Meta call by itself.
- No recruiter time study, repeat-use evidence, paid-pilot evidence, or buyer interviews have established time saved, product-market fit, or commercial viability yet.
