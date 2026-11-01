# EvidenceTrail scanned-CV Muse calibration — 28 Oct 2026

## Question tested

Does the current upload path read an image-only, two-column CV through local OCR, and does Muse still separate a hard professional credential from adjacent experience after that OCR step?

The public source is the NHS Commercial Solutions Procurement Director posting: <https://apps.trac.jobs/job-advert/7425380?ShowJobAdvert=&feedid=9005>. This case reuses the role and prewritten label rubric from the prior credential-boundary case, with a new fictional CV rendered as a scan. That isolates document ingestion; it is not a new independent job-role evaluation.

## Run control

- PDF: one page, two columns, image only, no searchable text layer; about 30 KB
- Local extraction: OCR used on page 1; key credential and experience wording recovered
- Muse: `muse-spark-1.3` Standard mode
- Requests: **2 expected, 2 reported**; no retries; no failed cases
- Reported usage: **5,976 input tokens; 14,322 output tokens**
- Estimated Standard token cost: **$0.0683385** before any cached-input discount; not a billing record
- Muse received OCR text from the existing pipeline. This run did not use Muse Vision.

## Result

| Requirement | Expected | Muse result | Result |
|---|---|---|---|
| MCIPS professional qualification | Unsupported | Unsupported | Correct |
| MBA or MSc / higher degree | Direct | Direct | Correct |
| UK/EU procurement-law knowledge, with Indian public-procurement experience in the CV | Related | Related | Correct |

The scanned case aligned **3/3** findings with its prewritten labels. Exact quote/page verification was **3/3**. No related transfer was missed or overclaimed. The evaluation report records `ocr_used: true` and `ocr_pages: [1]` so the semantic score cannot be mistaken for a text-layer PDF run.

## Cumulative view

Across the post-fix, credential-boundary, and scanned-CV batches: **5 fictional CV fixtures, 4 unique public job sources, 18 labeled findings, 16/18 (88.9%) strict category accuracy, and 10 reported Muse calls**. The two duration-label disagreements remain visible and gated to human review. Combined estimated Standard token cost is **$0.26429475**, before any cached-input discounts.

One scanned CV is a successful point check, not an OCR accuracy estimate. Keep the OCR indicator visible in demo traces and retain image-only failures in future calibration reports.

Detailed sanitized result: `live_semantic_results_20261028_iter4_scanned.json`. Cumulative report: `live_semantic_results_20261028_cumulative5.json`.
