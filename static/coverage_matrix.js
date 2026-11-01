/* EvidenceTrail criterion-level coverage. Zero Muse requests; no candidate scoring.
 * All states describe the supplied CV DOCUMENT, not the person's ability.
 * CommonJS export enables deterministic Node tests without a browser.
 */
(function(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.EvidenceCoverage = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function() {
  "use strict";
  const GROUPS = Object.freeze({
    complete: {label:"All criteria directly documented", detail:"Every approved requirement has direct PDF evidence. Not proof the claims are true."},
    partial: {label:"Partial evidence / scope questions", detail:"Some relevant CV evidence exists, but one or more exact requirements remain unproven."},
    attention: {label:"Evidence gaps / discrepancies", detail:"Little directly documented evidence or a discrepancy requiring recruiter clarification. Never auto-reject."},
    pending: {label:"Awaiting analysis", detail:"No verified evidence yet; never assume an unprocessed CV lacks qualifications."},
    failed: {label:"Analysis needs attention", detail:"Processing failed; the applicant is still visible and can be reviewed manually."}
  });
  const ORDER = Object.freeze(["complete","partial","attention","pending","failed"]);

  function signal(q) {
    if (!q || typeof q !== "object") return "missing";
    if (q.status === "conflicting") return "discrepancy";
    if (q.status === "supported" && q.evidence_type === "direct") return "direct";
    if (
      q.evidence_type === "related" ||
      q.review_reason_code === "explicit_scope_limit_not_contradiction" ||
      q.review_reason_code === "document_absence_not_contradiction"
    ) return "related";
    return "missing";
  }
  function coverage(result, expected) {
    if (!result || !Array.isArray(result.requirements)) return null;
    // A partial payload is never allowed to masquerade as complete coverage.
    const count = Number.isInteger(expected) && expected > 0 ? expected : result.requirements.length;
    if (count < 1) return null;
    const signals = Array.from({length:count}, (_,i) => signal(result.requirements[i]));
    const counts = {
      direct: signals.filter(x => x === "direct").length,
      related: signals.filter(x => x === "related").length,
      missing: signals.filter(x => x === "missing").length,
      discrepancy: signals.filter(x => x === "discrepancy").length
    };
    let group;
    if (result.requirements.length === count && counts.direct === count) group = "complete";
    else if (counts.discrepancy > 0 || (counts.direct === 0 && counts.related === 0)) group = "attention";
    else group = "partial";
    return {group, count, signals, counts};
  }
  function groupFor(row, result, expected) {
    const evidence = coverage(result,expected);
    if (evidence) return evidence.group;
    return row && row.state === "failed" ? "failed" : "pending";
  }
  function sortStable(rows, results, expected) {
    return rows.map((row,position) => ({
      row, position, group: groupFor(row,results.get(row.id),expected)
    })).sort((a,b)=>ORDER.indexOf(a.group)-ORDER.indexOf(b.group)||a.position-b.position);
  }
  return {GROUPS, ORDER, signal, coverage, groupFor, sortStable};
});
