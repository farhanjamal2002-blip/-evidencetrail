const form = document.getElementById("analysis-form");
const cvInput = document.getElementById("cv");
const jobInput = document.getElementById("job-description");
const fileName = document.getElementById("file-name");
const charCount = document.getElementById("char-count");
const analyzeButton = document.getElementById("analyze-button");
const roleAuditButton = document.getElementById("role-audit-button");
const roleWorksheetButton = document.getElementById("role-worksheet-download");
const roleAuditStatus = document.getElementById("role-audit-status");
const errorBox = document.getElementById("error-box");
const analysisStatus = document.getElementById("analysis-status");
const analysisStatusText = document.getElementById("analysis-status-text");
const results = document.getElementById("results");
const uploadZone = document.querySelector(".upload-zone");
const modelReady = form.dataset.modelReady === "true";
const mockMode = form.dataset.mockMode === "true";
const analysisReady = modelReady || mockMode;
const maxPdfBytes = Number(cvInput.dataset.maxBytes) || 12 * 1024 * 1024;
let currentReport = "";
let reviewEntries = Object.create(null);
let currentClarificationBrief = { items: [] };
let currentCandidateResponses = Object.create(null);
let currentApplicationPrep = { items: [] };
let applicationPrepChecks = Object.create(null);
let analysisTimer = null;
let roleAuditRequestId = 0;
let currentRoleAudit = null;
let sourcePdfFile = null;
let sourcePdfPayload = null;
let pdfDocumentPromise = null;
let currentPdfRenderTask = null;
let currentPdfRenderSequence = 0;
let currentPdfPage = 1;
let currentPdfZoom = 1;
let activeSourceQuote = "";
let sourceViewerResizeTimer = null;
let pdfWorkerBlobUrl = "";
const PDFJS_BASE_URL = "/static/vendor/pdfjs/";
const sourceViewerLaunch = document.getElementById("source-viewer-launch");
const sourceViewer = document.getElementById("source-viewer");
const sourceViewerStatus = document.getElementById("source-viewer-status");
const sourceViewerPageLabel = document.getElementById("source-viewer-page-label");
const sourceViewerStage = document.getElementById("source-viewer-stage");
const sourcePdfPage = document.getElementById("source-pdf-page");
const sourcePdfCanvas = document.getElementById("source-pdf-canvas");
const sourcePdfHighlights = document.getElementById("source-pdf-highlights");
const PDFJS_ASSET_VERSION = "20261027-2";

const demoJob = [
  "Role: Procurement Automation Lead",
  "",
  "Join our fast-paced, competitive team; strong communication skills are essential.",
  "",
  "Requirements:",
  "1. At least five years of Python experience.",
  "2. Current AWS Solutions Architect Professional certification.",
  "3. At least seven years of procurement experience.",
  "4. At least three years of team leadership experience."
].join("\n");

roleAuditButton.addEventListener("click", async function () {
  const description = jobInput.value.trim();
  if (!description) {
    roleAuditStatus.textContent = "Paste a job description first.";
    roleAuditStatus.hidden = false;
    return;
  }
  if (description.length > 18000) {
    roleAuditStatus.textContent = "Keep the job description under 18,000 characters.";
    roleAuditStatus.hidden = false;
    return;
  }

  roleAuditButton.disabled = true;
  roleAuditButton.textContent = "Building the evidence plan…";
  roleAuditStatus.textContent = "Running the check on this app. No CV or Meta request is involved.";
  roleAuditStatus.hidden = false;
  const requestId = ++roleAuditRequestId;
  try {
    const body = new FormData();
    body.append("job_description", description);
    const response = await fetch("/api/role-audit", { method: "POST", body: body });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "The role check could not run.");
    if (requestId !== roleAuditRequestId || description !== jobInput.value.trim()) return;
    const audit = result.role_clarity_audit || {};
    currentRoleAudit = audit;
    renderRoleClarityAudit(audit);
    const total = Number(audit.criteria_count || 0);
    const cues = Number(audit.count || 0);
    const shown = Array.isArray(audit.criteria) ? audit.criteria.length : 0;
    const omitted = Number(audit.criteria_truncated || 0);
    roleAuditStatus.textContent = total || cues
      ? "Role evidence plan ready · " + shown + " listed requirement(s) prepared with evidence prompts" +
        (omitted ? " · " + omitted + " more omitted at the display limit" : "") +
        " · " + cues + " optional wording cue(s). Download the worksheet or edit the job text to rerun."
      : "Role evidence plan ready. No numbered or bulleted requirements or listed wording cues were detected; review the job text manually.";
  } catch (error) {
    if (requestId !== roleAuditRequestId) return;
    roleAuditStatus.textContent = error.message || "The role check could not run. Try again.";
  } finally {
    if (requestId === roleAuditRequestId) {
      roleAuditButton.disabled = false;
      roleAuditButton.textContent = "Build role evidence plan";
    }
  }
});

cvInput.addEventListener("change", function () {
  const file = cvInput.files && cvInput.files[0];
  const resultsWereCleared = clearCurrentResults(true);
  if (!file) {
    fileName.textContent = "Choose a PDF or drop it here";
    if (!resultsWereCleared) hideError();
    return;
  }
  const fileError = getPdfFileError(file);
  if (fileError) {
    cvInput.value = "";
    fileName.textContent = "Choose a PDF or drop it here";
    showError(fileError);
    return;
  }
  fileName.textContent = file.name;
  if (!resultsWereCleared) hideError();
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
  if (!droppedFile) return;
  const fileError = getPdfFileError(droppedFile);
  if (fileError) {
    showError(fileError);
    return;
  }
  const transfer = new DataTransfer();
  transfer.items.add(droppedFile);
  cvInput.files = transfer.files;
  cvInput.dispatchEvent(new Event("change"));
  hideError();
});

jobInput.addEventListener("input", function () {
  clearCurrentResults(true);
  charCount.textContent = String(jobInput.value.length);
});

const loadDemoButton = document.getElementById("load-demo-case");
const loadDemoButtonLabel = mockMode
  ? "Load sample inputs for a local simulation"
  : modelReady ? "Load sample inputs for a real run" : "Load sample inputs";
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
    loadDemoButton.textContent = loadDemoButtonLabel;
  }
});

const previewDemoButton = document.getElementById("preview-demo-results");
const previewDemoButtonLabel = previewDemoButton.textContent.trim();
previewDemoButton.addEventListener("click", async function () {
  previewDemoButton.disabled = true;
  previewDemoButton.textContent = "Preparing synthetic preview…";
  hideError();
  try {
    const responses = await Promise.all([
      fetch("/demo/preview"),
      fetch("/demo/cv.pdf")
    ]);
    if (!responses[0].ok || !responses[1].ok) {
      throw new Error("The synthetic preview could not be prepared.");
    }
    const payload = await responses[0].json();
    const samplePdf = await responses[1].blob();
    const sampleFile = new File([samplePdf], "evidencetrail-demo-cv.pdf", {
      type: "application/pdf",
    });
    renderResults(payload, sampleFile);
  } catch (error) {
    showError(error.message || "The synthetic preview could not be loaded.");
  } finally {
    previewDemoButton.disabled = false;
    previewDemoButton.textContent = previewDemoButtonLabel;
  }
});

form.addEventListener("submit", async function (event) {
  event.preventDefault();
  hideError();
  if (!analysisReady) {
    showError("Real analysis is paused until the server API key is configured. Your files were not submitted.");
    return;
  }
  if (!cvInput.files || !cvInput.files.length) {
    showError("Choose the synthetic demo CV or another PDF first.");
    return;
  }

  const submittedPdfFile = cvInput.files[0];
  const formData = new FormData(form);
  clearCurrentResults(false);
  analyzeButton.disabled = true;
  analyzeButton.setAttribute("aria-busy", "true");
  analyzeButton.querySelector("span:first-child").textContent = mockMode
    ? "Local mock is exercising the review pipeline…"
    : "Muse is mapping and checking source evidence…";
  cvInput.disabled = true;
  jobInput.readOnly = true;
  document.getElementById("consent").disabled = true;
  loadDemoButton.disabled = true;
  previewDemoButton.disabled = true;
  const analysisStartedAt = Date.now();
  function updateAnalysisStatus() {
    const elapsedSeconds = Math.floor((Date.now() - analysisStartedAt) / 1000);
    analysisStatusText.textContent = "Two-pass Muse Spark analysis in progress · " +
      elapsedSeconds + " seconds elapsed.";
  }
  analysisStatus.hidden = false;
  updateAnalysisStatus();
  analysisTimer = window.setInterval(updateAnalysisStatus, 5000);
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
    analyzeButton.disabled = !analysisReady;
    analyzeButton.removeAttribute("aria-busy");
    analyzeButton.querySelector("span:first-child").textContent = mockMode
      ? "Run local mock review"
      : modelReady ? "Analyze with Muse Spark" : "Real analysis unavailable";
    cvInput.disabled = false;
    jobInput.readOnly = false;
    document.getElementById("consent").disabled = false;
    loadDemoButton.disabled = false;
    previewDemoButton.disabled = false;
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

function getPdfFileError(file) {
  if (!/\.pdf$/i.test(file.name || "")) return "Choose a PDF file.";
  if (!file.size) return "That PDF is empty. Choose another file.";
  if (file.size > maxPdfBytes) {
    const limitMb = Math.max(1, Math.round(maxPdfBytes / (1024 * 1024)));
    return "Keep the PDF under " + limitMb + " MB.";
  }
  return "";
}

function clearCurrentResults(showNotice) {
  roleAuditRequestId += 1;
  currentRoleAudit = null;
  roleWorksheetButton.disabled = true;
  document.getElementById("role-clarity-audit").hidden = true;
  document.getElementById("role-clarity-audit-items").replaceChildren();
  document.getElementById("role-clarity-audit-limit").hidden = true;
  document.getElementById("role-criteria-items").replaceChildren();
  document.getElementById("role-criteria-limit").hidden = true;
  document.getElementById("role-language-reference").hidden = true;
  roleAuditStatus.textContent = "";
  roleAuditStatus.hidden = true;
  roleAuditButton.disabled = false;
  roleAuditButton.textContent = "Build role evidence plan";
  if (results.hidden) return false;

  results.hidden = true;
  currentReport = "";
  reviewEntries = Object.create(null);
  currentClarificationBrief = { items: [] };
  currentCandidateResponses = Object.create(null);
  currentApplicationPrep = { items: [] };
  applicationPrepChecks = Object.create(null);
  if (currentPdfRenderTask) {
    currentPdfRenderTask.cancel();
    currentPdfRenderTask = null;
  }
  currentPdfRenderSequence += 1;
  sourcePdfFile = null;
  sourcePdfPayload = null;
  pdfDocumentPromise = null;
  activeSourceQuote = "";
  sourceViewer.hidden = true;
  sourceViewerLaunch.hidden = true;
  sourceViewerStatus.textContent = "";
  sourceViewerPageLabel.textContent = "Open a source passage to begin";
  sourcePdfPage.hidden = true;
  sourcePdfHighlights.replaceChildren();
  document.getElementById("findings-list").replaceChildren();
  document.getElementById("source-pages").replaceChildren();
  document.getElementById("evidence-graph").replaceChildren();
  document.getElementById("job-list-coverage").hidden = true;
  document.getElementById("job-list-coverage-items").replaceChildren();
  document.getElementById("job-list-coverage-limit").hidden = true;
  document.getElementById("summary-counts").replaceChildren();
  document.getElementById("provenance-details").replaceChildren();
  document.getElementById("run-meta").textContent = "";
  document.getElementById("ocr-review-warning").textContent = "";
  document.getElementById("ocr-review-warning").hidden = true;
  document.getElementById("quote-audit").textContent = "";
  document.getElementById("review-summary").textContent = "";
  document.getElementById("preview-notice").textContent = "";
  document.getElementById("preview-notice").hidden = true;
  document.getElementById("omitted-requirements-panel").hidden = true;
  document.getElementById("omitted-requirements-list").replaceChildren();
  document.getElementById("rejected-citations-panel").hidden = true;
  document.getElementById("rejected-citations-summary").textContent = "";
  document.getElementById("rejected-citations-intro").textContent = "";
  document.getElementById("rejected-citations-list").replaceChildren();
  if (showNotice) {
    showError("The CV or job description changed, so the previous evidence map was cleared. Run another analysis to refresh it.");
  }
  return true;
}

function renderResults(payload, analyzedFile) {
  const previewNotice = document.getElementById("preview-notice");
  previewNotice.hidden = !payload.preview_mode && payload.provider_mode !== "mock";
  previewNotice.textContent = payload.preview_mode
    ? "Synthetic preview only: these hand-authored findings use a fictional CV. No Muse Spark or Meta Model API request was made."
    : payload.provider_mode === "mock"
      ? "Local mock simulation only: deterministic heuristics exercise the same pipeline, but this is not Muse analysis and must not be used as a hiring assessment. No Meta API call or model tokens."
      : "";
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
  renderApplicationPrep(payload.application_prep || null);
  renderClarificationBrief(payload.clarification_brief || { items: [] });
  updateReviewSummary();
  renderEvidenceGraph(payload.evidence_graph || { requirements: [] });
  renderJobListCoverage(payload.job_item_coverage || {});
  renderRoleClarityAudit(payload.role_clarity_audit || {});

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
  const callLabel = payload.preview_mode
    ? "synthetic example · no Meta API request"
    : payload.provider_mode === "mock"
      ? "local mock pipeline · no Meta API request"
      : Number(payload.analysis_calls || 0) === 2
        ? "2 real Muse Spark passes · requirement mapping + source adjudication"
        : payload.analysis_calls + " real Muse Spark pass(es)";
  const firstUsage = usage.first_pass || {};
  const secondUsage = usage.verification_pass || {};
  const tokenDetails = payload.preview_mode || payload.provider_mode === "mock"
    ? ""
    : " · pass 1 " +
    (firstUsage.input_tokens || 0).toLocaleString() + " in / " +
    (firstUsage.output_tokens || 0).toLocaleString() + " out · pass 2 " +
    (secondUsage.input_tokens || 0).toLocaleString() + " in / " +
    (secondUsage.output_tokens || 0).toLocaleString() + " out · total " +
    (usage.input_tokens || 0).toLocaleString() + " in / " +
    (usage.output_tokens || 0).toLocaleString() + " out";
  document.getElementById("run-meta").textContent =
    payload.model + " · " + callLabel + tokenDetails + ocrText +
    (rejectedCount ? " · " + rejectedCount +
      (payload.provider_mode === "mock" ? " mock-proposed requirement(s) omitted" : " model-proposed requirement(s) omitted") : "");
  const ocrWarning = document.getElementById("ocr-review-warning");
  const ocrPages = Array.isArray(payload.ocr_pages) ? payload.ocr_pages : [];
  ocrWarning.hidden = ocrPages.length === 0;
  ocrWarning.textContent = ocrPages.length
    ? "OCR was used on page(s) " + ocrPages.join(", ") +
      ". OCR can misread scanned text. Confirm highlighted quotes in the original CV; a missing OCR match does not prove the qualification is absent."
    : "";
  const rejectedPanel = document.getElementById("rejected-citations-panel");
  const rejectedSummary = document.getElementById("rejected-citations-summary");
  const rejectedIntro = document.getElementById("rejected-citations-intro");
  const rejectedList = document.getElementById("rejected-citations-list");
  rejectedList.replaceChildren();
  const verificationAudit = payload.verification_audit || {};
  const rejectedCitations = Array.isArray(verificationAudit.rejected_citations)
    ? verificationAudit.rejected_citations
    : [];
  const rejectedTotal = Number(verificationAudit.excluded || 0);
  rejectedPanel.hidden = false;
  if (payload.preview_mode) {
    rejectedSummary.textContent = "Verifier rejection ledger · synthetic preview";
    rejectedIntro.textContent = "This sample made no model call and contains no rejected model proposal. Live analyses list any second-pass citation rejected by local source checks.";
  } else {
    rejectedSummary.textContent = rejectedTotal + " proposed citation" +
      (rejectedTotal === 1 ? "" : "s") + " rejected by local checks";
    rejectedIntro.textContent = rejectedTotal
      ? (payload.provider_mode === "mock"
        ? "These mock proposals did not pass source validation, so they are excluded from the displayed status, highlights, and evidence graph."
        : "These model proposals did not pass source validation, so they are excluded from the displayed status, highlights, and evidence graph.")
      : "No second-pass citations were rejected in this run. Every displayed citation still passed the local source checks.";
    const rejectionLabels = {
      source_not_allowed: "Source ID was not allowed for this requirement",
      invalid_evidence_role: "Evidence role was not supported",
      empty_quote: "The proposed quote was empty",
      quote_outside_retrieved_span: "Quote was outside the retrieved source text",
      source_page_unavailable: "The cited page was unavailable",
      quote_not_found_on_cited_page: "Quote could not be located on the cited PDF page",
      duplicate_citation: "Duplicate citation"
    };
    rejectedCitations.forEach(function (record) {
      const item = document.createElement("li");
      item.className = "rejected-item";
      const reason = document.createElement("strong");
      reason.textContent = rejectionLabels[record.reason] || "Rejected by local source validation";
      const source = document.createElement("span");
      source.textContent = (record.requirement_id || "") + " · " +
        (record.source_id || "no source ID") + (record.role ? " · " + record.role : "");
      item.append(reason, source);
      if (record.quote) {
        const quote = document.createElement("blockquote");
        quote.textContent = record.quote;
        item.appendChild(quote);
      }
      rejectedList.appendChild(item);
    });
    if (rejectedTotal > rejectedCitations.length) {
      const more = document.createElement("li");
      more.className = "rejected-more";
      more.textContent = (rejectedTotal - rejectedCitations.length) +
        " additional rejected citation(s) are counted in the audit but not displayed.";
      rejectedList.appendChild(more);
    }
  }

  const quoteAudit = payload.quote_audit || {};
  const proposedQuotes = Number(quoteAudit.proposed || 0);
  const verifiedQuotes = Number(quoteAudit.verified || 0);
  const excludedQuotes = Number(quoteAudit.excluded || 0);
  const secondProposed = Number(quoteAudit.verification_proposed || 0);
  const secondVerified = Number(quoteAudit.verification_verified || 0);
  const secondExcluded = Number(quoteAudit.verification_excluded || 0);
  const ambiguous = Number(quoteAudit.ambiguous_requirements || 0);
  const auditNode = document.getElementById("quote-audit");
  if (payload.preview_mode) {
    auditNode.textContent =
      "Synthetic sample only: quotes are locally checked against the fictional PDF; " +
      "no model verification or token usage is represented.";
  } else {
    auditNode.textContent =
      "Pass 1 exact quote check: " + verifiedQuotes + "/" + proposedQuotes +
      " matched the PDF (" + excludedQuotes + " excluded). Pass 2 source adjudication: " +
      secondVerified + "/" + secondProposed + " citations matched an allowed retrieved span and PDF page (" +
      secondExcluded + " excluded). " + ambiguous + " requirement(s) marked ambiguous. " +
      "A matching quote proves text presence, not qualification truth.";
  }

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

  document.getElementById("result-caption").textContent = payload.preview_mode
    ? "This fictional sample shows the finished review screen. The findings are illustrative, not Muse output. Select the sample inputs and run Analyze for a real Muse Spark result."
    : "Muse maps requirements, then reviews locally retrieved source spans. EvidenceTrail verifies each displayed citation against the PDF and shows the source trail for human review; it does not verify real-world qualifications.";

  const provenance = document.getElementById("provenance-details");
  provenance.replaceChildren();
  [
    ["Model", payload.model || ""],
    [payload.preview_mode ? "Preview generated (UTC)" : "Analysis time (UTC)", payload.created_at || ""],
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

function renderJobListCoverage(coverage) {
  const panel = document.getElementById("job-list-coverage");
  const summary = document.getElementById("job-list-coverage-summary");
  const list = document.getElementById("job-list-coverage-items");
  const limitNote = document.getElementById("job-list-coverage-limit");
  list.replaceChildren();
  const items = Array.isArray(coverage.items) ? coverage.items : [];
  panel.hidden = !items.length;
  if (!items.length) return;

  const matched = Number(coverage.matched || 0);
  const needsReview = Number(coverage.needs_review || 0);
  summary.textContent = "Job-description list audit · " + matched +
    " wording match(es) · " + needsReview + " need review";
  items.forEach(function (entry) {
    const item = document.createElement("li");
    const label = document.createElement("strong");
    const status = entry.status === "matched" ? "wording match" : "needs review";
    label.className = entry.status === "matched"
      ? "coverage-matched"
      : "coverage-needs-review";
    label.textContent = String(entry.id || "JD") + " · " + status +
      (entry.requirement_id ? " → " + entry.requirement_id : "");
    const text = document.createElement("span");
    text.textContent = String(entry.text || "");
    item.append(label, text);
    list.appendChild(item);
  });
  const truncated = Number(coverage.truncated || 0);
  limitNote.hidden = truncated < 1;
  limitNote.textContent = truncated +
    " additional list item(s) were not displayed because of the audit limit.";
}

function renderRoleClarityAudit(audit) {
  currentRoleAudit = audit;
  const panel = document.getElementById("role-clarity-audit");
  const summary = document.getElementById("role-clarity-audit-summary");
  const disclosure = document.getElementById("role-clarity-audit-disclosure");
  const criteriaList = document.getElementById("role-criteria-items");
  const criteriaLimitNote = document.getElementById("role-criteria-limit");
  const cuesList = document.getElementById("role-clarity-audit-items");
  const cuesLimitNote = document.getElementById("role-clarity-audit-limit");
  const languageReference = document.getElementById("role-language-reference");
  const worksheetButton = document.getElementById("role-worksheet-download");
  const criteria = Array.isArray(audit.criteria) ? audit.criteria : [];
  const items = Array.isArray(audit.items) ? audit.items : [];
  criteriaList.replaceChildren();
  cuesList.replaceChildren();
  languageReference.hidden = !items.length;
  languageReference.open = false;
  worksheetButton.disabled = !criteria.length;
  panel.hidden = !items.length && !criteria.length;
  panel.open = criteria.length > 0;
  if (panel.hidden) return;

  const count = Number(audit.count || 0);
  const criterionCount = Number(audit.criteria_count || criteria.length);
  summary.textContent = "Free role preflight · " + criterionCount + " criterion" +
    (criterionCount === 1 ? "" : "s") + " · " + count + " optional wording cue" +
    (count === 1 ? "" : "s");
  disclosure.textContent = String(audit.disclosure ||
    "Keyword-based drafting prompts only. Review them before use; no criterion is rated.");
  criteria.forEach(function (entry) {
    const item = document.createElement("li");
    const heading = document.createElement("strong");
    heading.textContent = "JD line " + String(entry.line || "—") + " · " +
      String(entry.kind || "Requirement") + " · Priority: " +
      String(entry.priority || "Not stated");
    const source = document.createElement("blockquote");
    source.textContent = String(entry.text || "");
    const priorityBasis = document.createElement("span");
    priorityBasis.className = "role-audit-priority";
    priorityBasis.textContent = "Priority wording: " + String(entry.priority_basis || "Not stated");
    const reviewer = document.createElement("span");
    reviewer.className = "role-audit-prompt";
    reviewer.textContent = "Before reviewing applications: " + String(entry.reviewer_prompt || "");
    const interview = document.createElement("span");
    interview.className = "role-audit-interview";
    interview.textContent = "Draft interview question: " + String(entry.interview_question || "");
    const candidate = document.createElement("span");
    candidate.className = "role-audit-candidate";
    candidate.textContent = "For a candidate: " + String(entry.candidate_prompt || "");
    const rewrite = document.createElement("span");
    rewrite.className = "role-audit-rewrite";
    rewrite.textContent = "Possible tightening: " + String(entry.rewrite_prompt || "");
    item.append(heading, source, priorityBasis, reviewer, interview, candidate, rewrite);
    if (entry.possible_exact_duplicate_of) {
      const duplicate = document.createElement("span");
      duplicate.className = "role-audit-duplicate";
      duplicate.textContent = "Exact duplicate of " + String(entry.possible_exact_duplicate_of) + " · check whether both lines are needed.";
      item.appendChild(duplicate);
    }
    criteriaList.appendChild(item);
  });
  items.forEach(function (entry) {
    const item = document.createElement("li");
    const label = document.createElement("strong");
    label.textContent = String(entry.category || "Wording cue") + " · “" +
      String(entry.cue || "") + "”";
    const excerpt = document.createElement("blockquote");
    excerpt.textContent = String(entry.excerpt || "");
    const question = document.createElement("span");
    question.className = "role-audit-prompt";
    question.textContent = "Reviewer prompt: " + String(entry.review_question || "");
    const rewrite = document.createElement("span");
    rewrite.className = "role-audit-rewrite";
    rewrite.textContent = "Tighten it: " + String(entry.rewrite_prompt || "");
    item.append(label, excerpt, question, rewrite);
    cuesList.appendChild(item);
  });
  const criteriaTruncated = Number(audit.criteria_truncated || 0);
  criteriaLimitNote.hidden = criteriaTruncated < 1;
  criteriaLimitNote.textContent = criteriaTruncated +
    " additional requirement(s) were omitted from this view.";
  const cuesTruncated = Number(audit.truncated || 0);
  cuesLimitNote.hidden = cuesTruncated < 1;
  cuesLimitNote.textContent = cuesTruncated +
    " additional language cue(s) were omitted from this view.";
}

function escapeRoleWorksheetHtml(value) {
  return String(value == null ? "" : value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function buildRoleWorksheetHtml(audit) {
  const criteria = Array.isArray(audit.criteria) ? audit.criteria : [];
  const truncated = Number(audit.criteria_truncated || 0);
  const rows = criteria.map(function (entry) {
    const duplicate = entry.possible_exact_duplicate_of
      ? "<p><strong>Duplicate check:</strong> exact duplicate of " +
        escapeRoleWorksheetHtml(entry.possible_exact_duplicate_of) + " · review whether both lines are needed.</p>"
      : "";
    return "<article><h2>JD line " + escapeRoleWorksheetHtml(entry.line) + " · " +
      escapeRoleWorksheetHtml(entry.kind) + "</h2><blockquote>" +
      escapeRoleWorksheetHtml(entry.text) + "</blockquote><p><strong>Priority:</strong> " +
      escapeRoleWorksheetHtml(entry.priority || "Not stated") + " — " +
      escapeRoleWorksheetHtml(entry.priority_basis || "No explicit priority wording found") +
      "</p><p><strong>Reviewer evidence check:</strong> " +
      escapeRoleWorksheetHtml(entry.reviewer_prompt) +
      "</p><p><strong>Draft interview question:</strong> " +
      escapeRoleWorksheetHtml(entry.interview_question) +
      "</p><p><strong>Candidate self-check:</strong> " +
      escapeRoleWorksheetHtml(entry.candidate_prompt) +
      "</p><p><strong>Possible wording refinement:</strong> " +
      escapeRoleWorksheetHtml(entry.rewrite_prompt) + "</p>" + duplicate + "</article>";
  }).join("");
  return "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">" +
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>EvidenceTrail role worksheet</title>" +
    "<style>body{font:16px/1.6 system-ui,sans-serif;max-width:850px;margin:36px auto;padding:0 20px;color:#172333;background:#f6f8fb}h1{font-size:30px}h2{font-size:18px}article{margin:18px 0;padding:18px 22px;border:1px solid #dbe3ed;border-radius:12px;background:#fff;break-inside:avoid}blockquote{margin:10px 0;padding:12px;border-left:3px solid #456dd7;background:#f5f7fc}p{margin:9px 0}footer{margin-top:30px;color:#58677a;font-size:13px}@media print{body{background:#fff;margin:0;padding:0}}</style>" +
    "</head><body><h1>Role criteria evidence plan</h1><p>Prepared from numbered and bulleted job-description lines by EvidenceTrail. Use this worksheet to clarify observable evidence and prepare a consistent review.</p>" +
    "<p>Draft interview questions should be reviewed by a job expert; if used, ask the same relevant question and apply the same documented standard to each candidate.</p>" +
    (truncated ? "<p><strong>Coverage limit:</strong> " + escapeRoleWorksheetHtml(truncated) + " additional listed requirement(s) are not included in this worksheet. Check the original posting for the rest.</p>" : "") +
    "<p>Priority labels reflect explicit words in each line only. They do not infer importance, rate the role, assess applicants, or provide legal advice. Check all prompts before use.</p>" +
    rows + "<footer>Prepared " + escapeRoleWorksheetHtml(new Date().toLocaleString()) +
    " · This worksheet contains job criteria only. No CV or applicant data is included.</footer></body></html>";
}

roleWorksheetButton.addEventListener("click", function () {
  if (!currentRoleAudit || !Array.isArray(currentRoleAudit.criteria) || !currentRoleAudit.criteria.length) return;
  const blob = new Blob([buildRoleWorksheetHtml(currentRoleAudit)], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "evidencetrail-role-worksheet.html";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  roleAuditStatus.textContent = "Worksheet downloaded. It contains the job criteria only, with no CV or applicant data.";
  roleAuditStatus.hidden = false;
});

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

function renderApplicationPrep(prep) {
  const panel = document.getElementById("application-prep");
  const list = document.getElementById("application-prep-items");
  const disclosure = document.getElementById("application-prep-disclosure");
  const empty = document.getElementById("application-prep-empty");
  const status = document.getElementById("application-prep-status");
  applicationPrepChecks = Object.create(null);
  currentApplicationPrep = {
    items: prep && Array.isArray(prep.items) ? prep.items : [],
  };
  list.replaceChildren();
  status.textContent = "";
  panel.hidden = !prep;
  if (!prep) return;

  disclosure.textContent = prep.disclosure ||
    "This is a document checklist for candidates. Check every detail against your own records and only add accurate information.";
  empty.hidden = currentApplicationPrep.items.length !== 0;
  empty.textContent = "No missing, conflicting, or ambiguous items were flagged in this document review. Verify each CV claim against your own records before applying.";

  currentApplicationPrep.items.forEach(function (entry, index) {
    const item = document.createElement("li");
    item.className = "application-prep-item";
    item.dataset.requirementId = String(entry.requirement_id || "");
    const meta = document.createElement("div");
    meta.className = "application-prep-meta";
    meta.textContent = String(entry.requirement_id || "") + " · " +
      String(entry.status || "needs review").replaceAll("_", " ");
    const requirement = document.createElement("h4");
    requirement.textContent = String(entry.requirement || "");
    const action = document.createElement("p");
    action.className = "application-prep-action";
    action.textContent = String(entry.action || "Review this item against your records.");
    item.append(meta, requirement, action);

    const evidence = Array.isArray(entry.evidence) ? entry.evidence : [];
    if (evidence.length) {
      const sources = document.createElement("div");
      sources.className = "application-prep-sources";
      evidence.forEach(function (source) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "application-prep-source";
        button.dataset.page = String(source.page);
        button.dataset.quote = String(source.quote || "");
        button.textContent = (source.role === "contradicts" ? "Conflicting passage" : "Related passage") +
          " · CV page " + String(source.page) + " · “" + String(source.quote || "") + "”";
        sources.appendChild(button);
      });
      item.appendChild(sources);
    }

    const reviewLabel = document.createElement("label");
    reviewLabel.className = "application-prep-check-label";
    const check = document.createElement("input");
    check.type = "checkbox";
    check.dataset.requirementId = String(entry.requirement_id || "");
    check.dataset.itemIndex = String(index);
    reviewLabel.append(check, document.createTextNode(" I checked this against my records"));
    item.appendChild(reviewLabel);
    list.appendChild(item);
  });
}

function applicationPrepText() {
  const lines = [
    "EvidenceTrail · before-you-apply checklist",
    "Document review only. This does not determine whether you have a qualification.",
    "Check your records; add or correct CV details only when accurate.",
    "",
  ];
  if (!currentApplicationPrep.items.length) {
    lines.push("No missing, conflicting, or ambiguous items were flagged in this document review.");
  }
  currentApplicationPrep.items.forEach(function (entry) {
    const checked = applicationPrepChecks[entry.requirement_id] ? "x" : " ";
    lines.push("[" + checked + "] " + String(entry.requirement_id || "") + " · " + String(entry.requirement || ""));
    lines.push(String(entry.action || ""));
    (Array.isArray(entry.evidence) ? entry.evidence : []).forEach(function (source) {
      lines.push("CV page " + String(source.page) + " · “" + String(source.quote || "") + "”");
    });
    lines.push("");
  });
  return lines.join("\n").trim() + "\n";
}

function renderClarificationBrief(brief) {
  const section = document.getElementById("clarification-brief");
  const list = document.getElementById("clarification-brief-items");
  const disclosure = document.getElementById("clarification-brief-disclosure");
  const status = document.getElementById("clarification-brief-status");
  currentClarificationBrief = {
    items: Array.isArray(brief.items) ? brief.items : [],
  };
  currentCandidateResponses = Object.create(null);
  list.replaceChildren();
  status.textContent = "";
  section.hidden = currentClarificationBrief.items.length === 0;
  if (section.hidden) return;

  disclosure.textContent = brief.disclosure ||
    "Draft prompts for consistent, job-related follow-up. Review before use; they are not sent to anyone and do not make a hiring decision.";
  currentClarificationBrief.items.forEach(function (entry) {
    const item = document.createElement("li");
    item.className = "clarification-brief-item";
    item.dataset.requirementId = String(entry.requirement_id || "");
    const meta = document.createElement("div");
    meta.className = "clarification-brief-item-head";
    meta.textContent = String(entry.requirement_id || "") + " · " +
      String(entry.status || "needs review").replaceAll("_", " ");
    const requirement = document.createElement("h4");
    requirement.textContent = String(entry.requirement || "");
    const question = document.createElement("p");
    question.className = "clarification-question";
    question.textContent = String(entry.question || "");
    const reason = document.createElement("p");
    reason.className = "clarification-reason";
    reason.textContent = String(entry.reason || "");
    item.append(meta, requirement, question, reason);

    const evidence = Array.isArray(entry.evidence) ? entry.evidence : [];
    if (evidence.length) {
      const sources = document.createElement("div");
      sources.className = "clarification-sources";
      evidence.forEach(function (source) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "clarification-source";
        button.dataset.page = String(source.page);
        button.dataset.quote = String(source.quote || "");
        button.textContent = (source.role === "contradicts" ? "Conflicting passage" : "Related passage") +
          " · page " + String(source.page) + " · “" + String(source.quote || "") + "”";
        sources.appendChild(button);
      });
      item.appendChild(sources);
    }

    const responseSection = document.createElement("div");
    responseSection.className = "candidate-response-entry";
    const responseLabel = document.createElement("label");
    const responseId = "candidate-response-" + String(entry.requirement_id || "item");
    responseLabel.className = "candidate-response-label";
    responseLabel.htmlFor = responseId;
    responseLabel.textContent = "Candidate reply · optional session record";
    const responseInput = document.createElement("textarea");
    responseInput.id = responseId;
    responseInput.className = "candidate-response-input";
    responseInput.maxLength = 1500;
    responseInput.placeholder = "Record the candidate’s reply in their own words. This will stay separate from CV evidence.";
    const responseActions = document.createElement("div");
    responseActions.className = "candidate-response-actions";
    const saveResponse = document.createElement("button");
    saveResponse.type = "button";
    saveResponse.className = "candidate-response-save";
    saveResponse.dataset.action = "save-response";
    saveResponse.textContent = "Record reply in pack";
    const removeResponse = document.createElement("button");
    removeResponse.type = "button";
    removeResponse.className = "candidate-response-remove";
    removeResponse.dataset.action = "remove-response";
    removeResponse.textContent = "Remove";
    removeResponse.hidden = true;
    const responseStatus = document.createElement("p");
    responseStatus.className = "candidate-response-status";
    responseStatus.setAttribute("role", "status");
    responseStatus.textContent = "No candidate reply recorded.";
    responseActions.append(saveResponse, removeResponse);
    responseSection.append(responseLabel, responseInput, responseActions, responseStatus);
    item.appendChild(responseSection);
    list.appendChild(item);
  });
}

function clarificationBriefText() {
  const lines = [
    "EvidenceTrail · draft clarification questions",
    "Review before use. These prompts are not a hiring decision.",
    "",
  ];
  currentClarificationBrief.items.forEach(function (entry) {
    lines.push(String(entry.requirement_id || "") + " · " + String(entry.requirement || ""));
    lines.push(String(entry.question || ""));
    (Array.isArray(entry.evidence) ? entry.evidence : []).forEach(function (source) {
      lines.push("Context · CV page " + String(source.page) + " · “" + String(source.quote || "") + "”");
    });
    lines.push("");
  });
  return lines.join("\n").trim();
}

async function copyClarificationBrief() {
  const status = document.getElementById("clarification-brief-status");
  const text = clarificationBriefText();
  if (!text) return;
  try {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      await navigator.clipboard.writeText(text);
    } else {
      const fallback = document.createElement("textarea");
      fallback.value = text;
      fallback.setAttribute("readonly", "");
      fallback.style.position = "fixed";
      fallback.style.opacity = "0";
      document.body.appendChild(fallback);
      fallback.select();
      const copied = document.execCommand("copy");
      fallback.remove();
      if (!copied) throw new Error("Clipboard unavailable");
    }
    status.textContent = "Questions copied. Review them and apply the same job-related criteria consistently.";
  } catch (_error) {
    status.textContent = "Copy was blocked by the browser. Select the questions and copy them manually.";
  }
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

  reportDocument.querySelectorAll(".clarification-item[data-requirement-id]").forEach(function (item) {
    const response = currentCandidateResponses[item.dataset.requirementId];
    if (!response) return;
    const record = reportDocument.createElement("section");
    record.className = "candidate-response-record";
    const title = reportDocument.createElement("h4");
    title.textContent = "Candidate-provided follow-up · not independently verified";
    const recorded = reportDocument.createElement("p");
    recorded.textContent = "Recorded in this browser session (UTC): " + response.recordedAt;
    const boundary = reportDocument.createElement("p");
    boundary.textContent = "This statement was added after CV analysis. It is separate from the CV, was not sent to Muse, and did not change the evidence status.";
    const reply = reportDocument.createElement("blockquote");
    reply.textContent = response.text;
    record.append(title, recorded, boundary, reply);
    item.appendChild(record);
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

document.getElementById("clarification-brief-items").addEventListener("click", function (event) {
  const action = event.target instanceof Element
    ? event.target.closest("button[data-action]")
    : null;
  if (action) {
    const row = action.closest(".clarification-brief-item");
    if (!row) return;
    const requirementId = row.dataset.requirementId || "";
    const input = row.querySelector(".candidate-response-input");
    const status = row.querySelector(".candidate-response-status");
    const remove = row.querySelector(".candidate-response-remove");
    if (!input || !status || !remove) return;

    if (action.dataset.action === "remove-response") {
      delete currentCandidateResponses[requirementId];
      input.value = "";
      remove.hidden = true;
      status.textContent = "Recorded candidate reply removed from this session.";
      return;
    }
    if (action.dataset.action === "save-response") {
      const text = input.value.trim();
      if (!text) {
        status.textContent = "Enter a candidate reply before recording it.";
        input.focus();
        return;
      }
      currentCandidateResponses[requirementId] = {
        text: text,
        recordedAt: new Date().toISOString(),
      };
      remove.hidden = false;
      status.textContent = "Reply recorded in this tab. It stays separate from CV evidence and will be included in the downloaded pack.";
      return;
    }
  }

  const target = event.target instanceof Element
    ? event.target.closest(".clarification-source")
    : null;
  if (!target || !sourcePdfFile || !sourcePdfPayload) return;
  void openInteractivePdf(Number(target.dataset.page), target.dataset.quote || "");
});

document.getElementById("clarification-brief-items").addEventListener("input", function (event) {
  const input = event.target instanceof Element
    ? event.target.closest(".candidate-response-input")
    : null;
  if (!input) return;
  const row = input.closest(".clarification-brief-item");
  if (!row) return;
  const requirementId = row.dataset.requirementId || "";
  const status = row.querySelector(".candidate-response-status");
  const remove = row.querySelector(".candidate-response-remove");
  delete currentCandidateResponses[requirementId];
  if (remove) remove.hidden = true;
  if (status) {
    status.textContent = input.value.trim()
      ? "Unsaved edit. Record the reply to include it in the pack."
      : "No candidate reply recorded.";
  }
});

document.getElementById("copy-clarification-brief").addEventListener("click", function () {
  void copyClarificationBrief();
});

document.getElementById("application-prep-items").addEventListener("click", function (event) {
  const target = event.target instanceof Element
    ? event.target.closest(".application-prep-source")
    : null;
  if (!target || !sourcePdfFile || !sourcePdfPayload) return;
  void openInteractivePdf(Number(target.dataset.page), target.dataset.quote || "");
});

document.getElementById("application-prep-items").addEventListener("change", function (event) {
  const target = event.target instanceof HTMLInputElement && event.target.type === "checkbox"
    ? event.target
    : null;
  if (!target) return;
  applicationPrepChecks[target.dataset.requirementId || ""] = target.checked;
});

document.getElementById("download-application-prep").addEventListener("click", function () {
  const blob = new Blob([applicationPrepText()], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "evidencetrail-before-you-apply.txt";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  document.getElementById("application-prep-status").textContent =
    "Checklist downloaded. The evidence labels stay unchanged; verify all details against your records.";
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
    PDFJS_BASE_URL + "pdf.min.js?v=" + PDFJS_ASSET_VERSION
  );
  if (!pdfWorkerBlobUrl) {
    const response = await fetch(
      PDFJS_BASE_URL + "pdf-engine.min.js?v=" + PDFJS_ASSET_VERSION
    );
    if (!response.ok) throw new Error("The local PDF worker could not be loaded.");
    const workerSource = await response.text();
    pdfWorkerBlobUrl = URL.createObjectURL(
      new Blob([workerSource], { type: "text/javascript" })
    );
  }
  pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerBlobUrl;
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
    console.error("EvidenceTrail PDF viewer failed to open", error);
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
