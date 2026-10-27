# Meta Global AI Developer Hackathon — Compliance and Submission Guide

This guide maps the public event criteria and the event-detail screenshots shared by the entrant to EvidenceTrail’s product design. The organizer’s official rules and waiver remain the controlling documents; the selected entrant must read and accept them in the submission flow.

Sources:
- Public event page: https://cerebralvalley.ai/e/meta-ai-developer-hackathon
- Event details / rules page: https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details?backUrl=%2Fe%2Fmeta-ai-developer-hackathon

## Rules mapped to the project

| Area | EvidenceTrail implementation | Submission check |
|---|---|---|
| Theme fit | EvidenceTrail helps a reviewer trace job requirements to passages in a CV and keeps the hiring decision with a person. | Explain the real hiring-document problem and show the end-to-end evidence review. |
| Meta model use | When configured, the server sends the original CV PDF and job description to Muse Spark 1.3 through Meta Model API in one structured request. Muse performs the semantic requirement/evidence mapping; deterministic code checks quoted passages and page locations against the source. | Show the actual Muse analysis and the source-check result in the demo. Keep the API key in server-side secret settings. |
| Sample behavior | The fictional sample case fills the CV and job-description inputs. Analysis results come from the normal analysis flow. | Show an actual analysis response from the demo run. |
| Evidence and human review | Quotes are checked against the supplied CV. “Not found” is not treated as proof of absence. The app does not score or rank candidates or make hiring decisions. | Show supported, not-found, and conflicting examples; explain that the report does not verify real-world credentials. |
| Consent and upload handling | The user must consent before the CV and job description are sent to Meta. EvidenceTrail has no persistent CV storage; FastAPI may hold larger uploads in request-scoped temporary storage. | Keep the consent disclosure visible. Avoid claiming that uploads never touch disk. |
| Submission artifacts | The repository includes a three-minute demo script and the app exports a standalone HTML evidence pack. | Use the same build for the demo and submission; make the app, public repository, and video accessible to judges. |
| Deadline and process | The public event page lists submissions due 4 November 2026 at 9:00 PM ET. The supplied rules screenshots say late submissions are not considered and teams appoint one representative. | Submit before the cutoff. Confirm the selected track, entrant/team details, representative, and one-project submission are correct. |
| Eligibility and official rules | The public page lists geographic, sanctions, and organizer-affiliation restrictions and says selected participants must accept the official rules. | The entrant must verify eligibility and read and accept the full rules and waiver in the organizer’s flow. |
| Third-party code | The README identifies the open-source stack and Mozilla PDF.js 6.4.299 with its Apache-2.0 license. | Preserve the applicable notices when adding third-party libraries. |

## Before submission

1. Set MODEL_API_KEY only in the hosting provider’s server-side secret settings. Do not put it in browser code, the repository, or the recording.
2. Run the normal analysis flow and inspect the actual Muse result, source verification, page highlights, and exported evidence pack.
3. Record the three-minute demo from that same build. Show the real analysis response and explain what the source checks do.
4. Check the app, repository, and video links from a signed-out browser.
5. Confirm the track, entrant/team and representative details, eligibility, and accepted rules in the submission flow.
6. Submit before 4 November 2026 at 9:00 PM ET.

## Product claims to preserve

- EvidenceTrail checks whether a quoted passage occurs in the supplied document; it does not verify a real-world credential or employment claim.
- “Not found” means the supplied CV did not provide verified support; it does not mean the candidate lacks the qualification.
- The report is an evidence review, not a candidate score, ranking, or hiring decision.
