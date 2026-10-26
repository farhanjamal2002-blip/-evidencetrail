# EvidenceTrail — three-minute demo

## Recording setup

- The prepared case uses a synthetic two-page CV and three focused requirements: one supported, one not found, and one conflicting.
- Select “Load the complete sample case.” The fictional CV and matching job description are prepared locally.
- Confirm the Meta data-sharing checkbox and run one live analysis. Loading the sample does not use API credits.
- Keep the API key out of the browser, screen recording, repository, and submission video.
- Record the full screen at readable zoom. Have the result page ready to scroll smoothly after the live request.

## Shot list and voiceover

### 0:00–0:25 — The problem

**Show:** The job description and the clearly fictional CV.

**Say:** “A match score tells a hiring team what a system thinks. It rarely shows the exact evidence behind that opinion. EvidenceTrail turns the review into something a person can inspect: each job requirement, the CV passage, and the page it came from.”

### 0:25–0:45 — The product

**Show:** Load the complete sample case, then show the upload form and privacy disclosure. Point out that it has no candidate score.

**Say:** “I built this as an evidence review, not an automated hiring decision. The sample is synthetic and deliberately includes a missing qualification and inconsistent experience claims.”

### 0:45–1:20 — The real Muse analysis

**Show:** Click “Analyze with Muse Spark.” Keep the loading state visible briefly, then show the model name, one real analysis call, and token usage.

**Say:** “Muse Spark reads the original CV alongside the job description. It breaks the role into requirements and proposes exact passages that support or conflict with each one. This is the core analysis the product is built around.”

### 1:20–2:15 — Inspect and review the evidence

**Show:** One supported result, the not-found certification, and the conflicting procurement-years result. Open the highlighted source page for each relevant quote and use the color key: teal supports; red conflicts. Mark the certification as “Needs follow-up” and add a note such as “Ask for the requested credential evidence.”

**Say:** “A quote only appears if the app can find its exact text in the uploaded PDF. The source page and highlight come from the PDF itself; the model’s page number is only a hint. Muse interprets the passage, and a human reviews that interpretation. ‘Not found’ means this document did not provide verified support; it does not mean the person lacks the skill.”

### 2:15–2:45 — Export the evidence pack

**Show:** Download the standalone HTML report. Scroll through the quote, highlighted page, reviewer note, and CV and job-description fingerprints.

**Say:** “The pack keeps each finding connected to its source and records the human follow-up separately from Muse’s analysis. A reviewer can share the same evidence trail with a colleague.”

### 2:45–3:00 — Close

**Show:** Return to the evidence map and end on the product name.

**Say:** “Muse does the semantic mapping. Deterministic code verifies every displayed quote against the original document. The result is faster review with a visible trail, while the hiring decision stays with a human.”

## Before submitting

- Use the same build shown in the video and linked from the public repository.
- Confirm the deployed demo works without showing or exposing the API key.
- Make sure the video link and repository are publicly accessible to judges.
- Review the final report once more for the three expected outcomes and the PDF highlights.
