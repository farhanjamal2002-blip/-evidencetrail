# Muse latency review — 2026-10-29

## Result

Muse response generation is the dominant wait. In the five-case sequential calibration, the five API calls accounted for 96–98% of end-to-end time. PDF extraction, local quote/page verification, timeline math, and report assembly contributed only about 2–3 seconds across all five CVs.

The app previously omitted `reasoning_effort`, so Muse Spark used its default. A controlled comparison on the same five fictional CVs and public-job-derived JDs found `medium` to be the best measured balance: faster than the prior default, all five analyses completed, and the run had no Related-to-Direct overclaim. `low` was faster again but made one such overclaim, so it is not the default.

## Sequential five-case comparison

| Setting | Median Muse call | Range | Five-case elapsed | Cases completed | Strict label score | After deterministic timeline gate | Related → Direct |
|---|---:|---:|---:|---:|---:|---:|---:|
| Provider default (xhigh) | 27.5 s | 21.7–40.7 s | 144.9 s | 4/5 | 10/14 (71.4%) on returned cases | 11/14 (78.6%) | 0 |
| Medium | 22.5 s | 17.6–27.3 s | 117.3 s | 5/5 | 14/18 (77.8%) | 16/18 (88.9%) | 0 |
| Low | 16.4 s | 15.3–19.0 s | 86.8 s | 5/5 | 13/18 (72.2%) | 15/18 (83.3%) | 1 |

The default run made five API calls, but one result failed app-level processing after the API response; one response used the full 10,000 completion-token limit. The sanitized report does not prove the token cap caused the failure. Its accuracy denominator excludes that failed case, so it is not directly comparable with the two complete runs.

The medium run also had one missed Related label, two date conflicts correctly routed by the deterministic gate, and 22/22 proposed quotes page-matched. The low run had two missed Related labels and 23/23 page-matched quotes. These are results on a small fixed calibration set, not a general accuracy claim.

## Actual recruiter batch path

A separate live request used `/api/analyze-batch` on the unified one-job, five-CV fictional demo, with Muse Spark 1.3 at medium effort:

- End-to-end batch: **64.2 seconds**.
- Five of five candidates completed, with exactly one Muse request per candidate and no retries.
- API request latency ranged from **17.8 to 34.6 seconds**.
- The request start times show the app filling its two concurrent analysis slots; local extraction and finalization added less than one second outside the API-active window.
- Estimated standard-rate token cost: **$0.109738**. This is a token-rate estimate, not provider billing.

The batch completes much faster than the five sequential calibration calls because candidate analyses overlap. Muse remains the bottleneck; local PDF work is not where the wait is going.

The same batch was then run once with five request slots:

| Concurrent slots | Batch elapsed | Candidates | API latency range | Strict labels | After timeline gate | Related → Direct |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 64.2 s | 5/5 | 17.8–34.6 s | Not scored in that run | Not scored in that run | Not scored in that run |
| 5 | 27.9 s | 5/5 | 16.0–27.2 s | 8/10 (80%) | 9/10 (90%) | 1 |

The five-slot run had one Related-to-Direct overclaim on the career-switcher CV and one missed Related label; 17/17 proposed quotes were page-matched. A separate single-CV rerun of that profile at medium effort labeled both findings Related, so the overclaim was not reproduced. This does not establish that concurrency caused the difference; it shows the same input can receive different semantic labels across runs. For the hackathon build, the five-slot default is chosen for the measured speed and exposed as `MAX_CONCURRENT_ANALYSES`; keep human review and do not claim stable accuracy from these small samples.

The targeted C3 repeat took 23.4 seconds end to end, with 23.2 seconds in the Muse request, confirming that the individual model call—not OCR or local verification—is the wait even for a normal text CV.

## Change made

`app.py` now sends `reasoning_effort=medium` by default and allows `MUSE_REASONING_EFFORT=low|medium|high|xhigh` for controlled tuning. Spark 1.3 remains the model. Quote verification and timeline checks remain local and deterministic. The live smoke and semantic evaluation reports now record the selected setting.

## Additional latency work

The analysis and legacy verification requests now set stable `prompt_cache_key` values, and response parsing records provider-reported cached input tokens and reasoning tokens. This can improve cache routing for repeated, identical prompt prefixes; caching is provider-managed, and these changes do not claim a speedup until an actual response reports cached tokens. The semantic evaluator and live smoke report expose those counters so the next intentional Muse run can measure it without inferring from wall-clock noise.

The server also lazily creates one Muse SDK client per process and reuses its HTTP connection pool across concurrent worker-thread requests. This avoids rebuilding a client/pool for each CV and allows keep-alive connections to be reused on later requests. The pool is replaced if the API key changes and closed at process exit. The endpoint was unavailable for a fresh benchmark in this session, so the incremental latency saved by client reuse is not yet measured.

The API response no longer repeats page-preview images in a separate base64 `pages` map: those images are already embedded in `report_html` for the offline evidence pack. The browser now extracts thumbnail sources from that HTML. Against the two saved five-candidate replay payloads, dropping the duplicate map removes 35.6–35.8% of result JSON bytes. This reduces response transfer and duplicate browser-side payload handling; it does not reduce model generation time. Muse API generation remains the dominant end-to-end wait.

## Verification

- Muse request-contract tests: 5 passed.
- Live smoke-summary tests: 2 passed.
- Offline stress suite passed, including fake-Muse response validation, citation attacks, and malformed-PDF cases.
- Local unit coverage checks prompt-cache request fields, cache/reasoning-token parsing, and source thumbnails recovered from the self-contained evidence pack.
- After these payload and telemetry changes: all **99 Python unit tests**, all **13 Node tests**, the offline stress suite, and `git diff --check` passed. These checks made no Muse calls.
- Client-pool reuse now has a concurrency test proving ten parallel first accesses construct a single SDK client.
- Live five-CV batch: HTTP 200, five completed, five Muse calls, no retries.
- The smoke script's first post-call report attempt hit a local `NameError` after Muse had returned HTTP 200. The report-only bug was fixed, and the summary tests passed. No retry was made for that smoke request.

## Artifacts

- [Low-effort calibration](live_latency_low_reasoning_20261029.json)
- [Default-effort calibration](live_latency_default_reasoning_20261029.json)
- [Medium-effort calibration](live_latency_medium_reasoning_20261029.json)
- [Live batch latency report](live_batch_latency_medium_20261029.json)
- [Five-slot batch comparison](live_batch_latency_medium_concurrency5_20261029.json)
- [Targeted career-switcher repeat](targeted_career_switcher_medium_20261029.json)
