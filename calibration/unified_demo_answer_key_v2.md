# Unified demo answer key — demo-v2 (keep hidden from reviewers)

All five profiles are fictional. Record reviewer decisions and issue detection before consulting this key. The labels are prewritten calibration targets, not objective judgments about a person.

| Candidate | Planted issue | Requirement 1 target | Requirement 2 target | Expected review signal |
|---|---|---|---|---|
| C1 | Concrete supplier-contract history | Direct · Specific | Direct · Specific | Nine dated years in supplier operations and sourcing; named suppliers, negotiated term, pricing, and implementation steps. |
| C2 | Generic skill list and filler | Related · Specific | Unsupported · Keyword only | Five dated years of supplier operations are shown, but only PO changes and supplier-record work establish scope. Commercial phrases are unsupported by a work example. |
| C3 | Career switch from hospital facilities | Related · Specific | Related · Specific | Bids, supplier quotes, service-level follow-up, renewals, and pricing escalation may transfer. Semiconductor/OSAT work and negotiation/sign-off ownership remain unproven. |
| C4 | Two overlapping full-time roles | Conflict to clarify · Specific | Direct · Specific | Deterministic date math flags the three-year overlap and gates the five-year criterion to human review. The second criterion has direct supporting work examples. |
| C5 | Image-only, two-column scan | Direct · Specific | Direct · Specific | OCR is required. Inspect the original page. The local verifier should block any proposal that cannot be found on the cited page; in the saved run, one of six proposed citations was blocked. |

## Observed live run (not the answer key)

The initial five-CV batch completed C1, C2, C4, and C5; C3 stopped at local schema validation. One separate, manual C3 recovery completed. Across the five completed result payloads, Muse matched 9/10 prewritten evidence labels; the deterministic timeline gate brought the adjudicated labels to 10/10. Strength labels matched 10/10. The local verifier accepted 18/19 proposed quotes and blocked one quote on C5. No related finding was labelled Direct in this set. The failed initial C3 request returned no token usage, so the reported successful-call cost estimate excludes any usage from that failed request.
