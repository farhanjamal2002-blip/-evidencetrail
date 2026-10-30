# Muse Spark Optimization Plan for the Meta Hackathon
## EvidenceTrail research-to-demo memo — 30 October 2026

**Purpose:** find the best measured Muse configuration for the EvidenceTrail judge walkthrough. Optimize evidence-grounded criterion decisions, latency, and token use together; do not optimize a single accuracy number by adding unbounded retries.

**Scope:** research and experiment plan only. This memo makes no new Muse performance claim, changes no release code, and authorizes no model calls. Existing RC1 remains frozen at commit 8489e45ae0f87d8421562618bda556c31911372b. The completed 12-pair replay is the baseline; its fictional author-written references are not human ratings or a real-world benchmark.

## Executive recommendation

Prioritize these three controlled experiments:

1. **Prompt decision sequence:** compare the current long system prompt with one small, explicit actor–action–scope–object check before status assignment. The current prompt already includes many detailed rules and strict JSON Schema; published extraction work shows that a structured prompt can lose to a simpler question in a specific task. Test on our own frozen cases instead of assuming that more instructions improve results.
2. **Selective reasoning effort:** keep minimal effort as the default unless a predeclared, measurable risk trigger is present. Compare minimal with medium on a few hard fictional cases; use a second call only if the benefit on false-supported decisions justifies the extra tokens and latency. Muse returns no token log probabilities, so its categorical certainty field must not be treated as calibrated confidence.
3. **Scanned-page vision path:** compare OCR-text-only with OCR text plus the same page image on the two fictional scan cases. Muse Spark supports image input, but our optional vision path was previously disabled after a grounding regression. Keep local quote/page verification authoritative; image interpretation cannot authenticate the quote.

The product advantage for judges is a demonstrable division of work: Muse interprets role and CV meaning; local deterministic code checks that evidence actually exists at the cited source; the recruiter sees the original text and retains control. The best optimization is the one that improves that loop without obscuring which component produced the result.

## Verified current baseline

From the frozen judge-release source and its documentation:

- Model ID is muse-spark-1.3. The analysis schema is strict JSON Schema; the local protocol validates parsed results.
- The normal live path makes one structured Muse request per CV. It sends locally extracted page-labelled text, not the original PDF. OCR is performed locally for scanned pages.
- The default reasoning effort is minimal. The app exposes configurable reasoning effort; earlier small calibration runs favored minimal for the current demo, but they do not establish a universally optimal setting.
- The release uses stable prompt-cache routing keys and records provider-reported token usage, including cached input and reasoning tokens. This makes actual cache and effort comparisons possible.
- Native Muse image input is optional and disabled by default. The existing source verifier independently checks quote text and page location.
- The public judge service is mock-only for fresh analysis; the saved replay contains genuine historical Muse outputs. A new prompt experiment must not be presented as the current public demo unless the exact build and its receipts are frozen and linked.

The prompt is already extensive. It specifies protected-characteristic exclusions, source-only analysis, actor/task scope distinctions, evidence categories, follow-up behavior, chronology extraction, and output-length constraints. Repeating or adding rules without ablation risks increasing conflicts, prompt length, false abstention, and latency.

## Research findings that change the optimization strategy

| Research / primary source | Finding relevant to EvidenceTrail | Engineering consequence |
| --- | --- | --- |
| Schulten et al., “A Practitioner’s Guide to Systematic Prompt Evaluation for Information Extraction,” EMNLP 2026 Industry Track. https://aclanthology.org/2026.emnlp-industry.59/ | Their high-stakes document-extraction study varies individual prompt components; a structured role/definition/rules/JSON prompt unexpectedly underperforms a simpler question-style prompt on their task. Results are task- and model-specific. | Do not add prompt-engineering folklore. Freeze the challenge set, change one prompt factor per arm, preserve every output, and choose by the error profile. This is the strongest direct case for testing a compact prompt against the current long prompt. |
| Xu et al., “Tree-of-Quote Prompting Improves Factuality and Attribution in Multi-Hop and Medical Reasoning,” EMNLP 2025. https://aclanthology.org/2025.emnlp-main.285/ | The method breaks a conclusion into subquestions, attaches quote evidence to each step, and advances only when quote quality suffices; their experiments report improved attribution on their own tasks. | Adapt the *structure*, not their claimed results: before assigning a CV label, explicitly check who acted, what action occurred, and whether scope/authority meets the exact requirement; return a source quote for each material proposition. The deterministic verifier still decides whether the quote exists. |
| Ling et al., “LLM Abstention Can Be a Prompt Artifact, in Addition to Genuine Uncertainty,” EMNLP 2026. https://aclanthology.org/2026.emnlp-main.549/ | Adding an unknown option can itself change model behavior and lower answer accuracy on their true/false tasks. | Track false-supported and missed-supported separately. Preserve positive, negative, and adjacent-work controls in every prompt experiment; do not celebrate more not_found labels as better calibration. Keep not_found distinct from conflicting and from review-required. |
| Chia et al., “M-LongDoc,” EMNLP 2025. https://aclanthology.org/2025.emnlp-main.469/ | Long-document evaluation and retrieval-aware processing are important; their reported tuning result is for a different model/task and hundreds-page documents. | Use the existing page-position counterfactual to test page 1/middle/last. If scaling beyond short CVs, evaluate recall-preserving page selection and ensure all pages that contain opposing claims remain available. Do not import their reported improvement as an EvidenceTrail result. |
| Meta Model API: reasoning. https://dev.meta.ai/docs/reasoning | Reasoning effort is a per-request control; higher effort spends more reasoning work. Raw chain-of-thought is not exposed, and Muse does not support log probabilities. | Compare output outcomes, provider usage, and latency by effort. Do not build a confidence score from hidden reasoning or the model’s self-reported certainty. |
| Meta Model API: prompt caching. https://dev.meta.ai/docs/prompt-caching | Stable prompt prefixes are cached automatically; stable instructions/examples should precede variable user content. Cache hits are visible in usage. | Retain stable instructions first and CV/job content last. Verify cached_tokens on repeated same-prefix requests before claiming cost/latency benefit. A stable cache key alone does not prove a hit. |
| Meta Model API: structured output and image understanding. https://dev.meta.ai/docs/structured-output and https://dev.meta.ai/docs/image-understanding | The API supports schema-constrained JSON and image input. | Keep the current strict schema as the experimental control. Evaluate vision as its own factor on scan cases, with local quote/page checks still required. |

## Tournament experiment plan

### P0 — One-factor prompt test

**Question:** Can a shorter, ordered decision checklist reduce applicant-actor and adjacent-task false support without increasing missed evidence?

- **Baseline:** frozen RC1 prompt, strict output schema, minimal effort, current text/OCR input.
- **Variant A (first):** retain the existing policy text and add no new examples; rewrite only the label decision paragraph as: requirement actor/action/scope → exact CV actor/action/scope → quote → status. Keep all prohibitions and output fields unchanged.
- **Variant B (only if A is useful):** keep A and add two short fixed examples: applicant-versus-manager actor swap, and concrete adjacent work that remains Related rather than Direct. Do not combine B with a reasoning-effort or vision change.
- **Cases:** use the existing frozen pairs, prioritizing M02/M03 (actor/responsibility), M05 (action), M09 (prompt injection), M10/M11 (adjacent work), and supported paraphrase controls M01/M04. Preserve original order and document hashes.
- **Readouts:** final-label agreement with author-written synthetic references; false-supported count; missed-supported count; pair-relation consistency; quote verification and correct page; malformed/invalid response count; input/output/cached/reasoning tokens; end-to-end latency.
- **Decision rule:** a variant advances only if false support does not increase, missed support does not materially worsen, and the critical actor/scope cases improve or remain stable. Publish all arms and denominators. With this small synthetic set, label the result exploratory and do not claim general model accuracy.
- **No human ratings:** the gold is explicitly synthetic and author-labelled. Do not use an LLM judge as ground truth.

### P0 — Minimal versus medium reasoning on hard cases

**Question:** Does more effort fix the hard semantic errors enough to justify extra cost and delay?

- Reuse stored minimal-effort outputs for a paired baseline; make fresh medium-effort calls only on a predeclared small subset with M02, M05, M07, and M12 representing actor, action, internal contradiction, and contradictory claims.
- Freeze prompt, input, model, schema, order, and retry policy. One request per case and zero automatic retries.
- Compare false support, missed support, final-label changes, quote/page validity, reasoning-token use, total tokens, and latency. A label change by itself is neither a win nor an error; compare to the prewritten case expectation.
- If the service exposes a reasoning-summary feature on the selected API route, consider it only for diagnostics; summaries are explanations, not proof. Preserve raw response and receipt for every call.
- **Decision:** keep minimal globally unless medium shows a reproducible improvement on the targeted failure mode. If improvement is selective, consider a transparent shadow/advisory escalation only after its trigger is predeclared and tested. Do not silently replace the original result.

### P1 — OCR text versus OCR plus Muse image input

**Question:** Does Muse’s visual reading recover useful content or layout relations that local OCR misses, while local source anchoring still works?

- Use only the existing fictional scanned CV fixtures; no real applicant documents.
- Compare identical OCR text sent alone versus the same OCR text plus the original page image. Keep prompt, schema, effort, and requirements fixed.
- Score exact recovered content against the fixture text, requirement labels, proposed quote existence, local page anchoring, OCR-only failures recovered, visual-only unsupported quotes, token usage, latency, and provider receipts.
- Do not enable visual evidence if Muse produces text that cannot be verified in the original PDF. Keep page-only fallback when OCR geometry is unavailable.
- Treat the prior vision grounding regression as a blocking counterexample to investigate, not as an isolated bad run to omit.
- **Tournament value:** a successful, bounded scan example could show a substantive Muse multimodal capability in the demo; an unsuccessful result should leave the stable OCR-only path in place.

### P1 — Cache and input budget measurement

No model-call experiment is needed to inspect historical receipt usage. Build a small report over saved receipts that compares input tokens, cached tokens, reasoning tokens, output tokens, latency, prompt version, and case. For any future controlled run:

1. Keep system instructions and fixed examples byte-for-byte stable at the start.
2. Put job-specific and CV-specific content after the stable prefix.
3. Keep a shared cache key only for requests that really share that prefix.
4. Measure first-request and subsequent-request cache counters separately.
5. Use the official input-token counting endpoint to size a proposed request before inference when useful.
6. Never describe a cache key, 1M context window, or API feature as a measured product gain without receipt evidence.

A short CV may not benefit much from retrieval trimming. For longer documents, test full text against page-level candidate context with recall safeguards: include top relevant pages and every page identified by deterministic scans as containing dates, explicit negation, role boundaries, or duplicate claims. Retrieval is allowed to prioritize; it must not silently discard contradictory evidence.

### P2 — Prompt compression after accuracy

Only after the one-factor prompt test, try deleting duplicate wording from the long prompt. Preserve every rule around source-only truth, protected traits, actor/scope/authority, negation, explicit contradiction, unsupported absence, and no hiring decisions. Compare token counts and outputs on the same frozen cases. Compression is accepted only if it reduces measured input/latency or cost without increasing false support or missing hard cases. Do not assume a shorter prompt is better.

## Minimal scorecard for every Muse run

Record one row per request and retain the raw response plus provider receipt:

- Source SHA, CV hash, JD hash, case/pair ID, and predeclared expected relation.
- Model ID, endpoint, prompt hash/version, schema hash, reasoning effort, request order, and any image/OCR mode.
- Provider response ID, HTTP outcome, retries, latency, input/output/cached/reasoning tokens, and estimated cost labelled as an estimate.
- Raw model status, EvidenceTrail final status, evidence type/strength, proposed quotes, accepted/rejected quote audit, cited/verified page.
- False-supported and missed-supported counts with denominators; pair consistency; stage of failure (OCR/extraction, retrieval, model interpretation, quote/page verifier, deterministic guard, or UI rendering).
- Exact code SHA used. No response IDs copied into records unless they were returned by the provider; no synthetic response receipts.

## The demo optimization that matters most

Build the judge moment around one truthful, high-signal case:

1. Show a Muse finding that cites a real passage.
2. Open its verification receipt and source page.
3. Show why the passage does not prove the applicant personally performed the claimed action, or show an explicit scope/timeline mismatch.
4. Show the original Muse label and the separately derived EvidenceTrail status together.
5. Show the clarification action and human-owned decision.
6. State the boundary plainly: “The quote exists here; that does not verify the claim outside this document.”

This shows genuine Meta interpretation and a useful independent safeguard in under a minute. It will help more than adding a long list of papers to the voiceover.

## Gates before any optimization reaches the judge build

- No experimental prompt, effort setting, or vision mode replaces frozen RC1 without a full diff review and exact-build replay.
- Do not spend on duplicate baseline calls when a saved receipt for the identical input/configuration exists.
- Do not run unregistered prompt variants and report only the best one. Predeclare variants and retain every outcome.
- Do not equate citation validity with semantic support, author-labelled synthetic performance with real-world accuracy, or self-reported certainty with calibrated probability.
- Keep the public replay clearly labelled as historical saved Muse output and the public fresh-analysis route mock-only unless deployment, consent, rate limits, and receipts are deliberately revalidated.

## Primary sources

- Meta Muse Spark 1.3 model and API overview: https://dev.meta.ai/models/muse-spark
- Meta Model API reasoning: https://dev.meta.ai/docs/reasoning
- Meta Model API prompt caching: https://dev.meta.ai/docs/prompt-caching
- Meta Model API structured output: https://dev.meta.ai/docs/structured-output
- Meta Model API image understanding: https://dev.meta.ai/docs/image-understanding
- Meta Model API token counting: https://dev.meta.ai/docs/token-counting
- Schulten et al., EMNLP 2026 Industry Track: https://aclanthology.org/2026.emnlp-industry.59/
- Xu et al., EMNLP 2025: https://aclanthology.org/2025.emnlp-main.285/
- Ling et al., EMNLP 2026: https://aclanthology.org/2026.emnlp-main.549/
- Chia et al., EMNLP 2025: https://aclanthology.org/2025.emnlp-main.469/

All paper-to-product interventions above are hypotheses to test on EvidenceTrail; published results belong to their authors and their evaluated tasks.
