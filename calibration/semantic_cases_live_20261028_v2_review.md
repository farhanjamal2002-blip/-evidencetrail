# Public-JD Muse calibration — demo-v2, 28 Oct 2026

## Scope and run control

Five fictional CVs were evaluated against five public-job-derived descriptions across public-sector procurement, GCC contract/supplier management, semiconductor operations, healthcare procurement, and an image-only scanned CV. Muse Spark 1.3 ran the existing two-pass workflow. No extra model was introduced and no automatic request retries were enabled.

The initial five-case batch completed four cases (eight successful calls reported). The semiconductor case received HTTP 503. A separate, one-case recovery then completed its two passes. The other four cases were not rerun. The failed 503 attempt returned no token usage; provider request count and debit for that attempt are unknown.

## Results across five completed result payloads

| Measure | Result |
|---|---:|
| Expected evidence labels | 18 |
| Muse label matches | 15/18 (83.3%) |
| Labels after deterministic timeline gate | 17/18 (94.4%) |
| Related-to-Direct overclaims | 0 |
| Missed Related findings | 1 |
| Expected timeline flags detected | 2/2 |
| Quotes passing local verification | 19/20 (95.0%) |
| Quotes blocked | 1 |
| Successful model calls reported | 10 |
| Successful-result token estimate | $0.2396995 |

The cost estimate uses 38,916 reported input tokens and 44,954 reported output tokens at the saved Standard rates. It covers successful results only; it excludes the failed HTTP 503 attempt and is not a provider billing record. The model API dashboard remains the source for actual spend.

## The remaining semantic miss

The one undercall is the India procurement case's requirement to apply public procurement rules and systems such as GFR, CVC guidance, and GeM. Muse classified the CV as Unsupported because it describes private-sector internal bid audit trails and corrective actions but lists no public-rule or GeM work. The prewritten target is Related: the audit-trail work could transfer, while actual GFR/CVC/GeM experience remains unproven.

This is the cautious direction of error. It did not overstate adjacent experience as direct. Keep the human-review distinction visible and do not change the saved score to match the expected label. A prompt change should be based on a source-grounded trace and reevaluated on the fixed set; no score is claimed for a prompt that has not been rerun.

## Interpretation limits

This is a small, human-labeled fictional set, not a general accuracy or fairness evaluation and not evidence of reduced review time. The expected related label is a contestable transfer judgment. A verified quote establishes text and location, not real-world credentials or job history. One case required a separately logged recovery after a service failure; the combined report preserves that fact rather than presenting it as one clean uninterrupted batch.
