"""Five predeclared fictional CVs through genuine Muse; exactly one attempt each.

No retries; no real applicants. This is intentionally a small synthetic semantic
probe, NOT representative accuracy or human-annotated evaluation. No candidate
rankings/rejections. Historical 20-CV replay remains unchanged.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
import app
from ownership_provenance import audit_verified_findings
from scripts.finalist_omission_corpus import CASES, make_cv_pdf, manifest_hash

IDS=("U02","U03","U05","U07","U23")
OUT=Path("artifacts/finalist-ownership-live")
OUT.mkdir(parents=True,exist_ok=True)

def main():
    if app.ANALYSIS_PROVIDER!="muse" or not app.MUSE_PROVIDER_ENABLED:
        raise SystemExit("Refusing genuine probe without explicit Muse provider enablement")
    if not app.configured_model_api_key():
        raise SystemExit("No configured key. No Muse calls attempted.")
    if os.getenv("EVIDENCETRAIL_ENABLE_META_VISION","false").lower()!="false":
        raise SystemExit("This probe is text plus local OCR only; vision must be disabled")
    corpus={x.id:x for x in CASES}
    if len(IDS)!=5 or len(set(IDS))!=5 or not all(i in corpus for i in IDS):
        raise SystemExit("Reference corpus mismatch; no Muse calls.")
    if any((OUT/(i+".attempt")).exists() for i in IDS):
        raise SystemExit("An attempt marker already exists; refusing duplicate paid calls")
    rows=[]
    for id_ in IDS:
        c=corpus[id_]
        original=make_cv_pdf(c)
        marker=OUT/(id_+".attempt")
        marker.write_text("Exactly one Meta request allowed for this synthetic CV.\n")
        start=time.monotonic()
        try:
            # TestClient is created per request, but the loaded application
            # rate limiter still applies across all five calls.
            with TestClient(app.app) as client:
                response=client.post("/api/analyze",data={
                    "job_description":"FICTIONAL REQUIREMENT:\n- "+c.requirement,
                    "locked_rubric_json":json.dumps([c.requirement]),
                    "consent":"true",
                    "visual_review":"false",
                },files={"cv":(id_+".pdf",original,"application/pdf")})
            item={
                "id":id_,"reference":c.reference,"trap":c.trap,
                "pdf_sha256":hashlib.sha256(original).hexdigest(),
                "response_http":response.status_code,
                "elapsed_seconds":round(time.monotonic()-start,2),
            }
            if response.status_code==200:
                data=response.json()
                f=data.get("requirements") or []
                item["provider"]=data.get("provider_mode")
                item["model"]=data.get("model")
                item["model_calls"]=data.get("analysis_calls")
                usage=((data.get("usage") or {}).get("analysis_pass") or {})
                item["provider_response_id"]=usage.get("provider_response_id")
                item["has_authentic_receipt"]=bool(
                    isinstance(item["provider_response_id"],str)
                    and item["provider_response_id"].strip()
                )
                item["usage"]={name:usage.get(name) for name in [
                    "input_tokens","output_tokens","cached_input_tokens",
                    "reasoning_tokens","api_latency_ms"
                ] if name in usage}
                item["quote_audit"]=data.get("quote_audit")
                item["ocr_pages"]=data.get("ocr_pages")
                item["results"]=[{
                    "reference":c.reference,
                    "raw":z.get("raw_status"),
                    "final":z.get("status"),
                    "evidence_type":z.get("evidence_type"),
                    "raw_matches_reference":z.get("raw_status")==c.reference,
                    "final_matches_reference":z.get("status")==c.reference,
                    "citation_count":len(z.get("evidence") or []),
                } for z in f]
                item["shadow_review_warnings"]=len(audit_verified_findings(f))
                if len(f)!=1:
                    item["error"]="Model did not return exactly one requirement"
                if item["provider"]!="muse" or item["model_calls"]!=1 or not item["has_authentic_receipt"]:
                    item["error"]="Genuine provider receipt or call count incomplete"
            else:
                item["error"]="HTTP failure; no retry"
            rows.append(item)
            # Do not leak response IDs or exact source text in Actions logs.
            print("OWNERSHIP_MUSE_CASE="+json.dumps({
                k:v for k,v in item.items() if k not in (
                    "provider_response_id","pdf_sha256"
                )
            }),flush=True)
        except Exception as exc:
            rows.append({"id":id_,"reference":c.reference,
                         "error":"Unrecoverable "+type(exc).__name__+" (no retry)"})
            print("OWNERSHIP_MUSE_CASE="+json.dumps({
                "id":id_,"error_type":type(exc).__name__
            }),flush=True)

    success=[r for r in rows if r.get("response_http")==200 and
             not r.get("error") and r.get("has_authentic_receipt")]
    final_false_support=sum(
        r["results"][0]["final"]=="supported" and r["reference"]!="supported"
        for r in success if r.get("results")
    )
    final_missed_support=sum(
        r["reference"]=="supported" and r["results"][0]["final"]!="supported"
        for r in success if r.get("results")
    )
    summary={
        "source":"genuine Meta Muse Spark provider, five synthetic fictional CVs",
        "reference_origin":"author-constructed before paid evaluation, not independently annotated",
        "corpus_sha256":manifest_hash(),
        "predeclared_ids":list(IDS),
        "attempts_max":5,
        "attempts_executed":len(rows),
        "successful_with_receipts":len(success),
        "false_supported":final_false_support,
        "missed_supported":final_missed_support,
        "raw_reference_matches":sum(
            r["results"][0]["raw_matches_reference"] for r in success if r.get("results")),
        "final_reference_matches":sum(
            r["results"][0]["final_matches_reference"] for r in success if r.get("results")),
        "no_retries":True,
        "new_live_vision_input":False,
        "no_changes_to_saved_20_cv_replay":True,
        "error_cases":[r["id"] for r in rows if r.get("error")],
        "limitations":[
            "These author-made 5 examples are not representative candidate accuracy",
            "Source quote presence is not independent truth or personal action proof",
            "This checks only OCR/text, not native image-input model improvements",
            "No auto-rejection, ranking or employment decision is performed"
        ],
    }
    (OUT/"report.json").write_text(
        json.dumps({"summary":summary,"cases":rows},indent=2,ensure_ascii=False)+"\n"
    )
    print("OWNERSHIP_MUSE_SUMMARY="+json.dumps(summary),flush=True)
    if len(success)!=len(IDS):
        raise SystemExit("Incomplete authentic Meta receipts; all attempts stopped, no retries")


if __name__=="__main__":
    main()
