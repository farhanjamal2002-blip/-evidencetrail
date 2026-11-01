(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.EvidenceTrailInterviewInvite = api;
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";

  function verifiedDirectTopics(findings) {
    const topics = [];
    const seen = new Set();
    (Array.isArray(findings) ? findings : []).forEach(function (finding) {
      if (!finding || finding.status !== "supported" || finding.evidence_type !== "direct") return;
      if (finding.certainty === "ambiguous") return;
      if (Array.isArray(finding.timeline_review_flags) && finding.timeline_review_flags.length) return;
      if (!["specific", "stated"].includes(finding.evidence_strength)) return;
      const hasVerifiedSupport = Array.isArray(finding.evidence) && finding.evidence.some(function (source) {
        return source && source.role === "supports" && typeof source.quote === "string" &&
          Number.isInteger(source.page) && source.page > 0;
      });
      if (!hasVerifiedSupport) return;
      const requirement = String(finding.requirement || "").trim();
      const key = requirement.toLocaleLowerCase().replace(/\s+/g, " ");
      if (!requirement || seen.has(key)) return;
      seen.add(key);
      topics.push(requirement);
    });
    return topics.slice(0, 3);
  }

  function buildDraft(findings) {
    const topics = verifiedDirectTopics(findings);
    const discussion = topics.length
      ? "We would like to learn more about your experience related to:\n" +
        topics.map(function (topic) { return "• " + topic; }).join("\n")
      : "We would like to learn more about your experience and discuss the role with you.";
    return [
      "Subject: Interview invitation — [role]",
      "",
      "Hello [candidate name],",
      "",
      "Thank you for your application. We would like to invite you to an interview.",
      "",
      discussion,
      "",
      "Please reply with a few times that work for you. We will confirm the meeting details separately.",
      "",
      "Kind regards,",
      "[recruiter name]",
    ].join("\n");
  }

  return { verifiedDirectTopics, buildDraft };
});
