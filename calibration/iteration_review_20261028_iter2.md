# EvidenceTrail Muse calibration review — 28 Oct 2026

## Run control

- Model: `muse-spark-1.3` (Standard mode)
- Cases: 3 fictional CVs against job descriptions paraphrased from public postings
- Requests: 6 reported; 0 automatic retries; 0 failed cases
- Reported usage: 26,237 input tokens and 29,878 output tokens
- Estimated Standard token cost: about **$0.1598**, calculated without a cached-input discount. This is an estimate, not a billing record.
- The report stores aggregate labels and counts only; it contains no CV passages or model-generated quotes.

## Changes under evaluation

1. Wording that says a credential or experience is not listed in the CV is treated as missing documentation, not as a contradiction about the candidate.
2. The deterministic timeline audit attaches a duration discrepancy to a related job requirement and moves that finding into human review.
3. Verification reporting separates exact page-and-quote matches from citations retained as evidence after semantic review.

## Results

| Case | Baseline | Iteration 2 | What changed |
|---|---:|---:|---|
| India public procurement manager | 1/4 | 3/4 | The absent public-system evidence is now Unsupported; the related finding is recovered. The duration discrepancy is gated for review. |
| UAE contract and supplier manager | 3/4 | 3/4 | The duration discrepancy is gated for review; other labels are unchanged. |
| Semiconductor supplier operations manager | 3/4 | 4/4 | The unsupported semiconductor requirement is no longer called Conflicting. |
| **Overall** | **7/12 (58.3%)** | **10/12 (83.3%)** | **+25 percentage points** |

Other measured results:

- False related transfers: **0**
- Related-to-direct overclaims: **0**
- Missed related findings: **1 → 0**
- Exact quote/page verification: **18/18 → 16/16**
- Expected timeline flags detected: **2/2** in both runs
- Timeline findings routed to human review in iteration 2: **2**

## Remaining discrepancy and label audit

The two strict-label errors are both duration requirements. Muse returns Direct with ambiguous certainty; the local timeline audit flags each and the reviewer UI routes it to Needs review.

- The India CV says “12 years” but lists dated roles from 2018 to 2026. It does not state that those are the candidate's complete work history.
- The UAE CV says “9 yrs” and separately says the experience covers 2017–2026, while the listed roles begin in 2019. It also does not say the listed roles are exhaustive.

The prepared gold labels call both cases Conflicting. Under the product rule that missing or incomplete documentation is not proof of a contradiction, that label needs independent review. The labels are left unchanged here; changing them after seeing model outputs would bias the score. For now, the deterministic Needs review state is the appropriate user-facing safeguard.

## Recommendation

Keep the timeline review gate. Do not spend another call repeating these same cases without a changed hypothesis. The next live batch should test a new, pre-labeled edge case—preferably one where a hard credential or explicit years-of-experience threshold is adjacent to genuinely transferable work—so it adds evidence the current set does not provide.

This is a small calibration set and a single post-fix run. The 83.3% strict category score is useful for comparing iterations, not a production accuracy claim or a candidate decision metric.

Detailed sanitized results: `live_semantic_results_20261028_iter2.json`. Baseline: `live_semantic_results_20261028.json`.
