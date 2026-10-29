# Fresh unseen fictional-CV semantic holdout — October 29, 2026

## Why this evaluation exists

After improving the multi-quote conflict safeguard on a first twenty-CV development corpus, EvidenceTrail correctly matched **80/80** hand-authored criterion references on that *in-sample* test. That score could not establish generalization, because the failures on those same examples influenced the fix.

We therefore authored a **separate holdout after freezing the rule**, with new job categories and new CV writing. The test locked its expected statuses and PDF fingerprints before making any genuine Meta request. We did not alter the verifier or change labels after seeing the holdout results.

## Genuine Meta Muse Spark 1.3 results

[Eight real Meta analyses and source/label preflight](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40927866580)

| Measure | Outcome |
|---|---:|
| New fictional two-page CVs | 8 |
| Job domains absent from first development corpus | 4 |
| Predeclared job criterion decisions | 32 |
| Genuine Meta inference requests | 8 (one per CV, zero retries) |
| Authentic provider receipts | 8 |
| Raw Meta reference matches | **18/32** |
| Source-verified EvidenceTrail reference matches | **32/32** |
| Correctly preserved direct evidence | 12/12 |
| Correctly preserved genuine competing CV claims | 4/4 |
| Correctly classified unproven duties | 16/16 |
| Final incorrectly \`supported\` | 0 |
| Final missed direct support | 0 |
| Final missed source contradictions | 0 |
| Median end-to-end latency in this eight-CV run | **4.56 seconds per CV** |

Original raw Muse confusion: 4 correct \`conflicting\`, 14 incorrect \`conflicting\` instead of \`not_found\`, 2 correct \`not_found\`, 12 correct \`supported\`. The deterministic verifier corrected all 14 unproven duties while retaining the four genuine conflicts.

### The four *new* test domains

- Pharmaceutical distribution: cold-chain investigations, GDP audits, ERP recall batch traceability and CAPA approvals.
- Renewable power: grid-tied inverter commissioning, SCADA configuration, lockout-tagout approval and EPC contract change negotiation.
- Legal operations: arbitration submissions, e-discovery privilege review, licensing negotiations and court e-filing.
- Education technology: Moodle publishing, curriculum assessments, individualized student education plans and exam moderation audits.

The eight fictional documents deliberately contrast actual personal ownership with related work, training-only keyword exposure, and genuinely incompatible statements in distinct CV sections. Every reference positive and incompatible pair has hand-authored source anchors, and the full PDFs and 32 reference labels were prevalidated before inference.

## Interpretation and limits

**This is a successful small, separate holdout**, not a claim of perfect product accuracy in general. The statuses were specified by the same development team writing the fictional CVs; they were not independently annotated by hiring professionals. The cases were authored after we knew the types of mistakes the product had made. The sample remains small and focused on a few failure classes. It's possible to perform much worse on messy real resumes, unfamiliar language, incomplete scanned CVs, or more ambiguous domain qualifications.

The verifier did NOT re-query Muse and did NOT use the expected reference labels while processing any CV. The audit retains the source model response IDs, raw model statuses, exact locally checked PDF evidence and final status. No rankings, candidate decisions or hiring recommendations were generated.

This is an evaluation of CV-document evidence semantics under controlled conditions, not fairness certification, commercial readiness, recruiter productivity savings, or validation that any CV claim is true in the world.

## What remains to win technical credibility

1. An externally annotated dataset with qualified recruiters or subject-matter reviewers, independently labeling multiple plausible readings.
2. Multilingual, OCR and unstructured real-world writing-style robustness under privacy-safe consent.
3. Human usability study comparing evidence misses and time to confident review against manual and incumbent-tool workflows.
4. Controlled paired prompt variants and source-based errors before changing the model prompt or considering open-weight post-training.

Previous same-corpus development tests:
- [Baseline 68/80](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40924546755)
- [Corrected 80/80](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40926435081)

The latest public demo remains a **saved genuine Muse replay**, not anonymous new inference. It runs without spending further Meta credits.
