# EvidenceTrail — semantic reliability benchmark (October 29, 2026)

## What we actually ran

- **1,000 synthetic, controlled policy cases**: 10 job domains × 10 predefined evidence/error families × 10 wording variations, with a reference status authored before making any prediction. The code exercises production `enforce_evidence_status_invariants` and `clarify_verified_findings`, applied to assumed **source-grounded** synthetic passages.
- The model-like initial labels are **injected**, not outputs from Meta. The 1,000-case run is a deterministic safeguard test and costs **0 Meta API calls**. [Passing benchmark](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40921386824).
- Controlled correctness: **500/1,000 initial labels** match our predeclared reference and **900/1,000 final labels** match after guards. This is **not** an estimate of real Muse, human-reviewed semantic accuracy, accuracy on unseen real applications, or commercial productivity.
- **100/1,000** deliberately missed-direct-qualification cases remain missed: the verifier is conservative and cannot recover evidence never recognized by the model. This is an identified false-negative failure mode, not a test we silently excluded.
- Local safeguard running time in this CI test: median **0.015 ms**, p95 **0.020 ms** per single-criterion case, excluding PDF extraction, model inference, network, browser and database. Not an end-to-end latency benchmark.

## Separate real model probe

[Live Meta probe](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40921846457): 10 synthetic one-criterion CV analyses, one live Muse call per CV, 4 preselected separate blind adjudicator calls against the same independent fictional reference. New model calls consume provider credits; the workflow caps the number of calls, prohibits retries, and never sends real candidate information. The second judge is **the same model family** and is not an independent human expert. Do not combine its agreements with raw/verifier accuracy.

## Scientific guardrails and next evaluation

1. **Keep explicit, locked, human-validated reference labels.** Do not let the same model generate a CV, decide the reference truth and then validate itself.
2. **Separate source-grounding from semantic interpretation.** A verified PDF quote proves the passage exists, not that a candidate possesses a skill.
3. **Report all confusion-matrix cells, not only improvements.** False negative, false positive, misused contradiction, exact-vs-related ambiguity, ungrounded quotes, OCR, date mistakes, conflicting claims, incomplete CVs and injection must be tracked individually.
4. **Hold out entire job domains and CV writing styles** from prompt adjustments. Ten repetitive templates per category are useful for rule coverage but not a substitute for new unseen documents.
5. **Measure reviewer impact** on fictional CVs with independent annotators: review minutes, evidence misses, false confirmations, uncertainty handling, and disagreement resolution. Do not infer recruiter productivity savings from incumbent UI conventions.
6. **A/B experiments**: baseline Muse prompt vs updated prompt, each with the *same* unseen CV corpus and fixed rubric. Source-verifier rules and evidence data should be identical across arms. Log genuine provider IDs, tokens, errors, median and p95 end-to-end latency, and credits used.
7. **Optimization policy**: improve prompt examples only after measurable error clusters; improve retrieval and PDF extraction deterministically; batch and cache identical CV+JD+rubric hashes; use a second model pass only for cases whose expected error reduction justifies incremental cost.
8. **Safety**: this is a support tool for a human reviewer, not applicant ranking or automated hiring. Any use involving actual applicants requires lawful processing, consent/privacy review, safeguards against unfair exclusion and separate validation.

## What we have NOT proved

- Muse's overall semantic accuracy is 90% (the 90% is controlled rule-guard behavior).
- Muse and its own second call constitute independent external evaluation.
- The 1,000 cases are 1,000 genuinely different CVs or realistic recruiting interactions.
- Existing workflow patterns establish commercial savings, labor displacement, fairness, or market superiority.
- The hosted Meta Muse Spark 1.3 model is currently user-fine-tunable through Meta Model API. Model API documentation centers on inference; Meta separately documents post-training for **open-weight** Muse Spark Open and Muse Glimmer. That is a different infrastructure/cost decision.

This evaluation branch intentionally does **not** deploy anything to public Render, merge to `main`, rewrite historical Meta receipts, or modify hiring decisions.
