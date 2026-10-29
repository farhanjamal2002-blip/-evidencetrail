# P0 semantic precision — hard two-page CV benchmark, October 29

**Scope:** source-grounded document evidence, not the reality of a candidate's abilities. Synthetic fictional CVs only.

## Results and honesty boundaries

Two **separate genuine Meta Muse Spark 1.3 runs**, each using 20 two-page fictional PDFs and four fixed job criteria, were compared with the same 80 human-authored source expectations locked before the original run.

| Actual pipeline | Raw Muse reference matches | Final EvidenceTrail reference matches | Real Meta calls | Median end-to-end |
|---|---:|---:|---:|---:|
| Before multi-quote scope calibration | 45/80 | **68/80** | 20 | 4.00s |
| After calibrated conflict guard | 44/80 | **80/80** | 20 | 4.12s |

- [Baseline workflow / full per-class confusion](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40924546755).
- [Corrected workflow / full per-class confusion](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40926435081).
- Both workflows prevalidated **20 fictional two-page CVs, four criteria each**, across procurement, data engineering, hospital quality, cybersecurity and finance.
- After correction: **30/30 directly documented**, **45/45 not documented**, **5/5 genuinely contradictory** reference items classified correctly. Zero false-positive support and no missed true discrepancy.
- Raw Muse produced **35 vs 36** not-documented items labeled \`conflicting\` across the two stochastic runs. **Do not present the 12-point absolute improvement as a paired comparison of identical model outputs.** Model calls were repeated; the output was not bit-identical.
- The original 12 remaining false conflicts were concentrated in adjacent/scope and keyword-heavy CVs with multiple quotations about work boundaries. Earlier post-verification treated any multiple quotes as possible self-contradiction.
- The calibration now requires explicit opposed personal claims for multi-quote contradictions unless local timeline flags independently call for human review. Model \`raw_status\`, source citations, provider receipts and the original saved judge replay are preserved.
- The original 20 saved-real-Muse applicant replay still has exactly **three true/discrepant review items** under its historical references and all existing tests pass.

**Crucial scientific limit:** the same 80 test labels were used to diagnose and refine the rule. This is an **in-sample development improvement**, NOT independent accuracy, not a population success rate, and not evidence that the app should automatically decide hiring outcomes. A new, held-out test set is the next release gate.

## Implementation

- \`semantic_review.py\`: only genuine source-checked Muse findings receive the new deterministic calibration; old mock contract left unchanged. The new explicit task-action/personal-denial matching is conservative. Ambiguous multi-quote situations are labeled *Scope or responsibility to clarify*, not "candidate disqualified".
- \`tests/test_multi_quote_scope.py\`: eight targeted regressions for two limiting quotes, no true opposing claims, positive+negative contract responsibility, pipeline ownership, audit leadership, timeline flags, missing input and idempotence.
- Existing 1,000-case controlled semantics benchmark still shows **900/1,000** corrected injected-policy references; 100 intentionally missed direct requirements remain misses. These are not real Meta model outputs.
- [Full release acceptance](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40926074658) passed all Python, JS, Chromium, Docker and original genuine replay tests.

## Next decision gate

Assess 8–20 **new** fictional CVs in unrelated job categories with four criteria each and independently predeclared, validated reference anchors, including dual contradictory claims, buried positive actions, keywords without role ownership, and unrelated adjacency. Freeze their reference and code before requesting Muse inference; make no further rule adjustments based on that holdout without explicitly treating it as development data.

Do not increase the public anonymous model request budget, change applicant ranking, or claim a fairness certification or measured recruiter savings.
