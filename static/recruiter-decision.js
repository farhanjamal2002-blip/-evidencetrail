(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.EvidenceTrailRecruiterDecision = api;
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";

  const reasonLabels = Object.freeze({
    required_evidence_not_shown: "Required evidence is not shown in the submitted CV",
    credential_not_documented: "Required credential is not documented",
    scope_needs_clarification: "Dates, scope, or ownership need clarification",
    related_not_sufficient: "Related experience does not meet this role's requirement",
    other: "Other job-related reason",
  });

  function requiresReason(decision) {
    return decision === "hold" || decision === "do_not_advance";
  }

  function normalizeRequirementIds(linkedRequirementIds) {
    if (!Array.isArray(linkedRequirementIds)) return [];
    return Array.from(new Set(linkedRequirementIds
      .filter(function (value) { return typeof value === "string"; })
      .map(function (value) { return value.trim(); })
      .filter(Boolean)));
  }

  function selectLinkedRequirements(requirements, linkedRequirementIds) {
    const selected = new Set(normalizeRequirementIds(linkedRequirementIds));
    if (!Array.isArray(requirements) || !selected.size) return [];
    return requirements.filter(function (finding) {
      return finding && selected.has(String(finding.id || ""));
    });
  }

  function validateDecision(decision, reason, note, linkedRequirementIds) {
    if (!requiresReason(decision)) return "";
    if (!Object.prototype.hasOwnProperty.call(reasonLabels, reason)) {
      return "Choose a job-related reason before recording Hold or Do not advance.";
    }
    if (!normalizeRequirementIds(linkedRequirementIds).length) {
      return "Link this decision to at least one job requirement.";
    }
    if (reason === "other" && !String(note || "").trim()) {
      return "Add a brief job-related note when you choose Other.";
    }
    return "";
  }

  function reasonLabel(reason) {
    return reasonLabels[reason] || "";
  }

  function recordDecision(currentEntry, decision, reason, note, recordedAt, linkedRequirementIds) {
    const entry = Object.assign({}, currentEntry || {});
    const requirementIds = normalizeRequirementIds(linkedRequirementIds);
    const validationError = validateDecision(decision, reason, note, requirementIds);
    if (validationError) {
      entry.decision = "undecided";
      entry.decisionReason = "";
      entry.decisionRequirementIds = [];
      entry.decisionUpdatedAt = null;
      return Object.freeze({ ok: false, error: validationError, entry: entry });
    }
    entry.decision = decision;
    entry.decisionReason = requiresReason(decision) ? reason : "";
    entry.decisionRequirementIds = requiresReason(decision) ? requirementIds : [];
    entry.decisionNote = String(note || "").trim();
    entry.decisionUpdatedAt = decision === "undecided" ? null : (recordedAt || null);
    return Object.freeze({ ok: true, error: "", entry: entry });
  }

  return Object.freeze({
    reasonLabels,
    requiresReason,
    normalizeRequirementIds,
    selectLinkedRequirements,
    validateDecision,
    reasonLabel,
    recordDecision,
  });
});
