# Meta Global AI Developer Hackathon — Compliance Checklist

Status checked: 27 October 2026

This is a project shipping checklist, not the organizer’s official rules document. It combines the public event page with the submission, judging, and rules screenshots supplied by the entrant. The selected participant must still read and accept the official rules and waiver in the organizer’s submission flow.

Sources:
- Public event page: https://cerebralvalley.ai/e/meta-ai-developer-hackathon
- Event details / rules page: https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details?backUrl=%2Fe%2Fmeta-ai-developer-hackathon

## Competition gate

| Requirement | Current evidence | Status | Required before submission |
|---|---|---|---|
| Fit a published theme | EvidenceTrail supports document-evidence review for hiring. The app shows source passages and leaves the hiring decision to a human. | Implemented | Demo the real workflow and explain the problem in the builder’s own terms. |
| Use Meta AI meaningfully | The server sends the original CV PDF and job description to Muse Spark 1.3 in one structured request. Muse performs the requirement/evidence analysis; deterministic code verifies quotes and page locations. | Code ready; live use unverified | Configure the key as a server-side secret, complete a real run, and show the Muse result and source checks in the video. |
| No simulated Meta results | The synthetic sample fills only the CV and job-description inputs. It does not preload or fabricate an analysis. Missing API configuration stops the request and states that no call was made. | Implemented | Keep the sample and demo honest; never present a local fixture as Muse output. |
| Clear evidence and human review | Quotes are checked against the uploaded CV; missing evidence is not treated as proof of absence; the app does not score or decide. | Implemented | Show supported, not-found, and conflicting examples from a genuine run. |
| Submission artifacts work | The repository contains a three-minute demo script. The exported pack is standalone HTML. | Incomplete | Deploy the app, record the required demo using the same build, and verify the repository, app, and video are publicly accessible. |
| Deadline and submission process | The public event page lists the project deadline as 4 November 2026 at 9:00 PM ET. The supplied rules screenshots say late entries are not considered and teams appoint one representative. | Entrant action | Submit before the cutoff. Confirm the selected track, entrant/team details, representative, and one-project submission are correct. |
| Eligibility and official rules | The public page lists geographic, sanctions, and organizer-affiliation exclusions and says selected participants must accept the official rules. | Entrant action | Verify eligibility and accept/read the full official rules and waiver in the organizer’s flow. The public page’s waiver view did not expose the full text during this check. |
| Third-party code attribution | README names the open-source stack and identifies PDF.js 6.4.299 with its Apache-2.0 license. | Implemented | Keep license notices with any additional libraries that are added. |

## Current highest-risk blocker

The code is wired for genuine Muse Spark use, but the API key is not configured and no live analysis has been run. Source code alone does not demonstrate that the submitted product works. Do not claim a live Muse integration until a real request succeeds and the demo shows it.

## Submission run-through

1. Set MODEL_API_KEY only in the server/host secret settings; never put it in browser code, the repository, or the recording.
2. Run one real analysis on the synthetic case and confirm the page shows the model, one analysis call, token usage, and quote-verification counts.
3. Inspect the original-PDF highlights, then download and open the evidence pack.
4. Record the three-minute demo from that same working build. Do not edit the result or imply that a synthetic response came from Muse.
5. Check all links from a signed-out browser and submit before 4 November, 9:00 PM ET.
6. Have the entrant verify the full official rules, eligibility, track, and representative details in the submission flow.

## Product claims to preserve

- EvidenceTrail verifies that quoted text occurs in the supplied document; it does not verify a real-world credential or employment claim.
- “Not found” means the supplied CV did not provide verified support; it does not mean the person lacks the qualification.
- The report is an evidence review, not a candidate ranking, score, or hiring decision.
