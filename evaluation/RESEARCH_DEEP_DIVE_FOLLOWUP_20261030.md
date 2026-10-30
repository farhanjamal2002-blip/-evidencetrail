# EvidenceTrail research deep-dive follow-up — new tests, not new claims

**Date:** 2026-10-30  
**Status:** literature-to-test proposal only. No new EvidenceTrail model or human-participant results were collected for this document. The fictional tests below are proposed; they must be frozen and labelled before any model run. This supplements `RESEARCH_DEEP_DIVE_ACTION_MATRIX_20261030.md` and does not change the frozen judge release.

## What the newer research adds

### 1. Test whether the document question is answerable before answering

**Zhou et al., “Beyond Blind Compliance: Benchmarking Task Verification in OCR Reasoning,” EMNLP 2026.** VeriOCRBench separates invalid OCR tasks into visual, contextual, factual, and logical problems, then includes clean controls to measure over-refusal. Its study reports that OCR models can answer invalid tasks and can also over-refuse after prompts are changed. [ACL Anthology](https://aclanthology.org/2026.emnlp-main.959/)

**EvidenceTrail adaptation:** add fictional CV cases where the requirement cannot safely be resolved from the supplied document: clipped or illegible text, a missing actor, an ambiguous pronoun, an OCR page number that cannot be located, and an internally inconsistent timeline. Pair each with a readable, clearly supported control. The expected action is to preserve the existing evidence label where possible and request review for the unresolved part; do not silently turn illegible or missing text into `not_found`.

**Metrics:** unsupported conclusion rate on invalid cases; correct failure-cause label; false `review_required` rate on readable controls; source-page/quote verification by legibility condition. Keep task validity, evidence status, and human-review action as separate fields.

### 2. Score OCR by downstream evidence retrieval, not just character accuracy

**Sun et al., “When Good OCR Is Not Enough: Benchmarking OCR Robustness for Retrieval-Augmented Generation,” ACL 2026 Industry Track.** Across 11 challenging document types, the authors report that conventional character error rates can look good while structural or semantic OCR errors still damage retrieval and downstream answers. They separate retrieval-side and generation-side effects. [ACL Anthology](https://aclanthology.org/2026.acl-industry.60/)

**Gao et al., “StruNRAG: Evaluation of OCR-Induced Structural Noise on RAG Robustness,” Findings of ACL 2026.** This work injects line insertion, paragraph interleaving, and line interleaving, and finds that structural noise can hurt retrieval even when a generator tolerates some local noise. [ACL Anthology](https://aclanthology.org/2026.findings-acl.955/)

**EvidenceTrail adaptation:** make a small, original, fictional CV set with the same text rendered as (a) clean text PDF, (b) two-column page with reading-order ambiguity, (c) scanned page, (d) line insertion, and (e) paragraph/column interleaving. Freeze the same requirement and gold passage across variants. Measure extraction, retrieval, final label, exact quote verification, and page localization separately. CER/WER are diagnostics only; they are not the headline reliability metric.

**Metrics:** gold-span retrieval recall; source-page precision/recall; unsupported-support and missed-support rates; stage of first failure; OCR character error as a secondary covariate. Include clean positive controls so a system that abstains on every scan cannot look robust.

### 3. Test whether conflicting passages are preserved instead of selectively cited

**Sneiderman et al., “The Citation-Faithfulness Illusion: Measuring Whether Grounded Answers Preserve Source Disagreement,” GroundLM 2026 workshop.** The paper identifies “disagreement collapse”: a system can cite a passage that supports its answer while omitting other retrieved evidence that materially disagrees. It proposes separate disagreement-recall and attribution-precision measures and a matched-pair, two-judge protocol. The paper presents an evaluation instrument and frozen design, not EvidenceTrail results. [ACL Anthology](https://aclanthology.org/2026.groundlm-1.17/)

**EvidenceTrail adaptation:** for an internally conflicting fictional CV, require the output to retain both first-person passages, their locations, and the fact that they disagree. Add a matched consistent control with similar wording. Do not import the paper’s source-credibility construct literally: two CV passages are one document’s inconsistent claims, not independent credible sources.

**Metrics:** conflicting-passage recall; attribution precision for each passage; rate of one-sided `supported` output when the other passage contradicts it; false-conflict rate on consistent controls. Keep internal CV conflict distinct from external fact-checking and from ContractNLI’s `refuted` label.

### 4. Treat uncertainty as an action that must survive distribution shift

**Wang et al., “SConU: Selective Conformal Uncertainty in Large Language Models,” ACL 2025.** The paper addresses the exchangeability problem: a calibration set can fail to control errors when test examples are outliers relative to that set. [ACL Anthology](https://aclanthology.org/2025.acl-long.934/)

**Cocchieri et al., “LLMs (Almost) Never Abstain Under Medical Uncertainty,” ACL 2026.** This study makes abstention an explicit option and evaluates over-commitment under missing or uncertain information. Medical results do not transfer directly to hiring documents, but the experimental lesson is relevant: an evaluator needs both uncertain/invalid cases and answerable controls. [ACL Anthology](https://aclanthology.org/2026.acl-long.1365/)

**EvidenceTrail adaptation:** do not add a confidence percentage or claim a conformal guarantee from free-form Muse text. First test the existing `review_required`/manual-review behavior across a held-out set that differs by role family, language, layout, and scan quality. If a calibrated numeric signal is ever introduced, it needs a separately held calibration set, a frozen threshold-selection procedure, a shift/outlier check, and evaluation on untouched documents.

**Metrics:** false-support risk among answered cases; supported-evidence miss rate; review-required coverage; error and review rates by prespecified document condition; performance on deliberately shifted conditions. Report denominators and every condition separately. A high abstention rate alone is not good calibration.

### 5. Measure reviewer process, not whether the explanation looks persuasive

**“Cognitive Forcing for Better Decision-Making: Reducing Overreliance on AI Systems Through Partial Explanations,” PACM HCI (2025).** The authors report that partial explanations reduced overreliance on incorrect AI suggestions relative to a baseline, though they did not match full explanations; effects also depended on task difficulty. [ACM DOI](https://doi.org/10.1145/3710946) · [Aalborg University research record](https://vbn.aau.dk/en/publications/cognitive-forcing-for-better-decision-making-reducing-overrelianc/)

**EvidenceTrail adaptation:** compare (A) immediate AI evidence summary, (B) reviewer first records an initial judgment and source quote before seeing the AI result, and (C) reviewer sees AI plus a direct link to the cited CV page and must confirm or reject the quote. Counterbalance matched fictional cases and include both easy and subtle AI errors. This is a small exploratory usability pilot, not hiring-effectiveness validation.

**Metrics:** wrong-AI-follow rate conditional on an incorrect AI result; correction rate after opening the original page; correct-AI acceptance; reviewer false-support and missed-support errors; time and completion; split by easy versus subtle errors. Show participant and case counts. Do not describe a tiny pilot as causal or representative.

## Concrete implementation sequence

1. Add the proposed answerability/OCR, structure-noise, conflict-preservation, and distribution-shift cases to a separate fictional test manifest. Keep their IDs, source files, expected labels, and perturbation rules frozen before model calls.
2. For the M02/M07 replay, use only the frozen author-written labels. Make their provenance explicit; do not call them independent gold. No human ratings are collected.
3. Run extraction and source-location checks without a model first. Then run a single predeclared model configuration on all variants, retaining failures and authentic provider receipts. Do not retry only failed or surprising cases.
4. Score each pipeline stage with its own numerator and denominator. Keep author-labelled synthetic, independently reviewed fictional, and published-dataset transfer results separate.
5. Only after the offline tests pass integrity checks, run the small reviewer pilot. Do not change the frozen judge demo, add a candidate score, or claim hiring accuracy/fairness from these transfer tests.

## Claim boundary

These papers offer methods and failure hypotheses, not proof that EvidenceTrail is reliable. The direct next engineering target is to catch unsupported applicant attribution, OCR-induced retrieval misses, omitted contradictory passages, and overconfident answers on unreadable inputs—while checking that clear evidence still gets through. Until the experiments above have been run with recorded inputs and independent labels, report this as a research plan only.
