# EvidenceTrail × KUL: recruiter review workflow

**From CV to evidence-backed review: every supported finding points to its source, and every hiring decision stays with the recruiter.**

EvidenceTrail is designed to make application review faster to inspect and easier to explain. Muse interprets candidate experience against a job rubric. Local code verifies source quotes and supported date arithmetic. The recruiter owns Advance, Hold, and Reject decisions. KUL remains the source of truth for candidates and hiring stages.

## Why this matters

In a Robert Half survey of more than 2,000 U.S. hiring managers conducted in November 2025, 65% said AI-enhanced resumes made candidate skills harder to verify. The survey also reports that 38% of hiring managers said their organizations were increasing the number of interviews per candidate as a validation step. These are self-reported U.S. findings; KUL-specific research remains to be done. ([Robert Half, March 10, 2026](https://press.roberthalf.com/2026-03-10-Robert-Half-survey-67-of-HR-leaders-report-AI-generated-applications-are-slowing-hiring))

## What we learn from existing products

Ashby documents job criteria, cited AI findings, unknown or skipped states, reviewer overrides, and criteria filters. Its documented criterion outcomes are Meets, Does not meet, and Undecided. Greenhouse documents a recruiter review stage, Advance/Reject actions, and rejection reasons. ([Ashby AI-Assisted Application Review](https://www.ashbyhq.com/product-updates/ai-assisted-application-review); [Ashby setup and review guide](https://docs.ashbyhq.com/ai-assisted-application-review); [Greenhouse Application Review](https://support.greenhouse.io/hc/en-us/articles/4401963991707-Application-review-stage))

**EvidenceTrail goes further on three documented design points:** it grades evidence strength as **Specific / Stated / Keyword only**; it checks proposed citations against the source page in code and blocks failures; and it gives **Related** its own state with a transfer explanation and the remaining gap. That describes the documented Ashby workflow and our implemented design; it makes no claim about every feature in every competing product.

## The recruiter workflow

### 1. Set the job criteria once

The recruiter pastes the job description. Muse drafts must-have and preferred criteria, preserving the source wording. It flags vague or contradictory requirements for the recruiter to resolve, including whether adjacent experience may count as related. The recruiter reviews and locks a rubric version for that requisition.

If the rubric changes, create a new version, retain a before/after record, and show which applications were evaluated under each version. The current standalone prototype does local JD preflight; a shared, recruiter-edited, versioned rubric remains a KUL integration milestone.

### 2. Open the application where it already lives

In the tournament build, the recruiter uploads CVs to the standalone demo. The current batch limit is five. After the tournament, KUL integration should open the CV from its existing application record so the recruiter does not download and re-upload it.

Extract text with page locations, use OCR for scanned pages, and show a clear processing or retry state when a file cannot be read. We tested an image-only, two-column fictional CV; that demonstrates a document failure mode without claiming how common it is across GCC applicants.

### 3. Muse interprets; local code verifies

For each job requirement, return one of five recruiter-facing states:

- **Clearly shown** — direct CV evidence supports the criterion.
- **Related** — experience may transfer; the finding names what remains unproven.
- **Not shown** — no supporting passage was found; this does not establish that the candidate lacks the skill.
- **Conflict to clarify** — evidence appears inconsistent, such as a date overlap.
- **Needs a closer look** — extraction or interpretation is uncertain.

The evidence strength ladder adds a separate signal:

- **Specific detail:** an anchored example, such as a named project, measurable result, employer, or date.
- **Stated only:** a claim without a concrete example in the CV.
- **Keyword only:** a skill or generic phrase appears without demonstrated use.

The local verifier suppresses support from evidence labeled `keyword_only` or `none`. For every proposed citation, the system checks the quote against the cited page. Failed quotes are excluded from supporting evidence and displayed with the failure reason. The timeline gate routes a detected date discrepancy to human clarification while retaining Muse’s original label and showing the deterministic check.

### 4. Review the whole batch without ranking people

The **requirement matrix** shows one requirement across the applicant batch. The **candidate dossier** shows one applicant’s complete evidence trail. Clicking a finding opens its source page and highlight. Cards put the evidence strength, quote-check result, remaining gap, and follow-up question in view.

The queue can surface work that needs attention, such as a blocked quote or conflict. The applicant order remains the recruiter’s chosen order or ATS stage order; the product does not turn evidence into an unexplained fit score. Keyboard navigation can be added if timed observation shows it saves meaningful effort.

### 5. Record the recruiter’s decision

The recruiter chooses **Advance / Call**, **Hold**, or **Reject**. Hold and Reject should require a job-related reason and allow a short note. A missing passage or date conflict can prompt review, but does not trigger automatic rejection. If a recruiter accepts related evidence, record that as the recruiter’s judgment for this role; the underlying evidence remains labeled Related.

Advance may prepare an editable interview invitation. For the first KUL release, the recruiter remains responsible for sending it; interview scheduling and interview evaluation stay in KUL’s later workflow.

### 6. Preserve the handoff and decision history

The hiring-manager brief should put the decision context first: directly supported requirements, related evidence the recruiter accepted, unresolved questions, and the recruiter’s note. The activity history should record the rubric version, model run, verified and blocked citations, timeline flags, overrides, decision, reason, and timestamp.

The tournament build can export the decision receipt. KUL integration should persist the audit events on the application record and apply KUL’s access and CV retention/deletion policies.

## What is implemented and measured so far

These Muse API runs used fixed fictional CVs. Recruiter use and production outcomes remain unmeasured:

- **Five-case calibration:** Muse matched 16 of 18 expected evidence labels. The deterministic timeline gate routed the two expected date conflicts to review, yielding 18 of 18 expected labels on this set. The same run had 23 of 24 proposed quotes pass the local page/quote check.
- **Current one-request unified demo run (29 Oct):** five Muse calls completed in 30.689 seconds. Muse matched 6/10 expected labels; the timeline gate raised this to 7/10; 14/14 proposed quotes passed local checks. One expected Related finding was labeled Direct, and the keyword-heavy profile's strength labels were missed. Keep this run separate from the older two-request frozen replay and the public-JD calibration. It is a small fictional calibration, not a general accuracy claim; details are in the [live workflow report](live_workflow_latency_20261029.md).
- **Strength-ladder pair:** the filler-heavy fictional CV received `keyword_only` on all three returned findings; the specific-example CV received `specific` on all three. This is one paired demonstration, not a broad accuracy estimate.
- **Separate scanned-CV audit:** OCR analysis matched all 3 expected labels. The verifier accepted 3 of 5 proposed quotes and blocked 2 because they could not be found on the cited page. This is a separate run and denominator from the five-case calibration.
- **Related evidence:** the older public-JD calibration had no related-to-direct overclaims, but the current unified demo run had one. Transfer classification remains an open failure mode; the small test sets do not establish a general rate.
- **Wonder model-choice check:** on the same five public-JD cases and prompts as Spark, Wonder matched 15/18 expected labels before the timeline gate and 17/18 after it, matching Spark's aggregate results. Wonder had zero false Related calls versus Spark's one, but made a different Direct-to-Unsupported miss and marked more findings ambiguous. Its successful-result token estimate was about four times Spark's. Keep Spark as the product default; see the [comparison review](semantic_cases_live_20261028_wonder1_review.md).
- **Spend:** the older Spark runs listed here had about **$0.87 in known token-based estimates**. The Wonder comparison adds **$0.904628** in successful-result estimate, and its separate UAE smoke adds **$0.23252**. Failed and interrupted attempts have unknown usage, so the provider dashboard is authoritative for actual spend; these estimates are not account totals.

The Strength Ladder, quote/page verifier, timeline gate, matrix/dossier, related-evidence gaps, invitation draft, and JSON/HTML exports are in the standalone EvidenceTrail build. KUL application integration, durable decision storage, and a shared locked rubric are still planned work.

## Prove recruiter time savings

No recruiter time study has been run yet. The unified one-job, five-CV fixture and rubric v2 have completed a live Muse run and have frozen result and replay artifacts; see the calibration report index. This is separate from the older five-case calibration, paired Strength Ladder demo, and blocked-quote audit. A Wonder-versus-Spark comparison also completed on the five public-JD cases, with its failed request and earlier interrupted attempt kept separate and usage marked unknown.

Run a no-new-Muse-call study: three reviewers, one job, the same five CVs, and the same rubric in both rounds. Round A uses PDFs and a paper rubric; Round B uses EvidenceTrail. Record minutes per decision and whether each person catches the prewritten date conflict and keyword-only filler. Score a blocked-quote issue only if the frozen unified run actually contains one; otherwise show the earlier scan catch as a separately labelled example. Swap the order for one reviewer and randomize candidate order where possible; repeating the same CVs can still create a practice effect. Treat the result as directional usability evidence, not proof of market fit. Use the [time-study run sheet](time_study_run_sheet_20261028.md) to record real observations.

For a KUL pilot, compare the current process with EvidenceTrail on an authorized requisition. Measure median review minutes, CV/source-page revisits, time to hiring-manager handoff, critical evidence misses, recruiter overrides, and repeat use. A proposed early gate is **at least 25% lower median review time with no increase in critical misses**. Product-market fit and commercial viability still require repeated use and a buyer willing to fund a pilot or deployment.

## Build order

**Tournament:** the unified fixture has frozen live results for replay. If Candidate 5 has no blocked quote, retain the earlier scan audit as a separate trace. Label every fixture and result set accurately.

**After the tournament:** connect reviews to KUL application records; add a shared locked rubric and durable decision history; implement access, retention, and deletion controls; then run the measured recruiter pilot.

**Every supported claim points to a source. Every decision has an owner.**
