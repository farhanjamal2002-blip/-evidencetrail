# EvidenceTrail — Muse Spark three-minute demo

## Recording setup

- The synthetic case uses a two-page CV and four listed job items. The static preview hand-authors three evidence findings (supported, not found, conflicting) and intentionally leaves one list item unmapped so the omission warning is visible. This warning is a synthetic demonstration, not a Muse result.
- The sample job description has four listed criteria and wording cues for the free role preflight. The preflight sends only the job description to the EvidenceTrail app server, makes no Meta call, and has no CV or applicant data to inspect.
- To inspect the interface before the key is configured, click “Open the sample review.” This is a hand-authored preview using fictional data; no model request runs, and it is not proof of a live model analysis.
- For the competition recording, click “Load sample inputs for a real run.” The fictional CV and job description are prepared locally.
- Confirm the Meta data-sharing checkbox and run the two-pass live analysis. Loading either preview/input does not use API credits; the live run makes two model requests.
- Keep the API key out of the browser, screen recording, repository, and submission video.
- Record the full screen at readable zoom. Have the result page ready to scroll smoothly after the live request.

## Shot list and voiceover

### 0:00–0:25 — The problem and plain-language product pitch

**Show:** The three-step review path, then the job description and clearly fictional CV. Point out the free role criteria preflight before the CV upload.

**Say:** “Job seekers need to know whether their CV actually shows the experience a role asks for. Reviewers need to inspect those claims quickly. EvidenceTrail connects requirements to source passages and leaves conclusions to people.”

### 0:25–0:45 — Criteria before candidate data

**Show:** Click “Build role evidence plan” before uploading the CV. Show the exact source line, category, explicit priority wording (or “Not stated”), reviewer evidence check, draft interview question, candidate self-check, and download the role worksheet. If time, open the secondary optional wording cues. Then open the synthetic sample review and point to supported, not found, and conflicting results.

**Say:** “Before you share a CV, EvidenceTrail can turn listed role requirements into an evidence plan. It reports priority wording only when the job post states it and exports a job-only worksheet; no CV or Meta request is involved. In the sample, one requirement is supported, one has no direct evidence, and one conflicts with another CV statement. ‘Not found’ means only that this document did not show it.”

### 0:45–1:20 — Muse Spark 1.3 analysis via Meta Model API

**Show:** Scroll to the form, load the sample inputs, confirm the data-sharing checkbox, and click “Analyze with Muse Spark.” Keep the two-pass loading state visible briefly, then show the model name, two real Muse passes, token usage, and source-check counts.

**Say:** “Muse Spark reads the job and CV to identify requirements and relevant claims. EvidenceTrail then finds nearby source passages and asks Muse Spark to review those passages. Before anything appears as evidence, the app checks that the quote is really in the CV and points to the right page.”

### 1:20–2:15 — Inspect evidence and capture follow-up

**Show:** Point to the evidence graph: each analyzed requirement connects to its retrieved, verified source quote. Show one supported result, the not-found certification, and the conflicting procurement-years result. Open a supporting and conflicting graph link in the zoomable original PDF. Use the color key: teal supports; red conflicts. Show the job-description list audit and explain that any weak wording match needs human review. Mark the certification as “Needs follow-up,” then show the neutral clarification question and record a clearly fictional candidate reply.

**Say:** “Follow the line from this requirement to the exact quote and page. The green passage appears to support the requirement; the red passage disagrees with another statement in the same CV. A quote being present does not prove the claim is true, so a person still checks the context. When a document is incomplete or unclear, EvidenceTrail drafts a neutral follow-up. A reply can be recorded as candidate-provided and unverified; it stays separate from the CV finding and is not sent back to Muse.”

### 2:15–2:45 — Export the evidence pack

**Show:** Download the standalone HTML report. Scroll through the quote, highlighted page, reviewer note, separately labeled candidate reply, and CV and job-description fingerprints.

**Say:** “The evidence pack keeps the requirements, source quotes, highlighted pages, reviewer notes, and candidate-provided follow-up together while preserving where each statement came from. The original CV finding stays unchanged.”

### 2:45–3:00 — Close

**Show:** Return to the evidence map and end on the product name.

**Say:** “Muse Spark interprets the documents. EvidenceTrail checks the citations against the CV. The reviewer makes the decision. That’s the whole point: every finding has a trail a person can inspect.”

## Before submitting

- Use the same build shown in the video and linked from the public repository.
- Confirm the deployed demo works without showing or exposing the API key.
- Make sure the video link and repository are publicly accessible to judges.
- Review the final report once more for the three expected outcomes and the PDF highlights.
