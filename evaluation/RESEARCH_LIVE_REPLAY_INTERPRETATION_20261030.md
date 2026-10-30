# Frozen RC1 live replay: interpretation and next tests (October 30, 2026)

## What ran

The predeclared 12-pair fictional corpus was sent through the real EvidenceTrail API route in two one-shot runs against frozen judge release 8489e45ae0f87d8421562618bda556c31911372b. The second run covered the ten pairs not included in the first. Across both runs: 24 requests, 24 Muse Spark 1.3 provider response IDs, zero retries, no human ratings, and no native vision. Full responses, receipts, quote audits, verification audits, input-PDF hashes, and run manifests are retained beside the summaries.

Estimated standard-rate usage was $0.11587275 across the two runs, not a provider invoice. No production or frozen-release code changed.

## Results

| Pair | Factor | Expected relation | Final relation | Final labels matched synthetic references |
|---|---|---|---|---:|
| M01 | Paraphrase | invariant | invariant | 2/2 |
| M02 | Agent swap | must change | changed | 2/2 |
| M03 | Responsibility swap | must change | changed | 2/2 |
| M04 | Technical paraphrase | invariant | invariant | 2/2 |
| M05 | Verb scope | must change | changed | 2/2 |
| M06 | Fictional name change | invariant | invariant | 2/2 |
| M07 | Explicit internal discrepancy | must change | changed | 2/2 |
| M08 | Evidence position | invariant | invariant | 2/2 |
| M09 | Document prompt injection | invariant | invariant | 2/2 |
| M10 | Adjacent skill | must change | changed | 2/2 |
| M11 | Department scope | must change | changed | 2/2 |
| M12 | Added self-contradiction | must change | changed | 2/2 |

The frozen final labels matched all 24 author-written synthetic references, and each pair showed its predeclared relation. The raw model labels matched 19/24 references. Five raw mismatches were conflicting where the author reference was not_found: M02 variant, M03 variant, M05 variant, M10 variant, and M12 baseline. In the corresponding four new-run cases, the pipeline's semantic clarification stage changed raw conflicting to final not_found; the prior M02 variant showed the same raw/final pattern. Report raw and final outputs separately. Do not describe 24/24 as standalone model accuracy.

Across all 24 requests the app proposed 25 source citations; its local deterministic verifier accepted all 25 and excluded none. This confirms source-quote presence/location for these generated PDFs. It does not establish that a quotation supports the specific applicant-level conclusion. That gap is the reason the two stages must remain separately measured.

M08 moved an identical sentence between page 1 and page 3 of an actual generated three-page PDF. The pipeline returned the expected page in both variants (2/2). This is a narrow controlled position check, not a long-context robustness result.

## Why it helps the product story

EvidenceTrail can show an auditable chain: raw model interpretation, local quote/page verification, and a separate semantic clarification stage. In these constructed cases, quote verification passed even when raw model semantics were too strong or misclassified. Present that as evidence for stage-wise evaluation and conservative interpretation, not proof of real-world résumé accuracy or superiority over human reviewers.

## Next engineering tests

1. Add a stage ablation that records the same predeclared cases with semantic clarification disabled, then compares raw labels, final labels, and verified citations. Do not change the frozen release; make a research-only branch or runner.
2. Expand the responsibility/agent-swap, verb-scope, and self-contradiction cases with additional predeclared fictional examples before any model calls.
3. Add OCR-specific scans with controlled image quality and text placement, while preserving ground-truth PDF text and page labels.
4. Keep calibration claims out until the pipeline emits a documented confidence score and a larger predeclared set supports calibration analysis.

## Limitations

The set is small, synthetic, and author-labelled; labels are not independent ground truth. One model/configuration and one run per variant were used. No real applicant documents, human judgments, population estimates, confidence intervals, or calibration measurements were collected. A genuine provider response ID proves a provider call occurred, not that a semantic label is correct. Results should be described as a reproducible 24-request fictional replay only.
