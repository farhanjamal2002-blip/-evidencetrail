"""One corrected genuine Muse timeline test — no retries or real applicant data.

This replaces a mathematically invalid synthetic reference fixture found after
the original ten-call pilot; do NOT quietly count the original as correct.
"""
import json
import textwrap
from pathlib import Path
import fitz
from fastapi.testclient import TestClient
import app
from scripts.semantic_policy_benchmark_1000 import create_case
from scripts.validate_semantic_scenarios import oracle_defects

assert app.ANALYSIS_PROVIDER=="muse" and app.MUSE_PROVIDER_ENABLED
assert app.configured_model_api_key()
case=create_case(6,6,3)
assert not oracle_defects(case),oracle_defects(case)
assert case["expected"]=="conflicting"
out=Path("artifacts/live-timeline-recheck")
out.mkdir(parents=True,exist_ok=True)
attempt=out/"single.attempt"
assert not attempt.exists()
attempt.write_text("one corrected timeline attempt\n")
pdf=fitz.open()
page=pdf.new_page()
page.insert_text((62,64),"FICTIONAL CV / EVALUATION ONLY")
y=98
for paragraph in case["cv_text"].splitlines():
    for line in textwrap.wrap(paragraph,75,break_long_words=False):
        page.insert_text((62,y),line,fontsize=10)
        y+=17
raw=pdf.tobytes(garbage=4,deflate=True)
pdf.close()
with TestClient(app.app) as client:
    r=client.post("/api/analyze",data={
        "job_description":"Requirements:\n- "+case["job_requirement"],
        "locked_rubric_json":json.dumps([case["job_requirement"]]),
        "consent":"true",
    },files={"cv":(case["id"]+".pdf",raw,"application/pdf")})
result={"id":case["id"],"http":r.status_code,"gold_predeclared":case["expected"]}
if r.status_code==200:
    data=r.json()
    fs=data.get("requirements") or []
    f=fs[0] if len(fs)==1 else {}
    receipt=((data.get("usage") or {}).get("analysis_pass") or {}).get("provider_response_id")
    result.update({
        "raw":f.get("raw_status"),"verified":f.get("status"),
        "raw_correct":f.get("raw_status")==case["expected"],
        "verified_correct":f.get("status")==case["expected"],
        "reason_code":f.get("review_reason_code"),
        "quote_audit":data.get("quote_audit"),
        "timeline_audit":data.get("timeline_audit"),
        "receipt":receipt,
        "has_real_receipt":isinstance(receipt,str) and bool(receipt),
        "reported_calls":data.get("analysis_calls"),
    })
(out/"report.json").write_text(json.dumps(result,indent=2)+"\n")
print("REPAIRED_TIMELINE_REAL_MUSE="+json.dumps({
    k:v for k,v in result.items() if k not in ("receipt","timeline_audit")
}),flush=True)
if r.status_code!=200 or not result.get("has_real_receipt") or result.get("reported_calls")!=1:
    raise SystemExit(1)
