# Finalist evidence audit — genuine Meta Muse ownership and native-vision tests

**Date:** October 30, 2026. **Scope:** fictional predeclared CVs only. This is a tiny calibration slice, **not a population accuracy, fairness, or performance estimate**. No applicant ranking or decisions were performed. The public judge release remains frozen and mock-only.

## A. Five controlled, genuine Meta Muse Spark 1.3 analyses

[Authentic Actions run with retained provider receipts and original audits](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/41016897397)

| Frozen CV ID | Requirement / adversarial pattern | Authored reference | Raw Muse | Final EvidenceTrail | Page-checked quotes | Result |
|---|---|---|---|---|---|---|
| U02 | Applicant prepared supplier comparisons; director performed negotiation | not_found | conflicting | not_found | 1/1 | source-grounded scope correction |
| U03 | Applicant directly claimed negotiations then explicitly denied it | conflicting | conflicting | conflicting | 2/2 | genuine conflict preserved |
| U05 | Applicant viewed Kubernetes dashboards; platform team administered cluster | not_found | conflicting | not_found | 1/1 | scope correction |
| U07 | Built Airflow scheduled pipelines described as DAG authoring | supported | supported | supported | 1/1 | meaningful paraphrase accepted |
| U23 | Image-only synthetic vaccination outreach CV | supported | supported | supported | 1/1 | local OCR preserved source |

- **Authentic provider responses:** 5/5 with real response IDs.
- **Raw labels matching author-built reference:** 3/5.
- **Final labels matching author-built reference:** 5/5.
- **Page-verified source quotations:** 6/6.
- **Scanned OCR cases:** 1/1.
- **Retries:** zero. No claims about statistical confidence or independent recruiter annotation.
- **Latencies (single observed runs):** U02 2.62 s; U03 3.79 s; U05 3.89 s; U07 1.69 s; U23 2.59 s. These are not service-level promises.
- Cached tokens were observed on some requests; **actual dollar cost was not independently reconciled**.

This shows that the existing pipeline can **resolve one-sided scope limitations without erasing genuine two-sided contradictions**. Do not call the 5/5 a general accuracy result.

## B. Genuine native Meta image-input test: U23

[Authentic single-call Actions run and retained provider receipt](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/41017119841)

The **same fictional U23 image-only source** was sent with explicit synthetic-data consent, this time with **both local OCR text and one bounded source-page image** in the Meta Muse chat-completions input. The underlying U23 author reference and CV generator did not change.

| Variable | OCR text-only U23 (run A) | OCR + native Muse vision U23 (run B) |
|---|---|---|
| Meta returned genuine response ID | Yes | Yes |
| Optional vision flag | Disabled | Explicitly enabled |
| Scanned PDF page locally OCR'ed | Page 1 | Page 1 |
| Native image blocks sent to Muse | 0 | 1 |
| Raw Muse finding | supported | supported |
| Quote proposals verified locally | 1/1 | **0/1** |
| Final evidence finding | supported | **not_found** |
| Input tokens | 2,333 | 3,710 |
| Output tokens | 380 | 438 |
| End-to-end request time | 2.59 s | 3.14 s |

**Interpretation:** The Meta-native multimodal transport **worked**: a real image was sent with OCR and the API returned a genuine response. However, the single proposed vision-assisted quote was **rejected by local source grounding**. No verified citation survived, so the final label fell to `not_found`. This is a **missed authored support** relative to OCR-only on this one case.

A rejected OCR match is **not proof of hallucination** or a false real-world CV statement; the source may be visually present with text rendering differences. The trace does not yet expose the exact rejected image-derived quote, so the precise textual cause cannot be established from this saved summary alone. It would be misleading to claim that Muse fabricated words.

**Decision for the hackathon:** Do **not** advertise native vision as an accuracy upgrade or make it the judge demo default. Keep the existing opt-in feature flag OFF on the isolated public judge server. Improve OCR-to-visual provenance alignment only after a controlled diagnostic demonstrates a correctable failure, and never silently relax the quote verifier.

## C. Role-ownership shadow warnings

[No-paid-call shadow evaluation](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/41016347438)

- The current **mock heuristic** labeled 11 of 24 author-created cases as supported when the author references did not establish personal responsibility.
- A new **advisory-only** source-attribution rule identified all 11 cases, plus two other review-worthy ambiguities; it generated zero warnings on the 11 authored positive examples.
- On the 20 historic genuine Muse replay cases, only **3** source passages were flagged: ET-005, ET-007 and ET-015. These are review questions, not independently confirmed Muse errors.
- **Zero candidate status changes** or automatic employment decisions from this new shadow rule; source quotes/labels remain untouched.

Do not infer that this regex warning has real-world precision or recall from these small, author-defined tests. A broader independently annotated evaluation is required before merging it into the judge release.

## D. Competition recommendation

1. **Keep judge release frozen:** genuine 20-CV saved Muse replay, verified PDF receipts, semantic corrections and human-controlled clarification are stronger, well-tested proof than a partly validated vision mode.
2. **Lead with a genuine semantic correction**, such as ET-003 (existing publicly replayable demonstration) or the new five-case receipt evidence in this document; clearly distinguish saved replay from fresh provider inference.
3. **Treat multimodal native image input as a documented experimental result**, with the 0/1 quote-grounding failure disclosed. The fact that the verifier blocked an unverified claim is technically important even if the mode did not improve its criterion label.
4. **Next engineering experiment:** retain bounded rejected-citation text and run OCR/exact-span alignment analysis first. Only if grounded should a suggested reconciliation pass for *human review*, not silent automatic support, be considered.
5. Do not promise reviewer time savings until a real user pilot is completed. Do not present synthetic outcomes as population accuracy.

### Grounded reference sources
- [Meta's documented Chat Completions image inputs](https://dev.meta.ai/docs/image-understanding) use `user.content` items `{type:"image_url",image_url:{url:"data:image/jpeg;base64,..."}}`.
- The two runs are linked above and contain the specific historical provider receipts in their retained artifacts.
- Synthetic test inputs and author expectations were frozen under `scripts/finalist_omission_corpus.py` before the live call. The generator hash is `eabd1e2da9130a5c8ffc2f3be7dedf6daeb13171ec9b563dd956ade289f7d7e5`.
