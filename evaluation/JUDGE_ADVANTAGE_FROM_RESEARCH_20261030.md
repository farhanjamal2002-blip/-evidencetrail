# Judge playbook — turn research into a defensible EvidenceTrail advantage

**Date:** 2026-10-30  
**Status:** presentation plan, not a report of new model or user-study results. Keep the judge demo on the frozen release. This playbook is for choosing what to show and what claims to avoid.

## The competitive claim

**EvidenceTrail separates three questions that a polished citation can blur together:**

1. Are these words actually present on this document page?
2. Do those words support this specific claim about the applicant?
3. What should a human reviewer do when the source is incomplete, unreadable, or inconsistent?

Our advantage is not “research proves EvidenceTrail is more accurate.” The defensible claim is: **we designed the system and its evaluation around distinct failure modes, then froze adversarial cases so failures can be measured instead of hidden by one score.**

## Recommended 90-second demo sequence

### 0:00–0:20 — A real citation can still imply the wrong person

Use the fictional actor-swap pair M02:

- Requirement: “Personally negotiated supplier agreements.”
- CV variant: the procurement director negotiated; the applicant prepared comparison notes.

Show the exact source text and page, then ask the reviewer whether it establishes the applicant's personal work. The expected reference is *not_found* for that requirement. The point is to distinguish **quote found** from **claim supported**. Do not say the model passed until an authentic run is saved and independently checked.

### 0:20–0:40 — Preserve both sides of a contradiction

Use one frozen timeline or negotiation-conflict pair (M07 or M12). Show both CV passages, their page locations, and the *conflicting* outcome together. The reviewer should not need to trust a summary that cites only one of the passages.

### 0:40–1:00 — Demonstrate the evidence boundary

Show that a source locator can confirm the words on the page while leaving the real-world truth of the CV claim unknown. State: **“We verify what the supplied document says; we do not verify whether the claim is true outside the document.”**

### 1:00–1:20 — Show what happens when the document is not answerable

Use a scanned or deliberately degraded fictional page only if the frozen release actually handles it. If the relevant words cannot be read or located, show the real system behavior and ask for human review. Do not stage a mock result as live model evidence. If this case is not implemented in the demo build, show the pre-registered test case as planned work and label it clearly.

### 1:20–1:30 — Close on the evaluator

Show the challenge-pair manifest and integrity harness. Explain that the test corpus is fictional and predeclared, and that CI validates the evaluator and refuses to invent benchmark scores. State that live model performance and independent semantic ratings remain unmeasured until their receipts and blinded judgments are recorded.

## Judge-facing one-liner

> “Research pushed us to separate a verified quote from a justified inference. EvidenceTrail shows the source, checks whether it is about the applicant, preserves conflicting passages, and leaves unresolved evidence for a human to review. We publish the test method separately from results we have not measured.”

## Evidence-to-demo map

| Research lesson | What to show | Existing evidence in the branch | What is still needed for a result |
|---|---|---|---|
| Citation existence is not semantic support | M02 actor swap | Frozen fictional pair and metric harness | Authentic end-to-end model output; two blind human sufficiency ratings |
| One-sided citation can hide disagreement | M07 or M12 conflict | Frozen pair; separate conflict label | Confirm both passages are surfaced by the live pipeline |
| Position and OCR structure can affect retrieval | M08 plus proposed OCR fixture families | Page-position pair; research protocol | Actual rendered fixtures and measured retrieval/page outcomes |
| Abstention can over-refuse or fail under shift | Clear positive controls beside unreadable/ambiguous cases | Research follow-up plan | Frozen answerability set, observed model output and denominators |
| Explanations do not guarantee appropriate reliance | Source-first reviewer flow | Study design only | Real pilot participants, task records, and participant/case counts |

## Rules for honest, strong judging

- Lead with the applicant-attribution failure. It is concrete, easy to understand, and central to the product.
- Let judges inspect the original passage and page. Do not replace evidence with a confidence percentage.
- Call author-labelled synthetic results **synthetic tests**. Call published methods **research-inspired** unless the original benchmark and protocol were reproduced.
- Show every predeclared case, including failures and review-required results. Do not rerun only the cases that look good.
- Keep not_found, conflicting, refuted, and review_required distinct.
- Do not claim better hiring outcomes, fairness, reduced time, lower bias, or higher accuracy without appropriate measured evidence.
- If an OCR or reviewer-flow feature is not present in the frozen build, present it as a planned evaluation—not a product capability.
- Keep the hackathon demo fast: one applicant-ownership failure, one conflict, one source verification, one boundary statement. Use the appendix only for judge questions.

## Next proof-producing work

1. Run the existing frozen pairs only after the model version, prompt, parser, and receipt-capture method are frozen.
2. Preserve raw response, final EvidenceTrail label, page/quote verification, failure stage, and genuine provider receipt for every variant. Keep all failed cases.
3. Ask two people who did not author the fictional examples to rate semantic sufficiency independently. Report agreement and disagreement; do not let the model grade itself.
4. Add OCR fixtures only when the exact images, gold passages, page numbers, and rendering perturbations are versioned and fixed before inference.
5. Keep the reviewer study last. A planned study or a tiny exploratory pilot is not evidence of real-world hiring impact.

**Current status:** the research PR contains the academic-methods protocol, 12 frozen fictional perturbation pairs, integrity tests, deep-dive matrices, and this judge playbook. It does not yet contain new live Muse results, independent ratings, or measured reviewer outcomes.
