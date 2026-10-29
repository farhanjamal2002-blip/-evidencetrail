# EvidenceTrail semantic evaluation — October 29, 2026

## Executive summary: two different experiments

### Controlled deterministic guard simulation — 1,000 scenarios

- **10 professional domains × 10 hand-specified evidence/error families × 10 phrasing variants**.
- Input "Muse proposals" were **deliberately injected model-shaped labels**, *not* 1,000 real model responses. A test author predeclared expected outcomes, then our actual \`enforce_evidence_status_invariants()\` and \`clarify_verified_findings()\` code processed those labels.
- **500/1,000** of injected raw labels matched the reference, versus **900/1,000** after production guards.
- **100/1,000** known missed-direct cases remained missed: the current verifier cannot discover qualifications absent from the model proposal.
- Source strings for every synthetic citation were checked to exist in the controlled CV text, but this is **not** a benchmark of real PyMuPDF/OCR grounding, fairness, or human applicant review.
- We initially found a **bad timeline oracle** that asserted internal date conflict without actually supplying opposing dates. We replaced it with two incompatible employment-history passages and added a preflight source-oracle audit, not a post-hoc change to real model outputs.
- Final independent fixture-consistency scan: **1,000 cases, 0 flagged gold-label construction defects** under the scripted checks. This does NOT constitute independent human annotation.
- Timing from GitHub hosted runner on final repaired run: policy-only median **0.0271 milliseconds**, p95 **0.0366 milliseconds**, excluding model calls, PDF extraction, OCR, browser, and network.
- [Final repaired offline suite](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40922464971) and \`artifacts/semantic-benchmark/policy_1000.json\`, \`oracle_quality.json\`.

### Genuine Muse Spark 1.3 checks — 10 valid fictional cases

- [Original genuine 10-CV Meta probe](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40921846457) made 10 authenticated, receipt-backed calls and four independent *requests* that blindly asked the same Muse model family to assess preselected cases. **All 14 API requests were pre-capped and there were no retries.**
- The original probe compared 9/10 cases correctly in both raw and verified labels *against its stored references*. But one reference was **invalid**: it claimed an independent chronology contradiction without placing contradictory dates in that PDF. That case is removed from the valid score, not counted as evidence of a product error or improvement.
- Among the original **nine valid cases**, raw Muse matched **8/9**, EvidenceTrail matched **9/9**. One genuine Muse single-scope \`conflicting\` proposal was corrected to \`not_found\` by the deterministic local semantic layer.
- [Fresh one-call replacement with actual opposing dates](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40922570145): Muse raw \`conflicting\`, final \`conflicting\`, **two independently grounded source quotations**, real provider ID. The source corpus contains incompatible references to the same role and employer.
- Combined **10 valid live fictional cases**: raw Meta **9/10**, EvidenceTrail **10/10** against references locked before each call.
- The four separate blind Muse calls matched 4/4 predeclared references, but the same model family adjudicated them; therefore they are **correlated model cross-checks, NOT independent human judges**.
- Original live pilot median **2.11 seconds/CV** on its ten first-pass requests, not the median for the separate timeline replacement and not a throughput SLA.
- Genuine live probes consumed **15 provider requests total across two runs**: ten primary calls + four blind adjudications + one repaired case. No new calls are necessary for the saved judge demo.

## The next accuracy bottleneck

All **100 synthetic missed-direct cases** remain false negatives even after post-processing. That is a real *architectural* weakness: deterministic post-verification can demote an unsupported positive, but cannot invent a correctly grounded supporting quotation that the first Muse pass didn't retrieve. The solution must be tested, not assumed:

1. Add varied, **unseen** fictional CVs with hidden adjudicator references and full job descriptions, not a thousand more paraphrases of ten templates.
2. Measure evidence-retrieval recall and false-positive rates by role and criterion (direct, related, absent, genuine internal discrepancy). Require source-grounded quotations and accepted PDF pages.
3. A/B one focused Muse prompt change with the **same unchanged source-verification code**, identical samples and strict call budgets. Look especially for missed directly stated qualifications in unconventional wording.
4. Use *selective* second-pass Muse review only for genuinely ambiguous cases where measured accuracy gain justifies added latency and credits; never turn the second opinion into the gold answer.
5. Only merge prompt or rule changes when independent, reserved test cases show higher recall **without an unacceptable increase in falsely supported qualifications**.
6. Test fairness and resume-style robustness by submitting semantically equivalent achievements with different writing styles and assessing whether the final evidence status changes.

## Product positioning and commercial claims

EvidenceTrail's strongest technical distinction is independently inspectable **original model proposal → verified PDF evidence → explicit local correction → human review**. The frontend now has source-backed click-to-highlight, an evidence matrix and an audit drawer. It does **not** support claiming that reviewers save a measured number of minutes, or that the demo is an enterprise-ready ATS. Those require separate human usability and production validation.

The public Render demonstration is intentionally based on saved genuine Muse receipts, to avoid exposing paid anonymous inference. This evaluation work is deliberately isolated from the public server and cannot leak real candidate data.

Meta's current Model API documentation documents **hosted Muse Spark inference**. It separately documents post-training for open-weight **Muse Spark Open** and **Muse Glimmer**. These are different deployment and cost choices. Do not claim hosted Muse Spark 1.3 is directly fine-tunable through the currently documented inference API.
