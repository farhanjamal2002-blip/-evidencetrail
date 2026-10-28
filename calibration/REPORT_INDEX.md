# EvidenceTrail calibration reports

All results use fictional CVs. Reports omit full CV text and accepted quote text. The targeted scanned-CV audit intentionally retains only rejected quote snippets, their cited page, and the verifier reason so the real catch can be reviewed. These snippets are not a full CV or a replayable model response.

## Reports

| Run | Written review | Machine-readable result |
|---|---|---|
| Initial live baseline | — | [Baseline JSON](live_semantic_results_20261028.json) |
| Iteration 2: post-fix three-case run | [Review](iteration_review_20261028_iter2.md) | [JSON](live_semantic_results_20261028_iter2.json) |
| Iteration 3: credential boundary | [Review](iteration_review_20261028_iter3.md) | [JSON](live_semantic_results_20261028_iter3_credential_boundary.json) |
| Iteration 4: image-only scanned CV | [Review](iteration_review_20261028_iter4.md) | [JSON](live_semantic_results_20261028_iter4_scanned.json) |
| Four-case cumulative snapshot | — | [JSON](live_semantic_results_20261028_cumulative4.json) |
| Five-case cumulative snapshot | — | [JSON](live_semantic_results_20261028_cumulative5.json) |
| Final frozen five-case run | [Final review](final_review_20261028.md) | [JSON](live_semantic_results_20261028_final.json) |
| Strength-ladder UI iteration | [Review](iteration_review_20261028_strength_ladder.md) | [Five-case JSON](live_semantic_results_20261028_strength_final.json) |
| Code-only timeline adjudication of the frozen five-case run | [Review](iteration_review_20261028_strength_ladder.md) | [Derived JSON](deterministic_timeline_adjudication_20261028.json) |
| One-time two-CV strength-ladder demo | [Review](iteration_review_20261028_strength_ladder.md) | [Sanitized live result](live_strength_ladder_demo_20261028.json) |
| Targeted scanned-CV verifier run with retained rejected quotes | [Review](iteration_review_20261028_strength_ladder.md) | [Live result and rejection details](live_semantic_results_20261028_scanned_quote_audit.json) |
| Pre-fix one-case smoke failure (usage unavailable) | — | [Failure record](live_semantic_results_20261028_strength_smoke_failure.json) |
| All four follow-up batches combined | — | [All-runs JSON](live_semantic_results_20261028_all_runs.json) |
| Product demand scan and local recruiter-workflow simulation | [Product signal + simulation report](product_signal_workflow_simulation_20261028.md) | Public evidence, saved Muse results, and a zero-call five-CV mock batch |
| Production workflow competitor benchmark and EvidenceTrail gap map | [Workflow benchmark and gap map](production_workflow_benchmark_20261028.md) | Competitor patterns, current repo gaps, KUL-first build order, and product-market proof criteria |
| EvidenceTrail × KUL recruiter workflow pitch | [Pitch draft](recruiter_workflow_pitch_20261028.md) | Workflow, implemented evidence features, carefully scoped Muse results, and pilot proof plan |
| Recruiter time study | [Run sheet](time_study_run_sheet_20261028.md) | No-Muse protocol and blank results form; the fixture exists, but its live results and three human reviewers are still pending |
| Unified one-job, five-CV demo fixture | [Fixture JSON](unified_supplier_operations_demo_20261028.json), [rubric v1](unified_demo_rubric_v1.md), [five-CV PDF bundle](unified_demo_cvs_20261028.zip), [answer key](unified_demo_answer_key_v1.md) | Five fictional profiles, one GlobalFoundries role, prewritten expected labels, an image-only scan, and an app button that loads these same inputs without submitting them |
| Unified demo live-run attempt | [Attempt record](unified_demo_attempt_20261028.json) | One run was interrupted before a response; call count and provider debit are unknown; no retry was made |

Calibration inputs: [public-JD / fictional-CV case set](semantic_cases.json).
