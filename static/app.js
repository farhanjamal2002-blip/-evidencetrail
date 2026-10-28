const form = document.getElementById("analysis-form");
const cvInput = document.getElementById("cv");
const jobInput = document.getElementById("job-description");
const draftInput = document.getElementById("application-draft");
const fileName = document.getElementById("file-name");
const charCount = document.getElementById("char-count");
const draftCharCount = document.getElementById("draft-char-count");
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
let currentResultPayload = null;
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
const maxBatchFiles = Number(cvInput.dataset.maxFiles) || 5;
let batchReports = [];
let batchReviewStates = [];
let batchFailures = [];
let activeBatchIndex = -1;
let batchReviewMode = "dossier";
const batchMatrixReviewLabels = Object.freeze({
  reviewed: "Evidence reviewed",
  follow_up: "Needs follow-up",
  related_accepted: "Related evidence accepted for this role",
  related_rejected: "Related evidence not accepted for this role",
});

const demoJob = [
  "Role: Procurement Automation Lead",
  "",
  "Join our fast-paced, competitive team; strong communication skills are essential.",
  "",
  "Requirements:",
  "1. At least five years of Python experience.",
  "2. Current AWS Solutions Architect Professional certification.",
  "3. At least seven years of procurement experience.",
  "4. Negotiate multi-year supply agreements with GCC manufacturers.",
  "5. At least three years of team leadership experience."
].join("\n");
const demoApplicationDraft = [
  "I built Python automations across six years of work.",
  "I have eight years of procurement experience.",
  "I hold a current AWS Solutions Architect Professional certification."
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
      ? "Role review checklist ready · " + shown + " listed requirement(s) prepared with evidence prompts" +
        (omitted ? " · " + omitted + " more omitted at the display limit" : "") +
        " · " + cues + " optional wording cue(s). Download the worksheet or edit the job text to rerun."
      : "Role review checklist ready. No numbered or bulleted requirements or listed wording cues were detected; review the job text manually.";
  } catch (error) {
    if (requestId !== roleAuditRequestId) return;
    roleAuditStatus.textContent = error.message || "The role check could not run. Try again.";
  } finally {
    if (requestId === roleAuditRequestId) {
      roleAuditButton.disabled = false;
      roleAuditButton.textContent = "Build role review checklist";
    }
  }
});

cvInput.addEventListener("change", function () {
  const files = Array.from(cvInput.files || []);
  const resultsWereCleared = clearCurrentResults(true);
  if (!files.length) {
    fileName.textContent = "Choose CV PDFs or drop them here";
    if (!resultsWereCleared) hideError();
    return;
  }
  const fileError = getSelectionError(files);
  if (fileError) {
    cvInput.value = "";
    fileName.textContent = "Choose CV PDFs or drop them here";
    showError(fileError);
    return;
  }
  fileName.textContent = files.length === 1
    ? files[0].name
    : files.length + " CVs selected · " + files.map(function (file) { return file.name; }).join(" · ");
  fileName.title = files.map(function (file) { return file.name; }).join("\n");
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
  const droppedFiles = Array.from((event.dataTransfer && event.dataTransfer.files) || []);
  if (!droppedFiles.length) return;
  const fileError = getSelectionError(droppedFiles);
  if (fileError) {
    showError(fileError);
    return;
  }
  const transfer = new DataTransfer();
  droppedFiles.forEach(function (file) { transfer.items.add(file); });
  cvInput.files = transfer.files;
  cvInput.dispatchEvent(new Event("change"));
  hideError();
});

jobInput.addEventListener("input", function () {
  clearCurrentResults(true);
  charCount.textContent = String(jobInput.value.length);
});

draftInput.addEventListener("input", function () {
  clearCurrentResults(true);
  draftCharCount.textContent = String(draftInput.value.length);
});

const loadDemoButton = document.getElementById("load-demo-case");
const loadUnifiedDemoButton = document.getElementById("load-unified-demo");
const loadUnifiedDemoButtonLabel = loadUnifiedDemoButton.textContent.trim();
loadUnifiedDemoButton.addEventListener("click", async function () {
  loadUnifiedDemoButton.disabled = true;
  loadUnifiedDemoButton.textContent = "Loading five fictional CVs…";
  hideError();
  try {
    const manifestResponse = await fetch("/demo/unified-inputs");
    if (!manifestResponse.ok) throw new Error("The unified demo set is unavailable.");
    const manifest = await manifestResponse.json();
    if (!Array.isArray(manifest.candidates) || manifest.candidates.length !== 5) {
      throw new Error("The prepared set must contain exactly five CVs.");
    }
    const preparedFiles = await Promise.all(manifest.candidates.map(async function (candidate) {
      const response = await fetch(candidate.download_url);
      if (!response.ok) throw new Error("A prepared CV could not be loaded.");
      const pdf = await response.blob();
      return new File([pdf], candidate.filename, { type: "application/pdf" });
    }));
    const transfer = new DataTransfer();
    preparedFiles.forEach(function (file) { transfer.items.add(file); });
    cvInput.files = transfer.files;
    cvInput.dispatchEvent(new Event("change"));
    jobInput.value = manifest.job_description;
    jobInput.dispatchEvent(new Event("input"));
    draftInput.value = "";
    draftInput.dispatchEvent(new Event("input"));
    document.getElementById("consent").checked = false;
    loadUnifiedDemoButton.textContent = "Five CVs loaded · " + manifest.rubric_version;
    jobInput.focus();
  } catch (error) {
    showError(error.message || "The unified demo set could not be loaded.");
    loadUnifiedDemoButton.textContent = loadUnifiedDemoButtonLabel;
  } finally {
    loadUnifiedDemoButton.disabled = false;
  }
});

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
    draftInput.value = demoApplicationDraft;
    draftInput.dispatchEvent(new Event("input"));
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
    clearCurrentResults(false);
    batchReports = [{
      candidateId: "C1",
      filename: sampleFile.name,
      file: sampleFile,
      result: payload,
      uploadIndex: 0,
      decision: "undecided",
      decisionNote: "",
      interviewInviteDraft: "",
      interviewInvitePreparedAt: null,
    }];
    batchReviewStates = [{}];
    activeBatchIndex = 0;
    renderResults(payload, sampleFile);
    renderBatchReview();
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
  const submittedFiles = Array.from(cvInput.files || []);
  if (!submittedFiles.length) {
    showError("Choose one or more candidate CV PDFs first.");
    return;
  }
  const selectionError = getSelectionError(submittedFiles);
  if (selectionError) {
    showError(selectionError);
    return;
  }
  if (submittedFiles.length > 1 && draftInput.value.trim()) {
    showError("Clear the optional candidate statement to run a batch. Batch review analyzes the job description against each CV.");
    return;
  }

  const isBatch = submittedFiles.length > 1;
  const formData = new FormData();
  formData.append("job_description", jobInput.value.trim());
  formData.append("consent", document.getElementById("consent").checked ? "true" : "false");
  if (isBatch) {
    submittedFiles.forEach(function (file) { formData.append("cvs", file, file.name); });
  } else {
    formData.append("cv", submittedFiles[0], submittedFiles[0].name);
    formData.append("application_draft", draftInput.value.trim());
  }
  clearCurrentResults(false);
  analyzeButton.disabled = true;
  analyzeButton.setAttribute("aria-busy", "true");
  analyzeButton.querySelector("span:first-child").textContent = mockMode
    ? (isBatch ? "Local mock is reviewing the CV batch…" : "Local mock is checking the CV…")
    : (isBatch ? "Muse is reviewing the CV batch…" : "Muse is mapping and checking source evidence…");
  cvInput.disabled = true;
  jobInput.readOnly = true;
  draftInput.readOnly = true;
  document.getElementById("consent").disabled = true;
  loadDemoButton.disabled = true;
  previewDemoButton.disabled = true;
  const analysisStartedAt = Date.now();
  function updateAnalysisStatus() {
    const elapsedSeconds = Math.floor((Date.now() - analysisStartedAt) / 1000);
    const prefix = mockMode ? "Two-pass local simulation" : "Two-pass Muse Spark analysis";
    const progress = isBatch
      ? " · processing " + submittedFiles.length + " CVs in upload order"
      : "";
    analysisStatusText.textContent = prefix + progress + " · " + elapsedSeconds + " seconds elapsed.";
  }
  analysisStatus.hidden = false;
  updateAnalysisStatus();
  analysisTimer = window.setInterval(updateAnalysisStatus, 5000);
  try {
    const response = await fetch(isBatch ? "/api/analyze-batch" : "/api/analyze", { method: "POST", body: formData });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Analysis could not be completed.");
    }
    if (!isBatch) {
      batchReports = [{
        candidateId: "C1",
        filename: submittedFiles[0].name,
        file: submittedFiles[0],
        result: payload,
        uploadIndex: 0,
        decision: "undecided",
        decisionNote: "",
        interviewInviteDraft: "",
        interviewInvitePreparedAt: null,
      }];
      batchReviewStates = [{}];
      batchFailures = [];
      activeBatchIndex = 0;
      renderResults(payload, submittedFiles[0]);
      renderBatchReview();
    } else {
      const entries = Array.isArray(payload.results) ? payload.results : [];
      batchReports = [];
      batchReviewStates = [];
      batchFailures = [];
      entries.forEach(function (entry, index) {
        const file = submittedFiles[index];
        if (entry && entry.result && file) {
          batchReports.push({
            candidateId: entry.candidate_id || "C" + (index + 1),
            filename: file.name,
            file: file,
            result: entry.result,
            uploadIndex: index,
            decision: "undecided",
            decisionNote: "",
            interviewInviteDraft: "",
            interviewInvitePreparedAt: null,
          });
          batchReviewStates.push({});
        } else {
          batchFailures.push({
            candidateId: entry && entry.candidate_id ? entry.candidate_id : "C" + (index + 1),
            filename: file ? file.name : "Candidate CV " + (index + 1),
            detail: entry && entry.error && entry.error.detail
              ? entry.error.detail
              : "This CV could not be analyzed.",
            uploadIndex: index,
          });
        }
      });
      if (!batchReports.length) {
        throw new Error("No CV in this batch produced an evidence review. Check the uploaded PDFs and try again.");
      }
      activeBatchIndex = 0;
      renderResults(batchReports[0].result, batchReports[0].file, batchReviewStates[0]);
      renderBatchReview();
    }
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
      : modelReady ? "Review CVs with Muse Spark" : "Real analysis unavailable";
    cvInput.disabled = false;
    jobInput.readOnly = false;
    draftInput.readOnly = false;
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

function getSelectionError(files) {
  if (!files.length) return "Choose one or more candidate CV PDFs first.";
  if (files.length > maxBatchFiles) return "Choose no more than " + maxBatchFiles + " CVs in one batch.";
  let totalBytes = 0;
  for (const file of files) {
    const error = getPdfFileError(file);
    if (error) return file.name + ": " + error;
    totalBytes += file.size;
  }
  if (totalBytes > maxPdfBytes * 3) return "Keep the combined batch under three times the per-file PDF limit.";
  return "";
}

function copyRecord(value) {
  return value && typeof value === "object" ? JSON.parse(JSON.stringify(value)) : {};
}

function captureActiveBatchReview() {
  if (activeBatchIndex < 0 || !batchReviewStates[activeBatchIndex]) return;
  batchReviewStates[activeBatchIndex] = {
    reviewEntries: copyRecord(reviewEntries),
    currentCandidateResponses: copyRecord(currentCandidateResponses),
    applicationPrepChecks: copyRecord(applicationPrepChecks),
  };
}

function batchMatrixRequirementKey(finding) {
  const requirement = String(finding.requirement || "").trim().toLocaleLowerCase().replace(/\s+/g, " ");
  const source = finding.job_source && typeof finding.job_source === "object"
    ? finding.job_source
    : {};
  const sourceText = String(source.text || "").trim().toLocaleLowerCase().replace(/\s+/g, " ");
  const line = Number(source.line);
  if (Number.isInteger(line) && line > 0 && sourceText) {
    // A single JD line may contain multiple atomic requirements; keep them distinct.
    return "jd:" + line + ":" + sourceText + ":requirement:" + requirement;
  }
  return requirement ? "requirement:" + requirement : "";
}

function renderBatchRequirementMatrix(root) {
  root.replaceChildren();
  const uploads = [
    ...batchReports.map(function (entry, reportIndex) {
      return {
        kind: "review",
        entry: entry,
        reportIndex: reportIndex,
        order: Number(entry.uploadIndex ?? reportIndex),
        reviewEntries: reportIndex === activeBatchIndex
          ? reviewEntries
          : (batchReviewStates[reportIndex] || {}).reviewEntries || {},
      };
    }),
    ...batchFailures.map(function (entry) {
      return {
        kind: "failure",
        entry: entry,
        order: Number(entry.uploadIndex ?? maxBatchFiles),
      };
    }),
  ].sort(function (a, b) { return a.order - b.order; });

  const rows = [];
  const rowsByKey = new Map();
  uploads.forEach(function (candidate) {
    if (candidate.kind !== "review") return;
    const findings = Array.isArray(candidate.entry.result.requirements)
      ? candidate.entry.result.requirements
      : [];
    findings.forEach(function (finding) {
      const key = batchMatrixRequirementKey(finding);
      if (!key) return;
      const jobSource = finding.job_source && typeof finding.job_source === "object"
        ? finding.job_source
        : {};
      const sourceLine = Number(jobSource.line);
      const hasSourceLine = Number.isInteger(sourceLine) && sourceLine > 0;
      let row = rowsByKey.get(key);
      if (!row) {
        row = {
          requirement: String(finding.requirement || "Requirement text unavailable"),
          priority: String(finding.job_priority || "Not stated"),
          priorityBasis: String(finding.priority_basis || ""),
          sourceLine: hasSourceLine ? sourceLine : 0,
          findings: Object.create(null),
        };
        rowsByKey.set(key, row);
        rows.push(row);
      }
      if (row.priority === "Not stated" && finding.job_priority && finding.job_priority !== "Not stated") {
        row.priority = String(finding.job_priority);
        row.priorityBasis = String(finding.priority_basis || "");
      }
      if (!row.sourceLine && hasSourceLine) row.sourceLine = sourceLine;
      row.findings[candidate.reportIndex] = finding;
    });
  });

  if (!rows.length) {
    const empty = document.createElement("p");
    empty.className = "batch-matrix-empty";
    empty.textContent = "No successful candidate reviews are available for comparison.";
    root.appendChild(empty);
    return;
  }

  const strengthLegend = document.createElement("div");
  strengthLegend.className = "batch-matrix-strength-legend";
  strengthLegend.setAttribute("aria-label", "Evidence strength legend");
  strengthLegend.setAttribute("role", "group");
  const strengthLegendTitle = document.createElement("strong");
  strengthLegendTitle.textContent = "Evidence detail";
  strengthLegend.appendChild(strengthLegendTitle);
  ["specific", "stated", "keyword_only", "none"].forEach(function (value) {
    const chip = createEvidenceStrengthChip(value);
    strengthLegend.appendChild(chip);
  });
  root.appendChild(strengthLegend);

  const scroller = document.createElement("div");
  scroller.className = "batch-matrix-scroll";
  const table = document.createElement("table");
  table.className = "batch-matrix-table";
  table.style.minWidth = (260 + uploads.length * 190) + "px";
  const caption = document.createElement("caption");
  caption.textContent = "Upload order is preserved; this view does not score or rank candidates. Priority reflects explicit job-post wording. A missing result means the requirement was not returned for that CV; it is not evidence that the candidate lacks the skill.";
  table.appendChild(caption);

  const head = document.createElement("thead");
  const headerRow = document.createElement("tr");
  const requirementHeading = document.createElement("th");
  requirementHeading.scope = "col";
  requirementHeading.className = "batch-matrix-requirement-heading";
  requirementHeading.textContent = "Job requirement";
  headerRow.appendChild(requirementHeading);
  uploads.forEach(function (candidate) {
    const heading = document.createElement("th");
    heading.scope = "col";
    heading.className = candidate.kind === "failure" ? "batch-matrix-failed-heading" : "";
    const title = document.createElement("strong");
    title.textContent = "Candidate " + (candidate.order + 1);
    const filename = document.createElement("span");
    filename.textContent = candidate.entry.filename || "CV";
    const order = document.createElement("small");
    order.textContent = "Upload #" + (candidate.order + 1) +
      (candidate.kind === "failure" ? " · not analyzed" : "");
    heading.append(title, filename, order);
    if (candidate.kind === "review") {
      const decision = document.createElement("small");
      decision.className = "batch-matrix-decision";
      decision.textContent = "Recruiter decision · " + recruiterDecisionLabel(candidate.entry.decision);
      heading.appendChild(decision);
    }
    headerRow.appendChild(heading);
  });
  head.appendChild(headerRow);
  table.appendChild(head);

  const body = document.createElement("tbody");
  const statusLabels = {
    direct: "Direct evidence",
    related: "Related experience",
    unsupported: "Not mentioned in CV",
    conflicting: "Details differ",
  };
  const strengthLabels = {
    specific: "Specific detail",
    stated: "Stated only",
    keyword_only: "Keyword only",
    none: "No passage",
  };
  rows.forEach(function (row) {
    const tableRow = document.createElement("tr");
    const requirementCell = document.createElement("th");
    requirementCell.scope = "row";
    requirementCell.className = "batch-matrix-requirement";
    const requirementLabel = document.createElement("span");
    requirementLabel.textContent = row.requirement;
    requirementCell.appendChild(requirementLabel);
    const priority = priorityPresentation({
      priority: row.priority,
      priority_basis: row.priorityBasis,
    });
    if (priority) {
      const priorityLabel = document.createElement("span");
      priorityLabel.className = "priority-badge batch-matrix-priority priority-" + priority.className;
      priorityLabel.textContent = priority.label;
      if (priority.basis) priorityLabel.title = "Based on job-post wording: " + priority.basis;
      requirementCell.appendChild(priorityLabel);
    }
    if (row.sourceLine) {
      const sourceLine = document.createElement("small");
      sourceLine.textContent = "Job wording · line " + row.sourceLine;
      requirementCell.appendChild(sourceLine);
    }
    tableRow.appendChild(requirementCell);

    uploads.forEach(function (candidate) {
      const cell = document.createElement("td");
      if (candidate.kind === "failure") {
        cell.className = "batch-matrix-unavailable";
        cell.textContent = "CV not analyzed";
        tableRow.appendChild(cell);
        return;
      }
      const finding = row.findings[candidate.reportIndex];
      if (!finding) {
        cell.className = "batch-matrix-unavailable";
        cell.textContent = "Not returned";
        tableRow.appendChild(cell);
        return;
      }

      const type = Object.prototype.hasOwnProperty.call(statusLabels, finding.evidence_type)
        ? finding.evidence_type
        : "unsupported";
      const timelineNeedsReview = Array.isArray(finding.timeline_review_flags) &&
        finding.timeline_review_flags.length > 0;
      const displayType = timelineNeedsReview ? "conflicting" : type;
      const displayLabel = timelineNeedsReview
        ? "Conflict to clarify"
        : statusLabels[type];
      const evidence = Array.isArray(finding.evidence) ? finding.evidence[0] : null;
      const pageNumber = evidence ? Number(evidence.page) : 0;
      const page = Number.isInteger(pageNumber) && pageNumber > 0 ? pageNumber : 0;
      const quote = evidence && typeof evidence.quote === "string" ? evidence.quote : "";
      const verificationAudit = candidate.entry.result.verification_audit || {};
      const rejectedForFinding = Array.isArray(verificationAudit.rejected_citations) &&
        verificationAudit.rejected_citations.some(function (record) {
          return String(record.requirement_id || "") === String(finding.id || "");
        });
      const button = document.createElement("button");
      button.type = "button";
      button.className = "batch-matrix-cell batch-matrix-" + displayType +
        (finding.certainty === "ambiguous" ? " batch-matrix-ambiguous" : "");
      button.dataset.matrixReportIndex = String(candidate.reportIndex);
      button.setAttribute(
        "aria-label",
        "Candidate " + (candidate.order + 1) + ", " + row.requirement + ": " +
          (timelineNeedsReview ? "Conflict to clarify. " + timelineMuseLabel(finding) : displayLabel) +
          (page ? ", CV page " + page + ". Open source." : ". Open candidate review.")
      );
      button.dataset.matrixAriaBase = button.getAttribute("aria-label");
      const status = document.createElement("strong");
      status.textContent = timelineNeedsReview
        ? "Conflict to clarify"
        : finding.certainty === "ambiguous" ? "Needs review" : statusLabels[type];
      const source = document.createElement("span");
      source.className = "batch-matrix-source";
      source.textContent = page
        ? "CV page " + page + " · Open source"
        : finding.evidence_strength === "keyword_only"
          ? "Keyword mention · no support accepted"
          : "Open candidate review";
      button.dataset.matrixFindingId = String(finding.id || "");
      button.append(status, source);
      if (timelineNeedsReview) {
        const provenance = document.createElement("span");
        provenance.className = "batch-matrix-timeline-provenance";
        provenance.textContent = timelineMuseLabel(finding);
        button.appendChild(provenance);
      }
      const quoteCheck = document.createElement("span");
      quoteCheck.className = "batch-matrix-check " + (page
        ? "batch-matrix-check-passed"
        : rejectedForFinding ? "batch-matrix-check-rejected"
          : finding.evidence_strength === "keyword_only" ? "batch-matrix-check-weak"
            : "batch-matrix-check-none");
      quoteCheck.textContent = page
        ? "Quote/page checked"
        : rejectedForFinding ? "Proposed quote rejected"
          : finding.evidence_strength === "keyword_only" ? "Keyword only · not evidence"
            : "No verified quote";
      button.appendChild(quoteCheck);
      const strength = Object.prototype.hasOwnProperty.call(strengthLabels, finding.evidence_strength)
        ? finding.evidence_strength
        : (evidence ? "stated" : "none");
      button.appendChild(createEvidenceStrengthChip(strength));
      const review = candidate.reviewEntries[String(finding.id || "")];
      const reviewLabel = review && batchMatrixReviewLabels[review.status];
      if (reviewLabel) {
        const reviewerState = document.createElement("span");
        reviewerState.className = "batch-matrix-review-state batch-matrix-review-" + review.status;
        reviewerState.textContent = "Recruiter: " + reviewLabel;
        button.appendChild(reviewerState);
        button.setAttribute("aria-label", button.dataset.matrixAriaBase + ", recruiter: " + reviewLabel);
      }
      if (quote) {
        const snippet = document.createElement("span");
        snippet.className = "batch-matrix-quote";
        snippet.textContent = "“" + quote + "”";
        button.appendChild(snippet);
      }
      if (page && quote) {
        button.dataset.page = String(page);
        button.dataset.quote = quote;
      }
      cell.appendChild(button);
      tableRow.appendChild(cell);
    });
    body.appendChild(tableRow);
  });
  table.appendChild(body);
  scroller.appendChild(table);
  root.appendChild(scroller);
}

function renderBatchReview() {
  const panel = document.getElementById("batch-review");
  const list = document.getElementById("batch-review-items");
  const matrix = document.getElementById("batch-review-matrix");
  if (!panel || !list || !matrix) return;
  list.replaceChildren();
  panel.hidden = batchReports.length <= 1 && batchFailures.length === 0;
  const matrixMode = !panel.hidden && batchReviewMode === "matrix";
  list.hidden = matrixMode;
  matrix.hidden = !matrixMode;
  document.getElementById("batch-review-dossier-view").setAttribute(
    "aria-pressed",
    batchReviewMode === "dossier" ? "true" : "false"
  );
  document.getElementById("batch-review-matrix-view").setAttribute(
    "aria-pressed",
    batchReviewMode === "matrix" ? "true" : "false"
  );
  if (matrixMode) renderBatchRequirementMatrix(matrix);
  if (panel.hidden) return;

  const reviewOrder = [
    ...batchReports.map(function (entry, index) {
      return { kind: "review", entry: entry, reportIndex: index, order: entry.uploadIndex ?? index };
    }),
    ...batchFailures.map(function (entry) {
      return { kind: "failure", entry: entry, order: entry.uploadIndex ?? maxBatchFiles };
    }),
  ].sort(function (a, b) { return a.order - b.order; });

  reviewOrder.forEach(function (row) {
    if (row.kind === "failure") {
      const item = document.createElement("div");
      item.className = "batch-candidate batch-candidate-failed";
      const title = document.createElement("strong");
      title.textContent = row.entry.candidateId + " · " + row.entry.filename;
      const detail = document.createElement("span");
      detail.textContent = "Not analyzed · " + row.entry.detail;
      item.append(title, detail);
      list.appendChild(item);
      return;
    }
    const entry = row.entry;
    const index = row.reportIndex;
    const requirements = Array.isArray(entry.result.requirements) ? entry.result.requirements : [];
    const counts = { direct: 0, related: 0, unsupported: 0, conflicting: 0 };
    requirements.forEach(function (finding) {
      const type = finding.evidence_type || "unsupported";
      if (Object.prototype.hasOwnProperty.call(counts, type)) counts[type] += 1;
    });
    const card = document.createElement("article");
    card.className = "batch-candidate" + (index === activeBatchIndex ? " is-active" : "");
    const title = document.createElement("strong");
    title.textContent = (entry.candidateId || "C" + (index + 1)) + " · " + entry.filename;
    const detail = document.createElement("span");
    detail.textContent = counts.direct + " direct · " + counts.related + " related · " +
      counts.unsupported + " not shown · " + counts.conflicting + " conflict" +
      (counts.conflicting === 1 ? "" : "s");
    const openButton = document.createElement("button");
    openButton.type = "button";
    openButton.className = "batch-open-candidate";
    openButton.dataset.batchIndex = String(index);
    openButton.setAttribute("aria-pressed", index === activeBatchIndex ? "true" : "false");
    openButton.append(title, detail);
    const decisionState = document.createElement("span");
    decisionState.className = "batch-decision-state batch-decision-state-" + (entry.decision || "undecided");
    decisionState.textContent = "Recruiter decision · " + recruiterDecisionLabel(entry.decision);
    card.append(openButton, decisionState);
    list.appendChild(card);
  });
}

function recruiterDecisionLabel(value) {
  return {
    undecided: "Not decided",
    advance: "Advance",
    hold: "Hold for follow-up",
    do_not_advance: "Do not advance",
  }[value] || "Not decided";
}

function activeCandidateEntry() {
  if (activeBatchIndex < 0 || !batchReports[activeBatchIndex]) return null;
  return batchReports[activeBatchIndex];
}

function renderRecruiterDecisionPanel() {
  const panel = document.getElementById("recruiter-decision");
  const entry = activeCandidateEntry();
  panel.hidden = !entry;
  if (!entry) return;

  const candidateLabel = (entry.candidateId || "Candidate " + (activeBatchIndex + 1)) +
    " · " + (entry.filename || "CV");
  document.getElementById("recruiter-decision-candidate").textContent = candidateLabel;
  document.getElementById("recruiter-decision-select").value = entry.decision || "undecided";
  document.getElementById("recruiter-decision-note").value = entry.decisionNote || "";
  const inviteDraft = document.getElementById("interview-invite-draft");
  const invitePanel = document.getElementById("interview-invite-panel");
  const inviteStatus = document.getElementById("interview-invite-status");
  inviteDraft.value = entry.interviewInviteDraft || "";
  invitePanel.hidden = !entry.interviewInviteDraft;
  inviteStatus.textContent = entry.interviewInviteDraft
    ? "Editable draft prepared" + (entry.interviewInvitePreparedAt
      ? " · " + new Date(entry.interviewInvitePreparedAt).toLocaleString()
      : "") + ". Not sent or scheduled."
    : "";

  const counts = { direct: 0, related: 0, unsupported: 0, conflicting: 0, review: 0 };
  const requirements = entry.result && Array.isArray(entry.result.requirements)
    ? entry.result.requirements
    : [];
  requirements.forEach(function (finding) {
    const state = plainFindingState(finding);
    if (state === "shown") counts.direct += 1;
    else if (state === "related") counts.related += 1;
    else if (state === "not_mentioned") counts.unsupported += 1;
    else if (state === "details_differ") counts.conflicting += 1;
    else counts.review += 1;
  });
  const parts = [];
  if (counts.direct) parts.push(counts.direct + " direct evidence");
  if (counts.related) parts.push(counts.related + " related");
  if (counts.unsupported) parts.push(counts.unsupported + " not mentioned");
  if (counts.conflicting) parts.push(counts.conflicting + " details differ");
  if (counts.review) parts.push(counts.review + " need a closer look");
  document.getElementById("recruiter-decision-evidence-summary").textContent =
    "CV evidence summary · " + (parts.length ? parts.join(" · ") : "no requirements returned") +
    ". These are document findings, not a candidate score.";

  const status = document.getElementById("recruiter-decision-status");
  status.textContent = entry.decision && entry.decision !== "undecided"
    ? "Decision recorded for this review" + (entry.decisionUpdatedAt
      ? " · " + new Date(entry.decisionUpdatedAt).toLocaleString()
      : "") + ". Included in the evidence pack."
    : "No recruiter decision recorded yet.";
}

function saveActiveRecruiterDecision() {
  const entry = activeCandidateEntry();
  if (!entry) return;
  const decision = document.getElementById("recruiter-decision-select").value;
  const note = document.getElementById("recruiter-decision-note").value.trim();
  entry.decision = decision;
  entry.decisionNote = note;
  entry.decisionUpdatedAt = decision === "undecided" ? null : new Date().toISOString();
  renderRecruiterDecisionPanel();
  renderBatchReview();
}

document.getElementById("recruiter-decision-select").addEventListener("change", saveActiveRecruiterDecision);
document.getElementById("recruiter-decision-note").addEventListener("input", function () {
  const entry = activeCandidateEntry();
  if (!entry) return;
  entry.decisionNote = this.value.trim();
  if (entry.decision && entry.decision !== "undecided") {
    entry.decisionUpdatedAt = new Date().toISOString();
  }
});

function prepareInterviewInvite() {
  const entry = activeCandidateEntry();
  if (!entry || !entry.result) return;
  entry.interviewInviteDraft = window.EvidenceTrailInterviewInvite.buildDraft(entry.result.requirements);
  entry.interviewInvitePreparedAt = new Date().toISOString();
  entry.decision = "advance";
  entry.decisionUpdatedAt = entry.interviewInvitePreparedAt;
  document.getElementById("recruiter-decision-select").value = "advance";
  renderRecruiterDecisionPanel();
  renderBatchReview();
  document.getElementById("interview-invite-panel").hidden = false;
  document.getElementById("interview-invite-draft").focus();
  document.getElementById("interview-invite-status").textContent =
    "Interview invitation prepared · recruiter decision recorded as Advance. Review and edit before using; nothing was sent or scheduled.";
}

async function copyInterviewInvite() {
  const field = document.getElementById("interview-invite-draft");
  const status = document.getElementById("interview-invite-status");
  if (!field.value.trim()) return;
  try {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      await navigator.clipboard.writeText(field.value);
    } else {
      field.focus();
      field.select();
      if (!document.execCommand("copy")) throw new Error("Clipboard unavailable");
    }
    status.textContent = "Draft copied. Review the placeholders and details before sending it outside EvidenceTrail.";
  } catch (_error) {
    status.textContent = "Copy was blocked. Select the draft and copy it manually.";
  }
}

document.getElementById("prepare-interview-invite").addEventListener("click", prepareInterviewInvite);
document.getElementById("copy-interview-invite").addEventListener("click", function () {
  void copyInterviewInvite();
});
document.getElementById("clear-interview-invite").addEventListener("click", function () {
  const entry = activeCandidateEntry();
  if (!entry) return;
  entry.interviewInviteDraft = "";
  entry.interviewInvitePreparedAt = null;
  renderRecruiterDecisionPanel();
});
document.getElementById("interview-invite-draft").addEventListener("input", function () {
  const entry = activeCandidateEntry();
  if (!entry) return;
  entry.interviewInviteDraft = this.value;
  document.getElementById("interview-invite-status").textContent = this.value.trim()
    ? "Draft edits stay in this tab until you download the report or shortlist audit. Not sent or scheduled."
    : "Draft cleared from this candidate.";
});

function updateBatchMatrixReviewStatus(reportIndex, findingId, status) {
  const matrix = document.getElementById("batch-review-matrix");
  if (!matrix || matrix.hidden) return;
  const label = batchMatrixReviewLabels[status] || "";
  matrix.querySelectorAll("button[data-matrix-report-index]").forEach(function (button) {
    if (Number(button.dataset.matrixReportIndex) !== reportIndex ||
      button.dataset.matrixFindingId !== findingId) return;
    let state = button.querySelector(".batch-matrix-review-state");
    if (!label) {
      if (state) state.remove();
      button.setAttribute("aria-label", button.dataset.matrixAriaBase || "");
      return;
    }
    if (!state) {
      state = document.createElement("span");
      const quote = button.querySelector(".batch-matrix-quote");
      if (quote) button.insertBefore(state, quote);
      else button.appendChild(state);
    }
    state.className = "batch-matrix-review-state batch-matrix-review-" + status;
    state.textContent = "Recruiter: " + label;
    button.setAttribute("aria-label", (button.dataset.matrixAriaBase || "") + ", recruiter: " + label);
  });
}

document.getElementById("batch-review-view-switch").addEventListener("click", function (event) {
  const button = event.target instanceof Element
    ? event.target.closest("button[data-batch-review-mode]")
    : null;
  if (!button) return;
  batchReviewMode = button.dataset.batchReviewMode === "matrix" ? "matrix" : "dossier";
  renderBatchReview();
});

document.getElementById("batch-review-items").addEventListener("click", function (event) {
  const button = event.target instanceof Element
    ? event.target.closest("button[data-batch-index]")
    : null;
  if (!button) return;
  const index = Number(button.dataset.batchIndex);
  if (!Number.isInteger(index) || !batchReports[index] || index === activeBatchIndex) return;
  captureActiveBatchReview();
  activeBatchIndex = index;
  renderResults(batchReports[index].result, batchReports[index].file, batchReviewStates[index]);
  renderBatchReview();
});

document.getElementById("batch-review-matrix").addEventListener("click", function (event) {
  const button = event.target instanceof Element
    ? event.target.closest("button[data-matrix-report-index]")
    : null;
  if (!button) return;
  const index = Number(button.dataset.matrixReportIndex);
  const entry = batchReports[index];
  if (!Number.isInteger(index) || !entry) return;
  if (index !== activeBatchIndex) {
    captureActiveBatchReview();
    activeBatchIndex = index;
    renderResults(entry.result, entry.file, batchReviewStates[index]);
    renderBatchReview();
  }
  const page = Number(button.dataset.page);
  const quote = button.dataset.quote || "";
  if (Number.isInteger(page) && page > 0 && quote) {
    void openInteractivePdf(page, quote);
  } else {
    document.getElementById("findings-list").scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
      block: "start",
    });
  }
});

document.getElementById("batch-review-download").addEventListener("click", function () {
  captureActiveBatchReview();
  const candidates = batchReports.map(function (entry, index) {
    const requirements = Array.isArray(entry.result.requirements) ? entry.result.requirements : [];
    const evidenceCounts = { direct: 0, related: 0, unsupported: 0, conflicting: 0 };
    requirements.forEach(function (finding) {
      const type = finding.evidence_type || "unsupported";
      if (Object.prototype.hasOwnProperty.call(evidenceCounts, type)) evidenceCounts[type] += 1;
    });
    const state = index === activeBatchIndex
      ? { reviewEntries: reviewEntries, currentCandidateResponses: currentCandidateResponses, applicationPrepChecks: applicationPrepChecks }
      : (batchReviewStates[index] || {});
    const itemReviews = Object.entries(state.reviewEntries || {}).map(function (item) {
      return { requirement_id: item[0], ...item[1] };
    });
    return {
      candidate_id: entry.candidateId || "C" + (index + 1),
      filename: entry.filename,
      upload_order: Number(entry.uploadIndex ?? index) + 1,
      recruiter_decision: entry.decision || "undecided",
      decision_note: entry.decisionNote || "",
      decision_recorded_at: entry.decisionUpdatedAt || null,
      interview_invite_draft: entry.interviewInviteDraft || "",
      interview_invite_prepared_at: entry.interviewInvitePreparedAt || null,
      evidence_counts: evidenceCounts,
      requirement_reviews: itemReviews,
      requirement_evidence: requirements,
      evidence_graph: entry.result.evidence_graph || {},
      clarification_brief: entry.result.clarification_brief || { items: [] },
      timeline_audit: entry.result.timeline_audit || {},
      verification_audit: entry.result.verification_audit || {},
      job_item_coverage: entry.result.job_item_coverage || {},
      quote_audit: entry.result.quote_audit || {},
      cv_sha256: entry.result.cv_sha256 || "",
      model: entry.result.model || "",
      analysis_created_at: entry.result.created_at || "",
    };
  });
  const failures = batchFailures.map(function (entry) {
    return {
      candidate_id: entry.candidateId,
      filename: entry.filename,
      upload_order: Number(entry.uploadIndex || 0) + 1,
      analysis_status: "failed",
      reason: entry.detail,
    };
  });
  const jobHash = batchReports.length && batchReports[0].result.job_sha256
    ? batchReports[0].result.job_sha256
    : "";
  const audit = {
    schema: "EvidenceTrail shortlist review v1",
    exported_at: new Date().toISOString(),
    job_description_sha256: jobHash,
    recruiter_control: true,
    automated_ranking: false,
    candidates,
    failed_candidates: failures,
    note: "Shortlist decisions and notes were entered by the recruiter. Evidence counts are document findings, not a candidate score. Download each CV's HTML evidence pack separately for the page images and interactive report.",
  };
  const blob = new Blob([JSON.stringify(audit, null, 2)], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "evidencetrail-shortlist-audit.json";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
});

function clearCurrentResults(showNotice) {
  batchReports = [];
  batchReviewStates = [];
  batchFailures = [];
  activeBatchIndex = -1;
  currentResultPayload = null;
  batchReviewMode = "dossier";
  const batchReviewPanel = document.getElementById("batch-review");
  const batchReviewItems = document.getElementById("batch-review-items");
  const batchReviewMatrix = document.getElementById("batch-review-matrix");
  if (batchReviewPanel) batchReviewPanel.hidden = true;
  if (batchReviewItems) batchReviewItems.replaceChildren();
  if (batchReviewItems) batchReviewItems.hidden = false;
  if (batchReviewMatrix) {
    batchReviewMatrix.replaceChildren();
    batchReviewMatrix.hidden = true;
  }
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
  roleAuditButton.textContent = "Build role review checklist";
  if (results.hidden) return false;

  results.hidden = true;
  currentReport = "";
  document.getElementById("recruiter-decision").hidden = true;
  document.getElementById("recruiter-decision-candidate").textContent = "";
  document.getElementById("recruiter-decision-evidence-summary").textContent = "";
  document.getElementById("recruiter-decision-status").textContent = "";
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
  document.getElementById("application-claim-audit").hidden = true;
  document.getElementById("application-claim-audit-summary").textContent = "";
  document.getElementById("application-claim-audit-items").replaceChildren();
  document.getElementById("source-pages").replaceChildren();
  document.getElementById("evidence-graph").replaceChildren();
  document.getElementById("job-list-coverage").hidden = true;
  document.getElementById("job-list-coverage-items").replaceChildren();
  document.getElementById("job-list-coverage-limit").hidden = true;
  document.getElementById("summary-counts").replaceChildren();
  document.getElementById("plain-summary-title").textContent = "";
  document.getElementById("plain-summary-detail").textContent = "";
  const verifierChip = document.getElementById("verifier-chip");
  verifierChip.textContent = "";
  verifierChip.className = "verifier-chip";
  verifierChip.hidden = true;
  document.getElementById("job-coverage-summary").textContent = "";
  document.getElementById("job-coverage-summary").hidden = true;
  document.getElementById("technical-audit-summary").textContent = "Open verification details";
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

function renderVerifierChip(payload) {
  const chip = document.getElementById("verifier-chip");
  chip.replaceChildren();
  chip.hidden = false;
  chip.className = "verifier-chip";

  const label = document.createElement("strong");
  const detail = document.createElement("span");
  if (payload.preview_mode) {
    chip.classList.add("verifier-chip-preview");
    label.textContent = "Synthetic preview";
    detail.textContent = "Hand-authored example; no live verification or model call.";
  } else if (payload.provider_mode === "mock") {
    chip.classList.add("verifier-chip-preview");
    label.textContent = "Local mock";
    detail.textContent = "Deterministic simulation; no Muse verification or model call.";
  } else {
    const audit = payload.quote_audit || {};
    const proposed = Number(audit.verification_proposed || 0);
    const matched = Number(audit.verification_verified || 0);
    const excluded = Number(audit.verification_excluded || 0);
    if (excluded > 0) {
      chip.classList.add("verifier-chip-warning");
      label.textContent = "Source check · " + matched + "/" + proposed + " quote/page matches · " + excluded + " excluded";
    } else if (proposed > 0) {
      chip.classList.add("verifier-chip-passed");
      label.textContent = "Source check · " + matched + "/" + proposed + " quote/page matches";
    } else {
      chip.classList.add("verifier-chip-neutral");
      label.textContent = "Source check · no citation proposed";
    }
    detail.textContent = "Text presence and page only; review the original CV to judge what it means.";
  }
  chip.append(label, detail);
}

function renderResults(payload, analyzedFile, savedState) {
  currentResultPayload = payload;
  const previewNotice = document.getElementById("preview-notice");
  previewNotice.hidden = !payload.preview_mode && payload.provider_mode !== "mock";
  previewNotice.textContent = payload.preview_mode
    ? "Synthetic preview only: these hand-authored findings use a fictional CV. No Muse Spark or Meta Model API request was made."
    : payload.provider_mode === "mock"
      ? "Local mock simulation only: deterministic heuristics exercise the same pipeline, but this is not Muse analysis and must not be used as a hiring assessment. No Meta API call or model tokens."
      : "";
  renderVerifierChip(payload);
  const findingsList = document.getElementById("findings-list");
  const counts = { shown: 0, related: 0, not_mentioned: 0, details_differ: 0, needs_review: 0 };
  const roleCriteriaByLine = Object.create(null);
  const roleCriteria = payload.role_clarity_audit && Array.isArray(payload.role_clarity_audit.criteria)
    ? payload.role_clarity_audit.criteria
    : [];
  roleCriteria.forEach(function (criterion) {
    const line = Number(criterion.line);
    if (Number.isInteger(line) && line > 0) roleCriteriaByLine[line] = criterion;
  });
  const restoredState = savedState && typeof savedState === "object" ? savedState : {};
  reviewEntries = Object.assign(Object.create(null), copyRecord(restoredState.reviewEntries));
  currentCandidateResponses = Object.assign(
    Object.create(null),
    copyRecord(restoredState.currentCandidateResponses)
  );
  applicationPrepChecks = Object.assign(
    Object.create(null),
    copyRecord(restoredState.applicationPrepChecks)
  );
  findingsList.replaceChildren();
  const findingsToReview = [];
  const relatedFindings = [];
  const findingsWithEvidence = [];
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
    const state = plainFindingState(finding);
    counts[state] = (counts[state] || 0) + 1;
    const sourceLine = finding.job_source && Number.isInteger(finding.job_source.line)
      ? finding.job_source.line
      : null;
    const criterion = sourceLine === null ? null : roleCriteriaByLine[sourceLine] || null;
    const row = { finding: finding, criterion: criterion };
    if (state === "shown") findingsWithEvidence.push(row);
    else if (state === "related") relatedFindings.push(row);
    else findingsToReview.push(row);
  });
  const appendFindingGroup = function (titleText, helpText, rows) {
    if (!rows.length) return;
    const group = document.createElement("section");
    group.className = "finding-group";
    const heading = document.createElement("h3");
    heading.textContent = titleText;
    const help = document.createElement("p");
    help.textContent = helpText;
    const cards = document.createElement("div");
    cards.className = "finding-group-cards";
    rows.forEach(function (row) {
      cards.appendChild(buildFindingCard(row.finding, row.criterion));
    });
    group.append(heading, help, cards);
    findingsList.appendChild(group);
  };
  appendFindingGroup(
    "Needs your attention first",
    "Start with missing, conflicting, or unclear evidence. Check the job wording and CV passages before drawing a conclusion.",
    findingsToReview
  );
  appendFindingGroup(
    "Related experience to review",
    "Muse sees a possible connection to the job need. Review what may transfer and what the CV still does not establish.",
    relatedFindings
  );
  appendFindingGroup(
    "CV passages found",
    "These passages directly describe the job need. Open each one to inspect the exact wording in context.",
    findingsWithEvidence
  );
  renderApplicationClaimAudit(payload.application_claim_audit || {});
  renderTimelineAudit(payload.timeline_audit || {});
  renderApplicationPrep(payload.application_prep || null);
  renderClarificationBrief(payload.clarification_brief || { items: [] });
  updateReviewSummary();
  renderEvidenceGraph(payload.evidence_graph || { requirements: [] });
  renderJobListCoverage(payload.job_item_coverage || {});
  renderRoleClarityAudit(payload.role_clarity_audit || {});

  const countsNode = document.getElementById("summary-counts");
  countsNode.replaceChildren();
  addCount(countsNode, counts.shown, "direct evidence", "supported");
  addCount(countsNode, counts.related, "related experience", "related");
  addCount(countsNode, counts.not_mentioned, "not mentioned", "not_found");
  addCount(countsNode, counts.details_differ, "details differ", "conflicting");
  addCount(countsNode, counts.needs_review, "check this", "needs_review");

  const totalRequirements = payload.requirements.length;
  const evidenceFound = counts.shown + counts.related;
  const summaryTitle = document.getElementById("plain-summary-title");
  const summaryDetail = document.getElementById("plain-summary-detail");
  const coverageSummary = document.getElementById("job-coverage-summary");
  summaryTitle.textContent = totalRequirements
    ? "We found direct or potentially related CV evidence for " + evidenceFound + " of " + totalRequirements + " job requirements."
    : "We couldn't identify any job requirements.";
  const evidenceNotes = [];
  if (counts.shown) evidenceNotes.push(counts.shown + " with direct evidence");
  if (counts.related) evidenceNotes.push(counts.related + " with possible related experience");
  if (counts.not_mentioned) {
    evidenceNotes.push(counts.not_mentioned + " not mentioned in the CV");
  }
  if (counts.details_differ) {
    evidenceNotes.push(counts.details_differ + " where CV details differ");
  }
  if (counts.needs_review) {
    evidenceNotes.push(counts.needs_review + " that need a closer look");
  }
  summaryDetail.textContent = totalRequirements
    ? (evidenceNotes.length ? evidenceNotes.join(" · ") + ". " : "No unclear or conflicting details were flagged. ") +
      "Related experience may transfer but does not prove the exact requirement. This only describes what appears in this CV; if something isn't mentioned, that doesn't prove the person lacks it."
    : "Check the job description and try again. This review does not decide whether someone is suitable for the role.";
  renderRecruiterDecisionPanel();

  const coverage = payload.job_item_coverage || {};
  const unmappedCount = Array.isArray(coverage.items)
    ? coverage.items.filter(function (item) { return item.status === "needs_review"; }).length
    : 0;
  coverageSummary.hidden = unmappedCount === 0;
  coverageSummary.textContent = unmappedCount
    ? "Check coverage: " + unmappedCount + " job-post item" + (unmappedCount === 1 ? " was" : "s were") +
      " not mapped to a finding. The report may not cover the full role; open verification details to inspect."
    : "";

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
      ["supporting", "Teal highlight: direct evidence"],
      ["related", "Violet highlight: related experience"],
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
  document.getElementById("technical-audit-summary").textContent =
    "Verification details · " + verifiedQuotes + "/" + proposedQuotes + " quotes checked" +
    (excludedQuotes ? " · " + excludedQuotes + " excluded" : "");

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
    ? "Fictional example. Select a finding below to open the exact source evidence. This is not Muse output."
    : "Open any finding to see the source quote and page. EvidenceTrail checks document text; a person decides what it means.";

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
    const priority = priorityPresentation(entry);
    heading.textContent = "Job line " + String(entry.line || "—") + " · " +
      String(entry.kind || "Job need") + " · " +
      (priority ? priority.label : "Priority not stated");
    const source = document.createElement("blockquote");
    source.textContent = String(entry.text || "");
    const priorityBasis = document.createElement("span");
    priorityBasis.className = "role-audit-priority";
    priorityBasis.textContent = entry.priority_basis
      ? "The job post says: " + String(entry.priority_basis)
      : "The job post doesn't say whether this is required.";
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
    const timelineNeedsReview = Array.isArray(row.timeline_review_flags) && row.timeline_review_flags.length > 0;
    const relationLabel = timelineNeedsReview
      ? "Conflict to clarify · " + timelineMuseLabel(row)
      : row.evidence_type === "related"
        ? "related experience"
        : row.evidence_type === "direct"
          ? "direct evidence"
          : String(row.status || "not_found").replaceAll("_", " ");
    meta.className = "graph-meta status-" + (timelineNeedsReview
      ? "needs_review"
      : row.evidence_type === "related" ? "related" : String(row.status || "not_found"));
    meta.textContent = String(row.id || "") + " · " + relationLabel +
      (row.certainty === "ambiguous" && !timelineNeedsReview ? " · ambiguous" : "");
    const title = document.createElement("strong");
    title.textContent = String(row.requirement || "");
    requirement.append(meta, title);

    const jobSource = row.job_source && typeof row.job_source === "object"
      ? row.job_source
      : null;
    if (jobSource && jobSource.text) {
      const sourceBlock = document.createElement("div");
      sourceBlock.className = "graph-job-source";
      const sourceLabel = document.createElement("span");
      sourceLabel.textContent = Number.isInteger(jobSource.line)
        ? "JOB POST · STARTS AT LINE " + jobSource.line
        : "JOB POST · SOURCE TEXT CHECKED";
      const sourceText = document.createElement("q");
      sourceText.textContent = String(jobSource.text);
      sourceBlock.append(sourceLabel, sourceText);
      requirement.appendChild(sourceBlock);
    }

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
          (source.role === "contradicts" ? "is-conflict" : source.evidence_type === "related" ? "is-related" : "is-support");
        button.dataset.page = String(source.page);
        button.dataset.quote = String(source.quote || "");
        button.setAttribute("aria-label",
          (source.role === "contradicts" ? "Open conflicting passage" : source.evidence_type === "related" ? "Open related passage" : "Open supporting passage") +
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

function plainFindingState(finding) {
  if (Array.isArray(finding.timeline_review_flags) && finding.timeline_review_flags.length) return "needs_review";
  if (finding.status === "conflicting") return "details_differ";
  if (finding.certainty === "ambiguous") return "needs_review";
  if (finding.evidence_type === "related") return "related";
  if (finding.status === "supported") return "shown";
  if (finding.status === "not_found") return "not_mentioned";
  return "needs_review";
}

function plainFindingLabel(finding) {
  if (Array.isArray(finding.timeline_review_flags) && finding.timeline_review_flags.length) {
    return "Conflict to clarify";
  }
  const state = plainFindingState(finding);
  return {
    shown: "Shown in CV",
    related: "Related experience",
    not_mentioned: "Not mentioned",
    details_differ: "Details differ",
    needs_review: "Needs a closer look"
  }[state];
}

function timelineMuseLabel(finding) {
  const originalType = String(
    finding && (finding.muse_evidence_type || finding.evidence_type) || ""
  );
  const labels = {
    direct: "Direct",
    related: "Related",
    unsupported: "Unsupported",
    conflicting: "Conflicting",
  };
  return "Muse: " + (labels[originalType] || "Needs review") + " · Timeline check: conflict";
}

function evidenceStrengthValue(finding) {
  const value = String(finding && finding.evidence_strength || "");
  if (["specific", "stated", "keyword_only", "none"].includes(value)) return value;
  return Array.isArray(finding && finding.evidence) && finding.evidence.length
    ? "stated"
    : "none";
}

function evidenceStrengthLabel(value) {
  return {
    specific: "Specific detail",
    stated: "Stated only",
    keyword_only: "Keyword only",
    none: "No passage",
  }[value] || "No passage";
}

function createEvidenceStrengthChip(value) {
  const normalized = ["specific", "stated", "keyword_only", "none"].includes(value)
    ? value
    : "none";
  const explanations = {
    specific: "The passage gives a concrete action, scope, or result.",
    stated: "The CV states relevant experience but gives little concrete detail.",
    keyword_only: "A keyword or title mention alone is not supporting evidence.",
    none: "No relevant passage was found in the CV.",
  };
  const icons = {
    specific: "✓",
    stated: "●",
    keyword_only: "!",
    none: "○",
  };
  const chip = document.createElement("span");
  chip.className = "evidence-strength-chip evidence-strength-" + normalized;
  chip.setAttribute("aria-label", evidenceStrengthLabel(normalized));
  chip.title = explanations[normalized];
  const icon = document.createElement("span");
  icon.className = "evidence-strength-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = icons[normalized];
  const label = document.createElement("span");
  label.textContent = evidenceStrengthLabel(normalized);
  chip.append(icon, label);
  return chip;
}

function priorityPresentation(criterion) {
  if (!criterion) return null;
  const priority = String(criterion.priority || "Not stated");
  const labels = {
    "Explicitly required": ["Must have", "required"],
    "Preferred": ["Good to have", "preferred"],
    "Preferred · explicitly not required": ["Good to have", "preferred"],
    "Explicitly not required": ["Optional", "optional"],
    "Mixed priority wording": ["Priority unclear", "unclear"],
    "Not stated": ["Priority not stated", "not-stated"]
  };
  const presentation = labels[priority] || ["Priority not stated", "not-stated"];
  return {
    label: presentation[0],
    className: presentation[1],
    basis: String(criterion.priority_basis || "")
  };
}

function buildFindingCard(finding, criterion) {
  const card = document.createElement("article");
  card.className = "finding-card";
  const body = document.createElement("div");
  body.className = "finding-body";
  const header = document.createElement("div");
  header.className = "finding-header";
  const id = document.createElement("span");
  const findingNumber = String(finding.id || "").replace(/^R/i, "");
  id.textContent = findingNumber ? "JOB NEED " + findingNumber : "JOB NEED";
  const badges = document.createElement("div");
  badges.className = "finding-badges";
  const priority = priorityPresentation(criterion);
  if (priority) {
    const priorityBadge = document.createElement("span");
    priorityBadge.className = "priority-badge priority-" + priority.className;
    priorityBadge.textContent = priority.label;
    if (priority.basis) priorityBadge.title = "Based on job-post wording: " + priority.basis;
    badges.appendChild(priorityBadge);
  }
  const status = document.createElement("span");
  const displayState = plainFindingState(finding);
  status.className = "status-badge status-" + displayState;
  status.textContent = plainFindingLabel(finding);
  badges.appendChild(status);
  const strengthValue = evidenceStrengthValue(finding);
  badges.appendChild(createEvidenceStrengthChip(strengthValue));
  header.append(id, badges);

  const title = document.createElement("h3");
  title.textContent = finding.requirement;
  const note = document.createElement("p");
  note.className = "finding-note";
  note.textContent = Array.isArray(finding.timeline_review_flags) && finding.timeline_review_flags.length
    ? "The local date check found a timeline discrepancy. Review the dated roles and clarify before relying on this experience total."
    : finding.status === "conflicting"
    ? "The CV gives different details. Check both passages before deciding what they mean."
    : finding.evidence_strength === "keyword_only"
      ? "The CV mentions a keyword or title, but gives no described task or example to support this requirement."
    : finding.evidence_type === "related" && finding.certainty === "ambiguous"
      ? "Muse sees a possible connection, but the evidence or transfer needs a closer human review."
    : finding.certainty === "ambiguous"
      ? "The CV wording is unclear. Check the passages below before relying on this result."
      : finding.evidence_type === "related"
        ? "The CV describes experience that may transfer to this job need. It does not establish the exact requirement."
      : finding.status === "supported"
        ? "The CV includes a passage that may support this job need. Open it to review the wording."
      : finding.status === "not_found"
          ? "This CV doesn't mention this job need. The person may still have this experience."
          : "This result needs a closer look.";
  body.append(header, title);
  if (finding.certainty === "ambiguous") {
    const ambiguity = document.createElement("p");
    ambiguity.className = "ambiguity-flag";
    ambiguity.textContent = "Please check the original CV wording before relying on this result.";
    body.appendChild(ambiguity);
  }
  body.appendChild(note);
  if (Array.isArray(finding.timeline_review_flags) && finding.timeline_review_flags.length) {
    const provenance = document.createElement("p");
    provenance.className = "timeline-provenance";
    provenance.textContent = timelineMuseLabel(finding);
    body.appendChild(provenance);
  }

  if (finding.evidence_type === "related") {
    const transferCard = document.createElement("section");
    transferCard.className = "finding-transfer-card";
    const transferTitle = document.createElement("h4");
    transferTitle.textContent = "Why this experience may transfer";
    const transfer = document.createElement("p");
    transfer.className = "finding-transfer-explanation";
    transfer.textContent = String(finding.transfer_explanation ||
      "Muse suggests a possible connection, but no transfer explanation was returned. Review the CV passage before relying on it.");
    transferCard.append(transferTitle, transfer);

    const aspects = Array.isArray(finding.unproven_aspects)
      ? finding.unproven_aspects
      : [];
    const unproven = document.createElement("div");
    unproven.className = "finding-unproven";
    const unprovenTitle = document.createElement("strong");
    unprovenTitle.textContent = "Still to check";
    unproven.appendChild(unprovenTitle);
    if (aspects.length) {
      const unprovenList = document.createElement("ul");
      aspects.forEach(function (aspect) {
        const item = document.createElement("li");
        item.textContent = String(aspect);
        unprovenList.appendChild(item);
      });
      unproven.appendChild(unprovenList);
    } else {
      const noGap = document.createElement("p");
      noGap.textContent = "No specific gap was returned. Check the exact job requirement with the candidate.";
      unproven.appendChild(noGap);
    }
    transferCard.appendChild(unproven);

    if (finding.follow_up_question) {
      const questionLabel = document.createElement("strong");
      questionLabel.className = "finding-follow-up-label";
      questionLabel.textContent = "Suggested follow-up question";
      const question = document.createElement("blockquote");
      question.className = "finding-follow-up-question";
      question.textContent = String(finding.follow_up_question);
      transferCard.append(questionLabel, question);
    }
    body.appendChild(transferCard);
  }

  const proof = document.createElement("details");
  proof.className = "finding-proof";
  const proofSummary = document.createElement("summary");
  proofSummary.textContent = finding.evidence && finding.evidence.length
    ? "Show the job wording and CV passage"
    : "Show the job wording we checked";
  const proofBody = document.createElement("div");
  proofBody.className = "finding-proof-body";
  const jobSource = finding.job_source && typeof finding.job_source === "object"
    ? finding.job_source
    : null;
  if (jobSource && jobSource.text) {
    const source = document.createElement("div");
    source.className = "finding-job-source";
    const sourceLabel = document.createElement("span");
    sourceLabel.textContent = Number.isInteger(jobSource.line)
      ? "From the job post · line " + jobSource.line
      : "From the job post";
    const sourceQuote = document.createElement("blockquote");
    sourceQuote.textContent = String(jobSource.text);
    source.append(sourceLabel, sourceQuote);
    proofBody.appendChild(source);
  }
  if (finding.note) {
    const fullNote = document.createElement("p");
    fullNote.className = "finding-detail-note";
    fullNote.textContent = finding.note;
    proofBody.appendChild(fullNote);
  }

  if (finding.evidence && finding.evidence.length) {
    const quoteList = document.createElement("div");
    quoteList.className = "quote-list";
    finding.evidence.forEach(function (evidence) {
      const quote = document.createElement("div");
      quote.className = "quote-item" +
        (evidence.role === "contradicts" ? " contradicts" : evidence.evidence_type === "related" ? " related-evidence" : "");
      const role = document.createElement("span");
      role.className = "quote-role";
      const timelineNeedsReview = Array.isArray(finding.timeline_review_flags) && finding.timeline_review_flags.length > 0;
      const evidenceLabel = evidence.role === "contradicts"
        ? "CV says something different"
        : timelineNeedsReview
          ? "CV passage · timeline needs review"
        : finding.evidence_type === "related"
          ? "Related CV passage"
          : "Direct CV passage";
      role.textContent = evidenceLabel +
        (evidence.source_id ? " · " + evidence.source_id : "");
      const text = document.createElement("div");
      text.className = "quote-text";
      text.textContent = "“" + evidence.quote + "”";
      const anchor = document.createElement("a");
      anchor.className = "page-anchor";
      anchor.href = "#page-" + evidence.page;
      anchor.dataset.page = String(evidence.page);
      anchor.dataset.quote = evidence.quote;
      anchor.textContent = "Open this page in the CV · page " + evidence.page + " →";
      quote.append(role, text, anchor);
      quoteList.appendChild(quote);
    });
    proofBody.appendChild(quoteList);
  } else {
    const noQuote = document.createElement("p");
    noQuote.className = "finding-detail-note";
    noQuote.textContent = finding.evidence_strength === "keyword_only"
      ? "A keyword or title mention was found, but no described task or example supported this requirement. The mention wasn't counted as supporting evidence."
      : "We couldn't find a checked passage in this CV. That doesn't tell us whether the person has this experience.";
    proofBody.appendChild(noQuote);
  }
  proof.append(proofSummary, proofBody);
  body.appendChild(proof);
  card.dataset.findingId = finding.id;
  const reviewDetails = document.createElement("details");
  reviewDetails.className = "review-details";
  const reviewSummary = document.createElement("summary");
  reviewSummary.textContent = "Add reviewer note";
  reviewDetails.append(reviewSummary, buildReviewControls(finding));
  card.append(body, reviewDetails);
  return card;
}

function buildReviewControls(finding) {
  const findingId = String(finding.id || "");
  const isRelated = finding.evidence_type === "related";
  const section = document.createElement("section");
  section.className = "human-review-controls";
  const heading = document.createElement("h4");
  heading.textContent = "Human review";
  const explanation = document.createElement("p");
  explanation.className = "review-explanation";
  explanation.textContent = isRelated
    ? "Record whether this related experience counts for this requirement. This records your review, not a candidate-wide score."
    : "Record whether this evidence trail was reviewed. This is not a candidate decision.";

  const statusLabel = document.createElement("label");
  statusLabel.className = "review-label";
  statusLabel.htmlFor = "review-status-" + findingId;
  statusLabel.textContent = isRelated ? "Related experience decision" : "Review status";
  const status = document.createElement("select");
  status.id = "review-status-" + findingId;
  status.className = "review-input review-select";
  const reviewChoices = isRelated
    ? [
      ["not_reviewed", "Not reviewed"],
      ["related_accepted", "Counts as related for this role"],
      ["related_rejected", "Does not meet this requirement"],
      ["follow_up", "Needs follow-up"],
    ]
    : [
      ["not_reviewed", "Not reviewed"],
      ["reviewed", "Evidence reviewed"],
      ["follow_up", "Needs follow-up"],
    ];
  reviewChoices.forEach(function (choice) {
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

  const savedReview = reviewEntries[findingId] || { status: "not_reviewed", note: "" };
  status.value = savedReview.status || "not_reviewed";
  note.value = savedReview.note || "";

  function saveReview() {
    reviewEntries[findingId] = { status: status.value, note: note.value.trim() };
  }

  status.addEventListener("change", function () {
    saveReview();
    updateReviewSummary();
    updateBatchMatrixReviewStatus(activeBatchIndex, findingId, status.value);
  });
  note.addEventListener("input", saveReview);
  if (!reviewEntries[findingId]) {
    reviewEntries[findingId] = { status: "not_reviewed", note: "" };
  }
  section.append(heading, explanation, statusLabel, status, noteLabel, note);
  return section;
}

function renderApplicationPrep(prep) {
  const panel = document.getElementById("application-prep");
  const list = document.getElementById("application-prep-items");
  const disclosure = document.getElementById("application-prep-disclosure");
  const empty = document.getElementById("application-prep-empty");
  const status = document.getElementById("application-prep-status");
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
    const jobSource = entry.job_source && typeof entry.job_source === "object"
      ? entry.job_source
      : null;
    let jobSourceNode = null;
    if (jobSource && jobSource.text) {
      jobSourceNode = document.createElement("div");
      jobSourceNode.className = "application-prep-job-source";
      const sourceLabel = document.createElement("span");
      sourceLabel.textContent = Number.isInteger(jobSource.line)
        ? "Job post · starts at line " + jobSource.line
        : "Job post wording checked";
      const sourceText = document.createElement("blockquote");
      sourceText.textContent = String(jobSource.text);
      jobSourceNode.append(sourceLabel, sourceText);
    }
    const action = document.createElement("p");
    action.className = "application-prep-action";
    action.textContent = String(entry.action || "Review this item against your records.");
    item.append(meta, requirement);
    if (jobSourceNode) item.appendChild(jobSourceNode);
    item.appendChild(action);

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
    check.checked = Boolean(applicationPrepChecks[entry.requirement_id]);
    reviewLabel.append(check, document.createTextNode(" I checked this against my records"));
    item.appendChild(reviewLabel);
    list.appendChild(item);
  });
}

function renderTimelineAudit(audit) {
  const panel = document.getElementById("timeline-audit");
  const summary = document.getElementById("timeline-audit-summary");
  const flags = document.getElementById("timeline-audit-flags");
  const areaSummary = document.getElementById("timeline-area-summary");
  const episodesPanel = document.getElementById("timeline-episodes-panel");
  const episodesSummary = document.getElementById("timeline-episodes-summary");
  const episodesList = document.getElementById("timeline-episodes");
  const episodes = Array.isArray(audit.episodes) ? audit.episodes : [];
  const timelineFlags = Array.isArray(audit.flags) ? audit.flags : [];
  const areaTenure = Array.isArray(audit.tenure_by_area) ? audit.tenure_by_area : [];
  flags.replaceChildren();
  episodesList.replaceChildren();
  panel.hidden = !episodes.length && !timelineFlags.length;
  if (panel.hidden) return;

  const months = Math.max(0, Number(audit.dated_employment_months) || 0);
  const overlapCount = Array.isArray(audit.overlaps) ? audit.overlaps.length : 0;
  const claimCount = Array.isArray(audit.experience_claims)
    ? audit.experience_claims.filter(function (claim) { return claim.status === "review"; }).length
    : 0;
  summary.textContent = episodes.length + " dated role(s) · about " + (months / 12).toFixed(1) +
    " unique years shown" + (overlapCount ? " · " + overlapCount + " overlap(s)" : "") +
    (claimCount ? " · " + claimCount + " duration claim(s) to clarify" : "");
  areaSummary.hidden = !areaTenure.length;
  areaSummary.textContent = areaTenure.length
    ? "Dated months by verified work area: " + areaTenure.map(function (entry) {
      return String(entry.area || "Work area") + " · " + Number(entry.months || 0) + " months";
    }).join("; ")
    : "";

  timelineFlags.forEach(function (flag) {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = flag.type === "employment_date_overlap"
      ? "Employment dates overlap"
      : "Stated experience is longer than the dated roles shown";
    const note = document.createElement("p");
    const linkedRequirements = (Array.isArray(audit.requirement_links) ? audit.requirement_links : [])
      .filter(function (link) { return link.topic === flag.topic; })
      .map(function (link) { return String(link.requirement_id || ""); })
      .filter(Boolean);
    note.textContent = String(flag.review_note || "Review these dates with the candidate.") +
      (linkedRequirements.length ? " Affected job need(s): " + Array.from(new Set(linkedRequirements)).join(", ") + "." : "");
    item.append(title, note);
    flags.appendChild(item);
  });

  episodesPanel.hidden = !episodes.length;
  episodesSummary.textContent = "Quote-verified dated roles · " + episodes.length;
  episodes.forEach(function (episode) {
    const item = document.createElement("li");
    const heading = document.createElement("strong");
    heading.textContent = String(episode.role || "Role not confirmed") + " · " +
      String(episode.start_date || "") + "–" + String(episode.end_date || "");
    item.appendChild(heading);
    if (episode.date_quote) {
      const source = document.createElement("button");
      source.type = "button";
      source.className = "timeline-source";
      source.dataset.page = String(episode.date_page || "");
      source.dataset.quote = String(episode.date_quote);
      source.textContent = "CV page " + String(episode.date_page || "—") + " · “" +
        String(episode.date_quote) + "” · Open source ↗";
      item.appendChild(source);
    }
    episodesList.appendChild(item);
  });
}

function renderApplicationClaimAudit(audit) {
  const panel = document.getElementById("application-claim-audit");
  const summary = document.getElementById("application-claim-audit-summary");
  const root = document.getElementById("application-claim-audit-items");
  root.replaceChildren();
  const claims = Array.isArray(audit.results) ? audit.results : [];
  panel.hidden = !claims.length;
  if (!claims.length) return;

  const counts = { supported: 0, not_found: 0, conflicting: 0 };
  claims.forEach(function (claim) { counts[claim.status] = (counts[claim.status] || 0) + 1; });
  summary.textContent = counts.supported + " supported by the CV · " + counts.not_found +
    " not mentioned · " + counts.conflicting + " with details that differ";

  claims.forEach(function (claim) {
    const card = document.createElement("article");
    card.className = "application-claim-card";
    const head = document.createElement("div");
    head.className = "application-claim-card-head";
    const id = document.createElement("span");
    id.textContent = claim.id || "Claim";
    const status = document.createElement("span");
    status.className = "status-badge status-" + claim.status;
    status.textContent = claim.status === "supported"
      ? "CV shows support"
      : claim.status === "conflicting" ? "Details differ" : "Not mentioned in CV";
    head.append(id, status);

    const text = document.createElement("blockquote");
    text.textContent = "“" + String(claim.claim || "") + "”";
    const note = document.createElement("p");
    note.textContent = String(claim.note || "");
    card.append(head, text, note);

    (Array.isArray(claim.evidence) ? claim.evidence : []).forEach(function (evidence) {
      const source = document.createElement("button");
      source.type = "button";
      source.className = "claim-source" + (evidence.role === "contradicts" ? " is-conflict" : "");
      source.dataset.page = String(evidence.page || "");
      source.dataset.quote = String(evidence.quote || "");
      const label = document.createElement("strong");
      label.textContent = (evidence.role === "contradicts" ? "Different CV passage" : "CV passage") +
        " · page " + String(evidence.page || "—");
      source.append(label, document.createTextNode("“" + String(evidence.quote || "") + "” · Open source ↗"));
      card.appendChild(source);
    });
    root.appendChild(card);
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
    const jobSource = entry.job_source && typeof entry.job_source === "object"
      ? entry.job_source
      : null;
    if (jobSource && jobSource.text) {
      lines.push((Number.isInteger(jobSource.line) ? "Job post starting at line " + jobSource.line : "Job post wording") + ": " + String(jobSource.text));
    }
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
    const savedResponse = currentCandidateResponses[entry.requirement_id];
    if (savedResponse && typeof savedResponse === "object") {
      responseInput.value = String(savedResponse.text || "");
    }
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
    removeResponse.hidden = !savedResponse;
    const responseStatus = document.createElement("p");
    responseStatus.className = "candidate-response-status";
    responseStatus.setAttribute("role", "status");
    responseStatus.textContent = savedResponse
      ? "Reply recorded in this tab. It stays separate from CV evidence and is included in the download."
      : "No candidate reply recorded.";
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
  const reviewed = entries.filter(function (entry) {
    return ["reviewed", "related_accepted", "related_rejected"].includes(entry.status);
  }).length;
  const relatedAccepted = entries.filter(function (entry) { return entry.status === "related_accepted"; }).length;
  const relatedRejected = entries.filter(function (entry) { return entry.status === "related_rejected"; }).length;
  const followUp = entries.filter(function (entry) { return entry.status === "follow_up"; }).length;
  const pending = entries.length - reviewed - followUp;
  const relatedSummary = relatedAccepted || relatedRejected
    ? " · " + relatedAccepted + " related accepted · " + relatedRejected + " not accepted"
    : "";
  summary.textContent = reviewed + " reviewed" + relatedSummary + " · " + followUp + " need follow-up · " +
    pending + " not reviewed. Notes stay in this tab until you download the pack.";
}

function buildReviewedReport(reportHtml) {
  const reportDocument = new DOMParser().parseFromString(reportHtml, "text/html");
  const labels = {
    not_reviewed: "Not reviewed",
    reviewed: "Evidence reviewed",
    follow_up: "Needs follow-up",
    related_accepted: "Related experience accepted for this role",
    related_rejected: "Related experience does not meet this requirement",
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

  const activeEntry = activeCandidateEntry();
  const result = currentResultPayload || (activeEntry && activeEntry.result) || {};
  if (activeEntry) {
    const handoff = reportDocument.createElement("section");
    handoff.className = "recruiter-handoff";
    const heading = reportDocument.createElement("h2");
    heading.textContent = "Recruiter hand-off";
    const candidate = reportDocument.createElement("p");
    candidate.textContent = (activeEntry.candidateId || "Candidate " + (activeBatchIndex + 1)) +
      " · " + (activeEntry.filename || "CV");
    const decision = reportDocument.createElement("p");
    decision.className = "recruiter-handoff-decision";
    decision.textContent = "Recruiter decision: " + recruiterDecisionLabel(activeEntry.decision);
    if (activeEntry.decisionUpdatedAt) {
      decision.textContent += " · recorded " + activeEntry.decisionUpdatedAt + " (UTC)";
    }
    handoff.append(heading, candidate, decision);

    if (activeEntry.interviewInviteDraft) {
      const invite = reportDocument.createElement("section");
      invite.className = "recruiter-interview-invite";
      const inviteHeading = reportDocument.createElement("h3");
      inviteHeading.textContent = "Interview invitation draft · not sent";
      const inviteBoundary = reportDocument.createElement("p");
      inviteBoundary.textContent = "Recruiter-edited text. EvidenceTrail has not contacted the candidate or scheduled an interview.";
      const inviteText = reportDocument.createElement("pre");
      inviteText.textContent = activeEntry.interviewInviteDraft;
      invite.append(inviteHeading, inviteBoundary, inviteText);
      handoff.appendChild(invite);
    }

    const requirements = Array.isArray(result.requirements) ? result.requirements : [];
    const categories = { shown: 0, related: 0, not_mentioned: 0, details_differ: 0, needs_review: 0 };
    requirements.forEach(function (finding) {
      const state = plainFindingState(finding);
      categories[state] = (categories[state] || 0) + 1;
    });
    const evidenceSummary = reportDocument.createElement("p");
    evidenceSummary.textContent = "CV evidence summary: " + categories.shown + " direct · " +
      categories.related + " related · " + categories.not_mentioned + " not mentioned · " +
      categories.details_differ + " details differ · " + categories.needs_review + " need a closer look. " +
      "These are document findings, not a candidate score.";
    handoff.appendChild(evidenceSummary);

    const acceptedRelated = requirements.filter(function (finding) {
      return finding.evidence_type === "related" && reviewEntries[finding.id] &&
        reviewEntries[finding.id].status === "related_accepted";
    });
    const acceptedHeading = reportDocument.createElement("h3");
    acceptedHeading.textContent = "Related evidence the recruiter accepted for this role";
    handoff.appendChild(acceptedHeading);
    if (acceptedRelated.length) {
      const acceptedList = reportDocument.createElement("ul");
      acceptedRelated.forEach(function (finding) {
        const item = reportDocument.createElement("li");
        const review = reviewEntries[finding.id] || {};
        item.textContent = String(finding.id || "") + " · " + String(finding.requirement || "") +
          (review.note ? " · Reviewer note: " + review.note : "");
        acceptedList.appendChild(item);
      });
      handoff.appendChild(acceptedList);
    } else {
      const noneAccepted = reportDocument.createElement("p");
      noneAccepted.textContent = "No related evidence was marked as accepted.";
      handoff.appendChild(noneAccepted);
    }

    const followUps = result.clarification_brief && Array.isArray(result.clarification_brief.items)
      ? result.clarification_brief.items
      : [];
    if (followUps.length) {
      const followUpHeading = reportDocument.createElement("h3");
      followUpHeading.textContent = "Questions to carry forward";
      const followUpList = reportDocument.createElement("ul");
      followUps.forEach(function (entry) {
        const item = reportDocument.createElement("li");
        item.textContent = String(entry.requirement_id || "") + " · " +
          String(entry.question || entry.requirement || "Review this requirement");
        followUpList.appendChild(item);
      });
      handoff.append(followUpHeading, followUpList);
    }

    if (activeEntry.decisionNote) {
      const noteHeading = reportDocument.createElement("h3");
      noteHeading.textContent = "Handoff note";
      const note = reportDocument.createElement("p");
      note.textContent = activeEntry.decisionNote;
      handoff.append(noteHeading, note);
    }
    const boundary = reportDocument.createElement("p");
    boundary.className = "recruiter-handoff-boundary";
    boundary.textContent = "The decision and notes above were entered by the recruiter. Muse findings describe supplied documents and do not determine suitability.";
    handoff.appendChild(boundary);

    const reportStyle = reportDocument.querySelector("style");
    if (reportStyle) {
      reportStyle.textContent += "\n.recruiter-handoff{margin:18px 0 24px;padding:16px 18px;border:1px solid #c9d9f1;border-radius:12px;background:#f7faff}.recruiter-handoff h2{margin:0 0 8px}.recruiter-handoff h3{margin:14px 0 6px;font-size:14px}.recruiter-handoff p,.recruiter-handoff li{font-size:12px;line-height:1.55}.recruiter-handoff-decision{font-weight:750;color:#26364d}.recruiter-handoff-boundary{padding-top:8px;border-top:1px solid #dfe7f2;color:#68778d}.recruiter-interview-invite{margin-top:14px;padding:12px;border:1px solid #d7e1ef;border-radius:8px;background:#fff}.recruiter-interview-invite pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;font-size:12px;line-height:1.55}";
    }
    const introForHandoff = reportDocument.querySelector("main .sub");
    if (introForHandoff) introForHandoff.insertAdjacentElement("afterend", handoff);
    else reportDocument.querySelector("main").prepend(handoff);
  }

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

document.getElementById("application-claim-audit-items").addEventListener("click", function (event) {
  const target = event.target instanceof Element
    ? event.target.closest(".claim-source")
    : null;
  if (!target || !sourcePdfFile || !sourcePdfPayload) return;
  void openInteractivePdf(Number(target.dataset.page), target.dataset.quote || "");
});

document.getElementById("timeline-audit").addEventListener("click", function (event) {
  const target = event.target instanceof Element
    ? event.target.closest(".timeline-source")
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
        (evidence.role === "contradicts" ? "conflicting" : evidence.evidence_type === "related" ? "related" : "supporting") +
        (activeSourceQuote && evidence.quote === activeSourceQuote ? " is-active" : "");
      marker.style.left = (x0 / pageWidth * 100) + "%";
      marker.style.top = (y0 / pageHeight * 100) + "%";
      marker.style.width = ((x1 - x0) / pageWidth * 100) + "%";
      marker.style.height = ((y1 - y0) / pageHeight * 100) + "%";
      marker.title = entry.finding.id + " · " +
        (evidence.role === "contradicts" ? "conflicting statement" : evidence.evidence_type === "related" ? "related CV passage" : "direct CV passage") +
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
