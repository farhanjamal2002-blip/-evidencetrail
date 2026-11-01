const assert = require("node:assert/strict");
const test = require("node:test");
const coverage = require("../static/requirement-coverage.js");

test("matching requirement lists do not create a batch warning", () => {
  assert.deepEqual(coverage.compare([["req-1", "req-2"], ["req-1", "req-2"]]), {
    consistent: true,
    candidateCount: 2,
    requirementCount: 2,
    missingAssignments: 0,
    candidatesWithGaps: 0,
  });
});

test("different requirement lists count missing rows without treating them as unsupported", () => {
  assert.deepEqual(coverage.compare([["req-1", "req-2"], ["req-1", "req-3"]]), {
    consistent: false,
    candidateCount: 2,
    requirementCount: 3,
    missingAssignments: 2,
    candidatesWithGaps: 2,
  });
});
