"""Genuine unseen, post-fix Meta Muse evaluation: 8 CVs, 32 locked labels.

Do not edit the reference labels after seeing the model's output.
One real request per fictional two-page CV; no retries. Real provider receipts
saved in private short-retention CI artifact; no raw keys or candidate data.
"""
from pathlib import Path
from collections import Counter
import json
import statistics
import time
from fastapi.testclient import TestClient
import app
from scripts.fresh_holdout_cv_corpus import CASES,manifest,pdf_for_case

assert app.ANALYSIS_PROVIDER=="muse" and app.MUSE_PROVIDER_ENABLED
assert app.configured_model_api_key()
m=manifest()
assert m["cases"]==8 and m["criterion_instances"]==32 and not m["issues"],m
OUT=Path("artifacts/fresh-holdout")
OUT.mkdir(parents=True,exist_ok=True)
(OUT/"reference_manifest.json").write_text(json.dumps(m,indent=2)+"\n")
rows=[];errors=[]
with TestClient(app.app) as client:
    for case in CASES:
        name=case["id"]
        marker=OUT/(name+".attempt")
        assert not marker.exists(),"Never repeat a potentially charged analysis"
        marker.write_text("one real Meta request\n")
        t=time.monotonic()
        resp=client.post("/api/analyze",data={
            "job_description":"POSITION: "+case["role"]+"\nREQUIREMENTS:\n"+"\n".join("- "+q for q in case["criteria"]),
            "locked_rubric_json":json.dumps(case["criteria"]),
            "consent":"true",
        },files={"cv":(name+".pdf",pdf_for_case(case),"application/pdf")})
        row={"id":name,"sector":case["sector"],"http":resp.status_code,
             "seconds":round(time.monotonic()-t,3)}
        if resp.status_code==200:
            data=resp.json()
            findings=data.get("requirements") or []
            receipt=((data.get("usage") or {}).get("analysis_pass") or {}).get("provider_response_id")
            row.update({
                "real_receipt":isinstance(receipt,str) and bool(receipt),
                "receipt":receipt,
                "provider_mode":data.get("provider_mode"),
                "model_calls":data.get("analysis_calls"),
                "quote_audit":data.get("quote_audit"),
                "requirements":[{
                    "index":i+1,
                    "reference":case["expected"][i],
                    "raw":findings[i].get("raw_status") if i<len(findings) else None,
                    "verified":findings[i].get("status") if i<len(findings) else None,
                    "evidence_type":findings[i].get("evidence_type") if i<len(findings) else None,
                    "reason_code":findings[i].get("review_reason_code") if i<len(findings) else None,
                    "quote_count":len(findings[i].get("evidence") or []) if i<len(findings) else 0,
                } for i in range(4)]
            })
            if data.get("provider_mode")!="muse" or len(findings)!=4 or data.get("analysis_calls")!=1 or not row["real_receipt"]:
                errors.append({"id":name,"reason":"invalid true-provider response or missing criterion"})
        else:errors.append({"id":name,"reason":"HTTP failure","status":resp.status_code})
        rows.append(row)
        print("HOLDOUT_CV_CASE="+json.dumps({k:v for k,v in row.items() if k!="receipt"}),flush=True)

pairs=[(r,q) for r in rows for q in r.get("requirements",[])]
def matrix(field):
    counts=Counter((q["reference"],q.get(field)) for _,q in pairs)
    return {f"{expected} -> {actual}":n for (expected,actual),n in sorted(counts.items())}
mistakes=[{"id":r["id"],"reference":q["reference"],"raw":q.get("raw"),
           "verified":q.get("verified"),"criterion":q["index"]}
          for r,q in pairs if q["reference"]!=q.get("verified")]
summary={
    "locked_reference_cases":8,"expected_criteria":32,"successful_cases":sum(r["http"]==200 for r in rows),
    "evaluated_criteria":len(pairs),"authentic_receipts":sum(bool(r.get("real_receipt")) for r in rows),
    "live_model_calls_attempted":len(rows),
    "raw_reference_matches":sum(q["reference"]==q.get("raw") for _,q in pairs),
    "verified_reference_matches":sum(q["reference"]==q.get("verified") for _,q in pairs),
    "raw_confusion":matrix("raw"),"verified_confusion":matrix("verified"),
    "false_supported":sum(q.get("verified")=="supported" and q["reference"]!="supported" for _,q in pairs),
    "missed_direct":sum(q["reference"]=="supported" and q.get("verified")!="supported" for _,q in pairs),
    "missed_conflicts":sum(q["reference"]=="conflicting" and q.get("verified")!="conflicting" for _,q in pairs),
    "mistakes":mistakes,"errors":errors,
    "median_seconds_per_cv":round(statistics.median(r["seconds"] for r in rows),2) if rows else None,
    "limitation":"Eight hand-written fictional CVs with predeclared source reference labels across four new domains; not external expert annotation or production accuracy.",
}
(OUT/"report.json").write_text(json.dumps({"summary":summary,"cases":rows},indent=2)+"\n")
print("FRESH_HOLDOUT_SUMMARY="+json.dumps(summary),flush=True)
if errors or len(rows)!=8 or len(pairs)!=32:raise SystemExit(1)
