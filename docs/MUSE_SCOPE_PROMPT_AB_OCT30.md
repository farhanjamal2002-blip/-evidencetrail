# EvidenceTrail Muse semantic calibration — paired A/B on 20 synthetic CVs

## The decision

**Candidate change:** tighten the *first-pass Muse system prompt* so that `conflicting` means two incompatible claims **inside the CV**, not that the job asks for something the applicant has not documented. Retains one model pass per CV, same source verifier, same preserved raw model status, no extra calls when browsing saved results, and no candidate scores.

## Exact paired benchmark (October 29–30, 2026)

The evaluator used **the same 20 predefined two-page fictional PDF documents**, same four approved requirements per PDF (80 criterion outcomes), same API/model and verification code, and the same expected labels authored before either run. Two separate sets of 20 real Muse requests; provider receipts and detailed confusion matrices are retained in GitHub Actions artifacts.

| Metric | Current baseline prompt | Revised prompt |
| --- | ---: | ---: |
| Raw Muse status agreement with synthetic references | **45 / 80** | **80 / 80** |
| EvidenceTrail final status agreement | **68 / 80** | **80 / 80** |
| Correct direct-support status | 30 / 30 | 30 / 30 |
| Correct real CV-internal contradictions | 5 / 5 | 5 / 5 |
| Correct missing/limited scope references | 33 / 45 | 45 / 45 |
| Falsely supported criteria | 0 | 0 |
| Missed directly supported criteria | 0 | 0 |
| Median one-CV end-to-end analysis | **4.00 s** | **4.47 s** |
| Real Meta requests | 20 | 20 |

### Primary references

- [Original source-locked benchmark](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40924546755)
- [Revised-prompt same-source benchmark](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40932201249)
- [Full local, Docker and Chromium regression gate](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40932879541)

## Why the change helped

The old prompt allowed a sentence such as a coordinator *preparing notes* while a senior manager *negotiated the actual supplier agreement* to be labeled `conflicting`, even though no two CV passages were actually logically incompatible. Multiple page-verified quotes can still be **two statements about different tasks**. Our local verifier demoted many such errors, but twelve remained.

The revised prompt uses explicit positive and negative decision boundaries:

- `supported`: the CV directly documents personal work at the required scope.
- `not_found`: the requirement is missing, only adjacent work is documented, or an explicit role boundary indicates that personal responsibility is unproven.
- `conflicting`: *two incompatible claims in the CV itself* about personal responsibility to be clarified with the applicant.
- Cited quotations must be exact and page-grounded; no automatic rejection or rank.

## Limits and integrity

1. **This is a single A/B sample, not a statistically independent cross-validation.** The prompt improvement was *developed after inspecting the baseline errors on these same 20 CVs*. Therefore the better score is on a **development set**, not untouched holdout evidence. It is encouraging but cannot establish generalization to a larger universe.
2. **The gold labels are hand-authored fictional references**, not blinded human recruiter annotations and not actual candidate performance facts. Some synthetic wording is very explicit.
3. **Prompt policy examples resemble part of the test data.** This was an intentionally targeted fix. Before claiming accuracy improvement for general recruiting, evaluate a second, unseen corpus with different roles, writing styles and contradiction patterns, and include source citations and adverse cases.
4. The median latency rose by **0.47 seconds** in this small sample, likely a trade-off for clearer label decisions. This is not a guaranteed cost or performance increase.
5. **Raw model and local verifier are separately measured.** Do not claim 80/80 is due solely to the deterministic layer. In fact the revised raw Muse outputs matched all 80 on this sample; the verification layer preserved their status while continuing to check source grounding.
6. **No fine-tuning was performed.** This is a versioned prompt change on hosted Muse Spark 1.3, not model-weight training.

## Ship gate

Keep the public replay immutable and keep the new prompt isolated until the full Python/JS/Chromium/Docker gate passes. Then merge into the hackathon demo branch. The public free demo uses the recorded real responses and remains **mock-only for new anonymous uploads**.

Next upgrade: test genuinely new cases and improve recall under messy, indirect wording, without more false positives.