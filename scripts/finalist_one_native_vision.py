"""ONE genuine Meta Muse image + OCR CV request (fictional; no retries).

This is the first native image-input provider validation. The user explicitly
consents in this test to sending a fictional scanned CV page to Meta. No real
personal data, no public paid endpoint, no retries. The OCR-only reference was
already recorded in a separate controlled test.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
import pymupdf as fitz
import app
from multimodal_intake import optional_meta_vision_parts
from scripts.finalist_omission_corpus import CASES, make_cv_pdf, manifest_hash

OUT=Path("artifacts/finalist-native-vision")
OUT.mkdir(parents=True,exist_ok=True)


def main():
    if app.ANALYSIS_PROVIDER!="muse" or not app.MUSE_PROVIDER_ENABLED:
        raise SystemExit("Wrong provider; no calls")
    if not app.configured_model_api_key() or not app.MUSE_VISION_ENABLED:
        raise SystemExit("Vision flag or model key missing; no calls")
    case=next(c for c in CASES if c.id=="U23")
    assert case.scanned and case.reference=="supported"
    pdf=make_cv_pdf(case)
    with fitz.open(stream=pdf,filetype="pdf") as document:
        assert len(document)==1 and not document[0].get_text().strip()
    parts=optional_meta_vision_parts(pdf,[1])
    assert [p["type"] for p in parts]==["text","image_url"]
    assert len(parts[1]["image_url"]["url"])<1_300_000
    attempt=OUT/"U23-one-native-vision.attempt"
    if attempt.exists():
        raise SystemExit("One-time probe already attempted; no duplicate request")
    attempt.write_text("Exactly one consented fictional Meta vision request; no retry.\n")

    started=time.monotonic()
    try:
        with TestClient(app.app) as client:
            resp=client.post("/api/analyze",data={
                "job_description":"FICTIONAL REQUIREMENT:\n- "+case.requirement,
                "locked_rubric_json":json.dumps([case.requirement]),
                "consent":"true",
                "visual_review":"true",
            },files={"cv":("U23-fictional-image-only.pdf",pdf,"application/pdf")})
        summary={
            "fictional_id":"U23",
            "reference":"supported",
            "input_kind":"one-page image-only PDF",
            "http":resp.status_code,
            "seconds":round(time.monotonic()-started,2),
            "attempts":1,
            "retries":0,
            "input_image_blocks_prepared":1,
            "predeclared_corpus_sha256":manifest_hash(),
        }
        if resp.status_code!=200:
            summary["error"]="Provider request failed; no retries"
        else:
            data=resp.json()
            row=(data.get("requirements") or [{}])[0]
            usage=(data.get("usage") or {}).get("analysis_pass") or {}
            receipt=usage.get("provider_response_id")
            doc=data.get("input_document") or {}
            summary.update({
                "provider_mode":data.get("provider_mode"),
                "model":data.get("model"),
                "authentic_receipt":isinstance(receipt,str) and bool(receipt),
                "provider_response_id":receipt,
                "model_calls":data.get("analysis_calls"),
                "vision_model_calls":doc.get("vision_model_calls"),
                "vision_pages_supplied":doc.get("vision_pages_supplied"),
                "vision_opt_in":doc.get("vision_opt_in"),
                "ocr_pages":data.get("ocr_pages"),
                "quote_audit":data.get("quote_audit"),
                "raw":row.get("raw_status"),
                "final":row.get("status"),
                "evidence_type":row.get("evidence_type"),
                "author_reference_matches":row.get("status")==case.reference,
                "usage":{k:usage.get(k) for k in (
                    "input_tokens","output_tokens","cached_input_tokens",
                    "reasoning_tokens","api_latency_ms","vision_pages_supplied"
                ) if k in usage},
            })
            if (summary["provider_mode"]!="muse" or summary["model_calls"]!=1
                or not summary["authentic_receipt"] or
                summary["vision_model_calls"]!=1 or
                summary["vision_pages_supplied"]!=1 or
                summary["ocr_pages"]!=[1]):
                summary["error"]="Genuine image-input or OCR receipt incomplete"
        (OUT/"report.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
        public={k:v for k,v in summary.items() if k!="provider_response_id"}
        print("GENUINE_VISION_REPORT="+json.dumps(public),flush=True)
        if summary.get("error"):
            raise SystemExit(1)
    except Exception as exc:
        if not (OUT/"report.json").exists():
            (OUT/"report.json").write_text(json.dumps({
                "fictional_id":"U23","attempts":1,"retries":0,
                "error_type":type(exc).__name__,"no_success_claim":True
            },indent=2)+"\n")
        raise


if __name__=="__main__":
    main()
