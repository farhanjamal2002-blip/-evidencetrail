# Actor-swap replay — 90-second judge walkthrough
## Locked to the frozen M02 run (30 October 2026)

### Purpose

Show the difference between a source quote existing and the source supporting an applicant-level claim. Use the actual frozen M02 actor-swap pair and saved Muse outputs. This walkthrough makes no Glimmer/Wonder comparison claim.

### Actual recorded case

- Frozen release: `8489e45ae0f87d8421562618bda556c31911372b`
- Pair: M02, requirement: **Personally negotiated supplier agreements**
- Baseline text: “I personally negotiated the terms of supplier agreements.”
- Actor-swap text: “My procurement director negotiated the terms of supplier agreements; I only prepared comparison notes.”
- Baseline: expected `supported`; raw Muse `supported`; final `supported`.
- Actor-swap: expected `not_found`; raw Muse `conflicting`; final pipeline `not_found`.
- The M02/M07 run contains four requests, four authentic provider receipts, zero retries, and no human ratings. Detailed result summary: [run.json](https://github.com/farhanjamal2002-blip/-evidencetrail/blob/eval/academic-methods-oct30/artifacts/live-m02-m07-frozen-20261030/run.json).
- Across the full 24-request replay, 25/25 proposed citations passed deterministic quote/page verification. That is a replay-wide statistic; do not present it as an M02-only count. Full interpretation: [RESEARCH_LIVE_REPLAY_INTERPRETATION_20261030.md](../evaluation/RESEARCH_LIVE_REPLAY_INTERPRETATION_20261030.md).

### 90-second sequence

**0:00–0:15 — The claim**

Show the requirement “Personally negotiated supplier agreements.” Say: “A source can contain the right action words and still attribute the action to someone else.”

**0:15–0:35 — Two source variants**

Show the two actual M02 passages side by side. Highlight only the actor/responsibility difference: “I personally negotiated…” versus “My procurement director negotiated…; I only prepared comparison notes.”

**0:35–0:55 — Muse proposal vs final pipeline result**

Show the saved labels, preserving raw and final separately:

| Case | Raw Muse label | Final pipeline label |
| --- | --- | --- |
| Applicant negotiated | supported | supported |
| Director negotiated | conflicting | not_found |

Say: “The actor swap changes the final finding. In the director case, the pipeline keeps Muse’s initial uncertainty visible and the final evidence status does not claim the applicant negotiated.”

**0:55–1:15 — Source verification**

Open the saved source page and its case-level quote/page audit before narrating a page number or bounding box. The full replay had 25 verified citations across 24 requests; state that only as a replay-wide count. Explain that quote/page verification establishes text location, while the label addresses applicant attribution.

**1:15–1:30 — Close**

Say: “EvidenceTrail checks both where the text came from and what it supports. It shows the evidence and leaves the recruiter in control.”

### Claims that are not established by this run

Do not use the proposed Q3 postmortem, names Sarah Chen, page 4/bounding box [72.0, 410.5, 520.0, 465.2], 0.96 lexical-overlap score, or a structured raw `actor` field as if those were measured in M02. Do not say a keyword baseline scored above 0.95 or falsely marked the case supported; no such baseline result was recorded. These can become a separate fixture only after creation, execution, and receipt preservation.

The public judge build and frozen release remain unchanged. The M02 pair is author-labelled synthetic evaluation, not a general résumé accuracy claim.
