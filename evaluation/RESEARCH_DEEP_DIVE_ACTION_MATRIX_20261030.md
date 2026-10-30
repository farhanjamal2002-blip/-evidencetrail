# EvidenceTrail — deeper research findings and next experiments (October 30, 2026)

**Evidence status:** literature review and experiment pre-registration only. The papers' results are NOT EvidenceTrail's results. No academic benchmark, independent recruiter experiment or new Muse call was performed in creating this document. Existing public release SHA `8489e45ae0f87d8421562618bda556c31911372b` remains frozen.

## The single highest-value discovery: verified quotation ≠ justified inference

A page check proves the displayed words are genuinely on the supplied CV, but does **not** establish that those words entail the job requirement **about the applicant**. A second human-reviewed *semantic attribution* layer is necessary before claiming semantic reliability.

| Priority | Published research (verified publisher source) | What the researchers test | EvidenceTrail-specific experimental intervention | Failure metric |
|---|---|---|---|---|
| P0 | **CogniBench (ACL 2025)** https://aclanthology.org/2025.acl-long.1046/ | Source-supported rephrasings vs unsupported *cognitive inferences* | Annotate whether the verified quotation entails (a) *who* performed the task, (b) *what* action, and (c) relevant scope; create second-tier reviewer warning, never a silent automatic rejection | citation-is-real-but-inference-unsupported count |
| P0 | **RefChecker (EMNLP 2024)** https://aclanthology.org/2024.emnlp-main.395/ | Structured claim-triplet extraction and source checking | Decompose a requirement into subject/action/object and compare against the actor/action/object of the accepted source quote | wrong-person, wrong-action, wrong-object false-support counts |
| P0 | **ALCE (EMNLP 2023)** https://aclanthology.org/2023.emnlp-main.398/ | Citation support quality separate from answer correctness | Require independently inspected *sufficient* evidence, and distinguish partial from sufficient support across two source passages | evidence sufficiency/partial citation and source recall |
| P0 | **CiteVQA (arXiv 2026, v2)** https://arxiv.org/abs/2605.12882 | Strict Attributed Accuracy jointly requires a correct answer and relevant, spatially aligned cited region | Add a strict supported-finding gate: correct status + all gold page/span IDs cited + deterministic source verification + blinded human attribution judged supportive | joint answer-and-source attribution pass rate; report answer-only and citation-only alongside it |
| P0 | **Buçinca et al. (CSCW 2021)** https://www.iis.seas.harvard.edu/papers/2021/bucinca2021trust.shtml | AI overreliance; forcing a person to reason before seeing/accepting AI can improve appropriate use, often with usability cost | Compare immediate AI-result visibility against original-source-first inspection, **in an exploratory controlled reviewer pilot** | wrong-AI-follow rate, reviewer errors, task time, satisfaction |
| P0 | **Bansal et al. (CHI 2021)** https://doi.org/10.1145/3411764.3445717 | Complementary human–AI team performance; explanations can increase reliance even on incorrect AI outputs | Compare human-only, human+AI, human+AI+explicit source checks; separate correction of incorrect AI from acceptance of correct AI | complementary accuracy and conditional agreement with wrong AI |
| P1 | **Lost in the Middle (TACL 2024)** https://aclanthology.org/2024.tacl-1.9/ | Evidence position affects long-context retrieval accuracy | Copy the exact same 1–2 source statements to first, middle and last page while holding job requirement and facts constant | max per-position change in supported/missed-support and citation recall |
| P1 | **FActScore (EMNLP 2023)** https://aclanthology.org/2023.emnlp-main.741/ | Atomic claims and evidence-supported factuality | Split CV inference claims into indivisible propositions and audit each separately | percent of atomic document claims with *semantic* support (not public candidate score) |
| P1 | **RAGChecker (NeurIPS 2024)** https://www.amazon.science/publications/ragchecker-a-fine-grained-framework-for-diagnosing-retrieval-augmented-generation | Retrieval and generation errors diagnosed independently | Separate pipeline failure taxonomy: OCR/extraction vs source retrieval vs Muse interpretation vs quote verifier vs human review | error count and denominator by stage; don't confuse 5/5 labels with 5/5 retrieval |
| P1 | **TRUE (NAACL 2022)** https://aclanthology.org/2022.naacl-main.287/ | Example-level factual-consistency metrics over multiple data sources | Evaluate individual criterion errors with blind reference, not one aggregate per-20-CV accuracy headline | per-criterion confusion and disagreements across source/semantic gold |
| P1 | **SciFact (EMNLP 2020)** https://aclanthology.org/2020.emnlp-main.609/ | SUPPORT / REFUTE with explicit source rationale | Independently annotate refutation apart from internal CV contradiction; measure multi-passage rationale retrieval | refuted-as-conflicting mistakes, rationale evidence recall |
| P1 | **Human and LLM-Based Resume Matching: An Observational Study (NAACL 2025)** https://aclanthology.org/2025.findings-naacl.270/ | 736 actual resumes; comparison of human and AI assessments in hiring | Reproduce paired-blind disagreements on permitted **fictional**, not private real applicants; quantify AI/human disagreement and false-sufficiency, **without ranking applicants** | disagreement distribution, human ambiguity and error counts |
| P2 | **Small Changes, Large Consequences (AACL/IJCNLP 2025)** https://aclanthology.org/2025.ijcnlp-long.143/ | Sensitive-attribute perturbations expose brittle hiring AI summary and retrieval behavior | Separately test whether changing *job-irrelevant synthetic identity tokens* modifies extracted evidence or requirement labels with identical qualifications; do not infer actual protected traits or announce compliance | counterfactual evidence-status invariance (synthetic robustness only) |
| P2 | **PopResume (EMNLP 2026)** https://aclanthology.org/2026.emnlp-main.2/ | Causal fairness on model-based resume scores with population structure | Study their audit *limitations* to avoid claiming that no-score UI automatically establishes hiring fairness. Their path-specific-effect estimands don't directly apply to our no-ranking workflow | privacy-preserving differential annotation quality research plan; do not report PSE without a suitable design |
| P2 | **DocILE (ICDAR 2023)** https://docile.rossum.ai/ | Layout/document extraction localization with many classes | Build a held-out multi-column/scanned CV source-location challenge using our own licensed fictional documents | text recall and box/page localization separate from model answer |
| P2 | **AI Self-preferencing in Algorithmic Hiring (EAAMO 2025)** https://doi.org/10.1145/3757887.3767676 | LLM evaluators may favor familiar model-generated resumes | Avoid treating polished AI-style prose as direct proof of personal job ownership; test invariant evidence for equal facts differently phrased | author-style invariance in extraction and source interpretation |

**Not a model implementation instruction:** some papers propose specialized detector models or generators. Merely using their metric or paper is not reproducing their neural models. We should disclose that our task-specific metric is **inspired by** the paper, rather than claiming we ran CogniBench/FActScore/RefChecker. Publication source/abstract and copyrights remain with their original authors.

## Minimum viable research before the hackathon: two affordable experiments

### Experiment 1 — Truthful adversarial source-sufficiency audit (P0)
**Predetermined corpus:** 12 paired *fictional* CV-claim challenges in `evaluation/RESEARCH_METAMORPHIC_PAIRS.json`. Each pair has a single stated change. Hold the job requirement fixed, label *expected invariance or expected change* before running a model. Compare raw Muse interpretation, final EvidenceTrail interpretation, cited page and sufficiency of the cited quote. To make a genuine model claim, record authentic Meta IDs and report all failures; mock simulation scores do not qualify. For 12 pairs, cost can be substantial; a smaller capped sample may be run, clearly labelled exploratory.

**Independent semantics:** require two blind human raters to decide whether a real quotation *sufficiently establishes the specific applicant's job activity*. The model and one author cannot adjudicate its own correctness. Show disagreements.

**Position-specific test:** one positive source moved without editing the claim across first/middle/last CV page. No label or quote-content changes should be presumed an actual model result until real independent analysis happens.

### Experiment 2 — Human-AI reliance, not prettier explanation (P0)
Counterbalance an ordinary PDF-first review with an AI-assisted view for distinct but matched fictional CVs; optionally introduce a third arm where a reviewer must open the PDF before recording a conclusion. Record timestamps, evidence corrections, missed support, inappropriate reliance on incorrect AI suggestions, and reviewer burden. **Never manufacture participants or observed time savings**; when there are no volunteers the claim is *methodology designed*, not *product validated*.

## Candidate architecture implication (NOT a request to merge into RC1)

Separate three distinct badges/receipts:

1. **Source exists at page N:** objective deterministic verification against submitted text/OCR.
2. **Citation semantically supports the exact requirement:** needs separately tested entailment/actor verification and/or human annotation. A citation about a manager cannot prove applicant ownership. Report partial/unclear, not a confidence percentage.
3. **Document statement is true outside the CV:** unknown without real-world independent verification. EvidenceTrail must NOT claim it verified the CV's factual truth.

If the research reveals a useful deterministic attribution warning, initially run it in **shadow/advisory-only** mode and measure false alarms; don't demote candidates or replace verified source findings automatically.

## Reporting/provenance obligations

- Pre-commit corpus hashes, full source/license provenance, split by whole document, author labels vs independent blind labels, exact model version and release source SHA.
- Distinguish gold `refuted` from internally `conflicting`, and `review_required` from no documented evidence.
- Report supported, false supported, missed supported, human-review frequency, source-page precision/recall, semantic citation sufficiency and failure-stage error counts with actual denominators.
- Repeated prompts or formatting changes are **multiple comparisons**: pre-register and report all, don't select only successful variants.
- Applicant demographic/identity audits are sensitive high-stakes research and **cannot** establish discrimination-free employment outcomes through a handful of fictional perturbations.
- Stop research early rather than jeopardize voiceover, accepted track verification and on-time official portal submission. The frozen public judge demo stays on tested RC1 and native Meta vision remains disabled after the single recorded grounding regression.

## Paper source checking and rights

This document links only publication or institutional landing pages and summarizes public abstracts, rather than copying copyrighted paper text or rehosting PDF/benchmark datasets. Do not automatically ingest controlled DocVQA/DocILE images or real resumes. Verify repository licenses and accepted-use terms before using paper-related code or datasets. All actual observed EvidenceTrail results must come from its own saved receipts or reproducible evaluation artifacts.
