const assert = require("node:assert/strict");
const test = require("node:test");
const { buildDraft, verifiedDirectTopics } = require("../static/interview-invite.js");

const direct = (requirement, overrides = {}) => ({
  requirement,
  status: "supported",
  evidence_type: "direct",
  certainty: "clear",
  evidence_strength: "specific",
  evidence: [{ role: "supports", quote: "A locally verified passage.", page: 1 }],
  ...overrides,
});

test("invitation topics come only from clear, source-anchored direct evidence", () => {
  const topics = verifiedDirectTopics([
    direct("Supplier contract negotiations"),
    direct("Supplier contract negotiations"),
    direct("Related vendor coordination", { evidence_type: "related" }),
    direct("Ambiguous dates", { timeline_review_flags: ["concurrent_roles"] }),
    direct("Keyword mention only", { evidence_strength: "keyword_only" }),
    direct("Missing citation", { evidence: [] }),
    direct("Uncertain interpretation", { certainty: "ambiguous" }),
  ]);

  assert.deepEqual(topics, ["Supplier contract negotiations"]);
});

test("draft excludes quote text and leaves candidate, role, and recruiter editable", () => {
  const draft = buildDraft([direct("Multi-year GCC supplier agreements")]);

  assert.match(draft, /\[role\]/);
  assert.match(draft, /\[candidate name\]/);
  assert.match(draft, /\[recruiter name\]/);
  assert.match(draft, /Multi-year GCC supplier agreements/);
  assert.doesNotMatch(draft, /A locally verified passage/);
  assert.equal((draft.match(/\n• /g) || []).length, 1);
});

test("draft uses neutral wording when no direct evidence qualifies", () => {
  const draft = buildDraft([direct("A buzzword", { evidence_strength: "keyword_only" })]);

  assert.match(draft, /discuss the role with you/);
  assert.doesNotMatch(draft, /A buzzword/);
});

test("draft limits discussion points to three", () => {
  const draft = buildDraft([
    direct("Requirement one"),
    direct("Requirement two"),
    direct("Requirement three"),
    direct("Requirement four"),
  ]);

  assert.match(draft, /Requirement one/);
  assert.match(draft, /Requirement three/);
  assert.doesNotMatch(draft, /Requirement four/);
});
