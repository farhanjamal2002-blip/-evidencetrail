# Verified semantic conflict calibration — 29 October 2026

## Scope
EvidenceTrail labels evidence in supplied hiring CVs as `supported`, `not_found` or `conflicting`. It does not determine whether a candidate is qualified or whether a CV claim is true outside the uploaded document.

A model's `contradicts` citation role is a proposal, not proof of CV self-contradiction. The local policy now requires an opposing source-backed positive claim before retaining a non-timeline conflict. One or several quoted limitations alone indicate that the exact required experience was **not established** by the CV. Authentic contradictions and independently checked timeline discrepancies remain reviewable.

The model's raw label, all verified quotations and their page references remain in the audit. Page highlights follow the final clarified scope label.

## Controlled real-Muse runs

| Run | Corpus | Muse raw matches | Verified final matches | False conflicts | Genuine conflicts retained |
|---|---|---:|---:|---:|---:|
| [Baseline PR #18](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40924546755) | 20 two-page fictional CVs, 80 predetermined labels | 45/80 | 68/80 | 12 | 5/5 |
| [Same-corpus post-fix replay](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40928748624) | Same locked 20 fictional CVs | 45/80 | 80/80 | 0 | 5/5 |
| [New separate synthetic holdout](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40929602808) | 20 separately authored two-page CVs, five new sectors and 80 new labels | 25/80 | 80/80 | 0 | 5/5 |

Every recheck submitted 20 requests, received 20 successful authentic Muse responses with nonempty provider receipts and performed local source-quotation checks. Neither run had false-supported labels or missed direct-supported labels. The new holdout's prepared corpus, reference labels and PDF hashes were committed before the first Muse call: [holdout branch at f4f1416](https://github.com/farhanjamal2002-blip/-evidencetrail/tree/f4f1416d048a94b2c57d3232d2d9b5dd9005ad30).

The [no-cost Python, JavaScript and offline regression CI](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40929859901) passed with the additional PDF highlight reconciliation tests.

## Interpretation and limits

- These are hand-authored, synthetic CVs with predetermined expected labels, **not** an independent panel of recruiter judgments or a sample of real applications. Do not use the percentages as deployment accuracy estimates.
- The same-corpus replay confirms a regression fix. The new five-sector corpus supplies a more distinct challenge, but both benchmarks deliberately contain explicit role-limitation and opposite-claim patterns. This is not a broad adversarial evaluation.
- Correct quotation grounding proves only that a sentence appears on the cited PDF page. It does **not** establish that the person's claim is true.
- Retaining a genuine conflict means displaying two apparently opposing CV statements for human clarification; it is **not** an allegation of dishonesty.
- Longer, messy, multilingual, scanned, ambiguous-ownership and time-separated contradictory claims require further independent testing.
- No public Render deployment or main-branch merge was performed as part of these evaluations. No live applicant data was used.
