# Named-system transfer prompt trial — 28 Oct 2026

## Scope and control

This is a separate exploratory run on the same five fictional public-job-derived cases used by the earlier v2 public-JD calibration. The only intended change was an instruction distinguishing documented use of a named law, standard, product, or public-sector system from concrete analogous work. Muse Spark 1.3 ran the existing two-pass path with structured outputs. Temperature and top-p were omitted so Meta's defaults applied. No automatic retries were enabled.

Four cases completed in the initial batch. The UAE case returned a connection error and was recovered in a separate two-call run; no other case was rerun. The failed request's provider usage is unknown. The combined report contains five completed result payloads and ten reported successful calls.

## Results

| Measure | Earlier public-JD v2 prompt | Named-system transfer prompt |
|---|---:|---:|
| Expected evidence labels matched by Muse | 15/18 (83.3%) | 15/18 (83.3%) |
| Labels after deterministic timeline gate | 17/18 (94.4%) | 17/18 (94.4%) |
| Expected Related labels found | 3/4 | 4/4 |
| Direct/other targets classified as Related | 0 | 1 |
| Related classified as Direct | 0 | 0 |
| Timeline flags detected | 2/2 | 2/2 |
| Quotes passing local checks | 19/20 (95.0%) | 21/21 (100%) |
| Blocked quotes in this run | 1 | 0 |
| Successful-result token estimate | $0.2396995 | $0.22597975 |

The change recovered the expected Related finding in the India public-procurement case. The remaining label miss shifted to the UAE case: a requirement expected as Direct was labeled Related. This is a conservative under-call, not a Related-to-Direct overclaim. Aggregate label accuracy did not improve. The new prompt profile therefore presents a trade-off, not a demonstrated accuracy gain.

The UAE gold label deserves independent review. The CV says it processed amendments and renewals, tracked service levels, escalated claims, and supported settlement discussions; the requirement asks the person to manage amendments, renewals, service levels, claims, and disputes. A reviewer could reasonably question whether support and escalation establish direct ownership. The expected label is preserved for comparability; it was not changed after seeing Muse's answer.

All 21 proposed quotes in this profile passed the local source checks. This run did not reproduce the earlier scanned-CV blocked quote. Keep the earlier blocked-quote result and this clean run separate; do not combine their denominators or claim every scan is blocked or verified.

## Usage and limits

The successful payloads report 40,561 input and 41,242 output tokens. The $0.22597975 estimate uses the saved Standard rates and covers successful results only; it excludes the initial connection failure and is not a provider billing record. Check the Meta usage dashboard for actual debit. No additional model was used.

This remains five fictional cases with human-prepared expected labels, not a general accuracy, fairness, adoption, or recruiter-time study. Model output can vary between calls. The current instruction is useful for surfacing concrete analogous work but should not be described as an accuracy fix from this sample. Related findings remain clearly labeled for recruiter review.

Machine-readable records: `semantic_cases_live_20261028_transfer_prompt_v2_combined.json`, the initial batch and attempt records, and the separate UAE recovery and attempt records.
