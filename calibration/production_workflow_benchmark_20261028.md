# Production workflow benchmark and gap map — 28 Oct 2026

## Direction

Build EvidenceTrail as an evidence-review layer inside KUL’s candidate workflow, not as a second ATS. Copy the mature workflow primitives recruiters already understand: one role rubric, an application pipeline, a next-action queue, reasoned dispositions, a candidate activity history, and reporting. Upgrade the review step with EvidenceTrail’s source-page proof, failed-citation blocking, uncertainty handling, transfer explanations, and deterministic date checks.

The current EvidenceTrail repo is a useful evidence-review prototype. It is not yet the production hiring system: there is no durable candidate store, ATS connection, authenticated user/role model, or stage history. Recruiter decisions stay in the current browser session until export; batches are capped at five and processed sequentially.

## What to learn from competitors

| Product | Workflow pattern worth adopting | EvidenceTrail’s upgrade |
|---|---|---|
| Greenhouse | Job-specific review stages; one-click advance; rejection reasons; candidate email workflow; stage pipeline showing next action, last activity, and time in stage. | Attach the selected reason to the exact requirement/evidence record and retain the reviewer action in a durable audit history. |
| Ashby | Define criteria on the job, review candidates in bulk, move to next/oldest/newest, add feedback, require a rejection reason, leave unclear results unknown, and override AI output. | Keep the candidate unranked; make each criterion open the actual PDF page; block a citation that fails local page verification; explain any related transfer and its unproven parts. |
| Lever | Treat candidate progress as an activity story; use explicit archive reasons; filter by last interaction and next step. | Include evidence verification, recruiter overrides, rubric version, and AI run details as distinct events in that history. |
| Workable | Keep applications, profile, evaluation, and stage selection together in the pipeline. | Make the evidence panel part of the candidate application rather than asking recruiters to copy a CV into a detached tool. |
| Frappe HR / Odoo | Open-source reference for applicant records, configurable stages, refusal reasons, interview/offer records, and progression to an employee record. | Reuse data/workflow concepts and schemas if useful; keep KUL’s existing stack and Muse/document pipeline instead of rebuilding an ERP/ATS. |

None of these references proves EvidenceTrail is better. Ashby already markets citations, unknown states, reviewer overrides, and bulk review. Greenhouse and Ashby already support human advance/reject decisions. The difference we can test is the strength of local page/quote verification and how well related evidence is presented for messy documents.

## Current workflow compared with the production pattern

| Step | Current EvidenceTrail | Gap for production use | Priority |
|---|---|---|---|
| Job setup | Paste a JD; local preflight extracts numbered/bulleted lines. | No recruiter-edited, shared rubric locked for all applications and tracked by version. | P0 |
| Application intake | Recruiter uploads PDFs manually; at most five per batch. | Candidate already exists in KUL/ATS; no connector, webhook, or persistent application record. | P0 |
| Evidence analysis | Muse plus local retrieval, quote/page checks, OCR, and timeline math. | Sequential per-CV requests and repeated job context; no work queue, retry/resume, or role-level metrics. | P1 after pilot |
| Recruiter review | Requirement matrix, source viewer, related-evidence decision, notes, candidate Advance/Hold/Do not advance. | Actions are browser-session state; no structured disposition reason, assigned owner, due date, or activity timeline. | P0 |
| Candidate communication | Editable interview-invitation draft; nothing is sent or scheduled. | No rejection-draft workflow or communication history. | P1 |
| Hiring outcome | Shortlist JSON/HTML export. | No stages/outcomes such as contacted, interview requested, offer, hired, declined, or withdrawn. | P1; use KUL’s existing lifecycle |
| Learning and ROI | Saved semantic calibration artifacts. | No production task timing, override rates, stage conversion, repeat usage, or willingness-to-pay evidence. | P0 for product-market proof |
| Trust and governance | Consent notice; no persistent CV storage; Standard Muse mode; no automated ranking. | No auth/permissions, tenant controls, configured retention/deletion, candidate notice workflow, or independent bias audit. | Required before real production deployment |

## Recommended recruiter workflow

1. **Open a requisition.** The recruiter defines or pastes the role requirements. Muse may draft normalized criteria once; the recruiter edits must-have/preferred labels, removes irrelevant requirements, and locks a rubric version before reviewing candidates. Preserve the source sentence for each criterion.
2. **Receive applications into the existing pipeline.** KUL or the current ATS remains the source of truth for candidate identity, CV, job, owner, and stage. EvidenceTrail receives the application record through an in-app call or integration; recruiters should not download and re-upload the same CV.
3. **Run a first-pass review queue.** Apply explicit application-form constraints and standard ATS filters first. Queue candidates in the existing stage/order. Show “Needs recruiter action,” “Waiting on candidate,” or “Ready for decision,” along with last activity and time in stage. This improves flow without a fit score or AI ranking.
4. **Review evidence by requirement.** Muse interprets the role criteria against the CV. Local code verifies each cited quote/page and checks supported timeline arithmetic. Show direct evidence, related evidence with the remaining gap, not shown, conflict, or needs review. Every cell opens the source page; a rejected quote is visible in the audit, not presented as evidence.
5. **Record one human disposition.** Advance, Hold, or Reject. Hold and Reject require a job-related reason. Advance opens an editable interview-invitation draft. Reject can prepare a clear message draft. Sending, scheduling, and interview evaluation stay in the existing KUL workflow for the first release.
6. **Keep a candidate activity history.** Record application received, rubric version, model run, verified/rejected citations, recruiter override, status change, reason, note, and communication draft/sent event with user and timestamp. Persist decision metadata and source fingerprints; set and enforce a CV retention/deletion policy in the host product.
7. **Measure the workflow.** Track time to first review and decision, time in stage, reviewer overrides, quote rejection rate, missing/ambiguous findings, stage conversion, and repeat use. This is how we prove that EvidenceTrail saves time without silently increasing missed candidates.

## Build order tied to commercial proof

### P0 — prove the workflow and make one role consistent

- Create a recruiter-approved role rubric once and reuse it for every applicant on the requisition.
- Feed an actual KUL application into the review panel so CV intake does not add a second workflow.
- Persist the decision, reason, notes, rubric version, evidence audit, and timestamps in KUL’s existing candidate/application records.
- Keep the application decision human-owned and unranked.
- Run a small internal pilot on one real, authorized requisition. Compare current review with assisted review on the same candidate volume; measure time, critical misses, overrides, and whether the recruiter uses it again.

### P1 — finish the recruiter loop once the first pilot saves time

- Add the pipeline/action queue, last activity, time-in-stage, and simple reminders.
- Add structured hold/rejection reasons and editable candidate-message drafts.
- Keep offer/hire/decline/withdrawal in KUL’s existing lifecycle, so EvidenceTrail does not become a new ATS.
- Increase batch throughput with an asynchronous job queue only after the pilot shows recruiters want to process more candidates.

### P2 — scale after repeat use and commercial intent

- Add other ATS connectors and team permissions.
- Add reporting by job, stage, and recruiter, including evidence overrides and time saved.
- Offer configurable retention, applicant disclosures, audit export, and organization-level policies.
- Choose a paid plan only after a buyer commits to a pilot or budget. Price against measured recruiter hours saved and workflow value, not the token bill.

## Product-market and commercial tests

The initial target is a recruiter or recruiting team already receiving applications through KUL/another ATS and spending meaningful effort comparing a small shortlist where CV wording or structure makes evidence difficult to inspect. A generic “AI resume screener” is crowded, and the current five-file standalone flow is poorly suited to first-pass review of hundreds of applicants.

For an initial pilot, compare the same role and similar candidate volume in the existing process and EvidenceTrail. Record median review minutes, number of CV/source-page reopens, time to a hiring-manager handoff, critical evidence errors, recruiter overrides, and repeat use on the next requisition. A reasonable early gate is at least 25% lower median review time with no increase in critical misses; this is a proposed threshold, not a result. Commercial proof requires a concrete buyer action such as a paid pilot, a budgeted deployment, or repeat usage tied to a purchasing decision.

At the last saved five-CV calibration’s token profile, Muse costs roughly $0.048 per CV at current Standard prices. This is an estimate on fictional documents, not an invoice. Inference cost is unlikely to decide viability before integration, adoption, support, and governance do.

## Sources

- Greenhouse, [Visual Candidate Pipeline](https://support.greenhouse.io/hc/en-us/articles/4874727408795-Visual-Candidate-Pipeline), [Application Review stage](https://support.greenhouse.io/hc/en-us/articles/4401963991707-Application-review-stage), and [scorecard FAQ](https://support.greenhouse.io/hc/en-us/articles/15756249510427-Scorecards-FAQ).
- Ashby, [Application Review](https://docs.ashbyhq.com/application-review) and [AI-Assisted Application Review](https://www.ashbyhq.com/product-updates/ai-assisted-application-review).
- Lever, [Filtering candidates by last interaction](https://help.lever.co/s/article/Filtering-candidates-by-last-interaction) and [Operating the Archive](https://help.lever.co/s/article/Operating-the-Archive).
- Workable, [Candidate profile in pipeline view](https://help.workable.com/hc/en-us/articles/115012857047-Candidate-profile-in-pipeline-view-overview).
- Frappe HR, [Job Applicant](https://docs.frappe.io/hr/job-applicant), [Interview](https://docs.frappe.io/hr/interview), and [Job Offer](https://docs.frappe.io/hr/job-offer).
- Odoo, [Refuse applicants](https://www.odoo.com/documentation/19.0/applications/hr/recruitment/refuse_applicant.html) and [Recruitment](https://www.odoo.com/documentation/17.0/applications/hr/recruitment.html).
- Meta, [Model API pricing and rate limits](https://dev.meta.ai/docs/pricing-rate-limits).
