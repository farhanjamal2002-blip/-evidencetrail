"""Shadow-check historical genuine Muse citations for role-provenance ambiguity.

No new Muse calls: reads only the immutable, previously recorded fictional
applicant replay. The warnings are NOT gold labels or proof of a model error.
No evidence/status mutation or automatic hiring decision is permitted.
"""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from demo20_workflow import _load_verified_recording
from ownership_provenance import audit_verified_findings

OUT=Path("artifacts/finalist-unseen-omissions/historic-muse-shadow.json")


def run() -> dict:
    original=_load_verified_recording()
    before=deepcopy(original)
    flagged=[]
    for row in original["results"]:
        findings=row.get("requirements") or []
        for issue in audit_verified_findings(findings):
            flagged.append({
                "fictional_cv_id":row.get("id"),
                "requirement_id":issue.get("requirement_id"),
                "source_page":issue.get("page"),
                "historical_model_status":next((
                    f.get("raw_status") for f in findings
                    if f.get("id")==issue.get("requirement_id")
                ),None),
                "review_prompt":issue.get("suggested_question"),
                "source_quote":issue.get("source_text"),
                "not_an_adjudicated_model_error":True,
            })
    if original!=before:
        raise RuntimeError("Shadow audit altered the genuine saved Meta recording")
    return {
        "provenance":"unchanged historical saved genuine Meta Muse response",
        "new_model_requests":0,
        "saved_fictional_cv_count":len(original["results"]),
        "source_label_changes":0,
        "candidate_decisions":0,
        "advisory_count":len(flagged),
        "flagged":flagged,
        "limitations":[
            "These are regex-generated reviewer prompts, not correctness judgments.",
            "An accurate quote does not prove that its subject is the applicant.",
            "False positives and false negatives need independent human annotation.",
            "No novel provider run, candidate score, hiring recommendation, or rejection.",
        ],
    }


if __name__=="__main__":
    OUT.parent.mkdir(parents=True,exist_ok=True)
    summary=run()
    OUT.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        **{k:v for k,v in summary.items() if k!="flagged"},
        "advisory_samples":[{
            "fictional_cv_id":x["fictional_cv_id"],
            "requirement_id":x["requirement_id"],
            "source_quote":str(x["source_quote"])[:240],
            "historical_model_status":x.get("historical_model_status"),
        } for x in summary["flagged"][:12]],
    },indent=2,ensure_ascii=False))
