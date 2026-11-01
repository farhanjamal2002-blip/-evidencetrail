"""One-time genuine Muse replay for 20 fictional CVs.

No automatic retry, no fake results, no individual names or real personal data.
Only successfully received and locally verified records go into the saved replay.
The saved replay can be publicly viewed with ZERO API calls afterward.
"""
from __future__ import annotations
import hashlib,json,os,time
from pathlib import Path
from fastapi.testclient import TestClient
import app
from demo20_workflow import CASES, CRITERIA, JOB, make_cv_pdf

assert app.ANALYSIS_PROVIDER=="muse" and app.MUSE_PROVIDER_ENABLED
assert app.configured_model_api_key()
dest=Path("data/demo20_muse_replay.json")
dest.parent.mkdir(exist_ok=True)
if dest.exists():
    raise SystemExit("Replay already exists: refusing to send duplicate Muse requests.")
audit_dir=Path("artifacts/demo20-replay")
audit_dir.mkdir(parents=True,exist_ok=True)
started=time.time()
results=[]
issues=[]
with TestClient(app.app) as client:
    for i,(cid,*_) in enumerate(CASES,1):
        # A per-candidate marker is written before the request. There are no retries.
        marker=audit_dir/(cid+".attempt.json")
        if marker.exists():raise SystemExit("Duplicate attempt marker for "+cid)
        marker.write_text(json.dumps({"id":cid,"attempted":True,"seq":i})+"\n")
        cv=make_cv_pdf(cid)
        began=time.monotonic()
        try:
            response=client.post(
                "/api/analyze",
                data={"job_description":JOB,"locked_rubric_json":json.dumps(CRITERIA),"consent":"true"},
                files={"cv":(cid+".pdf",cv,"application/pdf")},
            )
            duration=round(time.monotonic()-began,3)
            if response.status_code!=200:
                issues.append({"id":cid,"status":response.status_code,"reason":"model_or_application_failure"})
                print(f"{cid}: HTTP {response.status_code} (no retry)",flush=True)
                continue
            payload=response.json()
            requirements=payload.get("requirements") or []
            usage=payload.get("usage") or {}
            provider_id=(usage.get("analysis_pass") or {}).get("provider_response_id")
            audit=payload.get("verification_audit") or {}
            quote_audit=payload.get("quote_audit") or {}
            if not isinstance(provider_id,str) or not provider_id.strip():
                issues.append({"id":cid,"reason":"missing_authentic_provider_receipt"})
                continue
            if payload.get("provider_mode")!="muse" or payload.get("analysis_calls")!=1:
                issues.append({"id":cid,"reason":"not_one_genuine_muse_request"})
                continue
            if len(requirements)!=len(CRITERIA):
                issues.append({"id":cid,"reason":"incomplete_job_rubric"})
                continue
            if not all(q.get("raw_status") or q.get("muse_status") for q in requirements):
                issues.append({"id":cid,"reason":"raw_audit_not_preserved"})
                continue
            if any(q.get("status")=="supported" and q.get("evidence_type")!="direct" for q in requirements):
                issues.append({"id":cid,"reason":"related_or_unverified_evidence_marked_supported"})
                continue
            if quote_audit.get("verified",0)>quote_audit.get("proposed",0):
                issues.append({"id":cid,"reason":"impossible_quote_audit"})
                continue
            cleaned=[]
            for q in requirements:
                # Preserve actual source quotes and page citations; omit full report and document.
                citations=[]
                for ev in (q.get("evidence") or [])[:6]:
                    citations.append({
                        "quote":ev.get("quote"),"page":ev.get("page"),
                        "role":ev.get("role"),"source_id":ev.get("source_id"),
                    })
                cleaned.append({
                    "requirement":q.get("requirement"),"status":q.get("status"),
                    "effective_status":q.get("effective_status"),"raw_status":q.get("raw_status"),
                    "evidence_type":q.get("evidence_type"),"evidence_strength":q.get("evidence_strength"),
                    "certainty":q.get("certainty"),"note":q.get("note"),"evidence":citations,
                })
            record={
                "id":cid,"cv_sha256":hashlib.sha256(cv).hexdigest(),
                "model":payload.get("model"),"provider_mode":"muse",
                "analysis_calls":1,"receipt":provider_id,
                "requirements":cleaned,"quote_audit":quote_audit,
                "verification_audit":{k:v for k,v in audit.items() if k in ("verified","proposed","excluded","rejected")},
                "ocr_pages":payload.get("ocr_pages") or [],
                "elapsed_seconds":duration,
            }
            results.append(record)
            print(f"{cid}: REAL_MUSE_RECEIPT=present, quote_verified={quote_audit.get('verified')}, secs={duration}",flush=True)
        except Exception as exc:
            issues.append({"id":cid,"reason":"exception","type":type(exc).__name__})
            print(f"{cid}: {type(exc).__name__}; no retry",flush=True)

summary={
    "schema":"evidencetrail-fixture-replay/v1",
    "source":"authentic Meta Muse Spark 1.3 responses on fictional CVs",
    "fictional_only":True,
    "job_sha256":hashlib.sha256(JOB.encode()).hexdigest(),
    "rubric_sha256":hashlib.sha256(json.dumps(CRITERIA).encode()).hexdigest(),
    "recorded_utc":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    "requested":len(CASES),"completed":len(results),
    "successful_quotes":sum(r["quote_audit"].get("verified",0) for r in results),
    "attempts_with_no_retry":True,"issues":issues,"results":results,
    "readme":"These are real saved Muse findings. Viewing them does NOT send any API request. This is NOT live inference or a commercial hiring assessment.",
}
# Persist only if at least 5 real results; partial outcomes always disclosed.
if len(results)>=5:
    dest.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(audit_dir/"summary.json").write_text(json.dumps({k:v for k,v in summary.items() if k!="results"},indent=2)+"\n")
print("FINAL_REPLAY_SUMMARY="+json.dumps({k:v for k,v in summary.items() if k!="results"}),flush=True)
if len(results)!=20:
    raise SystemExit("Partial replay. Saved successes, no fabricated findings; stopped with "+str(len(results))+"/20.")
