"""High-concurrency synthetic FastAPI stress (mock only; no external provider)."""
import hashlib,json,time,statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pymupdf
from fastapi.testclient import TestClient
import app

OUT=Path("artifacts/concurrency")
OUT.mkdir(parents=True,exist_ok=True)
JD="Role: Python Engineer\nRequirements:\n1. Five years of Python backend development.\n2. Current AWS certificate."

def pdf(marker):
    doc=pymupdf.open()
    page=doc.new_page()
    page.insert_text((40,80),"FICTIONAL CV -- "+marker+"\nPython backend systems from 2017-2026.",fontsize=10)
    b=doc.tobytes()
    doc.close()
    return b

def call(c,index):
    if index<100:
        route="/health"
        t=time.perf_counter()
        response=c.get(route)
    elif index<160:
        route="/api/role-audit"
        t=time.perf_counter()
        response=c.post(route,data={"job_description":JD})
    elif index<190:
        route="/api/analyze"
        t=time.perf_counter()
        response=c.post(route,data={"job_description":JD},files={"cv":("test.pdf",pdf(str(index)),"application/pdf")})
    elif index<210:
        route="/api/analyze"
        t=time.perf_counter()
        response=c.post(route,data={"job_description":JD,"consent":"true"},files={"cv":("broken.pdf",b"not-a-pdf","application/pdf")})
    else:
        route="/api/analyze"
        content=pdf("unique-"+str(index))
        t=time.perf_counter()
        response=c.post(route,data={"job_description":JD,"consent":"true"},files={"cv":(str(index)+".pdf",content,"application/pdf")})
    d={"request":index,"route":route,"status":response.status_code,"elapsed_ms":round((time.perf_counter()-t)*1000,2)}
    expect=200 if index<160 else 400 if index<210 else None
    if index>=210:
        if response.status_code==200:
            obj=response.json()
            d["content_hash_correct"]=obj.get("cv_sha256")==hashlib.sha256(content).hexdigest()
            d["no_muse_calls"]=obj.get("analysis_calls")==0
            d["has_report"]=str(obj.get("report_html","")).startswith("<!doctype html")
            d["pass"]=d["content_hash_correct"] and d["no_muse_calls"] and d["has_report"]
        elif response.status_code==429:
            d["pass"]=True
            d["bounded"]=True
        else:
            d["pass"]=False
            try:d["detail"]=str(response.json().get("detail"))[:100]
            except:pass
    else:
        d["pass"]=response.status_code==expect
    return d

assert app.ANALYSIS_PROVIDER=="mock"
n=240
with TestClient(app.app) as client:
    started=time.perf_counter()
    with ThreadPoolExecutor(max_workers=24) as pool:
        results=list(pool.map(lambda i:call(client,i),range(n)))
elapsed=round(time.perf_counter()-started,3)
failed=[r for r in results if not r["pass"]]
statuses={}
for r in results:
    key=str(r["status"])
    statuses[key]=statuses.get(key,0)+1
latencies=sorted(r["elapsed_ms"] for r in results)
summary={"requests":n,"parallel_workers":24,"elapsed_seconds":elapsed,
 "passed":n-len(failed),"failed":len(failed),"http_status_counts":statuses,
 "p95_request_ms":latencies[min(n-1,int(n*0.95))],
 "p99_request_ms":latencies[min(n-1,int(n*0.99))],
 "failures":failed,"model_requests":0,"frozen_sha":"8140662cae1e14fbae7b66f664a7d9d99b396674",
 "interpretation":"In-process cloud synthetic TestClient stress, not production user RPS or real-world latency."}
(OUT/"concurrency-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print("CONCURRENCY_SUMMARY="+json.dumps(summary),flush=True)
if failed:raise SystemExit(1)
