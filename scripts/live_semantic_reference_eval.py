"""Capped genuine Meta evaluation on 10 fictional CVs; four blind model checks.
Expected outcomes are set before calls, NOT determined by Muse.
No retries, no candidate data, no extra production traffic, keep receipts in artifacts.
"""
import json
import re
import statistics
import textwrap
import time
from pathlib import Path
import fitz
from fastapi.testclient import TestClient
import app
from scripts.semantic_policy_benchmark_1000 import create_case

assert app.ANALYSIS_PROVIDER=="muse" and app.MUSE_PROVIDER_ENABLED
assert app.configured_model_api_key()
OUT=Path("artifacts/live-semantic-eval")
OUT.mkdir(parents=True,exist_ok=True)
SELECTED=[create_case(i,i,3) for i in range(10)]
BLIND={"direct_correct","one_scope_not_conflict","opposing_cv_claims","related_overstated"}
assert len(SELECTED)==10 and sum(c["family"] in BLIND for c in SELECTED)==4

def fictional_pdf(text):
    doc=fitz.open()
    page=doc.new_page()
    page.insert_text((62,64),"FICTIONAL TEST RESUME",fontsize=11)
    y=102
    for paragraph in text.splitlines():
        for ln in textwrap.wrap(paragraph,78,break_long_words=False,break_on_hyphens=False):
            page.insert_text((62,y),ln,fontsize=10)
            y+=16
    data=doc.tobytes(garbage=4,deflate=True)
    doc.close()
    return data

def blind_meta_assessment(case):
    client=app.get_muse_client(app.configured_model_api_key())
    instruction=(
        "Review this fictional CV against exactly one job requirement. "
        "Respond as a JSON object with keys status, source_quote, explanation. "
        "Choose supported only if the required experience is directly described; "
        "conflicting only if two opposing CV claims exist; otherwise not_found. "
        "Related work or scope limitations are not direct proof. "
        "If quoting, copy the passage verbatim. Do not recommend hiring."
    )
    response=client.chat.completions.create(
        model=app.MODEL_ID,
        messages=[
            {"role":"developer","content":instruction},
            {"role":"user","content":"JOB REQUIREMENT:\n"+case["job_requirement"]
             +"\n\nFICTIONAL CV:\n"+case["cv_text"]},
        ],
        reasoning_effort="minimal",
        max_completion_tokens=450,
    )
    body=response.choices[0].message.content
    if not isinstance(body,str):raise RuntimeError("Missing blind model text")
    clean=body.strip()
    fence=chr(96)*3
    if clean.startswith(fence):
        clean=re.sub(r"^"+fence+r"(?:json)?\s*|\s*"+fence+r"$","",clean)
    parsed=json.loads(clean)
    label=parsed.get("status")
    if label not in ("supported","not_found","conflicting"):
        raise ValueError("Unexpected blind status")
    quote=parsed.get("source_quote")
    return {
        "label":label,
        "quote_grounded":not quote or (isinstance(quote,str) and quote in case["cv_text"]),
        "receipt":getattr(response,"id",None),
        "explanation":str(parsed.get("explanation") or "")[:500],
    }

cases=[];blind=[];errors=[]
with TestClient(app.app) as client:
    for case in SELECTED:
        cid=case["id"]
        attempt=OUT/(cid+".attempt")
        assert not attempt.exists(),"Duplicate paid Muse attempt blocked"
        attempt.write_text("one paid attempt\n")
        begin=time.monotonic()
        resp=client.post("/api/analyze",data={
            "job_description":"Requirements:\n- "+case["job_requirement"],
            "locked_rubric_json":json.dumps([case["job_requirement"]]),
            "consent":"true",
        },files={"cv":(cid+".pdf",fictional_pdf(case["cv_text"]),"application/pdf")})
        row={"id":cid,"domain":case["domain"],"family":case["family"],
             "reference":case["expected"],"http":resp.status_code,
             "duration_s":round(time.monotonic()-begin,3)}
        if resp.status_code==200:
            data=resp.json()
            fields=data.get("requirements") or []
            audit=data.get("quote_audit") or {}
            usage=(data.get("usage") or {}).get("analysis_pass") or {}
            receipt=usage.get("provider_response_id")
            f=fields[0] if len(fields)==1 else {}
            row.update({
                "raw":f.get("raw_status"),"final":f.get("status"),
                "evidence_type":f.get("evidence_type"),
                "correction":f.get("review_reason_code"),
                "quote_verified":audit.get("verified"),
                "quote_proposed":audit.get("proposed"),
                "real_provider_receipt":bool(isinstance(receipt,str) and receipt),
                "receipt":receipt,"reported_calls":data.get("analysis_calls"),
                "requirements":len(fields),
                "raw_correct":f.get("raw_status")==case["expected"],
                "final_correct":f.get("status")==case["expected"],
            })
            if data.get("provider_mode")!="muse" or len(fields)!=1 or row["reported_calls"]!=1 or not row["real_provider_receipt"]:
                errors.append({"id":cid,"type":"incomplete genuine response"})
        else:
            errors.append({"id":cid,"type":"request failed","http":resp.status_code})
        cases.append(row)
        if case["family"] in BLIND:
            marker=OUT/(cid+".blind.attempt")
            assert not marker.exists()
            marker.write_text("one blind adjudication attempt\n")
            try:
                judged=blind_meta_assessment(case)
                judged.update({"id":cid,"reference":case["expected"],
                               "primary_raw":row.get("raw"),
                               "primary_final":row.get("final"),
                               "agrees_with_reference":judged["label"]==case["expected"]})
                blind.append(judged)
                if not judged["quote_grounded"]:
                    errors.append({"id":cid,"type":"blind judge invented quote"})
            except Exception as exc:
                blind.append({"id":cid,"error_type":type(exc).__name__})
                errors.append({"id":cid,"type":"blind judge failure","error_type":type(exc).__name__})
        public={k:v for k,v in row.items() if k!="receipt"}
        print("LIVE_EVAL_CASE="+json.dumps(public),flush=True)

valid=[x for x in cases if x["http"]==200]
summary={
    "synthetic_scenarios_previously_run":1000,
    "live_meta_test_cases":len(cases),
    "live_successful":len(valid),
    "meta_primary_api_calls_attempted":len(cases),
    "meta_blind_adjudication_calls_attempted":len(blind),
    "total_model_calls_attempted":len(cases)+len(blind),
    "authentic_primary_receipts":sum(bool(x.get("real_provider_receipt")) for x in cases),
    "raw_reference_matches":sum(bool(x.get("raw_correct")) for x in valid),
    "verified_reference_matches":sum(bool(x.get("final_correct")) for x in valid),
    "blind_meta_reference_matches":sum(bool(x.get("agrees_with_reference")) for x in blind),
    "median_primary_seconds":round(statistics.median(x["duration_s"] for x in valid),2) if valid else None,
    "error_cases":errors,
    "warning":"Ten templated fictional CVs used genuine Muse; four separate blind reviews by the SAME model family are correlated and not human annotations or production accuracy.",
}
(OUT/"report.json").write_text(json.dumps({"summary":summary,"primary":cases,"blind":blind},indent=2)+"\n")
print("LIVE_EVAL_SUMMARY="+json.dumps(summary),flush=True)
if errors:raise SystemExit(1)
