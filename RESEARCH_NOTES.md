# EvidenceTrail research and product decisions

Research checked 27 October 2026. This is a focused product scan, not a legal review or a claim that the product is novel.

## What the research says

### Good review starts with job-related criteria

The U.S. Office of Personnel Management's hiring-process guidance starts by identifying the role's critical duties and the knowledge, skills, abilities, or competencies needed to perform them, then deciding which belong in the assessment. Its structured-interview guidance describes using the same questions in the same order, a common rating scale, and agreement on acceptable answers. That supports EvidenceTrail's role-first worksheet: clarify each criterion and prepare a draft question before looking at a CV. A human job expert still needs to review the question and define acceptable evidence. The worksheet does not establish validity, legal compliance, or a complete job analysis.

### A word list cannot diagnose bias

Gaucher, Friesen, and Kay (2011) reported experiments in which masculine-coded job-ad wording affected women's anticipated belongingness and job appeal, while the study did not find that the wording reduced women's perceived ability to do the job. Seong and Parker's 2024 replication and extension found that the main belongingness result appeared in the start-up condition but not the established-firm condition. The evidence supports treating wording as something a person may choose to review, not treating a list match as proof of bias or as a recommendation to avoid a job.

### Resume matching is already a crowded product area

Public projects already advertise explainable resume/job scoring, local open-weight screening, candidate-approved career evidence, and job-application preparation. A resume-to-job match by itself is not a credible novelty claim. EvidenceTrail's product claim is narrower: keep model interpretation attached to exact document passages, verify that the citation exists on the cited PDF page, expose uncertainty and rejected citations, and keep the person responsible for the decision. The no-score role worksheet adds value before a CV is uploaded and is independently useful to a candidate or a hiring team.

## Product decisions

- Keep the role criteria preflight free and separate from Muse. It accepts only job text, makes no Meta request, and does not write a review to persistent storage.
- Parse only numbered and bulleted lines as criteria. Show the source line and do not imply that the parser found every important requirement in the posting.
- Give each extracted line an explicit keyword bucket, reviewer evidence question, draft interview question, candidate self-check, and optional wording refinement. These are prompts to inspect, not ratings.
- Show required/preferred/optional priority only when a criterion or its section heading says so. Preserve the phrase that triggered the label; otherwise display “Not stated.” Never infer a pass/fail threshold.
- Export a standalone HTML worksheet containing job criteria only. Do not include a CV, candidate identity, hidden data, or model-generated judgments.
- Keep the historical word-list reference collapsed and optional. Matches are exact contextual cues; they are not a bias score, hiring recommendation, or legal finding.
- Keep the CV workflow source-grounded and non-ranking. “Not found” describes the supplied document, not the person's real qualifications.

## Next validation targets

Before adding another model or library, test the workflow with real job postings across several formats: numbered lists, bullets, wrapped lines, headings, embedded qualifications, preferred-but-not-required wording, duplicate requirements, and postings with no formal list. Measure how many important criteria the deterministic preflight misses and how often it mislabels explicit priority phrases. Then compare the Muse response with the exact PDF pages and ask a few job seekers and reviewers whether the worksheet is useful and understandable. The current mock suite checks behavior and safety boundaries; it does not measure semantic accuracy or user value.

## Sources

- U.S. Office of Personnel Management, [Confirm the Job Analysis and Assessment Strategy](https://www.opm.gov/policy-data-oversight/human-capital-management/hiring-reform/hiring-process-analysis-tool/confirm-the-job-analysis-and-assessment-strategy/).
- U.S. Office of Personnel Management, [Structured Interview Guide](https://www.opm.gov/policy-data-oversight/assessment-and-selection/structured-interviews/guide.pdf).
- Gaucher, Friesen, and Kay (2011), [Evidence That Gendered Wording in Job Advertisements Exists and Sustains Gender Inequality](https://doi.org/10.1037/a0022530), *Journal of Personality and Social Psychology*.
- Seong and Parker (2024), [Does Gendered Wording in Job Advertisements Deter Women from Joining Start-ups? A Replication and Extension](https://doi.org/10.1002/sej.1489), *Strategic Entrepreneurship Journal*.
- Public product examples: [DeepCandidate](https://github.com/CatalinBalut/deep-candidate-agent) and [Job-Eval](https://job-eval.com/). Their pages describe their own features; this note does not independently validate their performance.
- [Gender Decoder](https://github.com/lovedaybrooke/gender-decoder), the MIT-licensed historical word-list source used for the optional reference.
