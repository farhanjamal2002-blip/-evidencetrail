"""Four fictional PDFs processed over actual HTTP with two concurrent Meta calls.

Exactly four real calls, no retry, no real candidate PII. Independent receipt,
source hash and quote check per result. This is an acceptance probe, not a load test.
"""
import asyncio
import hashlib
import json
import statistics
import time
from pathlib import Path

import httpx
from demo20_workflow import CRITERIA, JOB, make_cv_pdf

URL = "http://127.0.0.1:8062/api/analyze"
IDS = ["ET-003", "ET-008", "ET-012", "ET-019"]
OUT = Path("artifacts/muse-live-concurrency")
OUT.mkdir(parents=True, exist_ok=True)
sem = asyncio.Semaphore(2)
results = []
started = time.monotonic()

async def analyze(client, cid):
    cv = make_cv_pdf(cid)
    marker = OUT / f"{cid}.attempt.json"
    assert not marker.exists(), f"Duplicate attempt prohibited for {cid}"
    marker.write_text(json.dumps({"id":cid,"once":True,"no_retry":True})+"\n")
    async with sem:
        began=time.monotonic()
        try:
            response = await client.post(
                URL,
                data={"job_description": JOB, "consent":"true", "locked_rubric_json":json.dumps(CRITERIA)},
                files={"cv":(cid+".pdf",cv,"application/pdf")},
            )
        except Exception as exc:
            return {"id":cid,"exception":type(exc).__name__,"error":"transport failure","seconds":round(time.monotonic()-began,3)}
    row={"id":cid,"http":response.status_code,"seconds":round(time.monotonic()-began,3)}
    if response.status_code!=200:
        try:row["error"]=str(response.json().get("detail","Unknown"))[:200]
        except ValueError:row["error"]="non-json HTTP error"
        return row
    p=response.json()
    receipt=(p.get("usage",{}).get("analysis_pass") or {}).get("provider_response_id")
    items=p.get("requirements") or []
    audit=p.get("quote_audit") or {}
    row.update({
        "provider":p.get("provider_mode"),"calls":p.get("analysis_calls"),"receipt_present":bool(receipt),
        "receipt":receipt if isinstance(receipt,str) else None,
        "cv_hash_correct":p.get("cv_sha256")==hashlib.sha256(cv).hexdigest(),
        "requirement_count":len(items),
        "raw_count":sum(bool(x.get("raw_status") or x.get("muse_status")) for x in items),
        "quote_proposed":audit.get("proposed",0),"quote_verified":audit.get("verified",0),
        "related_supported":sum(x.get("status")=="supported" and x.get("evidence_type")!="direct" for x in items),
        "ocr_pages":p.get("ocr_pages") or [],
    })
    return row

async def run():
    async with httpx.AsyncClient(timeout=95.0,limits=httpx.Limits(max_connections=2,max_keepalive_connections=2)) as client:
        return await asyncio.gather(*(analyze(client,cid) for cid in IDS))

results=asyncio.run(run())
issues=[]
for row in results:
    cid=row["id"]
    if row.get("http")!=200:
        issues.append({"id":cid,"reason":"HTTP or transport failure","code":row.get("http"),"type":row.get("exception")})
        continue
    if not row["receipt_present"] or row["provider"]!="muse" or row["calls"]!=1:
        issues.append({"id":cid,"reason":"not real single Muse response"})
    if not row["cv_hash_correct"] or row["requirement_count"]!=4 or row["raw_count"]!=4:
        issues.append({"id":cid,"reason":"cross-CV mixing, bad hash or incomplete rubric"})
    if row["quote_verified"]>row["quote_proposed"] or row["related_supported"]:
        issues.append({"id":cid,"reason":"source verification or semantic evidence invariant"})
    if cid=="ET-019" and 1 not in row["ocr_pages"]:
        issues.append({"id":cid,"reason":"OCR missing"})
summary={
    "real_meta_requests":sum(x.get("calls") or 0 for x in results),
    "concurrency":2,"cases":len(IDS),"successes":sum(x.get("http")==200 for x in results),
    "receipts":sum(bool(x.get("receipt_present")) for x in results),
    "pdf_sha256_matches":sum(bool(x.get("cv_hash_correct")) for x in results),
    "quotes_verified":sum(x.get("quote_verified") or 0 for x in results),
    "quotes_proposed":sum(x.get("quote_proposed") or 0 for x in results),
    "wall_seconds":round(time.monotonic()-started,3),
    "max_per_cv_seconds":max(x["seconds"] for x in results),
    "failures":issues,
    "disclosure":"Real HTTP on GitHub-hosted local uvicorn with actual Meta API; 4 fictional CVs, 2 concurrent requests, not a production throughput claim.",
}
(OUT/"report.json").write_text(json.dumps({"summary":summary,"cases":results},indent=2)+"\n")
print("LIVE_CONCURRENT_SUMMARY="+json.dumps(summary),flush=True)
for x in results:
    print("LIVE_CONCURRENT_CASE="+json.dumps({k:v for k,v in x.items() if k!="receipt"}),flush=True)
if issues:raise SystemExit(1)
