# EvidenceTrail — recruiter workflow demo

## Recording setup

- Review `calibration/iteration_review_20261028_strength_ladder.md`, the five-case JSON, and the one-time paired strength-ladder result before recording. The five-case set used 10 Muse requests; Muse alone matched 16/18 labels and the deterministic timeline gate resolves the two flagged date findings to **Conflict to clarify** (18/18 combined labels). The paired keyword-only/specific example used four requests with no retries. Do not rerun either set for the recording.
- Use fictional CVs only. The five calibration cases span four industries, including a deliberately messy image-only scan and date discrepancies.
- Keep `MODEL_API_KEY` in the server environment, out of the browser, repository, and recording.
- The app can review one CV or up to five against the same job description. Batch results stay in upload order and do not create a candidate score or automatic ranking.
- The saved five-case and paired reports omit response bodies and accepted CV quotes. The targeted scanned-CV report now retains the two actual rejected quote snippets, cited page, and failure reason. Use that saved trace for the amber catch; do not imply the report is a replayable full CV session.
- Finish the real analyses before recording and begin with the actual results visible; this keeps the video moving without substituting mock output for a live result. Keep each case clearly identified because the timeline example and scanned-CV verifier catch are separate candidates and roles.
- Record at readable zoom. Keep the source-check chip, evidence labels, and cited page legible at normal playback size.

## Two-minute walkthrough

### 0:00–0:12 — The promise

**Show:** Start on completed results with the role and reviewer decision controls visible.

**Say:** “A match score hides the reason. EvidenceTrail shows CV evidence, gaps, and the recruiter’s decision; it does not rank applicants.”

### 0:12–0:28 — Compare by requirement

**Show:** Open the two-CV strength-ladder batch in matrix view. Point to the same requirement across the two candidates, then the Specific and Keyword only labels.

**Say:** “The matrix compares requirements across candidates in upload order. One CV shows specific work; the other has keywords only.”

### 0:28–0:48 — Explain related experience

**Show:** Open the public-procurement candidate dossier. Show the related finding, source passage, transfer explanation, and remaining gap.

**Say:** “This candidate’s internal audit work may transfer to public procurement, but GFR, CVC, and GeM are unproven. Muse explains the link; the recruiter decides whether it counts.”

### 0:48–1:05 — Clarify the date discrepancy

**Show:** Open the 10-year experience finding. Point to **Conflict to clarify** and “Muse: Direct · Timeline check: conflict.”

**Say:** “The profile claims 12 years; dated roles cover about eight. The date gate marks Conflict to clarify and preserves Muse’s original label.”

### 1:05–1:25 — Show the real scan catch

**Show:** Switch to the separate image-only scan result. Show the MCIPS finding, then the amber source-check chip, then expand the rejection ledger for the exact reason and quote, and finish on scanned page 1.

**Say:** “The amber chip shows two of five quotes rejected. The ledger says each could not be found on page 1. Both stay out of the evidence.”

### 1:25–1:45 — Advance and prepare the hand-off

**Show:** Return to the candidate review, prepare an interview invitation, edit one placeholder, then open the HTML evidence pack.

**Say:** “The recruiter chooses to advance and gets an editable invitation draft grounded only in clear, verified evidence. Nothing is sent or scheduled. The hand-off carries the decision, draft, accepted related findings, gaps, and next questions.”

### 1:45–2:00 — Give the measured result and boundary

**Show:** Finish on the calibration summary, with the two result sets visibly separated.

**Say:** “Five-case calibration: Muse, 16 of 18; with the timeline gate, 18 of 18 combined. Separate scan: 3 of 3 labels; 3 of 5 quotes verified, 2 blocked. Muse interprets; the recruiter decides.”

## Before submission

- State the metrics as separate layers: **Muse alone: 16/18**; **after the deterministic timeline gate: 18/18 on this same set**; **23/24 proposed quotes passed local checks in the five-case run**. In one separate image-only scanned-CV rerun, **3/3 expected labels matched, 3/5 proposed quotes passed local checks, and the other 2/5 were blocked because they were not found on cited page 1**. Do not merge those quote denominators. The 18/18 figure is a derived, combined label result for the two flagged duration discrepancies, not Muse accuracy and not a general accuracy rate.
- The paired strength-ladder run matched both prewritten focal category and strength labels, used four Muse requests, and had an estimated $0.0483815 token cost. Call it a two-candidate demonstration, not a benchmark.
- Confirm that the live recording matches the submitted app build and the actual model output.
- Keep the fictional data and server-side key disclosure visible.
- Check the public app, repository, and video links from a signed-out browser before submission.
