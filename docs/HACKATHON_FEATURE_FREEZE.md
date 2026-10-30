# Hackathon feature freeze

**Status: FROZEN — October 30, 2026.** This locks product scope for the draft judge release. It changes no live service and merges no branches.

## Frozen product loop

1. Recruiter sets the job requirements and supplies CVs.
2. Local PDF extraction and OCR prepare page-labelled source text.
3. Muse Spark interprets each requirement against retrieved CV evidence.
4. Deterministic checks verify proposed quotations and pages; safeguards preserve the raw model label, final evidence status, and reason for any change.
5. Recruiter inspects the source, records a human review or follow-up note, and exports the evidence pack.

The product never scores or ranks candidates and never makes the hiring decision.

## Flagship proof

Use the saved fictional M02 actor-swap replay. Show that the quote/page check stays true while the actor attribution changes whether the passage supports the applicant. Keep the raw Muse result, final pipeline result, and authentic receipts visible. Label it as a saved replay on a small fictional set, not live inference or real-CV accuracy.

Use ET-018 only as a short supporting demo of instruction-like text treated as document content.

## Included in the freeze

- Muse Spark interpretation, local retrieval, exact quote/page verification, PDF highlights, and OCR where already supported.
- Received-order inbox, per-requirement evidence review, raw-to-final audit, and provider receipts.
- Human-controlled review/follow-up notes and evidence export.
- Saved replay fallback; the public judge path does not require a fresh model call.

## Explicitly deferred

- Glimmer or any other second-model challenge. The potential benefit is not yet demonstrated strongly enough to justify added latency, setup, and failure modes.
- Muse vision, SAM, Voice, Muse Image, Wonder escalation, or a new tool-calling loop.
- New workflow modules, ATS integration, or multi-tenant production operations. Existing interview-prep and self-attested-reply paths may remain in the repository but stay off the primary judge path.
- Public live Muse calls, scores, rankings, automatic rejection, or model-made hiring decisions.
- Claims of real-world résumé accuracy, superiority over human review, or general model superiority.

## Feature acceptance boundary

The feature set is locked. Permit only release-blocking correctness, accessibility, or judge-path reliability fixes; no new capabilities or model routing. The UI should be frozen against this exact loop. After UI freeze, consolidate the repository into one reviewed release path and resolve the cumulative PR's mergeability; do not merge the stacked PR chain blindly.
