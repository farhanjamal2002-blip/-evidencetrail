# EvidenceTrail Recruiter OS — build on the verified core

## Product invariant
EvidenceTrail is an **inspectable evidence layer**, not a replacement ATS and not an automated candidate judge. The existing Meta Muse 1.3 → local PDF text/OCR → source-grounding → scope/timeline gates → human decision path must remain authoritative. No score or automatic rejection; a missing CV claim does not mean missing ability.

## Implemented in this feature branch
- Existing 20-fictional-CV recruiter inbox and original recorded Muse receipts preserved.
- Job-criterion evidence inspector, source geometry, reviewer decisions and prior PDF/HTML exports preserved.
- New human-operated follow-up task, evidence-linked suggested question, editable message, manual status (draft / awaiting external reply / resolved), and copy action. It never sends.
- New received-order review stage summary and filter for drafted, waiting and resolved follow-ups. No candidate ranking or stage mutation without a human action.
- Formula-safe CSV workflow export and per-applicant JSON review export including follow-up.
- Downloadable, deterministic interview-preparation checklist grounded in approved criteria, evidence state and available PDF pages; no AI scores or new inference.
- Local PNG/JPEG CV → bounded one-page PDF conversion → existing OCR and exact source-verification pipeline; retains both original image and normalized PDF SHA-256 hashes.
- Optional native Meta Muse Spark 1.3 **image input** for scanned OCR pages, guarded by `EVIDENCETRAIL_ENABLE_META_VISION=true` and per-request `visual_review=true` and normal CV/Meta consent. Max two small page images, still only one model request for that CV. Off by default, never enabled in public synthetic demo, no paid request in CI. Vision assists layout interpretation only: it cannot establish verified quotations outside independently extracted page text.
- Regression CI: Python, JS, offline stress, and real headless Chromium demo review. Simulation uses zero paid Meta calls.

## Next planned modules (NOT shipped in this PR)
| Phase | Recruiter job | Product module | Safety and integration |
|---|---|---|---|
| 1 | Create vacancies | Templates, role approvals, source JD checklist, reusable rubrics | version and audit every rubric |
| 2 | Intake applications | ATS/webhook/email upload connectors, consent capture, duplicate detection | scoped auth and data minimization |
| 3 | Multimodal document review | Multiple PDF/images, OCR + opt-in vision, voice transcription of consented interviewer notes | preserve source/media timestamps, word/page provenance; never promote generated facts |
| 4 | Review work queue | Personal/team task assignments, response SLAs, resumable state, keyboard commands | tenant roles, reviewer audit and undo |
| 5 | Candidate communication | Human-approved Gmail/ATS outreach, reminders, status responses | explicit action/recipient confirmation; no auto rejection |
| 6 | Scheduling | Calendar availability, interview availability negotiation, reminders | connect an authorized calendar, verify timezone |
| 7 | Interview scorecards | Job-related structured questions, human-entered interview notes, compare requirement evidence | no prohibited traits, no sentiment/voice-based hiring scores |
| 8 | Offer and handoff | Human-approved offer preparation, supporting source documents | HRIS/ATS is system of record |
| 9 | QA and operations | Reviewer time, citation error rate, false-supported labels, accessibility and consent dashboards | aggregate redacted telemetry only; human adjudicated reference |

## Multimodal routing, explicitly separated
1. PDFs, images and scanned resumes: local preflight and OCR produce page-labelled source text.
2. The default Muse request receives page-labelled *text*, **not** raw image/PDF bytes.
3. If the server deliberately enables opt-in vision and the reviewer consents, selected OCR pages are also sent as Meta `image_url` content parts in that same Muse request. Only the original image regions supplement layout interpretation; the final quote must still match OCR text from the actual supplied PDF page.
4. Future audio interview notes should use opt-in transcription with a separate time-coded transcript and speaker-attribution caveat. No speech-based personality, accent or emotion evaluation.
5. If a vision/image output disagrees with local OCR or cannot be sourced, route to human clarification, not an asserted qualification.

## Measurable value rather than invented percentages
Run a randomized, consented A/B pilot on the same job criteria with manual versus assisted human document review, using a new untouched dataset. Pre-register:
- median and p90 recruiter active review seconds per CV
- review source navigation clicks and missed critical criteria
- independently adjudicated false-supported and missed-conflict counts
- percentage of escalated questions resolved by applicants/recruiters
- API requests, paid tokens, successful receipt count and CV byte size
- export completion, keyboard accessibility and unverified claims
A realistic *target* is 30–50% lower active review time without losing genuine discrepancies or overlooking relevant evidence. This is a hypothesis, not an observed result.

## Competition scope / release gate
Keep the current 20-person fictional demo and story easy for judges to understand. Freeze one commit, replay one real consented image-only case if the provider permits the visual flag, test accessibility and fallback, and produce a polished two-minute video. Never call the 80/80 synthetic evaluation real-world accuracy. Keep external ATS, mail, calendar and durable HR storage out of the hackathon release until properly connected.
