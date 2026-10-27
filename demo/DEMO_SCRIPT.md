# EvidenceTrail — Muse Spark three-minute demo

## Recording setup

- The prepared case uses a synthetic two-page CV and three focused requirements: one supported, one not found, and one conflicting.
- To inspect the interface before the key is configured, click “Open the sample review.” This is a hand-authored preview using fictional data; no model request runs, and it is not proof of a live model analysis.
- For the competition recording, click “Load sample inputs for a real run.” The fictional CV and job description are prepared locally.
- Confirm the Meta data-sharing checkbox and run the two-pass live analysis. Loading either preview/input does not use API credits; the live run makes two model requests.
- Keep the API key out of the browser, screen recording, repository, and submission video.
- Record the full screen at readable zoom. Have the result page ready to scroll smoothly after the live request.

## Shot list and voiceover

### 0:00–0:25 — The problem and plain-language product pitch

**Show:** The three-step review path, then the job description and clearly fictional CV.

**Say:** “A hiring reviewer has to compare every job requirement with a long CV. EvidenceTrail lines up each requirement with the words that support it and shows the page those words came from. It helps people review documents; it never decides who gets hired.”

### 0:25–0:45 — The product

**Show:** Open the sample review, then point to the labels for supported, not found, and conflicting. Explain that the data is fictional and the preview made no Meta call.

**Say:** “This sample has one requirement supported by the CV, one with no direct evidence, and one where the CV contradicts itself. ‘Not found’ only means this document did not show it; it is not a judgement about the person.”

### 0:45–1:20 — Muse Spark 1.3 analysis via Meta Model API

**Show:** Scroll to the form, load the sample inputs, confirm the data-sharing checkbox, and click “Analyze with Muse Spark.” Keep the two-pass loading state visible briefly, then show the model name, two real Muse passes, token usage, and source-check counts.

**Say:** “Muse Spark reads the job and CV to identify requirements and relevant claims. EvidenceTrail then finds nearby source passages and asks Muse Spark to review those passages. Before anything appears as evidence, the app checks that the quote is really in the CV and points to the right page.”

### 1:20–2:15 — Inspect and review the evidence

**Show:** Point to the evidence graph: each job requirement connects to its retrieved, verified source quote. Show one supported result, the not-found certification, and the conflicting procurement-years result. Open a supporting and conflicting graph link in the zoomable original PDF. Use the color key: teal supports; red conflicts. Mark the certification as “Needs follow-up” and add a reviewer note.

**Say:** “Follow the line from this requirement to the exact quote and page. The green passage appears to support the requirement; the red passage disagrees with another statement in the same CV. A quote being present does not prove the claim is true, so a person still checks the context.”

### 2:15–2:45 — Export the evidence pack

**Show:** Download the standalone HTML report. Scroll through the quote, highlighted page, reviewer note, and CV and job-description fingerprints.

**Say:** “The evidence pack keeps the requirements, source quotes, highlighted pages, and the reviewer’s notes together. That makes it easier for another reviewer to see why something needs follow-up.”

### 2:45–3:00 — Close

**Show:** Return to the evidence map and end on the product name.

**Say:** “Muse Spark interprets the documents. EvidenceTrail checks the citations against the CV. The reviewer makes the decision. That’s the whole point: every finding has a trail a person can inspect.”

## Before submitting

- Use the same build shown in the video and linked from the public repository.
- Confirm the deployed demo works without showing or exposing the API key.
- Make sure the video link and repository are publicly accessible to judges.
- Review the final report once more for the three expected outcomes and the PDF highlights.
