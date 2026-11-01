const assert = require("node:assert/strict");
const test = require("node:test");
const decision = require("../static/recruiter-decision.js");

test("Advance does not require a decline or hold reason", () => {
  assert.equal(decision.validateDecision("advance", "", ""), "");
  assert.equal(decision.validateDecision("undecided", "", ""), "");
});

test("Hold and Do not advance require a job-related reason", () => {
  assert.match(decision.validateDecision("hold", "", ""), /Choose a job-related reason/);
  assert.match(decision.validateDecision("do_not_advance", "", ""), /Choose a job-related reason/);
  assert.match(
    decision.validateDecision("hold", "scope_needs_clarification", "", []),
    /Link this decision to at least one job requirement/
  );
  assert.equal(decision.validateDecision(
    "hold", "scope_needs_clarification", "", ["R2"]
  ), "");
});

test("Other requires a short note and exports a readable reason label", () => {
  assert.match(decision.validateDecision(
    "do_not_advance", "other", "  ", ["R1"]
  ), /Add a brief job-related note/);
  assert.equal(decision.validateDecision(
    "do_not_advance", "other", "Credential is not documented", ["R1"]
  ), "");
  assert.equal(decision.reasonLabel("credential_not_documented"), "Required credential is not documented");
});

test("an incomplete new decision clears the prior decision instead of exporting a stale one", () => {
  const transition = decision.recordDecision(
    { decision: "advance", decisionReason: "", decisionUpdatedAt: "old timestamp" },
    "hold",
    "",
    "",
    "new timestamp",
    []
  );

  assert.equal(transition.ok, false);
  assert.equal(transition.entry.decision, "undecided");
  assert.equal(transition.entry.decisionReason, "");
  assert.deepEqual(transition.entry.decisionRequirementIds, []);
  assert.equal(transition.entry.decisionUpdatedAt, null);
});

test("a valid decision records its reason, linked criteria, and timestamp", () => {
  const transition = decision.recordDecision(
    {}, "do_not_advance", "credential_not_documented", "", "2026-10-28T12:00:00Z",
    ["R1", "R1", " R3 "]
  );

  assert.equal(transition.ok, true);
  assert.equal(transition.entry.decision, "do_not_advance");
  assert.equal(transition.entry.decisionReason, "credential_not_documented");
  assert.deepEqual(transition.entry.decisionRequirementIds, ["R1", "R3"]);
  assert.equal(transition.entry.decisionUpdatedAt, "2026-10-28T12:00:00Z");
});

test("Advance clears decision links and does not require a criterion", () => {
  const transition = decision.recordDecision(
    { decisionRequirementIds: ["R1"] }, "advance", "", "", "timestamp", ["R2"]
  );
  assert.equal(transition.ok, true);
  assert.deepEqual(transition.entry.decisionRequirementIds, []);
});

test("decision exports resolve only the selected criteria", () => {
  const requirements = [
    { id: "R1", requirement: "Five years procurement" },
    { id: "R2", requirement: "Current certification" },
  ];
  const linked = decision.selectLinkedRequirements(requirements, ["R2", "R9"]);
  assert.deepEqual(linked, [requirements[1]]);
});
