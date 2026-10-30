# EvidenceTrail research-replication protocol — evidence-first, not score-first

**Further paper-by-paper engineering plan:** [RESEARCH_DEEP_DIVE_ACTION_MATRIX_20261030.md](RESEARCH_DEEP_DIVE_ACTION_MATRIX_20261030.md), including CogniBench, RefChecker, ALCE, FActScore, RAGChecker, human overreliance, and peer-reviewed hiring research. The separately authored [12 CV perturbation pairs](RESEARCH_METAMORPHIC_PAIRS.json) have a no-cost, provenance-enforcing [metric runner](../scripts/metamorphic_research_metrics.py), but no real Muse predictions yet.

**Status:** PRE-REGISTERED EXPERIMENT DESIGN. No academic benchmark has yet been run against EvidenceTrail. This document adapts *methods* from named research papers; it does not copy their data/results into our own claims, reproduce their text, or imply the original authors endorse EvidenceTrail.

**Goal:** determine whether a recruiting-document evidence reviewer (a) identifies actually supported claims, (b) avoids accepting claims about *other* people, (c) points to the correct source, (d) preserves meaningful uncertainty without missing legitimate documented evidence, and (e) helps a human reviewer rather than inducing overreliance.

## Research that maps directly to our gaps

| Research / link | Originally established | Adaptation for EvidenceTrail | Non-negotiable caveat |
|---|---|---|---|
| Koreeda & Manning, **ContractNLI**, EMNLP 2021, https://aclanthology.org/2021.findings-emnlp.164/ | 607 contracts, hypothesis-level entailment, contradiction, not-mentioned and manually annotated evidence spans | Separate document inference from evidence-span retrieval; measure label confusion, source-span precision/recall | ContractNLI **contradiction** is *a claim refuted by a document*, NOT automatically EvidenceTrail's *conflicting CV passages*. Do not collapse them. Licensing CC BY 4.0 + download terms (https://stanfordnlp.github.io/contract-nli/) |
| Rashkin et al., **Attributable to Identified Sources (AIS)**, Computational Linguistics 2023, https://research.google/pubs/measuring-attribution-in-natural-language-generation-models/ | Two-stage human evaluation: understandable output then supported by identified source | Two independent reviewers judge (1) quotation/intelligibility and (2) whether it actually supports personal ownership of job requirement | A page match alone is NOT human semantic entailment or candidate truth |
| Mathew et al., **DocVQA**, WACV 2021, https://openaccess.thecvf.com/content/WACV2021/html/Mathew_DocVQA_A_Dataset_for_VQA_on_Document_Images_WACV_2021_paper.html | Images and text requiring visual layout, answers evaluated with OCR-tolerant text similarity | Compare OCR-only and explicitly consented vision on same held-out image docs; report ANLS and source-page success separately | DocVQA original images are **not freely redistributable**; the portal requires login/terms at https://site.docvqa.org/datasets. Don't automatically fetch or publish images without verifying rights |
| Dasigi et al., **QASPER**, NAACL 2021, https://aclanthology.org/2021.naacl-main.365/ | Long-document questions, annotated evidence, often multiple paragraphs | Score whether every necessary passage is found, not merely one keyword match | Research-paper comprehension is transfer, not CV hiring validity |
| Geifman & El-Yaniv, **SelectiveNet**, ICML 2019, https://proceedings.mlr.press/v97/geifman19a ; **AbstentionBench**, NeurIPS 2025, https://proceedings.neurips.cc/paper_files/paper/2025/hash/fb122bfc3f0127a94ded048b5b03496f-Abstract-Datasets_and_Benchmarks_Track.html | Quantify selective predictions, risk vs coverage, unanswerable questions | Separate explicit **review-required/abstained** decision from **not_found**. Report conditional error at fixed coverages only if a defensible ranking/uncertainty signal exists | No fake AI confidence score. If there is no calibrated uncertainty, report simple abstention and error counts, NOT AURC |
| Klingbeil, Grützner & Schreck, **Trust and reliance on AI**, Computers in Human Behavior 2024, https://doi.org/10.1016/j.chb.2024.108352 | Humans may follow bad AI advice over their own evidence | Randomize reviewers between manual source review and EvidenceTrail-assisted review; count wrong AI recommendations accepted, correct source interventions, elapsed time | An artificial short pilot is exploratory, not causal impact or production hiring performance |
| Friel, Belyi & Sanyal, **RAGBench**, 2024, https://arxiv.org/abs/2407.11005 | Actionable context relevance and grounded-generation assessment over 100k examples | Evaluate whether a quote is *relevant* and *sufficient* evidence in addition to byte/page presence | RAGBench is not a recruiter CV dataset; do not advertise it as hiring benchmark |

## Dataset plan (three independent tracks, never pooled into one accuracy number)

**Track A — public, pre-annotated cross-domain transfer**
1. Start with a **small, frozen, licensed test slice of ContractNLI**. Hold out entire documents; do not split hypotheses from one document between train/test. Use canonical published test split when available. Compare EvidenceTrail's model's raw inference to gold labels only through a carefully documented **four-way adapter**: entailment = supported; not-mentioned = not_found; contradiction = `explicitly_refuted` as a separate evaluation label; `conflicting_cv_statements` stays distinct. If the production schema cannot represent refutation, publish as *unsupported transfer mapping*, not a fictitious exact accuracy.
2. Use QASPER to measure multi-paragraph retrieval with paragraph-level gold spans, where data rights and dataset schema permit.
3. For DocVQA, use the **published metric** and a documented sample *only after terms/license are confirmed*. Use ANLS for OCR token matching but do **not** use approximate string overlap as proof that a hiring claim is semantically supported.
4. No public dataset contains everything about personal role ownership in CVs. Keep results separate by task/domain. Never upload CV PII or real applicant records to Meta merely for a benchmark.

**Track B — independently labelled hiring-specific holdout**
1. Construct 40–60 *fictional* new CVs across at least eight role families; include role-owner vs observer, teamwork, negation, supported paraphrase, timeline contradiction, two columns, OCR scans, duplicate resumes, irrelevant keyword stuffing, and adversarial instructions.
2. Have **two reviewers who did not author the CVs** independently annotate requirement/claim label and exact supporting passage(s), without seeing the model output or generated reference expectations.
3. Record disagreements separately. Resolve by an independent adjudicator where available; otherwise report the original disagreement distribution and exclude ambiguous examples from any 'gold' metric with full denominators disclosed.
4. Do not tune model prompts to the test set. Freeze prompt, model version, parser, OCR and source-verifier code SHA *before* evaluation; fixed source hashes, IDs and random seed. Keep observed failures in the data.
5. Distinguish: (i) no documented evidence `not_found`, (ii) explicitly refuted claim `refuted`, (iii) multiple inconsistent first-person assertions `conflicting`. Not found is *not* proof that the candidate lacks the ability.

**Track C — human recruiter usefulness / reliance**
1. Counterbalanced manual vs assisted review with different but balanced CVs. Reviewer sees a source PDF in *both* arms and does not see hidden QA labels; AI assistance arm can inspect and reject source citations.
2. Measure elapsed active seconds, false support, missed support, unjustified confidence/automation reliance, real source-navigation actions and task completion. Record order and case difficulty; keep failures, slow runs and incomplete tasks.
3. Do not publish a 30–50% time-saving figure unless it is actually observed with the raw task count and confidence/uncertainty limitations. A pilot with <4 reviewers is especially exploratory.

## Pre-registered metrics — no single headline score

**Per-example ground truth**
- `gold_status`: `supported`, `not_found`, `conflicting`, or `refuted` where a reference explicitly denies the proposed requirement. `refuted` must not be silently converted to `conflicting`.
- `predicted_status`: same label family or `review_required`. A review request is a *separate action*, not the document meaning of `not_found`.
- `source_verified`: did the deterministic engine re-find cited text/page? **Not** a semantic support label.
- `semantic_support_human`: did the cited passage actually entail the specific requirement about this applicant? Set only by blinded annotators; blank is unknown.
- `gold_pages`, `cited_pages`: positive, distinct page integers; no invented page coordinates. Missing citations are scored as missing rather than dropped.
- `case_group`: document/CV ID used to prevent leakage, group bootstrap or grouped splits.
- `model_receipt_id`: real provider response ID when available; saved replay is tagged as historical not newly spent inference.

**Main evidence metrics**
1. **False support rate:** predicted `supported` on gold other than supported / all gold other than supported (including refused/conflicting). This denominator makes false positives meaningful.
2. **Missed documented support rate:** any prediction other than supported on gold supported / all gold supported. Report `review_required` separately rather than hiding missed experience.
3. **Macro precision, recall, F1:** for *supported/not_found/conflicting* only on the comparable domain subset; no macro score across a dataset whose contradiction label lacks a production mapping. Include a full confusion matrix with missing/abstained predictions.
4. **Source-page precision and recall:** intersect cited gold pages, divided by all cited and all gold pages respectively. Score documents that have gold evidence but no predicted citations as zero recall. Page overlap does not imply quote-level exact grounding or semantic evidence.
5. **AIS-style semantic attribution:** share of citations independently judged sufficiently supportive among human-rated citations, with coverage and adjudicator disagreements. Do not count `source_verified` as AIS agreement.
6. **Unsupported/abstained coverage:** proportion `review_required` among all cases; false-support conditional rates for answered subset. With no calibrated confidence ranking, avoid false risk–coverage curves.
7. **Human pilot:** median and p90 *observed* active review seconds per arm, incorrect-evidence counts and completion. No invented effectiveness claim.

**Minimum reporting table**
- Dataset name/version/source/license, exact split/doc hash, N documents, N criteria, human annotation count, AI source+model version, raw vs corrected labels, false support, missed support, conflict detection, source-page precision/recall, human semantic attribution, abstention count, OCR subgroup, time/token/cost if measured, failure examples.
- Report per-domain; include confidence intervals only when sample size and sampling method allow meaningful interpretation, noting clustered CV/criteria dependence. Do not report 5/5 as population accuracy.

## Stop / release gates
- **No data provenance or unclear license:** do not run or publish those datasets.
- **Live Meta model score only if API actually called:** a fake/mock mode never qualifies.
- **Reference labels authored by the same team:** call *author-labelled synthetic*, not independent or real-world.
- **External validation regresses or meaningfully increases missed support:** do not merge heuristic changes into frozen demo.
- **Nearing hackathon deadline:** freeze, show methodology and honest partial results; avoid unvalidated academic feature creep.

## Academic attribution and honest presentation
Use hyperlinks and bibliography, mention *adapted protocols*, not replicated paper results unless replication is exact. ContractNLI data CC BY 4.0 requires attribution; DocVQA needs portal terms; don't imply affiliations or publish restricted data. Building an independent evaluation is research literacy—not plagiarism.
