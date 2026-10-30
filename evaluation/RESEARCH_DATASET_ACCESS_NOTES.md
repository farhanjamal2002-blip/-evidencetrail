# Practical access notes for external research benchmarks (October 30, 2026)

**Purpose:** avoid inaccessible, wrongly licensed, or label-less datasets in a rushed hackathon study. Nothing on this page represents a completed EvidenceTrail model evaluation.

## Best immediate source: ContractNLI
- Official host and download conditions: https://stanfordnlp.github.io/contract-nli/
- Origin: Koreeda & Manning, EMNLP Findings 2021.
- 607 non-disclosure agreements; 17 recurring hypotheses. JSON documents have annotated `text`, `spans`, `annotation_sets[].annotations[].choice` in the official description. Exact field keys are specified on the publisher site. Labels: `Entailment`, `Contradiction`, `NotMentioned`, with evidence spans for the first two categories.
- Publisher states **CC BY 4.0** and an additional *terms and conditions of use* section: clicking the official download indicates acceptance. Do **not** automatically fetch on the entrant's behalf until terms are reviewed and accepted. Include attribution and licensing.
- For our product: use a **separate external transfer study**; `Contradiction` should map to `refuted` for the test adapter, **not** automatically to EvidenceTrail's conflicting-within-CV label. Create a document-level split and preserve the original span-ID scheme for page/span metrics.
- Quality gate: first verify canonical release, exact split, original license and document hash; run a tiny exploration on correctly mapped labels, then decide whether a capped real Muse run is worth spending credits.

## Alternative open-source workflow: SciFact
- Original published paper and task: https://aclanthology.org/2020.emnlp-main.609/
- Official repository and documented download: https://github.com/allenai/scifact
- Crucial limitation: the repository explicitly says `claims_train.jsonl` and `claims_dev.jsonl` have public labels but `claims_test.jsonl` is **unlabeled**. Do not run 'test accuracy' against missing test gold or backfill labels from your own predictions.
- Strong use: source rationale and claim-refutation sensitivity **on published labeled development records**, disclosed as **development-split transfer**, not unseen final test performance. Confirm dataset license and source-document redistribution rights before downloading or publishing.

## Expensive or gated datasets
- DocVQA https://site.docvqa.org/datasets has access/usage conditions and a portal: no bulk download or republication before confirming rights. Our source-image geometry proof should use our **original fictional scanned PDFs** first.
- DocILE https://docile.rossum.ai/ requires a dataset-access request and includes business documents. Do not assert it is a no-sign-up unrestricted dataset.
- CogniBench code/data https://github.com/FUTUREEEEEE/CogniBench has an available public repository per its ACL paper; **separate code and dataset licenses must be checked** before reusing any of its assets, and its labels may not directly apply to CV ownership.
- Real-world résumé data from published hiring research often comes with privacy and consent constraints: do not seek, ingest, republish or send it to Meta as a shortcut.

## Recommended research sequence
1. **Now (zero cost):** freeze 12 author-generated fictional metamorphic pairs and validate their testing protocol and result scorer. Both are in this draft branch; they are not yet genuine model results.
2. **Next (cheap only with a clear reason):** compare perhaps 4 prespecified genuinely novel pairs with one capped Meta request per variant, preserving all provider receipts/failures and predeclared reference labels. Do not trigger automatically; the submission deadline takes priority.
3. **Next (requires human work):** two independent blind annotators rate whether exact source quotes semantically support applicant-owned work. Not the same as PDF quote existence.
4. **External transfer:** accept approved ContractNLI data license, align entailment/refutation labels carefully, and compare against published reference. Do not mix its accuracy numbers with fictional CV results.
5. **Publish only verified findings** along with coverage, failure counts, source attribution, version hashes, and explicit sample sizes; independent reviewer-time study remains a separate experiment.

## Results we explicitly do not yet have
- No ContractNLI, SciFact, CogniBench, DocVQA, DocILE or RAGChecker empirical EvidenceTrail score.
- No observed performance on the new 12 paired challenges.
- No independently annotated job-ownership gold set and no new production hiring dataset.
- No randomized human–AI overreliance pilot with real participants.
- No claim that copying an academic paper's method reproduces the original authors' model.
