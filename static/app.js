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
  findingsList.replaceChildren();
  document.getElementById("source-pages").replaceChildren();
  payload.requirements.forEach(function (finding) {
    counts[finding.status] = (counts[finding.status] || 0) + 1;
    findingsList.appendChild(buildFindingCard(finding));
  });

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
    "Every displayed passage below was checked against the uploaded PDF. " +
    "Requirements are shown only when their wording appears in the supplied job description.";

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
  card.appendChild(body);
  return card;
}

document.getElementById("download-report").addEventListener("click", function () {
  if (!currentReport) return;
  const blob = new Blob([currentReport], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "evidencetrail-evidence-pack.html";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
});
