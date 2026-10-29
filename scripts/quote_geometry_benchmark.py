"""Measure deterministic quote geometry on the 20 frozen fictional PDFs.
No Meta key, no calls, and never change the original replay.
"""
import json,collections
from pathlib import Path
from demo20_workflow import _load_verified_recording,make_cv_pdf
from pdf_quote_geometry import locate_quote_geometry
import fitz

original=_load_verified_recording()
stats=collections.Counter()
details=[]
for candidate in original["results"]:
    cid=candidate["id"];notes=[]
    with fitz.open(stream=make_cv_pdf(cid),filetype="pdf") as doc:
        for req_i,finding in enumerate(candidate["requirements"],1):
            for ci,citation in enumerate(finding.get("evidence") or [],1):
                page_no=citation.get("page")
                if not isinstance(page_no,int) or not 1<=page_no<=len(doc):
                    status="invalid_page";geom={"bounding_boxes":None,"char_span":None}
                else:
                    geom=locate_quote_geometry(doc[page_no-1],citation.get("quote",""),
                      is_ocr_page=page_no in (candidate.get("ocr_pages") or []))
                    status=geom["match_method"]
                stats[status]+=1
                notes.append({"requirement":req_i,"citation":ci,
                              "page":page_no,"method":status,
                              "bbox_count":len(geom.get("bounding_boxes") or []),
                              "has_char_span":geom.get("char_span") is not None})
    details.append({"id":cid,"counts":dict(collections.Counter(x["method"] for x in notes)),
                    "quotes":notes})
total=sum(stats.values())
resolved=stats["pymupdf_search_for"]+stats["normalized_word_span"]
qverified=sum(int(x.get("quote_audit",{}).get("verified") or 0) for x in original["results"])
summary={
 "verified_quotes_recorded":qverified,"source_citations_in_replay":total,
 "historical_verified_quotes_without_retained_citation":qverified-total,
 "exact_search_for":stats["pymupdf_search_for"],
 "normalized_word_span":stats["normalized_word_span"],
 "precisely_located":resolved,
 "ocr_page_level_only":stats["ocr_page_level_only"],
 "page_verified_no_bbox":stats["page_verified_no_bbox"],
 "invalid_page":stats["invalid_page"],
 "unlocated":stats["unlocated"],
 "disclosure":"20 strictly fictional source PDFs; no Muse requests; geometry located deterministically; exact char spans counted separately"
}
output=Path("artifacts/quote-geometry")
output.mkdir(parents=True,exist_ok=True)
(output/"benchmark.json").write_text(json.dumps({"summary":summary,"cases":details},indent=2)+"\n")
print("PDF_GEOMETRY_SUMMARY="+json.dumps(summary),flush=True)
for candidate in details:
    print("PDF_GEOMETRY_CASE="+json.dumps({"id":candidate["id"],"counts":candidate["counts"]}),flush=True)
assert 0<=total<=qverified, "Retained citations cannot outnumber verified historical quotations."
assert stats["invalid_page"]==0
assert resolved+stats["ocr_page_level_only"]+stats["page_verified_no_bbox"]+stats["unlocated"]==total
