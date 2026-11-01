# EvidenceTrail independent reviewer pilot — pre-registered protocol

**Purpose:** determine whether the app makes a real recruiter's document review faster **without making evidence judgments worse**. This file defines the test before seeing user results. No observed time savings have been gathered by this protocol.

## Recruitment and materials
- Aim for 4–6 unfamiliar recruiters/hiring reviewers; 2–3 is an exploratory convenience pilot, NOT representative evidence.
- Ask reviewers to consent; do not request real CVs or collect applicant names. Use 20–40 fictional CVs with balanced job family, wording, OCR, scope and genuine contradiction cases.
- Have **two** people independently write or adjudicate the reference interpretation before the first review if possible. Mark disagreements as ambiguous instead of manufacturing gold certainty.
- Do **not** let one reviewer review the identical CV twice across study arms. Split into balanced difficulty sets; counterbalance order (half manual first, half assisted first).

## Instructions to reviewers
Give one approved role checklist, PDF(s), and the same permitted actions in both conditions: determine what the supplied document supports, note uncertainty, and record a human review action. Manual condition uses ordinary PDFs + a blank criterion worksheet. Assisted condition uses EvidenceTrail (saved real Muse analysis plus original source). Reviewers can inspect the source and reject the AI.
No automatic candidate scores or ranking. Record task timestamps honestly, including verification time. Stop the clock only after the criterion worksheet and reviewer note are completed.

## CSV measurements and definitions
One row per reviewer × CV, columns defined in the template below.
- **active_seconds:** stopwatch from opening applicant to submitted review note, including app startup or file navigation if encountered in that task.
- **source_clicks:** approximate source PDF openings or navigation actions (manual and assisted).
- **criterion_unsupported_as_supported:** human recorded a supported interpretation when the independent reference has no supporting CV evidence. This is an important safety error.
- **criterion_supported_missed:** human failed to identify explicit documented support present in the reference. This matters for qualified applicants being overlooked.
- **unresolved_items:** legitimate unknown or conflicting findings still requiring follow-up; not an automatic error.
- **completed:** yes/no; unusable or timed-out runs must stay in the dataset.
- **reviewer_type:** recruiter/hiring manager/other and **experience band** only, no personal names.
- **model_calls:** zero for saved replay, one for truly live model analysis. Never claim historical saved calls were newly executed.
- **condition:** manual or assisted. **Order** and CV difficulty are recorded to assess learning and distribution effects.

## Report method
Only after collection:
1. Report N reviewers, N CV tasks, completion rate, median and p90 **active seconds** by condition and the proportional median improvement. Show raw numerators and denominators.
2. Report false-support and missed-support counts separately, by condition, plus a few real failure examples. Do not collapse these into an unsupported “accuracy score.”
3. Report order effects, unusual delays, inaccessible pages and evaluator disagreements. If small N, present the results as exploratory and **do not attach inferential significance**.
4. If the assisted workflow is slower or worsens false-supported or missed-supported judgments, disclose that and return to engineering; do not cherry-pick a winning subgroup.
5. Distinguish data from fictional CVs, saved genuine model outputs and live new model requests.

## Hackathon go/no-go
- **Strong impact story** only if time improves with no observed evidence-integrity regression in the pilot.
- **No independent reviewers available:** use a timed *illustration* only, clearly labelled a product demonstration; do not present it as measured productivity.
- **Never promise 30–50% savings.** That was an aspirational target and not a measured result.

CSV header:
```csv
reviewer_code,reviewer_type,experience_band,condition,order,cv_id,job_family,difficulty,active_seconds,source_clicks,criterion_unsupported_as_supported,criterion_supported_missed,unresolved_items,completed,model_calls,notes
```
