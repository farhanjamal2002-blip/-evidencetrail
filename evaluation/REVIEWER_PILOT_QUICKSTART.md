# Independent reviewer pilot — ready-to-run volunteer packet

**Status: not yet conducted.** This is the execution packet, not an impact claim or a substitute for observed reviews. Use only fictional CVs.

## Why run this
Measure the active time to an evidenced review, and independently count unsupported claims accepted and relevant evidence missed. Do not substitute satisfaction scores for task outcomes.

## Recruit 4 unfamiliar reviewers
Prefer recruiters or hiring managers not involved in building EvidenceTrail. Even four volunteers yield only an exploratory convenience sample, not representative population evidence. Record anonymous reviewer codes, rough experience band and task timing; not names, employers, email addresses or real CVs.

### Invitation text
> We are testing a fictional-document reviewer tool for a Meta hackathon. Would you independently review a few fictional CVs using ordinary PDF checking and a source-linked reviewer tool? No real applicants are involved and no hiring decisions will be made. We will measure time and whether evidence is missed or overstated. Participation is voluntary and findings are only shared in aggregate.

## Setup
- Frozen public demo: https://evidencetrail-judge-rc1-2026.onrender.com/demo20
- Manual arm: original fictional PDF links available from the public manifest at https://evidencetrail-judge-rc1-2026.onrender.com/demo20/manifest plus the same four recruiter-approved criteria. No model output or QA answer key.
- Assisted arm: same job and equivalent difficulty CVs, inspected in the saved genuine Muse replay; reviewers are free to inspect and disagree with all AI evidence.
- Don't show QA-only reference answers or any precomputed labels to participants.

## Counterbalanced allocation
Give each reviewer 8 *distinct* CVs: four manual and four assisted, covering clear support, role ownership, contradictions, and scanned CVs across both arms. Rotate which arm comes first (ABBA) to reduce order effects. Never let a reviewer inspect the identical CV twice. Pre-register assignments before results, and keep incomplete tasks. Independently adjudicate reference interpretations when possible; use ambiguous for disagreements.

## Stopwatch and error definitions
Start when source CV opens, stop only when the four-criterion worksheet and rationale are submitted. Include AI verification time, source navigation and app waiting. Record unsupported-as-supported, supported-as-missed, unresolved, source clicks, task completion and seconds, with the same definitions in both arms.

## Data collection and reporting
Use evaluation/reviewer_pilot_data_template.csv. Each row is one reviewer x fictional CV task. Running scripts/evaluate_reviewer_pilot.py reports descriptive medians and counts; a header-only file prints NO HUMAN REVIEWER DATA YET and refuses numeric productivity claims.

## Integrity and consent
Ask for permission to publish anonymous aggregate time/error results. No identifying data, personal candidate files or sensitive judgments. Preserve original rows and failures. A smaller or negative effect must be reported. Do not interpret this limited convenience pilot as a representative controlled trial, and do not call saved model responses new live inferences.