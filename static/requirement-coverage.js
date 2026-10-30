(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.EvidenceTrailRequirementCoverage = api;
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";

  function compare(requirementKeysByCandidate) {
    const candidateSets = (Array.isArray(requirementKeysByCandidate) ? requirementKeysByCandidate : [])
      .map(function (keys) { return new Set(Array.isArray(keys) ? keys.filter(Boolean) : []); });
    const union = new Set();
    candidateSets.forEach(function (keys) { keys.forEach(function (key) { union.add(key); }); });
    let missingAssignments = 0;
    let candidatesWithGaps = 0;
    candidateSets.forEach(function (keys) {
      const missing = union.size - keys.size;
      missingAssignments += missing;
      if (missing > 0) candidatesWithGaps += 1;
    });
    return Object.freeze({
      consistent: candidateSets.length < 2 || missingAssignments === 0,
      candidateCount: candidateSets.length,
      requirementCount: union.size,
      missingAssignments: missingAssignments,
      candidatesWithGaps: candidatesWithGaps,
    });
  }

  return Object.freeze({ compare: compare });
});
