# EvidenceTrail — Muse Spark three-minute demo

## Recording setup

- The prepared case uses a synthetic two-page CV and three focused requirements: one supported, one not found, and one conflicting.
- Select “Load the complete sample case.” The fictional CV and matching job description are prepared locally.
- Confirm the Meta data-sharing checkbox and run the two-pass live analysis. Loading the sample does not use API credits; the live run makes two model requests.
- Keep the API key out of the browser, screen recording, repository, and submission video.
- Record the full screen at readable zoom. Have the result page ready to scroll smoothly after the live request.

## Shot list and voiceover

### 0:00–0:25 — The problem

**Show:** The job description and the clearly fictional CV.

**Say:** “A match score tells a hiring team what a system thinks. It rarely shows the exact evidence behind that opinion. EvidenceTrail turns the review into something a person can inspect: each job requirement, the CV passage, and the page it came from.”

### 0:25–0:45 — The product

**Show:** Load the complete sample case, then show the upload form and privacy disclosure. Point out that it has no candidate score.

**Say:** “I built this as an evidence review, not an automated hiring decision. The sample is synthetic and deliberately includes a missing qualification and inconsistent experience claims.”

### 0:45–1:20 — Muse Spark 1.3 analysis via Meta Model API

**Show:** Click “Analyze with Muse Spark.” Keep the two-pass loading state visible briefly, then show the model name, two real Muse passes, per-pass and total token usage, and the first-pass and second-pass source-check counts.

**Say:** “Muse Spark 1.3 first maps the job into requirements and candidate evidence. EvidenceTrail then retrieves relevant source blocks locally and sends those bounded, page-linked spans to a second Muse review. The app verifies every final citation against its allowed span and the original PDF page.”

### 1:20–2:15 — Inspect and review the evidence

**Show:** Point to the evidence graph: each job requirement connects to its retrieved, verified source quote. Show one supported result, the not-found certification, and the conflicting procurement-years result. Open a supporting and conflicting graph link in the zoomable original PDF. Use the color key: teal supports; red conflicts. Mark the certification as “Needs follow-up” and add a reviewer note.

**Say:** “The graph preserves the path from requirement to source ID, quote, and page. The second Muse pass supplies the interpretation, while local code checks that each quote belongs to an allowed retrieved span and appears on the cited page. Ambiguous results stay flagged for review. ‘Not found’ means this document did not provide verified support; it does not mean the person lacks the skill.”

### 2:15–2:45 — Export the evidence pack

**Show:** Download the standalone HTML report. Scroll through the quote, highlighted page, reviewer note, and CV and job-description fingerprints.

**Say:** “The pack includes the source graph, two-pass audit counts, page highlights, and reviewer follow-up separately from Muse’s analysis. A reviewer can share the same evidence trail with a colleague.”

### 2:45–3:00 — Close

**Show:** Return to the evidence map and end on the product name.

**Say:** “Muse Spark maps and adjudicates the evidence; deterministic code validates source IDs, exact text, and cited page locations. The result is an inspectable path from job requirement to document source, while the hiring decision stays with a human.”

## Before submitting

- Use the same build shown in the video and linked from the public repository.
- Confirm the deployed demo works without showing or exposing the API key.
- Make sure the video link and repository are publicly accessible to judges.
- Review the final report once more for the three expected outcomes and the PDF highlights.
