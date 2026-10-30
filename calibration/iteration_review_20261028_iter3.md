# EvidenceTrail targeted Muse calibration — 28 Oct 2026

## Question tested

Can the live pipeline keep a named professional qualification unsupported when the fictional CV shows strong adjacent procurement experience, while still recognizing a degree directly and another country's procurement-law experience as potentially related?

The public posting is the NHS Commercial Solutions Procurement Director role: <https://apps.trac.jobs/job-advert/7425380?ShowJobAdvert=&feedid=9005>. Its person specification names an “MCIPS professional qualification,” an MBA/MSc or other higher degree, and expert knowledge of procurement, UK and EU legislation and regulations. The public posting was used to define the test criteria; the CV is fictional.

## Run control

- Model: `muse-spark-1.3` (Standard mode)
- Requests: **2 expected, 2 reported**, no retries, no failed cases
- Prewritten requirements: **3**
- Reported usage: **5,493 input tokens; 6,897 output tokens**
- Estimated Standard token cost: **$0.0361785** before any cached-input discount; this is not a billing record.
- The saved report contains labels, counts, and the public job source only. It contains no CV passages or model-generated quotes.

## Result

| Requirement | Expected | Muse result | Result |
|---|---|---|---|
| MCIPS professional qualification | Unsupported | Unsupported | Correct |
| MBA or MSc / higher degree | Direct | Direct | Correct |
| UK/EU procurement-law knowledge, with Indian public-procurement experience in the CV | Related | Related | Correct |

All three findings aligned with the prewritten labels. Coverage was **3/3**, strict category accuracy **3/3**, and exact quote/page verification **3/3**. The run produced no false related transfer, missed related finding, or related-to-direct overclaim.

## Cumulative view

Combining this targeted batch with the prior post-fix three-case run gives **13/15 (86.7%)** strict category accuracy across four fictional CVs and two separate live batches. The two duration-label disagreements remain visible and gated to human review in the earlier cases. Their gold labels have not been changed.

The two batches used 8 reported calls total and have a combined Standard token-cost estimate of **$0.19595625**, excluding cached-input discounts. See `live_semantic_results_20261028_cumulative4.json` for the per-case breakdown and batch provenance.

## Decision

This case supports the intended hard-credential boundary for this example. Keep the distinction visible in the demo: adjacent public-procurement experience can be related to UK/EU regulation, but it does not establish the separately named MCIPS qualification. One successful example does not establish a general error rate; retain the prewritten case and include failures in later reports without changing labels after the run.

Detailed sanitized result: `live_semantic_results_20261028_iter3_credential_boundary.json`.
