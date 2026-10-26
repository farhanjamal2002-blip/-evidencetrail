const form = document.getElementById("analysis-form");
const cvInput = document.getElementById("cv");
const jobInput = document.getElementById("job-description");
const fileName = document.getElementById("file-name");
const charCount = document.getElementById("char-count");
const analyzeButton = document.getElementById("analyze-button");
const errorBox = document.getElementById("error-box");
const results = document.getElementById("results");
const uploadZone = document.querySelector(".upload-zone");
let currentReport = "";
let reviewEntries = Object.create(null);

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

  analyzeButton.disabled = true;
  analyzeButton.querySelector("span:first-child").textContent = "Muse is reading the CV and job requirements…";
  const formData = new FormData(form);

  try {
    const response = await fetch("/api/analyze", { method: "POST", body: formData });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Analysis could not be completed.");
    }
    renderResults(payload);
  } catch (error) {
    showError(error.message || "Analysis failed. No result was generated.");
  } finally {
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

function renderResults(payload) {
  const findingsList = document.getElementById("findings-list");
  const counts = { supported: 0, not_found: 0, conflicting: 0 };
  reviewEntries = Object.create(null);
  findingsList.replaceChildren();
  document.getElementById("source-pages").replaceChildren();
  payload.requirements.forEach(function (finding) {
    counts[finding.status] = (counts[finding.status] || 0) + 1;
    findingsList.appendChild(buildFindingCard(finding));
  });
  updateReviewSummary();

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
  document.getElementById("run-meta").textContent =
    payload.model + " · " + payload.analysis_calls + " real analysis call · " +
    (usage.input_tokens || 0).toLocaleString() + " input tokens · " +
    (usage.output_tokens || 0).toLocaleString() + " output tokens" + ocrText +
    (rejectedCount ? " · " + rejectedCount + " unverified requirement(s) omitted" : "");
  document.getElementById("result-caption").textContent =
    "Every displayed quote was checked against the uploaded PDF. Muse's interpretation is shown for human review; the app verifies source text, not qualification truth.";

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
  results.scrollIntoView({ behavior: "smooth", block: "start" });
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
  body.append(header, title, note);

  if (finding.evidence && finding.evidence.length) {
    const quoteList = document.createElement("div");
    quoteList.className = "quote-list";
    finding.evidence.forEach(function (evidence) {
      const quote = document.createElement("div");
      quote.className = "quote-item" + (evidence.role === "contradicts" ? " contradicts" : "");
      const role = document.createElement("span");
      role.className = "quote-role";
      role.textContent = evidence.role === "contradicts" ? "Conflicting statement" : "Supporting passage";
      const text = document.createElement("div");
      text.className = "quote-text";
      text.textContent = "“" + evidence.quote + "”";
      const anchor = document.createElement("a");
      anchor.className = "page-anchor";
      anchor.href = "#page-" + evidence.page;
      anchor.textContent = "Open highlighted source · page " + evidence.page + " ↓";
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
