# EvidenceTrail — recruiter workflow demo

## Recording setup

- Record the P1 build only after the canonical five-CV Muse replay has been regenerated against the frozen UI and payload schema.
- Use fictional CVs. Keep candidates in upload order.
- Keep the server-side MODEL_API_KEY out of the browser, repository, and recording.
- Do not present the checked-in pre-P1 replay as the current canonical run. Add the new run's actual request count, timing, source-check counts, and result limitations after it completes.

## Two-minute walkthrough

### 0:00–0:12 — The promise

**Show:** Start on the completed review.

**Say:** “A match score hides why a CV appears to fit. EvidenceTrail shows the requirement, the source passage, and the recruiter’s decision. It does not rank candidates.”

### 0:12–0:30 — Compare the evidence

**Show:** Open the batch matrix. Point out the candidates remain in upload order and select one requirement across the CVs.

**Say:** “Evidence status uses five labels: Direct, Related, Conflict to clarify, Unsupported, and Not found. Every candidate stays in the order they were uploaded.”

### 0:30–0:50 — Verify the source

**Show:** Open a finding and its cited page. Show a verified quote and, if present in the canonical run, a blocked quote.

**Say:** “The source check is deterministic. A quote is marked Verified with its page, or Blocked when it cannot be found on the cited page.”

### 0:50–1:08 — Show the gate audit

**Show:** Open the finding with the seeded explicit denial or date discrepancy. Point to the raw/effective pill, for example, “Muse: Direct → Gate: Conflict to clarify.”

**Say:** “The audit keeps Muse’s original label and shows the deterministic gate’s final evidence status. The recruiter can inspect the source before deciding.”

### 1:08–1:30 — Make the human decision

**Show:** Record Advance, Hold, or Do not advance for the selected fictional candidate. Keep the decision and reason tied to the role criteria.

**Say:** “The recruiter owns the decision. EvidenceTrail does not score or automatically rank the candidate.”

### 1:30–1:48 — Export the evidence pack

**Show:** Open the per-CV evidence pack and point to the decision, evidence labels, verified citations, and page highlights.

**Say:** “The export carries the evidence trail and the recruiter’s recorded action. The workflow ends here.”

### 1:48–2:00 — State the measured result

**Show:** Finish on the canonical five-CV run receipt and the source-check totals.

**Say:** “This is the result from the recorded five-CV run. The labels and quote checks are shown separately; this small fictional set is a calibration example, not a general accuracy claim.”

## Before submission

- Fill this script's final line only from the canonical post-freeze replay artifact. Keep Muse’s raw labels separate from deterministic gate outcomes, and quote verification separate from semantic labels.
- Do not combine counts from separate runs or describe a small fictional calibration as a general accuracy rate.
- Confirm that the public app, repository, replay receipt, and video all reflect the same schema.
- Check the public app, repository, and video links from a signed-out browser before submission.
