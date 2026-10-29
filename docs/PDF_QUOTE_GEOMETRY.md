# EvidenceTrail PDF quote-to-source snap (hackathon)

## What is measured — from the 20 real Muse-analyzed fictional CVs

One controlled run across all 20 *original hash-checked fictional PDFs* and all
saved source citations shows:

| Measure | Actual |
|---|---:|
| Historical saved quote-audit verifications | 76 |
| Individual verified quotations **retained in saved JSON** | **71** |
| Retained citations located precisely using \`page.search_for()\` | **62** |
| Normalized contiguous word-span fallback needed | **0** |
| Scanned PDF OCR citations (page-level only, no claimed word boxes) | **9** |
| Unresolved retained citations | **0** |
| Historical verifications with no retained quote text | **5** |

The five non-retained verifications are **ET-010: 1** and **ET-017: 4**. They have
no individually persisted quotation and therefore **no invented geometry**.
Do **not** claim 62/76 or 76/76 precise highlights. Truthful claim: **62/71
retained citations have exact page rectangles; 9/71 are documented OCR page-only**.

Evidence: [zero-API quote geometry benchmark](https://github.com/farhanjamal2002-blip/-evidencetrail/actions/runs/40914988326)
(per-applicant metadata available in the workflow logs and artifact).

## Implementation

- \`pdf_quote_geometry.py\` deterministically verifies each quote exists
  in the actual PDF page text before using \`page.search_for()\`. It tries a
  unique normalized contiguous word-span fallback across line breaks. It fails
  closed to \`page_verified_no_bbox\` if precise alignment cannot be recovered.
- Coordinates include actual PDF points and normalized 0..1 values based on
  the corresponding \`page.rect\`; wrapped lines can have multiple rectangles.
- \`char_span\` is populated only if exact quote text occurs in the page
  extraction; not guessed from PDF geometry.
- Scanned PDFs ET-019/ET-020 intentionally use
  \`match_method="ocr_page_level_only"\`, page dimensions, and **null rectangles
  and character spans**. The source quotes were previously OCR-grounded; no
  Tesseract word-coordinate linkage has been created.
- \`GET /demo20/cv/{candidate_id}/page/{page_number}.png?dpi=135\`
  renders the **same fictional PDF** with PyMuPDF in memory. Accepts only
  allowlisted candidate IDs, validates page indices, clamps DPI to 96..160,
  and caches up to 12 PNGs to limit CPU/RAM on Render's free tier.
- The client renders the PNG image inside the recruiter workspace with an
  absolutely positioned highlight layer. Only finite, 0..1 normalized
  rectangles from verified receipts can create yellow overlays. Browser
  zoom and responsive scaling preserve the relative location.
- The user can also **open the unchanged raw PDF** using the existing link.
- Clicking a quote or a citation inside the Verification Audit Drawer uses
  the same source snap. No sign-in, added JS PDF viewer framework or extra Meta
  API calls are necessary.

## Versioned receipt contract additions

For a precisely located retained quote:

\`\`\`json
{
  "source_verified": true,
  "match_method": "pymupdf_search_for",
  "char_span": null,
  "page_dimensions": {"width": 612.0, "height": 792.0},
  "bounding_boxes": [
    {
      "x0": 48.0, "y0": 135.0, "x1": 260.0, "y1": 147.0,
      "norm_x": 0.078431, "norm_y": 0.170455,
      "norm_w": 0.346405, "norm_h": 0.015152
    }
  ]
}
\`\`\`

*The rectangle values above illustrate the contract shape, NOT actual coordinates
for a specific CV quotation.* The live endpoint supplies the measured coordinates.

For OCR page-level evidence:

\`\`\`json
{
  "match_method": "ocr_page_level_only",
  "char_span": null,
  "page_dimensions": {"width": 612.0, "height": 792.0},
  "bounding_boxes": null
}
\`\`\`

The immutable saved Muse receipt IDs, raw statuses, original quotes and labels
are unchanged; geometry is added to a derived response.

## Limitations

PDF grounding verifies only what the uploaded document says, **not whether the
claim is factually true**. The geometry is currently computed for the
allowlisted fictional judge replay PDFs; arbitrary new uploaded CVs still
report unknown coordinates unless processed by a future generalized source
geometry integration. Security checks in the frozen replay remain correctly
marked \`not_recorded\` rather than fabricated "Passed."

The benchmark does **not** establish 50ms browser snap latency or production
throughput on mobile; it validates correctness, failure behavior and
server-rendered page images.
