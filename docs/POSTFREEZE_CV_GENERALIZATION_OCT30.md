# EvidenceTrail — post-freeze source-backed semantic regression (October 30, 2026)

## Independent-of-the-prompt examples, but synthetic (NOT real hiring accuracy)

After freezing the revised Muse instructions from [PR #24](https://github.com/farhanjamal2002-blip/-evidencetrail/pull/24), the evaluation team authored a new challenge of **16 two-page fictional CVs in four previously untested industries**: renewable energy, learning design, maritime operations, and manufacturing quality. Each supplied three approved job requirements (48 criterion judgments).

- Four source styles per sector: evidence buried in a second page, explicit task limitations, two opposing statements in the CV, and keyword-heavy training material.
- Source author recorded the expected criterion labels **before** the first model call.
- [Preflight and real Meta run](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40935108963): 16/16 completed actual Muse Spark 1.3 calls, 16 genuine receipts, 48/48 valid criterion outputs, median **3.81 seconds/CV**.
- **Raw Muse matched 48/48** predeclared synthetic labels; **EvidenceTrail initially matched 46/48** due to two false-negative contradiction clearances caused by our local action-verb parser.
- Breakdown: 16/16 source-supported, 28/28 not documented, and only 2/4 opposing-claim discrepancies survived the original local post-processor.
- **Not an independent expert or representative real-world assessment.** These are synthetic, relatively explicit CVs, with references authored by the builder of the benchmark. The result is helpful regression evidence, not a general accuracy estimate.

### What the two actual verified Meta quotations revealed

**POST-02-03: genuine curriculum contradiction.**
- On one page: *I built the algebra and geometry teaching sequence and mapped each unit's outcomes to the national curriculum competencies.*
- In the second page declaration: *The role-scope addendum says I never designed or approved secondary mathematics curriculum content.*
- Muse correctly proposed `conflicting`. Local code incorrectly changed it to `not_found` because the `sign` substring inside `designed` was falsely parsed as an approval action.

**POST-04-03: genuine investigation-lead contradiction.**
- On one page: *I chaired the eight-discipline defect investigation, tested likely causes and signed the root-cause corrective action report.*
- In the other passage: *My signed job scope says I did not lead manufacturing defect root-cause investigations.*
- Muse correctly proposed `conflicting`. Local code incorrectly changed it to `not_found` because it did not recognize `chaired` as applicant-owned leadership.

### Targeted change and scope

The patch updates `semantic_review.py` to use **word-boundary action recognition** rather than substring search, plus narrowly adds `design/built` and `led/chaired` equivalences. It preserves the raw Meta label and exact PDF citations and does **not** promote any CV to `supported`.

Source-anchored unit tests protect both real opposing statements and near misses where someone **only tracked** an investigation. Other historical 20-CV receipts, page grounding, human decisions, and the public mock-only demo remain unchanged. No additional Meta call is required for the deterministic fix.

### API spending disclosure

An initial attempt made 16 model requests but failed in our test formatter because that evaluator assumed four criteria rather than three. Those responses did not produce a valid score. We corrected the formatter, wrote offline dry-run tests and persisted model responses before scoring, then ran the valid 16-case experiment. Thus up to **32 Meta calls** were attempted across the two post-freeze evaluation runs, but **only the latter is used in results**. Provider costs/credits were not measured here.

### Decision gate

Only merge after Python unit/integration, JS, browser and Docker regressions pass. The patch is justified by actual page-verified model citations but does not prove general-purpose semantic equivalence; additional independent human annotation and non-templated documents remain necessary.
