# EvidenceTrail recruiter time study — run sheet

**Purpose:** Compare the time and issue-detection performance of PDF-only review with EvidenceTrail on one fixed job and five fixed CVs. This is a small directional usability study. Do not describe it as a production or product-market-fit result.

**Muse spend:** None during the study. Freeze the rubric, CV PDFs, and EvidenceTrail findings before participants begin. Do not change them between rounds.

## Preflight — complete before inviting reviewers

- [x] One job description and one paper rubric used in both rounds: [rubric demo-v1](unified_demo_rubric_v1.md).
- [x] Five CV PDFs for that same job, with stable candidate IDs and upload order: [PDF assets](unified_demo_assets/).
- [ ] Frozen EvidenceTrail results for the same five CVs. The single live attempt did not return a completed batch; see [attempt record](unified_demo_attempt_20261028.json).
- [x] Prewritten planted-issue key: [answer key](unified_demo_answer_key_v1.md). Keep it hidden from reviewers.
- [ ] PDF-only packet and EvidenceTrail replay use the same CV content and rubric. Replay mode is pending the successful frozen Muse result.
- [ ] Three reviewers, timer, and observation sheets are ready. Do not show the answer key to reviewers.

**Fixture check:** The new unified one-job, five-CV fixture is assembled and its scan was confirmed image-only with OCR. Its live Muse results are not frozen yet. The prior five-case calibration, two-CV Strength Ladder demo, and earlier scan catch remain separate evidence sets.

**Blocked-quote rule:** Score the blocked-quote item only if the frozen unified Muse run actually contains a verifier-blocked quote. If it does not, mark that item “not present in this set” for both review conditions and keep the earlier scan audit labelled as a separate example. Never plant or edit a quote failure to force the study result.

## Participant protocol

After the live results and judge replay are frozen, recruit three people who can perform a basic recruiter-style CV review. Tell each person to review all five candidates against the rubric and record a decision plus a short reason. Give the same time limit and instructions in both rounds. Do not teach the planted issues. The human time study has not run.

| Reviewer | Round order | PDF-only total minutes | EvidenceTrail total minutes | Notes |
|---|---|---:|---:|---|
| P1 | PDF → EvidenceTrail |  |  |  |
| P2 | PDF → EvidenceTrail |  |  |  |
| P3 | EvidenceTrail → PDF |  |  |  |

Record the time when each decision is made, including time spent locating evidence. Use a stopwatch or screen recording with participant consent. Do not count setup or instructions in review time.

## Per-reviewer observation sheet

| Reviewer | Condition | Candidate | Minutes to decision | Date conflict noticed? | Keyword-only filler caught? | Actual blocked quote questioned? |
|---|---|---|---:|---|---|---|
| P1 | PDF-only |  |  |  |  |  |
| P1 | EvidenceTrail |  |  |  |  |  |
| P2 | PDF-only |  |  |  |  |  |
| P2 | EvidenceTrail |  |  |  |  |  |
| P3 | PDF-only |  |  |  |  |  |
| P3 | EvidenceTrail |  |  |  |  |  |

Duplicate the candidate rows for all five CVs per condition. Record an issue as caught only if the reviewer states the issue or points to the relevant source before seeing the answer key.

## Results to report

| Measure | PDF-only | EvidenceTrail |
|---|---:|---:|
| Median minutes per candidate decision |  |  |
| Total review time across the five CVs |  |  |
| Date-conflict detections (out of 3 reviewers) |  |  |
| Keyword-only filler detections (out of 3 reviewers) |  |  |
| Actual blocked-quote issue detections (out of 3 reviewers; only if present in this frozen run) |  |  |

Report the actual counts and timings, including any EvidenceTrail misses. Use wording such as: **“Directional study, 3 reviewers, 5 fictional CVs, one job; observed median review time was X versus Y, and reviewers caught A/B/C planted issues.”**

The same CVs in both conditions can cause a practice effect. One reversed order reduces that risk slightly; three reviewers are too few for a statistical claim. Do not convert this result into a general accuracy or time-savings guarantee.
