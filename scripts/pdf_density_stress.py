"""Worst-case bounded PDF stress with synthetic documents, local mock only."""
import json,os,resource,time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import pymupdf
from PIL import Image,ImageDraw
from fastapi.testclient import TestClient
import app

assert app.ANALYSIS_PROVIDER=="mock"
DIR=Path("artifacts/pdf-density")
DIR.mkdir(parents=True,exist_ok=True)
JD="Role: Python Operations Engineer\nRequirements:\n1. At least five years building Python production services.\n2. Current AWS Solutions Architect Professional certification."

def searchable_pdf():
    doc=pymupdf.open()
    for i in range(20):
        p=doc.new_page(width=612,height=792)
        p.insert_text((42,43),f"FICTIONAL CV - SEARCHABLE TEST - Page {i+1}/20")
        for n in range(25):
            p.insert_text((42,75+n*23),f"Operational dashboard service, Python API engineer, project {i*25+n}, production deployment log",fontsize=8)
    result=doc.tobytes()
    doc.close()
    return result

def image_only_pdf():
    img=Image.new("RGB",(900,1200),"white")
    draw=ImageDraw.Draw(img)
    for i in range(50):
        draw.text((30,35+i*22),f"FICTIONAL CV SCAN TEST - Python backend operations analyst {i}",fill="black")
    output=BytesIO()
    img.save(output,format="PNG")
    raw=output.getvalue()
    doc=pymupdf.open()
    for n in range(3):
        page=doc.new_page(width=612,height=792)
        page.insert_image(pymupdf.Rect(0,0,612,792),stream=raw)
    result=doc.tobytes()
    doc.close()
    return result

def run_cv(index,data):
    start=time.monotonic()
    with TestClient(app.app) as client:
        res=client.post("/api/analyze",data={"job_description":JD,"consent":"true"},files={"cv":(f"fictional-{index}.pdf",data,"application/pdf")})
    row={"cv":index,"status":res.status_code,"seconds":round(time.monotonic()-start,3)}
    if res.status_code==200:
        payload=res.json()
        row.update({"result_bytes":len(res.content),"pages_extracted":len(payload.get("page_dimensions",{})),
            "ocr_pages":payload.get("ocr_pages"),"muse_calls":payload.get("analysis_calls"),
            "source_verified":payload.get("quote_audit",{}).get("verified"),"pipeline_ms":payload.get("performance_ms",{}).get("pipeline_ms")})
    else:
        row["detail"]=str(res.json().get("detail","unknown"))[:160]
    return row

data1=searchable_pdf()
data2=image_only_pdf()
def stress(label,data,n):
    before=time.monotonic()
    with ThreadPoolExecutor(max_workers=n) as pool:
        values=list(pool.map(lambda i:run_cv(label+"-"+str(i),data),range(n)))
    return {"scenario":label,"pdf_bytes":len(data),"cvs":n,"wall_seconds":round(time.monotonic()-before,3),"max_rss_mb":round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1),"results":values}

results=[stress("20-page-searchable",data1,5),stress("3-page-image-only",data2,3)]
summary={"frozen_source_sha":"8140662cae1e14fbae7b66f664a7d9d99b396674","test_sha_kind":"patched branch",
         "scenarios":results,"reported_model_calls":0,"unexpected":sum(r["status"]!=200 for x in results for r in x["results"]),
         "notes":"GitHub runner mock-mode stress. Not equivalent to Render free-tier CPU/RAM or Muse latency."}
(DIR/"pdf-density-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print("PDF_DENSITY_SUMMARY="+json.dumps(summary),flush=True)
assert summary["unexpected"]==0
assert all(len(v["ocr_pages"])>=2 for x in results if "image-only" in x["scenario"] for v in x["results"])
