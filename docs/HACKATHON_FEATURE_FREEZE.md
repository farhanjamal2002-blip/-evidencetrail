# Hackathon feature freeze

Status: proposed scope for the draft judge release. This is a planning artifact only; it does not change the live service or merge branches.

## Frozen core loop

1. Recruiter sets the job requirements and supplies CVs.
2. Local PDF extraction and OCR prepare page-labelled source text.
3. Muse Spark interprets each requirement against retrieved CV evidence.
4. Deterministic checks verify proposed quotations and pages; safeguards retain the raw model label, final evidence status, and reason for any change.
5. Recruiter inspects the original passage, records a human review or follow-up note, and exports an evidence pack.

The product never scores or ranks candidates and never makes the hiring decision.

## Flagship proof

Use the saved fictional M02 actor-swap replay. Show that the quote/page check stays true while the actor attribution changes the conclusion about the applicant. Keep the raw Muse result, final pipeline result, and authentic receipts visible. Label this as a saved replay on a small fictional set, not live inference or real-CV accuracy.

ET-018 is a short supporting demo of instruction-like text being treated as document content. It is not a second product workflow.

## Retain in the submission

- Muse Spark interpretation, local retrieval, exact quote/page verification, PDF highlights, and OCR where already supported.
- Received-order inbox, per-requirement evidence review, audit/receipt view, human notes or follow-up, and evidence export.
- Saved replay fallback; no public judge-page API call is required.

## One bounded pre-freeze experiment: Glimmer

Glimmer is not yet an implemented or measured release feature. Before UI freeze, compare a blinded Glimmer challenge against predeclared fictional controls: actor swap, direct applicant support, no evidence, and genuine contradiction. Give it only the requirement and source passages, without Spark's label. Preserve receipts and disagreements; never majority-vote.

Include Glimmer only if it catches the actor-attribution gap without regressing the controls, has authentic receipts, and fits the time and credit budget. Otherwise lock the Spark + deterministic-verifier loop and defer Glimmer. No broad sweep or selective retrying.

## Explicitly out of scope

- Scores, rankings, automatic rejection, or model-made recruiter decisions.
- ATS integration, multi-tenant production operations, or new workflow modules.
- Public live Muse calls; saved receipts are the judge fallback.
- Muse vision, SAM, Voice, Muse Image, or Wonder escalation without a tested need and result.
- Claims of real-world résumé accuracy, superiority over human review, or general model superiority.

## Lock criteria

- The complete recruiter path works with saved results without a key or fresh model call.
- M02 shows source existence separately from applicant attribution, with its receipt and caveat.
- Supported, not-found, and genuine conflict remain distinct; OCR pages get no fabricated word coordinates.
- Received order and human control remain intact.
- The Glimmer test either passes the gate above or is explicitly deferred.

After these criteria are met, allow only release-blocking correctness, accessibility, or demo-path fixes. Then freeze the UI, consolidate the repository, and review the cumulative release PR. Do not merge the stacked PR chain blindly.
