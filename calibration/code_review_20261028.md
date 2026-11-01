# EvidenceTrail code review and live verification — 28 Oct 2026

## Scope

Reviewed the CV-to-evidence flow, Muse response validation, deterministic timeline audit, PDF generation and extraction, replay handling, report rendering, upload limits, and offline attack scenarios. This is a local source review and test run, not a formal third-party security audit.

The KUL GitHub runner reached `api.meta.ai` DNS but did not have `MODEL_API_KEY`, so its guard prevented a request. The existing EvidenceTrail workspace had its configured key in a local ignored `.env`; I used it in memory without printing or copying the value. The Render connector showed the EvidenceTrail service but did not offer a command runner. The local app reached Meta successfully. No key was put in the repo or browser.

## Changes completed

1. **Timeline checks:** explicit date-range connectors are required before tenure is counted. Ambiguous strings are excluded from tenure and shown for review with the original page and date text. Overlapping intervals are unioned so months are not double-counted; overlaps shorter than three months do not trigger the conflict gate.
2. **PDF date preservation:** the fixture PDF builder maps Unicode dash variants to ASCII hyphen before writing text. This fixes a real v1 artifact bug: PyMuPDF's built-in font had rendered en dashes as `?`, making dates such as `2021–2026` unverifiable as ranges.
3. **Muse boundary:** both Muse passes use developer-role instructions and strict JSON-schema output. Connection, auth, quota, and provider failures use safe, distinct operator messages without displaying credentials or raw provider errors.
4. **Judge replay:** a fixed `/demo/unified-replay` route serves only the saved fictional Muse replay, validates all five candidate payloads, and never calls the model. The app opens the results beside their original fictional PDFs, keeps the evidence matrix and recruiter decisions interactive, and labels the run as a frozen replay. The synthetic preview remains separately labeled.
5. **Calibration controls:** v1 PDFs and metrics are preserved as historical. Demo-v2 has its own corrected PDFs, rubric, answer key, metrics, and replay. The corrected gold labels distinguish dated supplier-operations experience from specialist procurement evidence and interpret “support supplier negotiations” as support, not final sign-off authority.

## Live Muse evidence

- A minimal `muse-spark-1.3` endpoint smoke returned HTTP 200 with 12 input and 4 output tokens.
- A separate local app smoke used two Muse passes; all three proposed quotes passed local verification. That sample had no Related finding and is not transfer evidence.
- The initial five-CV v2 batch completed C1, C2, C4, and C5. Muse reported 8 successful calls. C3 failed local schema validation; the batch did not automatically retry it.
- One manual C3-only recovery then completed its two Muse passes. No other CV was rerun. The first failed C3 attempt did not return token usage; its actual request count and spend are unknown.
- Combined across the five completed result payloads: Muse matched **9/10** prewritten evidence labels; the deterministic timeline gate produced **10/10** adjudicated labels; strength labels matched **10/10**; the local verifier accepted **18/19** proposed quotes and blocked one C5 quote. The timeline detector found the planted C4 overlap. No Related finding was labelled Direct in this small fictional set. Five findings were marked ambiguous for recruiter review.
- The five successful payloads report **31,590 input** and **42,834 output** tokens, equal to a **$0.221532** token-based estimate at the saved standard rates. This is not a billing record and excludes usage from the failed initial C3 request.
- A separate public-JD calibration covered five fictional cases. Four cases completed initially; one returned HTTP 503. One single-case recovery completed that case; no other case was repeated. Across its five completed payloads, Muse matched **15/18** expected labels, the timeline gate produced **17/18**, there were **0** Related-to-Direct overclaims and **1** missed Related judgment, **2/2** timeline flags were found, and **19/20** proposed quotes passed local checks. The successful results report 38,916 input and 44,954 output tokens, a **$0.2396995** estimate; failed 503 usage is unknown.
- A separate controlled prompt trial on the same five public-JD cases added a rule for named systems versus analogous work. The initial four cases completed; the UAE case had a connection failure and was recovered once in a separate two-call run. Results stayed **15/18** raw and **17/18** after the timeline gate. Related recall changed from **3/4 to 4/4**, while one expected Direct finding became Related; there were still no Related-to-Direct overclaims. Quote checks were **21/21** in this run, but the earlier verifier catch was not reproduced. Successful-result estimate: **$0.22597975**; failed connection usage is unknown. This is a trade-off on a small set, not an accuracy improvement.
- The evaluator supports a process-local `--model muse-wonder-1.0` comparison and model-specific Standard-rate estimates while leaving the product's Spark default unchanged. After the KUL bridge route was confirmed available, the five-case Wonder comparison completed across an initial four-case batch and one manual NHS recovery. Both this run and the saved Spark control use the same case-set and prompt hashes. They each matched 15/18 expected labels, and the deterministic timeline gate raised both to 17/18. Wonder had no false Related calls (Spark had one) but made a different Direct-to-Unsupported miss; quote checks passed 18/18 for Wonder and 21/21 for Spark. Wonder also produced nine ambiguous and two extra unmatched findings, versus Spark's four and zero. Wonder's successful-result estimate was $0.904628, about four times Spark's $0.22597975. This is a small fixed set; keep Spark as default. The initial Wonder batch had one schema-validation failure with unknown usage, and a previous interrupted attempt also has unknown usage; neither is counted as free. See `semantic_cases_live_20261028_wonder1_review.md` for the controlled comparison and accounting.
- A Muse review of the citation-validation excerpt, run with `reasoning_effort: low`, found no concrete citation bypass in the supplied code. Two earlier source-review attempts hit their completion-token caps before returning visible findings; they are recorded in `live_bridge_recovery_20261028.json`.

Machine-readable records: `live_bridge_recovery_20261028.json`, `unified_demo_attempt_20261028_v2.json`, `unified_demo_metrics_20261028_v2.json`, `unified_demo_metrics_20261028_v2_combined.json`, `unified_demo_replay_20261028_v2_combined.json`, and `unified_c3_recovery_20261028_v2.json`.

Public-JD calibration files: `semantic_cases_live_20261028_v2_review.md` and `semantic_cases_live_20261028_v2_combined.json` are the prior prompt-profile baseline. Its undercall was the expected Related transfer from private-sector bid audit trails to public procurement controls; Muse called it Unsupported. The separate `semantic_cases_live_20261028_transfer_prompt_v2_review.md` documents the follow-up prompt trial and its shifted error; do not present it as a measured accuracy fix.

## Verification

- Python: **88 unittest cases passed** using `.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -q`.
- Offline stress suite: all scenarios passed, including six malformed Muse replies, forged-citation rejection, and 128 malformed PDFs. It confirmed zero API requests.
- JavaScript syntax check: passed.
- JavaScript invitation tests: **4 passed**.
- The Python run emitted one Starlette/httpx test-client deprecation warning; it did not cause a failure.

## Remaining checkpoints

- The three-reviewer time study is still unrun; do not claim measured time savings or product-market fit.
- The frozen replay is implemented and locally tested, but the current Render URL still needs a fresh deployment and signed-out judge check.
- The KUL GitHub runner still needs its own key configuration if it is used for GitHub-side live calls; that is separate from the KUL bridge route used for the successful calibrated calls. No private KUL customer or candidate data was used.
- Keep Muse Spark 1.3 as the only model in the critical path. Quote/page checks, OCR, timeline math, and audit output are deterministic local work. Voice, Image, Wonder, and SAM are not required for the demo.
