/* Recruiter workflow logic; local-only, human-operated and evidence-first. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.EvidenceWorkflow = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const OPEN = new Set(["not_found", "conflicting", "related"]);
  const TASK_STATUSES = new Set(["draft", "waiting_external", "resolved"]);
  const DECISIONS = new Set(["Advance", "Hold", "Do not advance"]);

  function unresolvedFindings(result) {
    if (!result || !Array.isArray(result.requirements)) return [];
    return result.requirements.map((finding, index) => ({ finding, index }))
      .filter(({ finding }) => finding && (
        OPEN.has(String(finding.status)) ||
        finding.evidence_type === "related" ||
        finding.evidence_type === "unsupported" ||
        finding.certainty === "ambiguous"
      ));
  }

  function clarificationFor(result, preferredIndex) {
    const unresolved = unresolvedFindings(result);
    const selection = unresolved.find(item => item.index === preferredIndex) || unresolved[0];
    if (!selection) return null;
    const { finding, index } = selection;
    const criterion = String(finding.requirement || "").trim().slice(0, 600);
    if (!criterion) return null;
    const question = typeof finding.follow_up_question === "string" &&
      finding.follow_up_question.trim()
      ? finding.follow_up_question.trim().slice(0, 600)
      : "Can you describe your personal responsibilities relevant to this job requirement, including examples, dates and your level of authority? " +
        "Requirement: " + criterion;
    return {
      requirement_id: String(finding.id || "R" + (index + 1)),
      requirement_index: index,
      requirement: criterion,
      question,
      evidence_status: String(finding.status || "not_found"),
      source_verified: (finding.evidence || []).some(c => c && c.page >= 1 && c.quote),
    };
  }

  function createFollowUp(candidateId, result, preferredIndex, timestamp) {
    const c = clarificationFor(result, preferredIndex);
    if (!c) return null;
    return {
      candidate_id: String(candidateId),
      requirement_id: c.requirement_id,
      requirement_index: c.requirement_index,
      requirement: c.requirement,
      question: c.question,
      status: "draft",
      created_at: timestamp || null,
      updated_at: timestamp || null,
      comment: "",
      candidate_reply: "",
      candidate_reply_received_at: null,
      reply_source: null,
      reply_evidence_status: null,
      manually_marked_sent: false,
      // A follow-up does not alter evidence or automatically change a decision.
      evidence_status_at_creation: c.evidence_status,
    };
  }

  function updateFollowUp(task, updates, timestamp) {
    if (!task || typeof task !== "object") throw Error("An existing follow-up is required");
    const nextStatus = updates.status === undefined ? task.status : updates.status;
    if (!TASK_STATUSES.has(nextStatus)) throw Error("Invalid follow-up status");
    const question = updates.question === undefined ? task.question : String(updates.question).trim();
    if (!question || question.length > 1200) throw Error("A concise clarification question is required");
    const comment = updates.comment === undefined ? task.comment : String(updates.comment).trim();
    if (comment.length > 1000) throw Error("Keep notes under 1000 characters");
    const reply = updates.candidate_reply === undefined
      ? String(task.candidate_reply || "") : String(updates.candidate_reply).trim();
    if (reply.length > 2400) throw Error("Keep the candidate reply under 2400 characters");
    if (nextStatus === "resolved" && !reply.trim())
      throw Error("Record the candidate's actual reply before marking this follow-up resolved");
    const replyChanged = reply !== String(task.candidate_reply || "");
    const receivedAt = reply.trim()
      ? (replyChanged ? (timestamp || null) : task.candidate_reply_received_at || timestamp || null)
      : null;
    return {
      ...task,
      question, comment, status: nextStatus,
      candidate_reply: reply,
      candidate_reply_received_at: receivedAt,
      reply_source: reply.trim() ? "recruiter_pasted_external_candidate_message" : null,
      reply_evidence_status: reply.trim() ? "candidate_self_attested_unverified" : null,
      manually_marked_sent: nextStatus === "waiting_external" ? true :
        nextStatus === "draft" ? false : Boolean(task.manually_marked_sent),
      updated_at: timestamp || task.updated_at,
    };
  }

  function reviewStage(candidateId, result, decision, followup) {
    if (decision && DECISIONS.has(decision.action)) return "human_decided";
    if (!result) return "awaiting_evidence";
    if (followup && followup.status === "waiting_external") return "waiting_external";
    if (followup && followup.status === "resolved") return "clarification_received";
    if (followup && followup.status === "draft") return "follow_up_draft";
    if (unresolvedFindings(result).length) return "needs_clarification";
    return "ready_for_human_review";
  }

  function reviewSummary(items, results, decisions, followups) {
    const counts = { awaiting_evidence: 0, ready_for_human_review: 0,
      needs_clarification: 0, follow_up_draft: 0, waiting_external: 0,
      clarification_received: 0, human_decided: 0 };
    for (const item of items || []) {
      const id = item.id;
      const stage = reviewStage(id, results.get(id), decisions.get(id), followups.get(id));
      counts[stage] += 1;
    }
    return counts;
  }

  function messageFor(task, roleTitle) {
    if (!task || !String(task.question || "").trim()) throw Error("No question to send");
    const title = String(roleTitle || "the role").trim().slice(0, 180);
    // No identities or email destinations are inferred.
    return "Subject: Clarification about your application — " + title +
      "\n\nHello,\n\nThank you for your interest in the " + title +
      " position. To ensure we understand your experience correctly, could you clarify the following?\n\n" +
      String(task.question).trim() +
      "\n\nPlease share only information that accurately reflects your own experience. " +
      "This request is for human review, not an automated hiring decision.\n\nThank you.";
  }

  function messageForSelectedQuestions(questions, roleTitle) {
    if (!Array.isArray(questions) || !questions.length)
      throw Error("Select at least one unresolved requirement");
    if (questions.length > 20) throw Error("Too many clarification questions");
    const title = String(roleTitle || "the role").trim().slice(0, 180);
    const seen = new Set();
    const numbered = [];
    for (const q of questions) {
      const index = Number(q?.requirement_index);
      const question = String(q?.question || "").trim().slice(0, 1000);
      if (!question || !Number.isSafeInteger(index) || index < 0 || seen.has(index)) continue;
      seen.add(index);
      numbered.push(numbered.length + 1 + ". " + question);
    }
    if (!numbered.length) throw Error("No usable selected questions");
    return "Subject: Clarifications about your application — " + title
      + "\\n\\nHello,\\n\\nThank you for your application. Rather than assume a missing "
      + "CV detail means missing experience, could you clarify the following?\\n\\n"
      + numbered.join("\\n\\n")
      + "\\n\\nYou may provide brief examples and dates. Your response will be read "
      + "by a recruiter; it is not an automatic hiring decision.\\n\\nThank you.";
  }

  function safeCsvValue(value) {
    let text = String(value == null ? "" : value).replace(/[\r\n]+/g, " ");
    // Stop Excel/Sheets interpreting user-controlled CV data as formulas.
    if (/^[\s]*[=+@\-]/.test(text)) text = "'" + text;
    return '"' + text.replace(/"/g, '""') + '"';
  }

  function exportWorkflowCsv(items, results, decisions, followups) {
    const columns = ["candidate_id", "evidence_state", "review_stage", "human_decision",
      "reviewed_at", "follow_up_requirement", "follow_up_status", "follow_up_question",
      "follow_up_updated_at", "candidate_reply", "reply_received_at",
      "reply_evidence_status", "saved_muse_recording"];
    const lines = [columns.map(safeCsvValue).join(",")];
    for (const item of items || []) {
      const id = item.id, result = results.get(id), decision = decisions.get(id),
        task = followups.get(id);
      const values = [
        id, result ? "source_review_available" : "not_analyzed",
        reviewStage(id, result, decision, task), decision?.action || "",
        decision?.reviewed_at || "", task?.requirement_id || "",
        task?.status || "", task?.question || "", task?.updated_at || "",
        task?.candidate_reply || "", task?.candidate_reply_received_at || "",
        task?.reply_evidence_status || "",
        result?.saved_replay === true ? "recorded_muse" : "not_recorded",
      ];
      lines.push(values.map(safeCsvValue).join(","));
    }
    return lines.join("\r\n") + "\r\n";
  }

  function buildInterviewKit(candidateId, jobTitle, result) {
    if (!result || !Array.isArray(result.requirements)) return null;
    const questions = result.requirements.map((finding, index) => {
      const unresolved = unresolvedFindings({requirements:[finding]}).length > 0;
      const requirement = String(finding.requirement || "").slice(0,600);
      const existing = (finding.evidence || []).filter(c => c && 
        Number.isInteger(c.page) && c.page >= 1 && String(c.quote || "").trim());
      return {
        requirement_id: String(finding.id || "R" + (index + 1)),
        requirement,
        evidence_status: String(finding.status || "not_found"),
        question: unresolved ?
          "Can you explain your responsibilities for this requirement, including your personal role and a concrete example? " + requirement :
          "Please walk through one concrete example of this experience, your exact contributions and the outcome. " + requirement,
        source_pages: Array.from(new Set(existing.map(c => c.page))).sort((a,b) => a-b),
        // Citation existence is not external truth or a candidate qualification.
        source_claims: existing.slice(0,3).map(c => String(c.quote).slice(0,500)),
      };
    });
    return {
      applicant_id: String(candidateId),
      role: String(jobTitle || "Recruiter-approved job"),
      generated_by: "EvidenceTrail deterministic interview checklist, no new AI requests",
      decision_policy: "Human interviewer asks and evaluates; no score or automatic selection",
      questions,
    };
  }

  function interviewKitText(kit) {
    if (!kit) throw Error("Verified evidence is required before creating an interview kit");
    const lines = ["EVIDENCETRAIL — HUMAN INTERVIEW PREP", "Applicant: " + kit.applicant_id,
      "Role: " + kit.role, kit.decision_policy, "", "RECRUITER-APPROVED CRITERIA"];
    for (const [index, item] of kit.questions.entries()) {
      lines.push("", (index + 1) + ". " + item.requirement,
        "CV documentation status: " + item.evidence_status,
        "Suggested question: " + item.question,
        "CV page references: " + (item.source_pages.join(", ") || "Not established"));
    }
    lines.push("", "Questions are drafts. Verify all applicant claims independently.");
    return lines.join("\\n") + "\\n";
  }

  return { unresolvedFindings, clarificationFor, createFollowUp, updateFollowUp,
    reviewStage, reviewSummary, messageFor, messageForSelectedQuestions,
    safeCsvValue, exportWorkflowCsv, buildInterviewKit, interviewKitText };
});
