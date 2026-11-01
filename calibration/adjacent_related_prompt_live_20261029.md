# Adjacent-work transfer calibration — 2026-10-29

## Prompt change

The saved C2 result had treated purchase-order changes and supplier-record
maintenance as “Not shown” for a related supplier-operations requirement. The
active Muse prompt now states that concrete, narrower duties can be Related to
a broader adjacent function, while keeping strategic ownership, selection,
negotiation, pricing, and commercial authority unproven. It also limits dates
to the documented role. Keyword-only mentions remain Unsupported.

## Targeted live check

One live batch reviewed C2 and C3 against the same locked two-item rubric using
Muse Spark 1.3 at medium effort. It made **2 live model requests**, no retries,
and completed in **32.14 seconds**.

- **C2:** Muse returned Related for the dated PO-change/supplier-record work
  and Unsupported for the skills-list-only negotiation requirement. It matched
  **2/2** expected labels; the previous saved C2 run matched 1/2. Treat this as
  a targeted follow-up, not a general accuracy result.
- **C3:** Muse proposed Direct for negotiation work despite the CV’s explicit
  responsibility limit. The deterministic scope gate preserved Muse’s Direct
  label for audit and changed the final finding to Related / ambiguous with the
  limitation quote anchored to page 1. C3 was **1/2** on Muse labels and **2/2**
  after the local gate.
- Across four findings, Muse matched **3/4** expected labels; the local scope
  gate brought the final result to **4/4**. This tiny set should not be reported
  as an accuracy rate.
- All **6/6 proposed quote texts** were located on their cited pages. One C3
  citation was excluded by local role checks; quote presence alone does not
  establish relevance.

The result supports keeping both controls: Muse can surface plausible adjacent
work, and deterministic local rules must still correct explicit scope
overclaims. The new prompt did not eliminate the Direct-versus-Related error in
C3.

## Latency and cache telemetry

The two Muse API calls took **29.513 s** and **32.031 s**. Each reported
**1,009 cached input tokens** out of 2,433 and 2,473 input tokens respectively.
That is about 41% of each prompt input reported as cached. The API docs identify
`usage.prompt_tokens_details.cached_tokens` as the Chat Completions cache
counter and say a positive value means the stable prefix was reused.

Caching was confirmed, but it did not remove the long wait: Muse still spent
4,876 and 6,266 reasoning tokens on these responses. The bottleneck remains
model reasoning/output, and the matched single-CV test still supports medium as
the safer global default than low.

## Files

- Live summary: `adjacent_related_live_c2_c3_20261029.json`
- Attempt log: `adjacent_related_live_c2_c3_20261029_attempt.json`
- Previous five-CV C2 baseline: `unified_demo_metrics_20261029_live_latency.json`
