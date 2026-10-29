# EvidenceTrail Verification Receipt v1

**Purpose:** make the existing real Muse Spark 1.3 / EvidenceTrail verifier handoff inspectable **without any new model call**. This is an evidence audit, not a candidate score, truth-check, or compliance certification.

**Transport:**
- New \`POST /api/analyze\` results include \`verification_receipt\`.
- Saved, genuine fictional Muse replay \`GET /demo20/recorded-muse\` includes a \`verification_receipt\` on each item under \`results[]\`. This is derived from a deep copy of the immutable, hash-pinned model replay.
- The original \`requirements\`, \`raw_status\`, \`effective_status\`, \`receipt\`, \`quote_audit\` and source PDF remain available unmodified.

## Exact versioned shape

\`\`\`json
{
  "schema": "evidencetrail/verification-receipt/v1",
  "provider": {
    "mode": "muse",
    "model": "muse-spark-1.3",
    "response_id": "<original authentic provider ID>",
    "real_muse_response": true,
    "source": "saved_authentic_replay",
    "additional_model_calls_for_receipt": 0
  },
  "document": {
    "cv_sha256": "<actual PDF SHA-256>",
    "extraction_mode": "pdf_text_no_ocr_reported",
    "ocr_pages": [],
    "cited_pages": [1]
  },
  "quote_grounding": {
    "proposed": 4,
    "verified": 4,
    "excluded": 0,
    "citation_count": 4,
    "aggregate_source_audit_consistent": true,
    "method_detail": "not_recorded"
  },
  "semantic_overrides": {
    "raw_vs_verified_status_changes": 1,
    "unmodified_raw_labels": true
  },
  "input_guardrails": {
    "prompt_injection_scan": {"status": "not_recorded"},
    "hidden_text_scan": {"status": "not_recorded"},
    "input_sanitization_check": {"status": "not_recorded"}
  },
  "timeline": {
    "status": "not_recorded",
    "audit": null
  },
  "requirements": [
    {
      "requirement_index": 3,
      "requirement": "Hands-on SAP MM purchase orders and vendor record workflows.",
      "raw_muse_status": "conflicting",
      "verified_status": "not_found",
      "review_label": "Scope not established",
      "override_applied": true,
      "override_reason_code": "explicit_scope_limit_not_contradiction",
      "verification_explanation": "The cited statement limits the documented role or task; no incompatible second CV claim was verified.",
      "quote_citations": [
        {
          "page": 1,
          "source_id": "R3-Q1",
          "quote": "Used a warehouse management system, not SAP procurement.",
          "source_verified": true,
          "match_method": null,
          "char_span": null,
          "bounding_boxes": null
        }
      ],
      "timeline_review_flags": []
    }
  ],
  "disclaimer": "PDF grounding confirms the supplied document passage, not real-world truth or a candidate hiring decision. Unknown checks are not passed checks."
}
\`\`\`

**Example scope:** the excerpted requirement is ET-008/R3 from the real saved fictional Muse replay; other numeric fields illustrate the schema at the single-requirement level. A complete result has one entry per criterion. Never present an illustrative receipt ID or model reasoning as an actual provider message.

## Semantics and limitations

- **Source grounding** refers to the existing aggregate quote-verification audit and recorded pages. It is **not** a fresh byte-for-byte recheck at render time. The \`source_verified\` field is true only if the stored aggregate audit is consistent and accounts for the surviving citations. It is null when that consistency check cannot substantiate the claim.
- **Override count** is precisely the count of requirement \`raw_status != effective_status\`, not a generic "safety catches" count. In the 20-fictional-CV saved dataset there are **41 total status changes**: 33 new one-sided scope clarifications plus 8 pre-existing downstream verification changes. Do not relabel all 41 as contradictions or injection attacks.
- **OCR** is reported from the actual server \`ocr_pages\` list. \`pdf_text_no_ocr_reported\` means OCR pages were not recorded; it does not establish that every page has a complete searchable text layer.
- **Prompt injection, hidden text, input sanitation**: the historical replay does not include a per-document authoritative pass/fail signal. These are deliberately \`not_recorded\` even for synthetic adversarial fixture ET-018. The presence of that CV does not demonstrate a specific scanner triggered.
- **Model reasoning**: not present in the recorded payload as a separately attributable field. Show original Muse status, not fabricated chain-of-thought or an unverified "Muse explanation."
- **Geometry and offsets**: \`match_method\`, \`char_span\`, and \`bounding_boxes\` remain null until instrumented with actual source coordinate spans. Browser links open the cited PDF page today; a bounding-box snap is a *future feature*.
- **Timelines**: new live results may include a structured \`timeline_audit\`; the frozen replay omits that field, so the receipt is \`not_recorded\` for the saved 20.
- **No extra provider work**: receipt derivation is deterministic Python from the recorded/local analysis payload; 0 new Meta calls, and the UI inspector only reads the current result.

## Acceptance

Run \`python -m unittest tests.test_verification_receipt -v\`. The desktop/mobile Chromium smoke test opens the audit with its button and **A** key, checks ET-008's real raw-vs-final delta, ET-019 OCR, and honest unknown flags on ET-018. The full \`verification-receipt-acceptance.yml\` workflow runs the existing source, semantic, JS, PDF, Docker, and browser gates.

**Fictional demonstration only.** Review actions remain human-controlled and local to the browser.
