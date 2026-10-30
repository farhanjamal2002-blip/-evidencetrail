"""No-paid-call audit of newly authored fictional CV evidence omissions.

This reports a mock-engine diagnostic, NOT Muse model accuracy and NOT
real-world recruiting accuracy. Failed test cases remain visible in JSON.
"""
from __future__ import annotations
import json
import os
from collections import Counter
from pathlib import Path
import statistics
import sys

os.environ["EVIDENCETRAIL_PROVIDER"] = "mock"
os.environ["EVIDENCETRAIL_ENABLE_MUSE"] = "false"
os.environ["EVIDENCETRAIL_ENABLE_META_VISION"] = "false"
os.environ["MODEL_API_KEY"] = ""
os.environ["MAX_ANALYSES_PER_PROCESS"] = "1000"
os.environ["MAX_ANALYSES_PER_HOUR_PER_IP"] = "1000"
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
import app
from scripts.finalist_omission_corpus import CASES, make_cv_pdf, manifest_hash

OUT = Path("artifacts/finalist-unseen-omissions/report.json")


def run_audit() -> dict:
    if not app.MOCK_PROVIDER_ENABLED or app.MUSE_PROVIDER_ENABLED:
        raise RuntimeError("Unsafe evaluation provider: this benchmark requires mock-only mode")
    rows=[]
    with TestClient(app.app) as client:
        for case in CASES:
            source=make_cv_pdf(case)
            response=client.post(
                "/api/analyze",
                data={"consent":"true",
                      "job_description":"Fictional role requirements:\n- "+case.requirement},
                files={"cv":(case.id+".pdf",source,"application/pdf")},
            )
            if response.status_code != 200:
                rows.append({"case":case.id, "family":case.family,"expected":case.reference,
                             "observed":None,"http_status":response.status_code,
                             "error":response.json().get("detail","unknown")})
                continue
            payload=response.json()
            findings=payload.get("requirements") or []
            observed=findings[0].get("status") if len(findings)==1 else "invalid_requirement_count"
            rows.append({
                "case":case.id,"family":case.family,"trap":case.trap,
                "scanned":case.scanned,
                "expected":case.reference,"observed":observed,
                "matches_author_label":observed==case.reference,
                "ocr_pages":payload.get("ocr_pages") or [],
                "verified_quotes":sum(len(f.get("evidence") or []) for f in findings),
                "performance_ms":(payload.get("performance_ms") or {}).get("pipeline_ms"),
                "http_status":response.status_code,
            })
    counts=Counter((x["expected"],x.get("observed")) for x in rows)
    valid=[x for x in rows if x.get("observed") is not None]
    false_support=[x["case"] for x in valid if x["observed"]=="supported"
                   and x["expected"]!="supported"]
    missed_support=[x["case"] for x in valid if x["expected"]=="supported"
                    and x["observed"]!="supported"]
    missed_conflict=[x["case"] for x in valid if x["expected"]=="conflicting"
                     and x["observed"]!="conflicting"]
    other_mismatches=[x["case"] for x in valid
                      if x["observed"]!=x["expected"]
                      and x["case"] not in false_support+missed_support+missed_conflict]
    latencies=[v["performance_ms"] for v in valid
               if isinstance(v.get("performance_ms"),(int,float))]
    result={
        "title":"EvidenceTrail untuned author-labelled fictional omission diagnostic",
        "provider":"local mock only — NO META MODEL REQUESTS",
        "corpus_sha256":manifest_hash(),
        "reference_provenance":"author-constructed labels, not independently annotated",
        "cases":len(CASES),
        "http_completed":len(valid),
        "observed_matches_author_label":sum(x.get("matches_author_label",False) for x in rows),
        "confusion":[{"reference":a,"observed":b,"count":n}
                     for (a,b),n in sorted(counts.items())],
        "false_supported_cases":false_support,
        "missed_supported_cases":missed_support,
        "missed_conflicting_cases":missed_conflict,
        "other_mismatch_cases":other_mismatches,
        "scanned_cases":sum(c.scanned for c in CASES),
        "ocr_scanned_pages_seen":sum(bool(x.get("ocr_pages")) for x in valid if x["scanned"]),
        "median_pipeline_ms":round(statistics.median(latencies),1) if latencies else None,
        "new_paid_meta_calls":0,
        "rows":rows,
        "limitations":[
           "mock heuristic behavior is not Muse Spark accuracy",
           "synthetic labels are not independent recruiter annotations",
           "quote verification establishes source presence, not a true qualification",
           "a not_found CV finding does not mean candidate lacks ability",
           "the release candidate is frozen; this diagnostic branch does not deploy",
        ],
    }
    return result


def main():
    report=run_audit()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({key:val for key,val in report.items() if key!="rows"},
                     indent=2,ensure_ascii=False))
    if report["http_completed"]!=len(CASES):
        raise SystemExit("At least one case failed to complete; inspect JSON before interpreting any numbers")


if __name__=="__main__":
    main()
