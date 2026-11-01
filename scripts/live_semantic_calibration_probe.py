"""Live Muse check of scope-vs-CV-contradiction policy: four fictional CVs.

No retries; no real personal data; never print API credentials, source texts,
or raw provider IDs to CI logs. Saved historic Muse recording is unchanged.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from fastapi.testclient import TestClient
import app
from demo20_workflow import JOB, CRITERIA, make_cv_pdf

assert app.ANALYSIS_PROVIDER=="muse" and app.MUSE_PROVIDER_ENABLED
assert app.configured_model_api_key()
OUT=Path("artifacts/muse-semantic-calibration")
OUT.mkdir(parents=True,exist_ok=True)
ids=["ET-008","ET-014","ET-015","ET-019"]
items=[]
issues=[]
with TestClient(app.app) as client:
    for cid in ids:
        marker=OUT/(cid+".attempt")
        assert not marker.exists(), "No retry permitted for "+cid
        marker.write_text("first and only attempt\n")
        started=time.monotonic()
        try:
            res=client.post("/api/analyze",data={
                "job_description":JOB,
                "locked_rubric_json":json.dumps(CRITERIA),
                "consent":"true",
            },files={"cv":(cid+".pdf",make_cv_pdf(cid),"application/pdf")})
            row={"id":cid,"http":res.status_code,"seconds":round(time.monotonic()-started,3)}
            if res.status_code!=200:
                row["error"]="HTTP failure; no retry"
                issues.append({"id":cid,"reason":"non_200"})
            else:
                data=res.json()
                findings=data.get("requirements") or []
                receipts=((data.get("usage") or {}).get("analysis_pass") or {}).get("provider_response_id")
                audit=data.get("quote_audit") or {}
                row.update({
                    "provider":data.get("provider_mode"),
                    "authentic_receipt":bool(isinstance(receipts,str) and receipts.strip()),
                    "reported_calls":data.get("analysis_calls"),
                    "quotes_verified":audit.get("verified"),
                    "quotes_proposed":audit.get("proposed"),
                    "raw_labels":sum(bool(x.get("raw_status")) for x in findings),
                    "requirements":len(findings),
                    "semantic_counts":(data.get("verification_audit") or {}).get("semantic_review_clarifications"),
                    "outcomes":[{"n":i+1,"final":x.get("status"),"raw":x.get("raw_status"),
                                 "evidence_type":x.get("evidence_type"),
                                 "reason_code":x.get("review_reason_code"),
                                 "quotes":len(x.get("evidence") or [])} for i,x in enumerate(findings)],
                    "ocr_pages":data.get("ocr_pages") or [],
                })
                if not row["authentic_receipt"] or row["provider"]!="muse" or row["reported_calls"]!=1:
                    issues.append({"id":cid,"reason":"authenticity"})
                if row["requirements"]!=4 or row["raw_labels"]!=4 or row["quotes_verified"]>row["quotes_proposed"]:
                    issues.append({"id":cid,"reason":"audit"})
                for f in findings:
                    ev=f.get("evidence") or []
                    if f.get("status")=="supported" and f.get("evidence_type")!="direct":
                        issues.append({"id":cid,"reason":"non_direct_support"})
                    if f.get("status")=="conflicting" and len(ev)==1 and ev[0].get("role")=="contradicts" and not f.get("timeline_review_flags"):
                        issues.append({"id":cid,"reason":"single_quote_mislabeled_internal_conflict"})
                if cid=="ET-019" and 1 not in row["ocr_pages"]:
                    issues.append({"id":cid,"reason":"ocr_missing"})
            items.append(row)
            print("LIVE_SEMANTIC_CASE="+json.dumps(row),flush=True)
        except Exception as exc:
            issues.append({"id":cid,"reason":type(exc).__name__})
            print("LIVE_SEMANTIC_CASE="+json.dumps({"id":cid,"error_type":type(exc).__name__}),flush=True)
summary={
    "real_muse_cases":len(ids),
    "successes":sum(x.get("http")==200 for x in items),
    "authentic_receipts":sum(x.get("authentic_receipt",False) for x in items),
    "verified_quotes":sum(x.get("quotes_verified") or 0 for x in items),
    "proposed_quotes":sum(x.get("quotes_proposed") or 0 for x in items),
    "model_calls":sum(x.get("reported_calls") or 0 for x in items),
    "issues":issues,
    "disclosure":"Actual Meta Muse Spark calls on four fictional CVs; no retries, no real candidates, no production SLA."
}
(OUT/"summary.json").write_text(json.dumps({"summary":summary,"cases":items},indent=2)+"\n")
print("LIVE_SEMANTIC_SUMMARY="+json.dumps(summary),flush=True)
if issues:raise SystemExit(1)
