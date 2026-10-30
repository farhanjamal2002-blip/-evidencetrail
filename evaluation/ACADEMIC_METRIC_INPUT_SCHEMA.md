# Research evaluation input contract

The input file \`evaluation/academic_metric_inputs.jsonl\` is intentionally empty until a real reproducible experiment has produced predictions and reference annotations. The evaluator outputs **NO ACADEMIC BENCHMARK DATA YET** in that state.

**One JSON object per document × requirement**, no applicant names, email, phone numbers, or raw CV content:

\`\`\`json
{
  "document_id": "anonymous-case-001",
  "criterion_id": "R1",
  "domain": "fictional_cv",
  "reference_provenance": "independent_blinded",
  "gold_status": "supported",
  "predicted_status": "review_required",
  "source_verified": false,
  "gold_pages": [1],
  "cited_pages": [],
  "gold_span_ids": ["span-5"],
  "pred_span_ids": [],
  "semantic_attribution": "not_assessed",
  "attribution_human_reviewed": false
}
\`\`\`

The JSON above illustrates schema only, **not a published result**. Do not add it as a scored benchmark row.

Allowed domains: \`fictional_cv\`, \`contract_nli_transfer\`, \`qasper_transfer\`, \`docvqa_transfer\`, \`other_document_transfer\`. Allowed provenance: \`author_labelled_synthetic\`, \`independent_blinded\`, \`published_external_gold\`. Source claims require independent page checks and semantic annotation (not automatic lexical quote matching).

\`gold_status\` permits \`supported\`, \`not_found\`, \`conflicting\`, \`refuted\`. The prediction additionally permits \`review_required\`. These have *different* meanings: \`not_found\` is a document evidence outcome; \`review_required\` is a human-review decision; \`refuted\` is claim contradiction (ContractNLI) and NOT internal inconsistent CV statements. Do not manually coerce refuted to conflicting to improve accuracy.

\`gold_pages\` and \`cited_pages\` are distinct positive PDF page integers. \`gold_span_ids\` and \`pred_span_ids\` are canonical IDs *from the same source segmentation scheme*, not textual substrings invented after viewing the prediction. If a dataset doesn't provide spans, leave both arrays empty and don't claim span precision.

\`semantic_attribution\` can be \`supported\`, \`unsupported\`, \`ambiguous\`, \`not_assessed\`. The first two require actual human evaluation and \`attribution_human_reviewed=true\`, along with a cited page. No AIS claims from automated quotation matches.

Run:

\`\`\`bash
python -m unittest tests.test_academic_evidence_metrics -v
python scripts/academic_evidence_metrics.py evaluation/academic_metric_inputs.jsonl
\`\`\`

The report is JSON under \`artifacts/academic-methods/metric_report.json\`. No model request is made by this evaluator, no user files are transmitted, and results cannot be pooled across domains or gold provenance. Human reviewer timing is separately evaluated by \`scripts/evaluate_reviewer_pilot.py\` on real (currently uncollected) pilot rows.

**Publication caveats:** version the external licensed dataset and test split; do not copy 2021 paper benchmark scores as EvidenceTrail results. No confidence interval is calculated across correlated CV criteria. 
