# EvidenceTrail latency bottleneck review — 2026-10-29

## Scope and method

I followed the five-CV unified demo path through the app routes using the in-process ASGI transport and the local mock provider. This exercises upload handling, PDF extraction/OCR, evidence grounding, verification, page previews, report assembly, and replay loading without calling Muse. I also ran the production Muse route with its OpenAI-compatible client replaced by a local deterministic fake, so prompt construction, parsing, validation, and all downstream stages execute without a network request. No real browser engine was available locally, and the browser relay returned a gateway bearer-token error, so browser paint time remains unmeasured.

The live Muse timings below are from the already-recorded Muse Spark 1.3 medium runs. No Muse request or API credit was used for this review.

## What is slow

| Part of the recruiter flow | Measured result | What it means |
|---|---:|---|
| Muse Spark, one CV | 17.6–27.3 s; median 22.5 s in the five-case run | This is the dominant wait. The app already makes one Muse request per CV and verifies quotes/dates locally. |
| Five-CV batch, five concurrent slots | 27.9 s in the recorded live run | Parallel candidate analysis works. The comparable two-slot run took 64.2 s. Keep the five-slot setting for this five-CV workflow. |
| Ordinary CV, local mock route | About 0.36–0.40 s per CV in the latest run | PDF extraction, local rules, verification, page preview, and HTML assembly are not the long wait. |
| Scanned two-column CV | 1.04–1.30 s in extraction; the latest trace measured 1.299 s in Tesseract OCR | OCR is the clear local bottleneck on scans. Native text, box conversion, and OCR detection were each about 1 ms or less in that trace. |
| Frozen five-CV replay, initial response | 96,382 bytes, down from 476,193 bytes | The initial replay previously transferred all five full HTML packs and their embedded page images, although only one candidate was open. |
| Native-text extraction, synthetic 20-page / 11,650-word CV | Median 813 ms with MuPDF sorting; 211 ms with coordinate-based ordering | The live Muse path skips MuPDF's redundant sorting pass. The exact page-labelled prompt, word set, and quote boxes remained equal. |
| 20-page fake-client route, 12 cited pages | Pipeline 871 → 417 ms; preview rendering 599 → 110 ms; response 3.01 → 2.68 MB | No Muse request was made. All 12 proposed citations verified locally. Direct RGB preview generation removed the PNG round trip and full-page alpha composite. |

Local timing is from one concurrent mock-mode run and will vary with CPU load. The saved Muse run is the evidence for model latency; mock timings must not be presented as live semantic analysis speed.

## Changes made

1. **Quote anchoring searches the cited page first.** A correct page hint now verifies and returns immediately. A wrong hint still falls back through the other pages in document order, preserving the prior recovery behavior. Reading order and token-to-box streams are cached per extracted page so repeated quote checks do not redo layout grouping and tokenization.
2. **Frozen replay reports load on demand.** The initial five-candidate replay now contains structured findings and report URLs, not five embedded HTML packs. The full self-contained report is fetched only when the recruiter downloads it. This reduced the measured initial response by **79.8%**; the first report is about 71 KB and loads on request.
3. **PDF preview rendering reuses one open document.** All cited pages for a CV are rendered in one worker call from one PyMuPDF document. The old path reopened and closed the same PDF once per cited page.
4. **Tesseract language discovery is cached.** Installed OCR languages are checked once per process rather than once per scanned page.
5. **Repeated UI thumbnail parsing is cached, and image decode is lazy.** Revisiting the same result does not parse the embedded report HTML again just to recover page thumbnails.
6. **Analysis responses now include `performance_ms`.** It records upload-buffer read, PDF extraction/OCR, semantic pass, Muse API latency, grounding/timeline, local review rules, preview rendering, report assembly, and handler pipeline time. Mock runs explicitly show `muse_api_ms: null`.
7. **The concurrency-limit error now reports the configured value.** It previously said two analyses even when the configured limit was five.
8. **The live Muse path skips redundant native-text sorting.** MuPDF's sorted text, word, and block extraction took a median 813 ms on a synthetic 20-page, 11,650-word CV. The existing geometric formatter already orders words from their bounding boxes, so the live path now extracts unsorted native text and lets that formatter establish reading order. The mock path and standalone `extract_pdf()` callers keep sorted extraction by default. Across all 12 stored demo PDFs—including both image-only scans—the page-labelled model prompt, OCR decision, word/bounding-box set, and quote anchors were identical between modes. The synthetic extraction median fell to 211 ms (3.85× faster).
9. **Cited-page previews are capped at 1,000 pixels on the long edge.** On a sample print-like page, OCR recognized the same 731 words at the 1,000-pixel cap as at the previous 1,100-pixel cap. The original PDF remains the high-resolution record for detailed review. This reduced the 12-page response from 3,013,117 to about 2,680,000 bytes.
10. **Preview rendering draws on the page image directly.** Removing the full-page RGBA overlay and alpha-composite pass reduced image decode/draw time from about 502 ms to 277 ms for 12 pages. A direct draw differed from the previous alpha-composited pixels by at most 7 RGB levels on the synthetic check while preserving the same highlight regions.
11. **MuPDF preview pixels now go straight to Pillow as RGB.** The old path encoded each raster as PNG and immediately decoded it. Direct use of `pix.samples` produced byte-identical RGB pixels in a regression test and cut the conversion microbenchmark from 21.7 ms to 0.69 ms per page. Together with direct drawing, the 12-page preview stage fell from 599 ms to 110 ms in the fake-client route.
12. **Per-stage latency is now returned and retained in live smoke reports.** The response separates PDF opening, native text extraction, word/bbox conversion, OCR detection/execution, prompt build, model request, decode/validation, quote grounding, timeline, requirement audits, local verification, page rasterization, RGB conversion, highlight drawing, JPEG/base64, HTML pack, and response assembly. `live_smoke_test.py` now retains those timings without retaining CV text or accepted quotes.

## Dense CV stage-by-stage trace

This trace used a synthetic 20-page, 11,782-word CV; 12 citations on 12 pages; and a local fake API client. It made no network request. Timings below are one run and round to whole milliseconds, so small values can display as zero.

| Stage | Measured time | Notes |
|---|---:|---|
| HTTP upload read | <1 ms | 145,553-byte PDF |
| PDF open / structure / dimension checks | <3 ms combined | 20 pages |
| Native text extraction | 129 ms | Unsorted MuPDF extraction on the live path |
| Word + bounding-box conversion | 74 ms | 11,782 words |
| OCR decision | 1 ms | No OCR required for this native-text CV |
| Layout-formatted prompt text | 41 ms | 92,720 characters; fake Muse API latency was 0 ms |
| Fake response decode / schema validation | 1 ms | No network; not a model-speed estimate |
| Requirement + quote grounding | 30 ms | All 12 quotes located and page-anchored |
| Timeline audit / application-claim grounding | 2 ms / <1 ms | No date episodes or application draft in this case |
| JD coverage + role clarity + priority annotation | 2 ms combined | Deterministic local checks |
| Local quote/strength verification + timeline linking | 8 ms | All 12 citations verified |
| Preview PDF open / page raster | <1 ms / 35 ms | 12 cited pages |
| Pixmap → RGB / highlight draw | 17 ms / 2 ms | Direct raw RGB samples; same pixels as PNG decoding |
| JPEG / base64 | 48 ms / 4 ms | 1,000-pixel previews |
| Evidence graph / clarification / application prep | <1 ms combined | Small structured output |
| Hashing / HTML pack / response-object assembly | <1 ms / 13 ms / <1 ms | JSON response was about 2.68 MB |
| Full local app pipeline | 417 ms | Browser upload/paint time is not included |

The separate scanned-CV trace measured 1,300 ms total extraction, including 1,299 ms in OCR. This is why OCR quality was not traded for speed.

## Quote-search microbenchmark

On a synthetic 20-page CV with 4,848 extracted words, 20 repeated quote lookups with the correct page hint took 486 ms before the change and 1.28 ms after page-first lookup and cached token streams (about 99.7% less work in this repeated-lookup case). The benchmark preserves wrong-page fallback, and the unit tests exercise that behavior. This is a targeted synthetic benchmark, not a claim about every CV.

## What not to change yet

- Keep **Muse Spark 1.3 at medium reasoning effort**. The saved low-effort run was faster, but it produced a Related-to-Direct overclaim; medium had no such overclaim on the small measured set. This is an accuracy/latency tradeoff, not a safe speed knob to turn blindly.
- Keep using Muse for semantic interpretation. Do not ask it to calculate timeline overlaps or verify verbatim page quotes; the local deterministic checks already own those tasks.
- Do not claim prompt caching made Muse faster. The sequential medium run reported zero cached input tokens. The batch artifacts do not report a cache-hit counter, so the speed benefit remains unproven.
- OCR remains roughly a 1.0–1.3 second local cost on the prepared scanned CV. If that becomes material on a real batch, benchmark lower-resolution or selective OCR against quote recall before changing it.
- The live-route timing above used a local fake in place of `call_muse`; `muse_api_ms: 0` in that harness is not real Muse telemetry. The saved 17.6–27.3-second Muse timings remain the only evidence for model wait.

## Verification

- 105 Python unit tests passed.
- 13 Node tests passed.
- Python and JavaScript syntax checks passed; `git diff --check` passed.
- The five latency-focused tests cover OCR language caching, one-open multi-page preview rendering and preview dimensions, raw-pixel equivalence, page-first quote lookup with wrong-page fallback, and identical prompt/quote anchors between sorted and fast extraction.
- Route profiling used mock mode or a local fake in place of Muse and made zero live Muse calls.

## Follow-up live Muse baseline

A fresh five-CV run through the current one-request path is now recorded in [live_workflow_latency_20261029.md](live_workflow_latency_20261029.md). It confirms Muse API latency dominates each candidate pipeline (median 99.39%); scanned-CV OCR adds about 0.8 seconds. The same run also surfaced one Related-to-Direct overclaim, so the semantic boundary remains a higher product risk than local CPU latency.
