"""Bounded real HTTP soak of a local uvicorn process, not public production."""
import asyncio,hashlib,json,os,statistics,time
from collections import Counter
from pathlib import Path
import httpx
import pymupdf

BASE=os.environ.get("SOAK_URL","http://127.0.0.1:8020").rstrip("/")
CONCURRENCY=24
TOTAL=1000
OUT=Path("artifacts/http-soak")
OUT.mkdir(parents=True,exist_ok=True)
doc=pymupdf.open()
p=doc.new_page()
p.insert_text((40,60),"FICTIONAL CV - steady-state HTTP soak",fontsize=11)
p.insert_text((40,80),"Production Python backend services and API development: 2017-2026.",fontsize=10)
pdf=doc.tobytes()
doc.close()
JD="Role: Python Engineer\nRequirements:\n1. Five years of production Python API experience."

def scenario(i):
    value=i%10
    if value in (0,1,2):
        return "health"
    if value in (3,4):
        return "role_audit"
    if value==5:
        return "replay"
    if value==6:
        return "consent_block"
    if value==7:
        return "invalid_pdf"
    return "valid_mock"

async def main():
    sem=asyncio.Semaphore(CONCURRENCY)
    records=[]
    async with httpx.AsyncClient(timeout=30.0,limits=httpx.Limits(max_connections=32,max_keepalive_connections=32)) as c:
        async def one(i):
            mode=scenario(i)
            async with sem:
                st=time.perf_counter()
                try:
                    if mode=="health":r=await c.get(BASE+"/health")
                    elif mode=="role_audit":r=await c.post(BASE+"/api/role-audit",data={"job_description":JD})
                    elif mode=="replay":r=await c.get(BASE+"/demo/unified-replay")
                    elif mode=="consent_block":r=await c.post(BASE+"/api/analyze",data={"job_description":JD},files={"cv":("fictional.pdf",pdf,"application/pdf")})
                    elif mode=="invalid_pdf":r=await c.post(BASE+"/api/analyze",data={"job_description":JD,"consent":"true"},files={"cv":("bad.pdf",b"not-a-pdf","application/pdf")})
                    else:r=await c.post(BASE+"/api/analyze",data={"job_description":JD,"consent":"true"},files={"cv":("fictional.pdf",pdf,"application/pdf")})
                    elapsed=round((time.perf_counter()-st)*1000,2)
                    allowed={"health":{200},"role_audit":{200},"replay":{200},"consent_block":{400},"invalid_pdf":{400,429},"valid_mock":{200,429}}[mode]
                    ok=r.status_code in allowed
                    if mode=="valid_mock" and r.status_code==200:
                        payload=r.json()
                        ok=ok and payload.get("analysis_calls")==0 and payload.get("cv_sha256")==hashlib.sha256(pdf).hexdigest()
                        ok=ok and all(
                            not (row.get("status")=="supported" and row.get("evidence_type")=="related")
                            for row in payload.get("requirements",[])
                        )
                    records.append({"i":i,"scenario":mode,"status":r.status_code,"ms":elapsed,"ok":ok,"bytes":len(r.content)})
                except Exception as e:
                    records.append({"i":i,"scenario":mode,"status":None,"ms":round((time.perf_counter()-st)*1000,2),"ok":False,"error":type(e).__name__})
        started=time.perf_counter()
        await asyncio.gather(*(one(i) for i in range(TOTAL)))
        elapsed=round(time.perf_counter()-started,3)
    by={}
    for mode in sorted(set(x["scenario"] for x in records)):
        rows=[x for x in records if x["scenario"]==mode]
        values=sorted(x["ms"] for x in rows)
        by[mode]={"requests":len(rows),"statuses":dict(Counter(str(x["status"]) for x in rows)),
                  "unexpected":sum(not x["ok"] for x in rows),"p50_ms":values[len(values)//2],
                  "p95_ms":values[min(len(values)-1,int(len(values)*.95))],"max_ms":values[-1],
                  "response_bytes_total":sum(x.get("bytes",0) for x in rows)}
    failures=[r for r in records if not r["ok"]]
    result={"requests":TOTAL,"workers":CONCURRENCY,"seconds":elapsed,"throughput_request_per_second":round(TOTAL/elapsed,2),
      "unexpected_failures":len(failures),"sample_failures":failures[:20],"by_route":by,
      "notes":"Local uvicorn test with synthetic CVs and mock inference; not Muse model latency or production RPS."}
    (OUT/"http-soak-summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print("HTTP_SOAK_SUMMARY="+json.dumps(result),flush=True)
    if failures:raise SystemExit(1)

asyncio.run(main())
