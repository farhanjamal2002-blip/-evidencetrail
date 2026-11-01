# Muse reasoning-effort comparison — 2026-10-29

## Matched single-CV check

The same fictional career-switcher CV, job description, and two locked criteria
were submitted once at medium effort and once at low effort. Each request used
Muse Spark 1.3 and made no retry.

| Setting | Muse API time | End-to-end | Output tokens | Reasoning tokens | Muse labels | Source quotes |
|---|---:|---:|---:|---:|---|---|
| Medium | 25.058 s | 25.156 s | 3,969 | 3,158 | Related, Related | 4/4 matched and accepted |
| Low | 15.004 s | 15.120 s | 2,355 | 1,681 | Related, Related | 4/4 matched; 3 accepted, 1 excluded |

Low effort was about **40% faster** on this one profile. In the low run, the
excluded quote only said that semiconductor experience was not listed; the
local verifier correctly did not treat absence from the CV as proof of a
qualification conflict. Both runs left the explicit negotiation-scope
limitation visible, and neither needed the deterministic Direct-to-Related
override.

This is a one-profile latency comparison, not evidence that low effort is
equally reliable across the job or candidate set.

## Broader evidence and decision

In the earlier, separate 18-label public-JD calibration, medium matched **14/18**
labels, missed **1** expected Related label, and had **0** Related-to-Direct
overclaims. Low matched **13/18**, missed **2** Related labels, and had **1**
Related-to-Direct overclaim. That run predates the current explicit-scope gate;
the samples and prompt versions should not be merged into a single accuracy
claim.

**Keep medium as the product default.** Low is measurably faster for this C3
case, but its broader result was weaker on exactly the semantic boundary this
product must handle. The one-CV result is not enough to justify a global switch.

## Cache observation

Both matched calls reported zero cached input tokens. Meta documents automatic
prefix caching and the Chat Completions counter
`usage.prompt_tokens_details.cached_tokens`; the current requests already use a
stable prefix and cache key. These runs therefore show no cache hit and no
measured caching speedup. Cache hits depend on recent matching prefixes and
backend retention, so zero is possible after eviction.

## Artifacts

- Medium request: `scope_boundary_live_c3_20261029.json`
- Low request: `scope_boundary_live_c3_low_20261029.json`
- Broader medium/low calibration: `live_latency_medium_reasoning_20261029.json` and
  `live_latency_low_reasoning_20261029.json`
