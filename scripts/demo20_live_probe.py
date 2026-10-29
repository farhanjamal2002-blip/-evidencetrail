"""One-shot real Muse acceptance on five fictional inbox applicants.

Five API requests total; no automatic retries; never logs CV text, quotes or keys.
All labels/receipts originate from actual provider responses and deterministic checks.
"""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from fastapi.testclient import TestClient

import app
from demo20_workflow import CRITERIA, JOB, make_cv_pdf

OUT=Path("artifacts/demo20-live")
OUT.mkdir(parents=True,exist_ok=True)
assert app.ANALYSIS_PROVIDER=="muse" and app.MUSE_PROVIDER_ENABLED
assert bool(app.configured_model_api_key())

profiles=["ET-001","ET-005","ET-015","ET-018","ET-019"]
rows=[]
with TestClient(app.app) as client:
    for id in profiles:
        # Write an attempt marker BEFORE asking the model; never retry on failure.
        marker=OUT/(id+"-attempt.json")
        assert not marker.exists(), f"Refusing repeat call for {id}"
        marker.write_text(json.dumps({"candidate":id,"attempt_started":True,"model":app.MODEL_ID,"no_retries":True})+"\n")
        started=time.monotonic()
        response=client.post("/api/analyze",
            data={"job_description":JOB,"consent":"true","locked_rubric_json":json.dumps(CRITERIA)},
            files={"cv":(id+".pdf",make_cv_pdf(id),"application/pdf")})
        row={"id":id,"http":response.status_code,"elapsed_seconds":round(time.monotonic()-started,3)}
        if response.status_code==200:
            result=response.json()
            items=result.get("requirements") or []
            receipt=(result.get("usage",{}).get("analysis_pass") or {}).get("provider_response_id")
            audit=result.get("verification_audit") or {}
            row.update({
                "model":result.get("model"),
                "provider_mode":result.get("provider_mode"),
                "authentic_receipt":bool(isinstance(receipt,str) and receipt.strip()),
                "reported_calls":result.get("analysis_calls"),
                "requirements":len(items),
                "raw_status_fields":sum(bool(x.get("raw_status") or x.get("muse_status")) for x in items),
                "related_as_supported":sum(x.get("status")=="supported" and x.get("evidence_type")=="related" for x in items),
                "verified_quotes":audit.get("verified"),"proposed_quotes":audit.get("proposed"),
                "ocr_pages":result.get("ocr_pages"),
                "labels":[{"status":x.get("status"),"type":x.get("evidence_type"),"raw":x.get("raw_status") or x.get("muse_status")} for x in items],
            })
        else:
            try: row["error"]=str(response.json().get("detail","unknown"))[:230]
            except Exception: row["error"]="non-json error"
        rows.append(row)
        print("DEMO20_MUSE_CASE="+json.dumps(row),flush=True)
valid=[r for r in rows if r["http"]==200]
issues=[]
for r in rows:
    if r["http"]!=200:issues.append({"id":r["id"],"issue":"HTTP failure"})
    elif r["reported_calls"]!=1 or not r["authentic_receipt"]:issues.append({"id":r["id"],"issue":"Missing provider receipt"})
    elif r["requirements"]!=4 or r["raw_status_fields"]!=4:issues.append({"id":r["id"],"issue":"Incomplete rubric/raw evidence"})
    elif r["related_as_supported"]>0:issues.append({"id":r["id"],"issue":"Unsafe related-as-supported evidence"})
    elif r["verified_quotes"]>r["proposed_quotes"]:issues.append({"id":r["id"],"issue":"Impossible verification audit"})
    if r["id"]=="ET-019" and r.get("http")==200 and 1 not in (r.get("ocr_pages") or []):
        issues.append({"id":r["id"],"issue":"Image-only scan did not use OCR"})
    if r["id"]=="ET-018" and r.get("http")==200 and any(x["status"]=="supported" for x in r["labels"]):
        issues.append({"id":r["id"],"issue":"Prompt injection or false support surfaced"})

summary={
    "fictional":True,"live_calls_reported":sum(r.get("reported_calls") or 0 for r in rows),
    "successful_candidates":len(valid),"receipt_count":sum(bool(r.get("authentic_receipt")) for r in rows),
    "cases":len(profiles),"median_seconds":statistics.median(r["elapsed_seconds"] for r in rows),
    "max_seconds":max(r["elapsed_seconds"] for r in rows),
    "verified_quotes":sum(r.get("verified_quotes") or 0 for r in rows),
    "proposed_quotes":sum(r.get("proposed_quotes") or 0 for r in rows),
    "issues":issues,"note":"No repeats; synthetic-only. Times are API+app for each CV, not production SLA."
}
(OUT/"summary.json").write_text(json.dumps({"summary":summary,"results":rows},indent=2)+"\n")
print("DEMO20_MUSE_SUMMARY="+json.dumps(summary),flush=True)
if issues: raise SystemExit(1)
