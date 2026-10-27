# EvidenceTrail

Muse Spark maps job requirements to candidate-CV evidence, then adjudicates candidate passages retrieved from locally extracted source blocks. EvidenceTrail checks every displayed quote against the PDF, locates it on the source page, and builds a standalone HTML evidence pack.

The report describes supplied documents. It does not score or rank a candidate and it does not make a hiring decision.

See [HACKATHON_COMPLIANCE.md](HACKATHON_COMPLIANCE.md) for the rule-focused submission checklist.

## Muse Spark integration and open-source stack

The app is built with open-source Python packages, including FastAPI, PyMuPDF, Pillow, pytesseract, and a Python API client. Muse Spark 1.3 is the reasoning layer in a two-pass pipeline through Meta's hosted Model API: a structured requirement-mapping request followed by a structured source-span adjudication request. Between the calls, EvidenceTrail builds a provenance-bearing block catalog and locally ranks relevant spans with BM25-style term retrieval. Deterministic code checks cited text and page locations against the original PDF, derives the displayed status from citations that pass those checks, and renders a requirement-to-source graph. The API key stays server-side, and the report records the model identifier, source fingerprints, and both verification audits.

The optional interactive source viewer uses the Mozilla PDF.js 6.4.299 browser build, bundled under `static/vendor/pdfjs/` with its Apache-2.0 license. The viewer code and worker load from this app's own origin; the original CV stays in the browser while it is being viewed. A real analysis sends the CV to the app and Meta Model API only after consent. If the viewer cannot load, the highlighted page images and standalone HTML evidence pack remain available.

Meta's Muse Spark model and input-mode reference: https://dev.meta.ai/docs/models

## Run locally

Requirements: Python 3.11 or newer and Tesseract OCR. A Meta Model API key is required only for real analysis.

On any OS:

1. Create and activate a virtual environment.
2. Install dependencies with pip install -r requirements.txt.
3. To run real analysis, copy .env.example to .env and add your Meta API key as MODEL_API_KEY. Skip this step to explore the synthetic UI preview.
4. Start the app with uvicorn app:app --reload.
5. Open the local address http://127.0.0.1:8000.

The key stays on the server and must never be committed to the repository.
Click “Preview the finished result · no Meta call” to inspect the result screen without a key. That view uses hand-authored findings grounded in the fictional sample PDF; it is not a Muse result and must not be presented as a live model run. The app header reports whether MODEL_API_KEY is set; it does not validate the key or test API connectivity. If the key is missing, analysis stops before the app extracts or forwards the CV and no Meta call is made.
Each click on “Analyze with Muse Spark” makes two real model requests: the first maps job requirements to candidate CV evidence, and the second adjudicates locally retrieved source spans. Editing the app and loading the synthetic CV do not call the API. The sample analysis uses both requests. Token usage is shown in aggregate and by pass; actual usage depends on the documents and model responses.

The app uses the standard `muse-spark-1.3` model ID. Keep this standard mode for real CVs; Meta’s discounted contributor mode allows submitted content to be used to train future models.

`conflicting` means the CV contains an explicit statement that conflicts with the requirement or contains incompatible claims. Missing evidence remains `not_found`; it is not treated as proof that a candidate lacks a qualification.

Source verification confirms that a quoted text span exists in the supplied CV. Muse supplies the semantic interpretation; the reviewer checks whether that passage actually supports or conflicts with the requirement. Neither the model nor the app verifies real-world credentials or employment history.

The default demo guard allows up to 5 analyses per IP per hour, 20 analyses per running app process, and 2 simultaneous analysis pipelines. The concurrency cap covers PDF reading, extraction/OCR, the Muse request, and report rendering. Requests rejected because both pipeline slots are busy do not consume an analysis slot. Once a PDF passes the basic type and size checks, the request reserves a quota slot before parsing/OCR; malformed PDFs and failed Muse attempts count toward the hourly and process limits. The in-memory limits reset when the process restarts; use persistent rate limiting before running this as a public service.

Docker installs English and Arabic Tesseract language data. The app uses OCR only for pages where local PDF text extraction finds no readable text.

## Demo

The synthetic CV and job description are available in the app. “Preview the finished result · no Meta call” opens a locally generated, clearly labeled UI preview so the screens can be explored before a key is configured. “Load sample inputs for a real run” prepares the same fictional documents for an actual two-pass Muse analysis. The sample contains one supported requirement, one not found, and one internally conflicting claim.

## Analysis flow

1. The browser sends the CV PDF, job description, and explicit consent to the app.
2. PyMuPDF extracts page text, text blocks, word coordinates, and page dimensions. Tesseract supplies OCR text and word boxes for scanned pages.
3. The first structured Muse Spark request receives the original PDF and job description. It returns atomic job requirements and candidate quotes.
4. Local grounding drops requirements not found verbatim in the job description, removes duplicates, and matches first-pass quotes against the source words. Page hints do not decide where a quote is located.
5. EvidenceTrail builds compact source spans from document blocks, keeps page and bounding-box provenance, and ranks candidate spans for each requirement with a lightweight BM25-style lexical retriever. The second structured Muse Spark request receives the requirements and only their allowed candidate source spans, including source IDs, page, bounding box, text, and nearby context.
6. Muse returns a source-linked review. Local checks reject unknown source IDs, quotes absent from their cited span or context, quotes that cannot be located on the cited PDF page, and duplicate citations. The final status is derived from the citations that survive these checks; conflicting claims require explicit incompatible text, while no support remains not found. Uncertain or mismatched results are marked ambiguous for human review.
7. The app builds a requirement-to-source graph. Each graph edge can open the original PDF at the cited page and highlight. The report includes both-pass audit counts, verified quotes, page highlights, CV and job-description SHA-256 fingerprints, and the model identifier.

## Human review record

Reviewers can mark each evidence trail as not reviewed, evidence reviewed, or needing follow-up, then add a short note. These annotations stay in the current browser tab and are added to the downloaded pack; they are not sent to Muse or saved by the app. They record review of the documents, not a hiring decision.

The PDF is sent inline to Meta Model API for analysis with API-side output storage explicitly disabled. EvidenceTrail does not write uploaded CVs to a database, object store, or persistent application file path. FastAPI's multipart UploadFile handling uses a spooled temporary file, so an upload may be held in memory or temporarily placed on the host's temporary disk while the request is parsed and processed ([FastAPI upload-file documentation](https://fastapi.tiangolo.com/tutorial/request-files/#file-parameters-with-uploadfile)). The PDF and job description are sent to Meta only after the user consents. The app does not intentionally retain a durable copy after handling the request; temporary-file cleanup depends on the request/runtime lifecycle.

## Hosting

The repository includes a Render Blueprint at `render.yaml`. It defines a Docker web service in Singapore, uses the existing `/health` endpoint, and sets analysis concurrency to one. Deploy it without a model key to open the UI and synthetic result preview; real analysis remains disabled until the server key is added.

When you are ready for live Muse requests, add `MODEL_API_KEY` in the Render service's Environment page and redeploy. Never commit the key to GitHub or put it in browser code. The Dockerfile installs the OCR dependencies and binds Uvicorn to Render's `PORT`.

The Blueprint requests Render's free web plan. Free services may sleep when idle, so open the demo before a live walkthrough. The app stores no candidate data persistently and needs no attached disk.
