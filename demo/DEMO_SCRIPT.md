# EvidenceTrail — three-minute demo

## Recording setup

- Use the generated two-page CV. It contains no real candidate information.
- Paste the sample job description, confirm the Meta data-sharing checkbox, and run one live analysis.
- Keep the API key out of the browser, screen recording, repository, and submission video.
- Record the full screen at readable zoom. Have the result page ready to scroll smoothly after the live request.

## Shot list and voiceover

### 0:00–0:25 — The problem

**Show:** The job description and the clearly fictional CV.

**Say:** “A match score tells a hiring team what a system thinks. It rarely shows the exact evidence behind that opinion. EvidenceTrail turns the review into something a person can inspect: each job requirement, the CV passage, and the page it came from.”

### 0:25–0:45 — The product

**Show:** The upload form, privacy disclosure, and the sample case. Point out that it has no candidate score.

**Say:** “I built this as an evidence review, not an automated hiring decision. The sample is synthetic and deliberately includes a missing qualification and inconsistent experience claims.”

### 0:45–1:20 — The real Muse analysis

**Show:** Click “Analyze with Muse Spark.” Keep the loading state visible briefly, then show the model name, one real analysis call, and token usage.

**Say:** “Muse Spark reads the original CV alongside the job description. It breaks the role into requirements and proposes exact passages that support or conflict with each one. This is the core analysis the product is built around.”

### 1:20–2:15 — Inspect the evidence

**Show:** One supported result, the not-found certification, and the conflicting procurement-years result. Open the highlighted source page for each relevant quote.

**Say:** “A passage only appears if the app can find it in the uploaded PDF. The source page and highlight are produced from the PDF itself; the model’s page number is only a hint. ‘Not found’ means this document did not provide verified support. It does not mean the person lacks the skill.”

### 2:15–2:45 — Export the evidence pack

**Show:** Download the standalone HTML report. Scroll through the quote, highlighted page, and CV and job-description fingerprints.

**Say:** “The exported pack keeps the finding connected to its source, so a reviewer can audit the claim and share the same evidence with a colleague. It also records which model produced the analysis.”

### 2:45–3:00 — Close

**Show:** Return to the evidence map and end on the product name.

**Say:** “Muse does the semantic mapping. Deterministic code verifies every displayed quote against the original document. The result is faster review with a visible trail, while the hiring decision stays with a human.”

## Before submitting

- Use the same build shown in the video and linked from the public repository.
- Confirm the deployed demo works without showing or exposing the API key.
- Make sure the video link and repository are publicly accessible to judges.
- Review the final report once more for the three expected outcomes and the PDF highlights.
