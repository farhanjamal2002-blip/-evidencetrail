const form = document.getElementById("analysis-form");
const cvInput = document.getElementById("cv");
const jobInput = document.getElementById("job-description");
const fileName = document.getElementById("file-name");
const charCount = document.getElementById("char-count");
const analyzeButton = document.getElementById("analyze-button");
const errorBox = document.getElementById("error-box");
const analysisStatus = document.getElementById("analysis-status");
const analysisStatusText = document.getElementById("analysis-status-text");
const results = document.getElementById("results");
const uploadZone = document.querySelector(".upload-zone");
let currentReport = "";
let reviewEntries = Object.create(null);
let analysisTimer = null;
let sourcePdfFile = null;
let sourcePdfPayload = null;
let pdfDocumentPromise = null;
let currentPdfRenderTask = null;
let currentPdfRenderSequence = 0;
let currentPdfPage = 1;
let currentPdfZoom = 1;
let activeSourceQuote = "";
let sourceViewerResizeTimer = null;
const PDFJS_VERSION = "6.4.299";
const sourceViewerLaunch = document.getElementById("source-viewer-launch");
const sourceViewer = document.getElementById("source-viewer");
const sourceViewerStatus = document.getElementById("source-viewer-status");
const sourceViewerPageLabel = document.getElementById("source-viewer-page-label");
const sourceViewerStage = document.getElementById("source-viewer-stage");
const sourcePdfPage = document.getElementById("source-pdf-page");
const sourcePdfCanvas = document.getElementById("source-pdf-canvas");
const sourcePdfHighlights = document.getElementById("source-pdf-highlights");

const demoJob = [
  "Role: Procurement Automation Lead",
  "",
  "Requirements:",
  "1. At least five years of Python experience.",
  "2. Current AWS Solutions Architect Professional certification.",
  "3. At least seven years of procurement experience."
].join("\n");

cvInput.addEventListener("change", function () {
  const file = cvInput.files && cvInput.files[0];
  fileName.textContent = file ? file.name : "Choose a PDF or drop it here";
});

["dragenter", "dragover"].forEach(function (eventName) {
  uploadZone.addEventListener(eventName, function (event) {
    event.preventDefault();
    uploadZone.classList.add("is-dragging");
  });
});

["dragleave", "drop"].forEach(function (eventName) {
  uploadZone.addEventListener(eventName, function (event) {
    event.preventDefault();
    uploadZone.classList.remove("is-dragging");
  });
});

uploadZone.addEventListener("drop", function (event) {
  const droppedFile = event.dataTransfer.files && event.dataTransfer.files[0];
  if (!droppedFile || !droppedFile.name.toLowerCase().endsWith(".pdf")) {
    showError("Drop a PDF file here.");
    return;
  }
  const transfer = new DataTransfer();
  transfer.items.add(droppedFile);
  cvInput.files = transfer.files;
  cvInput.dispatchEvent(new Event("change"));
  hideError();
});

jobInput.addEventListener("input", function () {
  charCount.textContent = String(jobInput.value.length);
});

const loadDemoButton = document.getElementById("load-demo-case");
loadDemoButton.addEventListener("click", async function () {
  loadDemoButton.disabled = true;
  loadDemoButton.textContent = "Loading the fictional CV…";
  hideError();
  try {
    const response = await fetch("/demo/cv.pdf");
    if (!response.ok) throw new Error("The sample CV could not be loaded.");
    const samplePdf = await response.blob();
    const sampleFile = new File([samplePdf], "evidencetrail-demo-cv.pdf", {
      type: "application/pdf",
    });
    const transfer = new DataTransfer();
    transfer.items.add(sampleFile);
    cvInput.files = transfer.files;
    cvInput.dispatchEvent(new Event("change"));
    jobInput.value = demoJob;
    jobInput.dispatchEvent(new Event("input"));
    jobInput.focus();
  } catch (error) {
    showError(error.message || "The sample could not be loaded. Download the synthetic CV and choose it manually.");
  } finally {
    loadDemoButton.disabled = false;
    loadDemoButton.textContent = "Load the complete sample case";
  }
});

form.addEventListener("submit", async function (event) {
  event.preventDefault();
  hideError();
  if (!cvInput.files || !cvInput.files.length) {
    showError("Choose the synthetic demo CV or another PDF first.");
    return;
  }

  const submittedPdfFile = cvInput.files[0];
  analyzeButton.disabled = true;
  analyzeButton.querySelector("span:first-child").textContent = "Muse is mapping and checking source evidence…";
  const analysisStartedAt = Date.now();
  function updateAnalysisStatus() {
    const elapsedSeconds = Math.floor((Date.now() - analysisStartedAt) / 1000);
    analysisStatusText.textContent = "Two-pass Muse Spark analysis in progress · " +
      elapsedSeconds + " seconds elapsed.";
  }
  analysisStatus.hidden = false;
  updateAnalysisStatus();
  analysisTimer = window.setInterval(updateAnalysisStatus, 5000);
  const formData = new FormData(form);

  try {
    const response = await fetch("/api/analyze", { method: "POST", body: formData });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Analysis could not be completed.");
    }
    renderResults(payload, submittedPdfFile);
  } catch (error) {
    showError(error.message || "Analysis failed. No result was generated.");
  } finally {
    if (analysisTimer) window.clearInterval(analysisTimer);
    analysisTimer = null;
    analysisStatus.hidden = true;
    analyzeButton.disabled = false;
    analyzeButton.querySelector("span:first-child").textContent = "Analyze with Muse Spark";
  }
});

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function hideError() {
  errorBox.hidden = true;
  errorBox.textContent = "";
}

function renderResults(payload, analyzedFile) {
  const findingsList = document.getElementById("findings-list");
  const counts = { supported: 0, not_found: 0, conflicting: 0 };
  reviewEntries = Object.create(null);
  findingsList.replaceChildren();
  document.getElementById("source-pages").replaceChildren();
  if (currentPdfRenderTask) {
    currentPdfRenderTask.cancel();
    currentPdfRenderTask = null;
  }
  currentPdfRenderSequence += 1;
  sourcePdfFile = analyzedFile || null;
  sourcePdfPayload = payload;
  pdfDocumentPromise = null;
  currentPdfPage = 1;
  currentPdfZoom = 1;
  activeSourceQuote = "";
  sourceViewer.hidden = true;
  sourceViewerLaunch.hidden = !sourcePdfFile;
  sourceViewerStatus.textContent = "The selected PDF is rendered in your browser; it is not sent to the PDF.js CDN.";
  sourceViewerPageLabel.textContent = "Open a source passage to begin";
  sourcePdfPage.hidden = true;
  sourcePdfHighlights.replaceChildren();
  payload.requirements.forEach(function (finding) {
    counts[finding.status] = (counts[finding.status] || 0) + 1;
    findingsList.appendChild(buildFindingCard(finding));
  });
  updateReviewSummary();
  renderEvidenceGraph(payload.evidence_graph || { requirements: [] });

  const countsNode = document.getElementById("summary-counts");
  countsNode.replaceChildren();
  addCount(countsNode, counts.supported, "supported", "supported");
  addCount(countsNode, counts.not_found, "not found", "not_found");
  addCount(countsNode, counts.conflicting, "conflicting", "conflicting");

  const pageNumbers = Object.keys(payload.pages || {}).sort(function (a, b) {
    return Number(a) - Number(b);
  });
  const sourcePages = document.getElementById("source-pages");
  if (pageNumbers.length) {
    const heading = document.createElement("h3");
    heading.textContent = "Verified source pages";
    sourcePages.appendChild(heading);
    const legend = document.createElement("p");
    legend.className = "source-legend";
    [
      ["supporting", "Teal highlight: supporting passage"],
      ["conflicting", "Red highlight: conflicting statement"],
    ].forEach(function (item) {
      const legendItem = document.createElement("span");
      legendItem.className = "source-legend-item";
      const swatch = document.createElement("span");
      swatch.className = "source-swatch " + item[0];
      swatch.setAttribute("aria-hidden", "true");
      legendItem.append(swatch, document.createTextNode(item[1]));
      legend.appendChild(legendItem);
    });
    sourcePages.appendChild(legend);
    pageNumbers.forEach(function (number) {
      const page = document.createElement("section");
      page.className = "source-page";
      page.id = "page-" + number;
      const title = document.createElement("div");
      title.className = "source-page-head";
      title.textContent = "CV page " + number + " · verified highlights";
      const image = document.createElement("img");
      image.src = payload.pages[number];
      image.alt = "CV page " + number + " with verified passages highlighted";
      page.append(title, image);
      sourcePages.appendChild(page);
    });
  }

  const usage = payload.usage || {};
  const ocrText = payload.ocr_pages && payload.ocr_pages.length
    ? " · OCR used on page(s) " + payload.ocr_pages.join(", ")
    : "";
  const rejectedCount = Number(payload.excluded_unverified_requirements || 0);
  const callLabel = Number(payload.analysis_calls || 0) === 2
    ? "2 real Muse Spark passes · requirement mapping + source adjudication"
    : payload.analysis_calls + " real Muse Spark pass(es)";
  const firstUsage = usage.first_pass || {};
  const secondUsage = usage.verification_pass || {};
  const tokenDetails = " · pass 1 " +
    (firstUsage.input_tokens || 0).toLocaleString() + " in / " +
    (firstUsage.output_tokens || 0).toLocaleString() + " out · pass 2 " +
    (secondUsage.input_tokens || 0).toLocaleString() + " in / " +
    (secondUsage.output_tokens || 0).toLocaleString() + " out · total " +
    (usage.input_tokens || 0).toLocaleString() + " in / " +
    (usage.output_tokens || 0).toLocaleString() + " out";
  document.getElementById("run-meta").textContent =
    payload.model + " · " + callLabel + tokenDetails + ocrText +
    (rejectedCount ? " · " + rejectedCount + " model-proposed requirement(s) omitted" : "");
  const quoteAudit = payload.quote_audit || {};
  const proposedQuotes = Number(quoteAudit.proposed || 0);
  const verifiedQuotes = Number(quoteAudit.verified || 0);
  const excludedQuotes = Number(quoteAudit.excluded || 0);
  const secondProposed = Number(quoteAudit.verification_proposed || 0);
  const secondVerified = Number(quoteAudit.verification_verified || 0);
  const secondExcluded = Number(quoteAudit.verification_excluded || 0);
  const ambiguous = Number(quoteAudit.ambiguous_requirements || 0);
  document.getElementById("quote-audit").textContent =
    "Pass 1 exact quote check: " + verifiedQuotes + "/" + proposedQuotes +
    " matched the PDF (" + excludedQuotes + " excluded). Pass 2 source adjudication: " +
    secondVerified + "/" + secondProposed + " citations matched an allowed retrieved span and PDF page (" +
    secondExcluded + " excluded). " + ambiguous + " requirement(s) marked ambiguous. " +
    "A matching quote proves text presence, not qualification truth.";

  const omittedRequirements = Array.isArray(payload.omitted_requirement_audit)
    ? payload.omitted_requirement_audit
    : [];
  const omittedPanel = document.getElementById("omitted-requirements-panel");
  const omittedSummary = document.getElementById("omitted-requirements-summary");
  const omittedList = document.getElementById("omitted-requirements-list");
  omittedList.replaceChildren();
  if (omittedRequirements.length) {
    const omittedCount = omittedRequirements.length;
    omittedPanel.hidden = false;
    omittedSummary.textContent = omittedCount + " model-proposed requirement" +
      (omittedCount === 1 ? "" : "s") + " omitted before evidence review";
    const reasonLabels = {
      empty_requirement: "Muse returned an empty requirement.",
      not_in_job_description: "The wording was not found in the supplied job description.",
      duplicate_requirement: "A duplicate requirement was omitted."
    };
    omittedRequirements.forEach(function (entry) {
      const item = document.createElement("li");
      const requirement = document.createElement("strong");
      requirement.textContent = entry.requirement || "(blank requirement)";
      const reason = document.createElement("span");
      reason.textContent = reasonLabels[entry.reason] || "Omitted during local validation.";
      item.append(requirement, reason);
      omittedList.appendChild(item);
    });
  } else {
    omittedPanel.hidden = true;
  }

  document.getElementById("result-caption").textContent =
    "Muse maps requirements, then reviews locally retrieved source spans. EvidenceTrail verifies each displayed citation against the PDF and shows the source trail for human review; it does not verify real-world qualifications.";

  const provenance = document.getElementById("provenance-details");
  provenance.replaceChildren();
  [
    ["Model", payload.model || ""],
    ["Analysis time (UTC)", payload.created_at || ""],
    ["CV SHA-256", payload.cv_sha256 || ""],
    ["Job description SHA-256", payload.job_sha256 || ""],
  ].forEach(function (entry) {
    if (!entry[1]) return;
    const term = document.createElement("dt");
    term.textContent = entry[0];
    const value = document.createElement("dd");
    value.textContent = entry[1];
    provenance.append(term, value);
  });

  currentReport = payload.report_html || "";
  results.hidden = false;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  results.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
}

function renderEvidenceGraph(graph) {
  const root = document.getElementById("evidence-graph");
  root.replaceChildren();
  const requirements = Array.isArray(graph.requirements) ? graph.requirements : [];
  if (!requirements.length) {
    const empty = document.createElement("p");
    empty.className = "graph-empty";
    empty.textContent = "No requirement-to-source links were returned.";
    root.appendChild(empty);
    return;
  }

  requirements.forEach(function (row) {
    const item = document.createElement("article");
    item.className = "graph-row";

    const requirement = document.createElement("div");
    requirement.className = "graph-requirement";
    const meta = document.createElement("span");
    meta.className = "graph-meta status-" + String(row.status || "not_found");
    meta.textContent = String(row.id || "") + " · " +
      String(row.status || "not_found").replaceAll("_", " ") +
      (row.certainty === "ambiguous" ? " · ambiguous" : "");
    const title = document.createElement("strong");
    title.textContent = String(row.requirement || "");
    requirement.append(meta, title);

    const links = document.createElement("div");
    links.className = "graph-links";
    const arrow = document.createElement("span");
    arrow.className = "graph-arrow";
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = "→";
    links.appendChild(arrow);

    const sources = Array.isArray(row.sources) ? row.sources : [];
    if (!sources.length) {
      const empty = document.createElement("span");
      empty.className = "graph-empty";
      empty.textContent = "No locally verified source link";
      links.appendChild(empty);
    } else {
      sources.forEach(function (source) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "graph-source " +
          (source.role === "contradicts" ? "is-conflict" : "is-support");
        button.dataset.page = String(source.page);
        button.dataset.quote = String(source.quote || "");
        button.setAttribute("aria-label",
          (source.role === "contradicts" ? "Open conflicting passage" : "Open supporting passage") +
          " on page " + source.page);
        const label = document.createElement("span");
        label.textContent = "Page " + source.page + " · " + String(source.source_id || "");
        const quote = document.createElement("q");
        quote.textContent = String(source.quote || "");
        button.append(label, quote);
        links.appendChild(button);
      });
    }

    item.append(requirement, links);
    root.appendChild(item);
  });
}

function addCount(parent, value, label, status) {
  const item = document.createElement("div");
  item.className = "count-pill";
  const strong = document.createElement("strong");
  strong.className = "status-" + status;
  strong.textContent = String(value);
  item.append(strong, document.createTextNode(label));
  parent.appendChild(item);
}

function buildFindingCard(finding) {
  const card = document.createElement("article");
  card.className = "finding-card";
  const body = document.createElement("div");
  body.className = "finding-body";
  const header = document.createElement("div");
  header.className = "finding-header";
  const id = document.createElement("span");
  id.textContent = finding.id;
  const status = document.createElement("span");
  status.className = "status-badge status-" + finding.status;
  status.textContent = finding.status.replace("_", " ");
  header.append(id, status);

  const title = document.createElement("h3");
  title.textContent = finding.requirement;
  const note = document.createElement("p");
  note.className = "finding-note";
  note.textContent = finding.note;
  body.append(header, title);
  if (finding.certainty === "ambiguous") {
    const ambiguity = document.createElement("p");
    ambiguity.className = "ambiguity-flag";
    ambiguity.textContent = "Ambiguous result · inspect the source context before relying on this interpretation.";
    body.appendChild(ambiguity);
  }
  body.appendChild(note);

  if (finding.evidence && finding.evidence.length) {
    const quoteList = document.createElement("div");
    quoteList.className = "quote-list";
    finding.evidence.forEach(function (evidence) {
      const quote = document.createElement("div");
      quote.className = "quote-item" + (evidence.role === "contradicts" ? " contradicts" : "");
      const role = document.createElement("span");
      role.className = "quote-role";
      role.textContent = (evidence.role === "contradicts" ? "Conflicting statement" : "Supporting passage") +
        (evidence.source_id ? " · " + evidence.source_id : "");
      const text = document.createElement("div");
      text.className = "quote-text";
      text.textContent = "“" + evidence.quote + "”";
      const anchor = document.createElement("a");
      anchor.className = "page-anchor";
      anchor.href = "#page-" + evidence.page;
      anchor.dataset.page = String(evidence.page);
      anchor.dataset.quote = evidence.quote;
      anchor.textContent = "Inspect this passage in the original PDF · page " + evidence.page + " →";
      quote.append(role, text, anchor);
      quoteList.appendChild(quote);
    });
    body.appendChild(quoteList);
  }
  card.dataset.findingId = finding.id;
  card.append(body, buildReviewControls(finding.id));
  return card;
}

function buildReviewControls(findingId) {
  const section = document.createElement("section");
  section.className = "human-review-controls";
  const heading = document.createElement("h4");
  heading.textContent = "Human review";
  const explanation = document.createElement("p");
  explanation.className = "review-explanation";
  explanation.textContent = "Record whether this evidence trail was reviewed. This is not a candidate decision.";

  const statusLabel = document.createElement("label");
  statusLabel.className = "review-label";
  statusLabel.htmlFor = "review-status-" + findingId;
  statusLabel.textContent = "Review status";
  const status = document.createElement("select");
  status.id = "review-status-" + findingId;
  status.className = "review-input review-select";
  [
    ["not_reviewed", "Not reviewed"],
    ["reviewed", "Evidence reviewed"],
    ["follow_up", "Needs follow-up"],
  ].forEach(function (choice) {
    const option = document.createElement("option");
    option.value = choice[0];
    option.textContent = choice[1];
    status.appendChild(option);
  });

  const noteLabel = document.createElement("label");
  noteLabel.className = "review-label";
  noteLabel.htmlFor = "review-note-" + findingId;
  noteLabel.textContent = "Reviewer note (optional)";
  const note = document.createElement("textarea");
  note.id = "review-note-" + findingId;
  note.className = "review-input review-note-input";
  note.maxLength = 600;
  note.placeholder = "What should be checked next? Keep notes focused on the document evidence.";

  function saveReview() {
    reviewEntries[findingId] = { status: status.value, note: note.value.trim() };
  }

  status.addEventListener("change", function () {
    saveReview();
    updateReviewSummary();
  });
  note.addEventListener("input", saveReview);
  reviewEntries[findingId] = { status: "not_reviewed", note: "" };
  section.append(heading, explanation, statusLabel, status, noteLabel, note);
  return section;
}

function updateReviewSummary() {
  const summary = document.getElementById("review-summary");
  if (!summary) return;
  const entries = Object.values(reviewEntries);
  const reviewed = entries.filter(function (entry) { return entry.status === "reviewed"; }).length;
  const followUp = entries.filter(function (entry) { return entry.status === "follow_up"; }).length;
  const pending = entries.length - reviewed - followUp;
  summary.textContent = reviewed + " reviewed · " + followUp + " need follow-up · " +
    pending + " not reviewed. Notes stay in this tab until you download the pack.";
}

function buildReviewedReport(reportHtml) {
  const reportDocument = new DOMParser().parseFromString(reportHtml, "text/html");
  const labels = {
    not_reviewed: "Not reviewed",
    reviewed: "Evidence reviewed",
    follow_up: "Needs follow-up",
  };

  reportDocument.querySelectorAll(".finding[data-finding-id]").forEach(function (finding) {
    const findingId = finding.dataset.findingId;
    const entry = reviewEntries[findingId] || { status: "not_reviewed", note: "" };
    const record = reportDocument.createElement("section");
    record.className = "human-review-record";
    const title = reportDocument.createElement("h3");
    title.textContent = "Human review record";
    const status = reportDocument.createElement("p");
    status.textContent = "Review status: " + (labels[entry.status] || labels.not_reviewed);
    record.append(title, status);
    if (entry.note) {
      const note = reportDocument.createElement("p");
      note.textContent = "Reviewer note: " + entry.note;
      record.appendChild(note);
    }
    finding.appendChild(record);
  });

  const disclosure = reportDocument.createElement("p");
  disclosure.className = "sub review-disclosure";
  disclosure.textContent = "Human review records were entered by the reviewer and are separate from Muse output. They do not represent a hiring decision.";
  const intro = reportDocument.querySelector("main .sub");
  if (intro) intro.insertAdjacentElement("afterend", disclosure);
  return "<!doctype html>\n" + reportDocument.documentElement.outerHTML;
}

document.getElementById("findings-list").addEventListener("click", function (event) {
  const target = event.target instanceof Element ? event.target.closest(".page-anchor") : null;
  if (!target || !sourcePdfFile || !sourcePdfPayload) return;
  event.preventDefault();
  void openInteractivePdf(Number(target.dataset.page), target.dataset.quote || "");
});

document.getElementById("evidence-graph").addEventListener("click", function (event) {
  const target = event.target instanceof Element ? event.target.closest(".graph-source") : null;
  if (!target || !sourcePdfFile || !sourcePdfPayload) return;
  void openInteractivePdf(Number(target.dataset.page), target.dataset.quote || "");
});

document.getElementById("open-source-viewer").addEventListener("click", function () {
  void openInteractivePdf(1, "");
});

document.getElementById("close-source-viewer").addEventListener("click", function () {
  sourceViewer.hidden = true;
  document.getElementById("open-source-viewer").focus();
});

document.getElementById("source-viewer-previous").addEventListener("click", function () {
  void openInteractivePdf(Math.max(1, currentPdfPage - 1), "");
});

document.getElementById("source-viewer-next").addEventListener("click", function () {
  void openInteractivePdf(currentPdfPage + 1, "");
});

document.getElementById("source-viewer-zoom-in").addEventListener("click", function () {
  currentPdfZoom = Math.min(2.5, currentPdfZoom + 0.2);
  void openInteractivePdf(currentPdfPage, activeSourceQuote);
});

document.getElementById("source-viewer-zoom-out").addEventListener("click", function () {
  currentPdfZoom = Math.max(0.6, currentPdfZoom - 0.2);
  void openInteractivePdf(currentPdfPage, activeSourceQuote);
});

window.addEventListener("resize", function () {
  if (sourceViewer.hidden || !pdfDocumentPromise) return;
  window.clearTimeout(sourceViewerResizeTimer);
  sourceViewerResizeTimer = window.setTimeout(function () {
    void renderInteractivePdfPage(currentPdfPage);
  }, 160);
});

async function loadPdfJs() {
  const pdfjs = await import(
    "https://cdn.jsdelivr.net/npm/pdfjs-dist@" + PDFJS_VERSION + "/build/pdf.mjs"
  );
  pdfjs.GlobalWorkerOptions.workerSrc =
    "https://cdn.jsdelivr.net/npm/pdfjs-dist@" + PDFJS_VERSION + "/build/pdf.worker.mjs";
  return pdfjs;
}

async function loadSourcePdf() {
  if (!sourcePdfFile) throw new Error("The analyzed PDF is no longer available in this tab.");
  if (!pdfDocumentPromise) {
    pdfDocumentPromise = (async function () {
      const pdfjs = await loadPdfJs();
      const bytes = new Uint8Array(await sourcePdfFile.arrayBuffer());
      return pdfjs.getDocument({
        data: bytes,
        isEvalSupported: false,
        enableXfa: false,
        stopAtErrors: true,
      }).promise;
    })().catch(function (error) {
      pdfDocumentPromise = null;
      throw error;
    });
  }
  return pdfDocumentPromise;
}

async function openInteractivePdf(pageNumber, quote) {
  if (!sourcePdfFile || !sourcePdfPayload) return;
  sourceViewer.hidden = false;
  sourceViewerStatus.textContent = "Opening the original CV in the interactive viewer…";
  sourceViewer.scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
    block: "start",
  });
  activeSourceQuote = quote || "";
  try {
    const pdf = await loadSourcePdf();
    currentPdfPage = Math.max(1, Math.min(Number(pageNumber) || 1, pdf.numPages));
    await renderInteractivePdfPage(currentPdfPage);
  } catch (error) {
    sourceViewerPageLabel.textContent = "Interactive viewer unavailable";
    sourceViewerStatus.textContent =
      "The interactive PDF viewer could not load. The verified highlighted page images remain available below.";
    const fallback = document.getElementById("page-" + pageNumber);
    if (fallback) {
      fallback.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start",
      });
    }
  }
}

async function renderInteractivePdfPage(pageNumber) {
  const sequence = ++currentPdfRenderSequence;
  if (currentPdfRenderTask) {
    currentPdfRenderTask.cancel();
    currentPdfRenderTask = null;
  }
  const pdf = await loadSourcePdf();
  if (sequence !== currentPdfRenderSequence) return;
  const safePageNumber = Math.max(1, Math.min(Number(pageNumber) || 1, pdf.numPages));
  const page = await pdf.getPage(safePageNumber);
  if (sequence !== currentPdfRenderSequence) return;

  const baseViewport = page.getViewport({ scale: 1 });
  const availableWidth = Math.max(240, sourceViewerStage.clientWidth - 36);
  const fitScale = Math.min(1.35, availableWidth / baseViewport.width);
  const viewport = page.getViewport({ scale: fitScale * currentPdfZoom });
  const outputScale = Math.min(window.devicePixelRatio || 1, 2);
  const context = sourcePdfCanvas.getContext("2d", { alpha: false });

  sourcePdfCanvas.width = Math.floor(viewport.width * outputScale);
  sourcePdfCanvas.height = Math.floor(viewport.height * outputScale);
  sourcePdfCanvas.style.width = Math.floor(viewport.width) + "px";
  sourcePdfCanvas.style.height = Math.floor(viewport.height) + "px";
  sourcePdfPage.style.width = Math.floor(viewport.width) + "px";
  sourcePdfPage.style.height = Math.floor(viewport.height) + "px";
  sourcePdfPage.hidden = false;
  sourcePdfHighlights.replaceChildren();

  const pageSize = (sourcePdfPayload.page_dimensions || {})[String(safePageNumber)] || {};
  const pageWidth = Number(pageSize.width) || baseViewport.width;
  const pageHeight = Number(pageSize.height) || baseViewport.height;
  const pageEvidence = [];
  sourcePdfPayload.requirements.forEach(function (finding) {
    (finding.evidence || []).forEach(function (evidence) {
      if (Number(evidence.page) === safePageNumber) {
        pageEvidence.push({ finding: finding, evidence: evidence });
      }
    });
  });

  let highlightCount = 0;
  pageEvidence.forEach(function (entry) {
    const evidence = entry.evidence;
    (evidence.boxes || []).forEach(function (box) {
      if (!Array.isArray(box) || box.length !== 4) return;
      const x0 = Math.max(0, Math.min(pageWidth, Number(box[0]) || 0));
      const y0 = Math.max(0, Math.min(pageHeight, Number(box[1]) || 0));
      const x1 = Math.max(x0, Math.min(pageWidth, Number(box[2]) || 0));
      const y1 = Math.max(y0, Math.min(pageHeight, Number(box[3]) || 0));
      const marker = document.createElement("span");
      marker.className = "pdf-evidence-highlight " +
        (evidence.role === "contradicts" ? "conflicting" : "supporting") +
        (activeSourceQuote && evidence.quote === activeSourceQuote ? " is-active" : "");
      marker.style.left = (x0 / pageWidth * 100) + "%";
      marker.style.top = (y0 / pageHeight * 100) + "%";
      marker.style.width = ((x1 - x0) / pageWidth * 100) + "%";
      marker.style.height = ((y1 - y0) / pageHeight * 100) + "%";
      marker.title = entry.finding.id + " · " +
        (evidence.role === "contradicts" ? "conflicting statement" : "supporting passage") +
        " · " + entry.finding.requirement;
      sourcePdfHighlights.appendChild(marker);
      highlightCount += 1;
    });
  });

  const renderTask = page.render({
    canvasContext: context,
    viewport: viewport,
    transform: outputScale === 1 ? null : [outputScale, 0, 0, outputScale, 0, 0],
  });
  currentPdfRenderTask = renderTask;
  try {
    await renderTask.promise;
  } catch (error) {
    if (error.name !== "RenderingCancelledException") throw error;
    return;
  } finally {
    if (currentPdfRenderTask === renderTask) currentPdfRenderTask = null;
  }
  if (sequence !== currentPdfRenderSequence) return;

  sourceViewerPageLabel.textContent =
    "Page " + safePageNumber + " of " + pdf.numPages + " · " +
    Math.round(currentPdfZoom * 100) + "%";
  sourceViewerStatus.textContent = highlightCount
    ? highlightCount + " verified passage highlight(s) on this page. " +
      "Teal means supporting; red means conflicting."
    : "No verified quote was located on this page.";
  document.getElementById("source-viewer-previous").disabled = safePageNumber <= 1;
  document.getElementById("source-viewer-next").disabled = safePageNumber >= pdf.numPages;
  document.getElementById("source-viewer-zoom-out").disabled = currentPdfZoom <= 0.6;
  document.getElementById("source-viewer-zoom-in").disabled = currentPdfZoom >= 2.5;
}

document.getElementById("download-report").addEventListener("click", function () {
  if (!currentReport) return;
  const blob = new Blob([buildReviewedReport(currentReport)], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "evidencetrail-evidence-pack.html";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
});
