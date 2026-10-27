# EvidenceTrail

EvidenceTrail maps job requirements to exact CV passages. Muse Spark proposes the evidence; the application verifies each quote against the uploaded PDF, locates it on the source page, and builds a standalone HTML evidence pack.

The report describes supplied documents. It does not score or rank a candidate and it does not make a hiring decision.

## Model and open-source stack

The app is built with open-source Python packages, including FastAPI, PyMuPDF, Pillow, pytesseract, and the OpenAI-compatible Python SDK. Muse Spark is called through Meta's hosted Model API; it is not a locally hosted open-weight model. EvidenceTrail sends one structured request per analysis and keeps the API key server-side.

The optional interactive source viewer uses [Mozilla PDF.js](https://github.com/mozilla/pdf.js) 6.4.299 ([Apache-2.0](https://github.com/mozilla/pdf.js/blob/master/LICENSE)), loaded on demand from jsDelivr when a reviewer opens the viewer. The original CV is read from the browser's selected file; it is not sent to the PDF.js CDN. The regular analysis still sends the CV to the app and Meta Model API after consent. If the library cannot load, the existing highlighted page images and standalone HTML evidence pack remain available.

Meta's current model and input-mode reference: https://dev.meta.ai/docs/models

## Run locally

Requirements: Python 3.11 or newer, Tesseract OCR, and a Meta Model API key.

On any OS:

1. Create and activate a virtual environment.
2. Install dependencies with pip install -r requirements.txt.
3. Copy .env.example to .env and add your Meta API key as MODEL_API_KEY.
4. Start the app with uvicorn app:app --reload.
5. Open the local address http://127.0.0.1:8000.

The key stays on the server and must never be committed to the repository.
The app header reports whether MODEL_API_KEY is set; it does not validate the key or test API connectivity. If the key is missing, analysis stops before the app extracts or forwards the CV and no Meta call is made.
Each click on “Analyze with Muse Spark” makes one real model request. Editing the app and loading the synthetic CV do not call the API. The sample analysis does use the API.

The app uses the standard `muse-spark-1.3` model ID. Keep this standard mode for real CVs; Meta’s discounted contributor mode allows submitted content to be used to train future models.

`conflicting` means the CV contains an explicit statement that conflicts with the requirement or contains incompatible claims. Missing evidence remains `not_found`; it is not treated as proof that a candidate lacks a qualification.

Source verification confirms that a quoted text span exists in the supplied CV. Muse supplies the semantic interpretation; the reviewer checks whether that passage actually supports or conflicts with the requirement. Neither the model nor the app verifies real-world credentials or employment history.

The default demo guard allows up to 5 analyses per IP per hour, 20 analyses per running app process, and 2 simultaneous model calls. Requests rejected because both model-call slots are busy do not consume an analysis slot. Failed model attempts count toward the hourly and process limits. The in-memory limits reset when the process restarts; use persistent rate limiting before running this as a public service.

Docker installs English and Arabic Tesseract language data. The app uses OCR only for pages where local PDF text extraction finds no readable text.

## Demo

Use the synthetic CV at /demo/cv.pdf and load the sample job description in the app. It is fictional and contains an intentionally inconsistent procurement experience claim. The example is designed to show supported, not found, and conflicting outcomes in one analysis.

## Analysis flow

1. The browser sends a CV PDF, job description, and explicit consent to the app.
2. The app extracts local page text and word coordinates, with OCR fallback for scanned pages.
3. The app sends the original PDF and job description to Muse Spark in one structured analysis request.
4. The app verifies each quote as a contiguous sequence of source words against extracted or OCR text. Page hints from the model are treated as hints only. Quote candidates tied to rejected or duplicate requirements, or lacking an exact source match, are excluded; the run record reports proposed, matched, and excluded counts.
5. The app checks that each returned requirement appears as a complete sequence of words in the supplied job description. It drops requirements that do not and removes duplicate requirements; the report records how many unverified requirements were omitted.
6. The report includes verified quotes, page highlights, CV and job-description SHA-256 fingerprints, and the model identifier.

## Human review record

Reviewers can mark each evidence trail as not reviewed, evidence reviewed, or needing follow-up, then add a short note. These annotations stay in the current browser tab and are added to the downloaded pack; they are not sent to Muse or saved by the app. They record review of the documents, not a hiring decision.

The PDF is sent inline to Meta Model API for the analysis with API-side output storage explicitly disabled. The app does not save uploaded files to disk or retain them after the request. The PDF and job description leave the app for the Meta analysis, as disclosed in the interface.

## Hosting

The Dockerfile installs OCR dependencies. Set MODEL_API_KEY as a server-side secret in the hosting dashboard and deploy the project as a Python web service. The app exposes /health for a health check.
