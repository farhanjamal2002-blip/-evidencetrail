# Muse Wonder vs. Spark comparison — 28 Oct 2026

## Comparison setup

This compares Muse Wonder 1.0 with the saved Muse Spark 1.3 run on the same five fictional public-job cases. The dataset hash and both prompt hashes match, so the selected model was the intended change. Both use the existing two-pass Muse workflow and local quote/timeline checks. The product default remains Spark. Reasoning effort was omitted for both models so each used its default.

The configured KUL bridge route was available and returned live Muse results. An earlier Wonder attempt in this folder was interrupted before it produced a result; it is a separate attempt record and is not evidence about Wonder quality. In the completed batch, four cases returned successfully. The NHS case returned HTTP 502 after a response failed local schema validation. It was manually run once more as a two-call recovery; no automatic retry occurred.

## Results on the five completed payloads

| Measure | Muse Spark 1.3 | Muse Wonder 1.0 |
|---|---:|---:|
| Expected labels matched before timeline gate | 15/18 (83.3%) | 15/18 (83.3%) |
| Labels after deterministic timeline gate | 17/18 (94.4%) | 17/18 (94.4%) |
| Expected Related findings identified | 6/6 | 6/6 |
| Non-Related findings incorrectly called Related | 1 | 0 |
| Related findings incorrectly called Direct | 0 | 0 |
| Timeline flags detected | 2/2 | 2/2 |
| Locally verified proposed quotes | 21/21 | 18/18 |
| Ambiguous findings | 4 | 9 |
| Extra unmatched findings beyond the expected criteria | 0 | 2 |
| Successful-result token estimate | $0.22597975 | $0.904628 |

The models had the same aggregate label accuracy. They made different single errors: Spark called one expected Direct UAE contract finding Related; Wonder called one expected Direct semiconductor finding Unsupported. The timeline gate corrected the two date-conflict labels for both models. Wonder made no false Related transfer on this set, while Spark made one, but that did not improve aggregate accuracy. Wonder also marked more findings ambiguous and produced two extra unmatched findings, which could mean more recruiter review. The small sample does not establish that this difference will persist.

Wonder's known successful-result estimate for the five-case comparison is about four times Spark's. The estimate uses saved token counts and full Standard rates; it is not a provider billing record. The failed schema-validation request's usage is unknown. Including the separate two-call UAE smoke would bring the known successful-result estimate across completed Wonder runs to $1.137148, still excluding the interrupted attempt and any failed-request usage. Check Meta's usage dashboard for actual billing.

## Decision

Keep Spark as the default. The Wonder run did not improve the fixed-set aggregate score enough to justify changing the critical path. A selective Wonder escalation is a reasonable later experiment for cases Spark marks ambiguous, but it should only be added if a larger, independently labeled evaluation shows that it resolves uncertainty enough to justify its cost and extra latency. This comparison did not measure latency.

The main Wonder result has 18/18 proposed quotes pass local checks and no blocked quote. It does not replace the earlier separate scanned-CV verifier catch; that example remains its own run and denominator. These five cases are fictional calibration examples, not a general accuracy, fairness, adoption, or recruiter-time study. The UAE expected Direct label is contestable because the CV describes supporting settlement discussions while the JD asks for dispute ownership; the label was not changed after seeing either model's result.

## Request accounting

- Initial five-case batch: 8 successful calls reported across four completed cases; one case failed schema validation. Usage for the failed request is unknown.
- Manual NHS recovery: 2 successful calls reported; no retry of the other four candidates.
- Combined result: five candidate payloads, 10 successful calls reported, with the failed initial request kept separate.
- Earlier interrupted Wonder attempt: separate attempt ledger; request count and usage unknown. No result is included here.
- Separate UAE smoke: two successful calls, recorded separately and excluded from the five-case metrics.

Machine-readable comparison: `semantic_cases_live_20261028_wonder1_combined.json`. Source runs and attempt records are listed in `REPORT_INDEX.md`.
