# Evidence strength and reviewer UI iteration — 28 Oct 2026

## What changed

- The second Muse pass now returns an `evidence_strength`: `specific`, `stated`, `keyword_only`, or `none`. The prompt defines each level.
- The local verifier suppresses supporting citations when Muse labels them keyword-only or none. A keyword or title mention cannot support a finding on its own.
- The finding card now shows the related-evidence explanation, the remaining gaps, and Muse's follow-up question without requiring the reviewer to open a disclosure.
- The result summary shows a source-check chip with exact quote/page matches and exclusions. Synthetic preview and local mock results are labeled separately.
- The requirement matrix shows a strength chip and whether each displayed quote passed the local source/page check, was rejected, or has no accepted supporting quote.
- The calibration report records the strength distribution as a model-reported breakdown, not as measured strength accuracy.

## Frozen five-case Muse run

- Model: `muse-spark-1.3` Standard
- Cases: 5 fictional CVs across 4 industries; 18 expected findings
- Calls: 10 expected and reported; automatic retries disabled; no failed cases
- Token use: 38,702 input and 45,291 output
- Estimated Standard token cost: **$0.24086425** at the rates already used by the calibration reports. This is a token-based estimate, not a provider billing record.
- This five-case report contains aggregate labels and telemetry only. A later targeted scan report below stores rejected snippets with their cited page and failure reason, without saving a full CV or accepted quotes.

| Case | Muse-only labels | Quote/page check | Notes |
|---|---:|---:|---|
| India public procurement manager | 3/4 | 6/6 | The expected conflict was labeled Direct with ambiguous certainty; the timeline gate sent it to review. |
| UAE contract and supplier manager | 3/4 | 5/5 | The expected conflict was labeled Direct with ambiguous certainty; the timeline gate sent it to review. |
| Semiconductor supplier operations manager | 4/4 | 6/6 | All expected categories matched. |
| NHS procurement director, searchable PDF | 3/3 | 3/3 | The credential boundary remained Unsupported; related experience remained Related. |
| NHS procurement director, image-only scan | 3/3 | 3/4 | OCR ran on page 1; one of four proposed citations did not pass local quote/page verification. |
| **Total** | **16/18 (88.9%)** | **23/24 (95.8%)** | **One proposal was not verified.** |

Muse returned 10 `specific`, 5 `stated`, 0 `keyword_only`, and 3 `none` findings. The live set therefore did not exercise the keyword-only state; the offline test covers the rule that such a citation is withheld from support.

There were no false related transfers, missed related findings, or related-to-direct overclaims. Muse alone called both expected duration conflicts Direct with ambiguous certainty. The timeline check detected and linked both flags. The code-only update now retains `evidence_type: direct` and records `final_review_label: conflict_to_clarify` plus `final_evidence_type: conflicting`. The dossier, matrix, evidence graph, and HTML report display **Conflict to clarify** and show the provenance line “Muse: Direct · Timeline check: conflict.”

### Deterministic timeline adjudication on the same frozen run

- **Muse alone:** 16/18 labels (88.9%).
- **After the deterministic timeline gate:** 18/18 expected labels on this set.
- The two changes are the India and UAE duration requirements where the local date audit already found a verified discrepancy. No Muse calls were made for this code-only change. The original Muse labels remain stored and visible.
- Treat 18/18 as the combined result of Muse plus two rule-based human-review overrides, not as Muse accuracy or as evidence of general accuracy. Both labels ask the recruiter to clarify; neither says the candidate misrepresented experience.

The previous frozen run also scored 16/18; its quote denominator was 20 rather than 24. The new 23/24 quote result should not be presented as a measured improvement over 19/20 because the proposed citation counts differ.

## Spend and run notes

The five-case run above is the scored result. Two successful diagnostic checks in this iteration also returned provider usage: a one-request schema check used 1,596 input / 1,661 output tokens (about $0.0091), and a one-case end-to-end check used 8,858 input / 8,475 output tokens (about $0.0471).

Two non-scored attempts have no saved token usage: an initial one-case request returned a generic 502, and an earlier five-case command stopped after its first successful case because the report aggregator lacked the new strength counters. Neither attempt was automatically retried. The second attempt's two API calls completed, but its token usage was not saved. The provider dashboard is the source of truth for their debit.

Previous saved calibration batches total an estimated $0.486832. Adding the current scored run and the two successful diagnostic checks gave about $0.783842 in known token-based estimates, excluding usage from two non-scored attempts. The two-candidate strength-ladder run used 11,019 input and 8,143 output tokens, with an estimated Standard cost of $0.0483815. The targeted scanned-CV rerun used 6,142 input and 6,319 output tokens, an estimated $0.03453325. The updated known estimate is therefore about **$0.86675675**, still excluding those same two non-scored attempts. These are token estimates, not the provider's account balance.

## One-time two-candidate strength-ladder demo

- Public JD requirement: “Support supplier negotiations, pricing analysis, and commercial contract implementation.” Both CVs are fictional and use the same job description.
- The keyword-only CV contains a skills list and the specified generic filler sentence. All three returned findings were `keyword_only`; the first finding was `unsupported` and had no accepted quote.
- The second CV contains one concrete supplier-contract example. All three returned findings were `specific`; the first finding was `direct` and had one quote pass local PDF verification.
- The focal category and strength labels matched both prewritten expectations. This is one paired demonstration, not a benchmark.
- Muse split the single JD sentence into three findings per CV. Each CV's three returned findings had the same strength label (all keyword-only for Candidate 1; all specific for Candidate 2).
- The one batch used exactly four reported requests, no automatic retries, 11,019 input tokens, and 8,143 output tokens. Estimated cost: $0.0483815.
- Its sanitized machine report is `live_strength_ladder_demo_20261028.json`; the fictional input fixture is `strength_ladder_demo.json`. The run report does not store CV text, model quotes, or replayable response bodies. The saved quote counts cover the first returned finding only, while the strength distribution covers all three.

## One-time scanned-CV rerun with a real verifier catch

- Case: the fictional image-only, two-column procurement CV. Muse Spark used exactly two requests; both completed, with zero retries.
- OCR ran on page 1. All three expected evidence categories matched (3/3). Three of five proposed quote/page checks passed; two quotes were blocked because they could not be located on their cited page.
- Both rejected snippets refer to the MCIPS requirement and cite page 1. The text in each appears to splice wording from opposite columns, consistent with OCR column-order drift:

  > “Led public tendering and contract Professional credentials: no MCIPS”

  > “management for an Indian public health qualification is listed.”

- Rejection reason for each: `quote_not_found_on_cited_page`. These are real rejected proposals from this run, not reconstructed examples. The saved report records each quote, cited page, requirement, and reason.
- Usage: 6,142 input and 6,319 output tokens; estimated Standard token cost **$0.03453325**. This targeted result is separate from the earlier frozen five-case run (which had 3/4 quotes verified for its scan); do not combine their denominators.
- The API response and HTML evidence pack include the same quote, page, and reason. The saved calibration JSON preserves those fields without the full response body; no further Muse request is needed to inspect this catch.

## Verification

- **70 local tests passed**, including the timeline-label preservation/report tests and the paired-fixture test.
- Python compilation, `node --check static/app.js`, and `git diff --check` passed.
- The new demo preflight showed exactly four expected requests, configured Muse, zero automatic retries, and a sanitized report.
- The one live paired run completed all four requests with no retries or failed candidates. Its reported token estimate is $0.0483815; the exact provider debit is not established by token math.
- The scanned-CV rerun completed exactly two requests and saved both rejected quote snippets with page and reason.

Machine-readable results: [five-case Muse run](live_semantic_results_20261028_strength_final.json), [code-only timeline adjudication](deterministic_timeline_adjudication_20261028.json), [paired strength-ladder run](live_strength_ladder_demo_20261028.json), [scanned-CV quote audit](live_semantic_results_20261028_scanned_quote_audit.json), and [strength-ladder fixture](strength_ladder_demo.json). The two ready-to-upload fictional CV PDFs are in `demo_assets/`. The unsuccessful pre-fix smoke is retained separately: [smoke failure record](live_semantic_results_20261028_strength_smoke_failure.json).
