# EvidenceTrail — 20-second launch film

[Watch with sound](https://evidencetrail-judge-rc1-2026.onrender.com/static/evidencetrail-launch.mp4) · [Silent GIF](../docs/img/evidencetrail-launch.gif) · [Capture provenance](../docs/img/launch-provenance.json)

This is an edited product launch film, using exact crops of the live saved-replay interface with editorial typography and original synthesized sound. It is not a continuous screen recording or a fresh Muse inference. The separate [30-second judge walkthrough](https://evidencetrail-judge-rc1-2026.onrender.com/static/judge-path.mp4) preserves the uninterrupted UI path.

| Time | Story | Actual proof |
|---|---|---|
| 0–3s | The quote is real. | Exact M02 actor-swap quote from the live interface. |
| 3–6s | But who did the work? | The same passage credits the procurement director; the applicant prepared notes. |
| 6–10s | Verified quote. Wrong person. | Actual quote-on-page and applicant-attribution checks, followed by raw Muse `conflicting` → final `not_found`. |
| 10–14s | Five attribution corrections. | 19/24 raw → 24/24 final labels matching the author key; the five corrected case IDs are shown. |
| 14–17s | Content. Not commands. | The two actual outlined ET-018 instruction lines and the live “Treated as content” badge. |
| 17–20s | EvidenceTrail. Evidence you can inspect. | Product end card: built with Meta Muse Spark 1.3, source checks, human review, and no candidate scores. |

The result scene explicitly labels the set as **12 fictional pairs / 24 saved requests**, author-labelled and **not real-CV accuracy**. The saved-replay disclosure remains visible throughout. The film does not claim general prompt-injection protection or that CV statements are true in the real world.

Claim source: [the checked-in twelve-pair summary](../static/replay-artifacts/twelve-pair-summary.json). The five corrected cases are M02-variant, M03-variant, M05-variant, M10-variant, and M12-baseline. Source quotes, model labels, and PDF outlines in the film are screenshot crops, not recreated UI. The provenance JSON records the source deployment SHA and confirms zero new analysis requests during capture.

This promotional film complements the three-minute judge video; it does not replace the entrant's full recording or portal submission.
