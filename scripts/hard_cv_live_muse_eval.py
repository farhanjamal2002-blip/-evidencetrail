"""20 genuine Meta Muse one-pass analyses on NEW two-page fictional CVs.

Reference judgments and exact PDF files are locked before API calls.
One call per CV, no retries; 4 fixed requirements each (80 total judgments).
This tests actual /api/analyze end to end rather than fake Muse response strings.
The reference is hand-authored, not independently annotated by recruiters.
"""
import json
from collections import Counter
from pathlib import Path
import statistics
import time

from fastapi.testclient import TestClient
import app
from scripts.hard_cv_corpus import build_all_cases,corpus_manifest,render_pdf,verify_reference

assert app.ANALYSIS_PROVIDER=="muse" and app.MUSE_PROVIDER_ENABLED
assert app.configured_model_api_key(),"Missing previously configured private Meta API key"
OUT=Path("artifacts/hard-cv-evaluation")
OUT.mkdir(parents=True,exist_ok=True)
manifest=corpus_manifest()
assert manifest["cases"]==20 and manifest["criterion_instances"]==80
assert not any(manifest["invalid_references"].values()),manifest["invalid_references"]
(OUT/"locked_reference_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")

rows=[];failures=[];started=time.monotonic()
with TestClient(app.app) as client:
    for case in build_all_cases():
        cid=case["id"]
        marker=OUT/(cid+".attempt")
        assert not marker.exists(),"No duplicate paid Meta attempts: "+cid
        marker.write_text("one call, no retry\n")
        t=time.monotonic()
        try:
            resp=client.post("/api/analyze",data={
                "job_description":"POSITION: "+case["job_title"]+
                    "\nAPPROVED JOB REQUIREMENTS:\n"+"\n".join("- "+q for q in case["criteria"]),
                "locked_rubric_json":json.dumps(case["criteria"]),
                "consent":"true",
            },files={"cv":(cid+".pdf",render_pdf(case),"application/pdf")})
            row={"id":cid,"sector":case["sector"],"archetype":case["archetype"],
                 "http":resp.status_code,"seconds":round(time.monotonic()-t,3)}
            if resp.status_code==200:
                data=resp.json()
                f=data.get("requirements") or []
                usage=((data.get("usage") or {}).get("analysis_pass") or {})
                quote=data.get("quote_audit") or {}
                response_id=usage.get("provider_response_id")
                row.update({
                    "provider":data.get("provider_mode"),
                    "model":data.get("model"),
                    "real_receipt":isinstance(response_id,str) and bool(response_id),
                    "receipt_id":response_id,
                    "model_calls":data.get("analysis_calls"),
                    "quote_audit":quote,
                    "ocr_pages":data.get("ocr_pages") or [],
                    "requirements":[{
                        "index":i+1,"reference":case["expected"][i],
                        "raw":(f[i].get("raw_status") if i<len(f) else None),
                        "final":(f[i].get("status") if i<len(f) else None),
                        "evidence_type":(f[i].get("evidence_type") if i<len(f) else None),
                        "citation_count":len((f[i].get("evidence") or [])) if i<len(f) else 0,
                        # Synthetic fixtures only: preserve the evidence needed
                        # to audit false-positive double citations offline.
                        "verified_citations":[{
                            "role":cite.get("role"),
                            "page":cite.get("page"),
                            "quote":cite.get("quote"),
                            "source_id":cite.get("source_id"),
                        } for cite in ((f[i].get("evidence") or []) if i<len(f) else [])
                          if isinstance(cite,dict)],
                        "reason_code":f[i].get("review_reason_code") if i<len(f) else None,
                        "raw_correct":i<len(f) and f[i].get("raw_status")==case["expected"][i],
                        "final_correct":i<len(f) and f[i].get("status")==case["expected"][i],
                    } for i in range(4)],
                })
                if len(f)!=4 or data.get("provider_mode")!="muse" or data.get("analysis_calls")!=1 or not row["real_receipt"]:
                    failures.append({"id":cid,"reason":"incomplete genuine output or incorrect inference call count"})
            else:
                failures.append({"id":cid,"reason":"API response","http":resp.status_code})
            rows.append(row)
            # Source-free published CI logs, full provider IDs in retained artifact only.
            public={k:v for k,v in row.items() if k!="receipt_id"}
            # Do not put complete quotes or other detail in public CI logs.
            if "requirements" in public:
                public["requirements"]=[
                    {k:v for k,v in r.items() if k!="verified_citations"}
                    for r in public["requirements"]
                ]
            print("HARD_CV_META_CASE="+json.dumps(public),flush=True)
        except Exception as exc:
            failures.append({"id":cid,"reason":type(exc).__name__})
            rows.append({"id":cid,"error_type":type(exc).__name__})
            print("HARD_CV_META_CASE="+json.dumps({"id":cid,"error_type":type(exc).__name__}),flush=True)

all_f=[(row["sector"],row["archetype"],f) for row in rows
       for f in row.get("requirements",[])]
valid=[r for r in rows if r.get("http")==200]
def confusion(field):
    counts=Counter((f["reference"],f.get(field)) for _,_,f in all_f)
    return {str(a)+" -> "+str(b):v for (a,b),v in sorted(counts.items())}
categories={}
for group in sorted({r["archetype"] for r in valid}):
    f=[x for _,archetype,x in all_f if archetype==group]
    categories[group]={
        "labels":len(f),"raw_reference_matches":sum(x["raw_correct"] for x in f),
        "verified_reference_matches":sum(x["final_correct"] for x in f),
    }
problems=[{"case":row["id"],"archetype":row["archetype"],"criterion":f["index"],
           "reference":f["reference"],"raw":f.get("raw"),"final":f.get("final"),
           "evidence_type":f.get("evidence_type"),"reason_code":f.get("reason_code")}
          for row in valid for f in row["requirements"] if not f["final_correct"]]
summary={
    "test_type":"20 authentic Muse analyses on two-page synthetic CVs, 80 predeclared human-authored reference labels",
    "cases":len(rows),"completed":len(valid),"expected_criteria":80,"evaluated_criteria":len(all_f),
    "api_requests_attempted":len(rows),
    "authentic_provider_receipts":sum(r.get("real_receipt",False) for r in rows),
    "raw_reference_matches":sum(f["raw_correct"] for _,_,f in all_f),
    "verified_reference_matches":sum(f["final_correct"] for _,_,f in all_f),
    "raw_confusion":confusion("raw"),"final_confusion":confusion("final"),
    "by_archetype":categories,
    "false_supported":sum(f.get("final")=="supported" and f["reference"]!="supported" for _,_,f in all_f),
    "missed_supported":sum(f["reference"]=="supported" and f.get("final")!="supported" for _,_,f in all_f),
    "missed_discrepancy":sum(f["reference"]=="conflicting" and f.get("final")!="conflicting" for _,_,f in all_f),
    "failed_cases":problems,
    "error_cases":failures,
    "median_end_to_end_seconds":round(statistics.median(r["seconds"] for r in valid),2) if valid else None,
    "elapsed_wall_seconds":round(time.monotonic()-started,2),
    "disclaimer":"Hand-authored synthetic two-page documents with human-authored reference labels; not real applicants, independent expert assessment, or a production accuracy estimate.",
}
(OUT/"report.json").write_text(json.dumps({"summary":summary,"cases":rows},indent=2)+"\n")
public_summary={k:v for k,v in summary.items() if k not in ("failed_cases",)}
print("HARD_CV_META_SUMMARY="+json.dumps(public_summary),flush=True)
if failures or len(valid)!=20 or len(all_f)!=80:raise SystemExit(1)
