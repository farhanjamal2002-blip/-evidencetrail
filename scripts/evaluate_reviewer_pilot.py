"""Analyze *actual* anonymous reviewer tasks, never generate fake results.

Usage: python scripts/evaluate_reviewer_pilot.py path/to/real_results.csv
The default template is intentionally header-only; no time-saving claim is
generated without real collected volunteer measurements.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import statistics
import sys

REQUIRED = (
    "reviewer_code","reviewer_type","experience_band","condition","order",
    "cv_id","job_family","difficulty","active_seconds","source_clicks",
    "criterion_unsupported_as_supported","criterion_supported_missed",
    "unresolved_items","completed","model_calls","notes",
)
CONDITIONS = {"manual","assisted"}

def median(v):
    return round(statistics.median(v),2) if v else None

def p90(v):
    if not v:
        return None
    a=sorted(v)
    return round(a[max(0,math.ceil(0.9*len(a))-1)],2)

def read_rows(path: Path):
    with path.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != REQUIRED:
            raise ValueError("Header must exactly match the pre-registered pilot template")
        return list(reader)

def evaluate(rows: list[dict]) -> dict:
    if not rows:
        return {"status":"NO HUMAN REVIEWER DATA YET",
                "claims_authorized":False,"participants":0,"tasks":0}
    unique=set()
    groups={}
    noncompleted=0
    clean=[]
    for i,row in enumerate(rows,1):
        code=row["reviewer_code"].strip()
        cid=row["cv_id"].strip()
        arm=row["condition"].strip().lower()
        if not code or not cid.startswith("ET-") or arm not in CONDITIONS:
            raise ValueError("Invalid reviewer/task/condition on row "+str(i))
        key=(code,cid)
        if key in unique:
            raise ValueError("Repeated identical CV for one reviewer: "+str(key))
        unique.add(key)
        groups.setdefault(code,set()).add(arm)
        if row["completed"].strip().lower() not in {"yes","no"}:
            raise ValueError("Completed must be yes/no on row "+str(i))
        if row["completed"].strip().lower()=="no":
            noncompleted+=1
            continue
        try:
            n=float(row["active_seconds"])
            clicks=int(row["source_clicks"])
            false_support=int(row["criterion_unsupported_as_supported"])
            missed=int(row["criterion_supported_missed"])
            unresolved=int(row["unresolved_items"])
            calls=int(row["model_calls"])
        except (ValueError,TypeError) as exc:
            raise ValueError("Missing/non-numeric task measurement row "+str(i)) from exc
        if (not 0 < n <= 3600 or min(clicks,false_support,missed,unresolved,calls)<0 or
            false_support>4 or missed>4 or unresolved>4 or calls!=0):
            raise ValueError("Out-of-range result or unexpected new model call row "+str(i))
        clean.append({"code":code,"arm":arm,"seconds":n,"clicks":clicks,
                      "false_support":false_support,"missed":missed,
                      "unresolved":unresolved})
    valid_reviewers=[code for code,arms in groups.items() if arms==CONDITIONS]
    if len(valid_reviewers)<2 or len(clean)<8:
        return {"status":"INSUFFICIENT HUMAN REVIEWER DATA",
                "claims_authorized":False,"participants":len(groups),
                "both_arm_reviewers":len(valid_reviewers),
                "tasks":len(rows),"completed_tasks":len(clean),
                "incomplete_tasks":noncompleted}
    by_arm={arm:[x for x in clean if x["arm"]==arm] for arm in ("manual","assisted")}
    if any(len(x)<4 for x in by_arm.values()):
        return {"status":"INSUFFICIENT TASKS PER ARM","claims_authorized":False,
                "tasks":len(rows),"completed_tasks":len(clean),
                "incomplete_tasks":noncompleted}
    m=median([x["seconds"] for x in by_arm["manual"]])
    a=median([x["seconds"] for x in by_arm["assisted"]])
    paired=[]
    for code in valid_reviewers:
        cm=[x["seconds"] for x in by_arm["manual"] if x["code"]==code]
        ca=[x["seconds"] for x in by_arm["assisted"] if x["code"]==code]
        if cm and ca:
            paired.append(round(100*(median(cm)-median(ca))/median(cm),2))
    metrics={
        arm:{
            "tasks":len(v),"median_seconds":median([x["seconds"] for x in v]),
            "p90_seconds":p90([x["seconds"] for x in v]),
            "median_source_clicks":median([x["clicks"] for x in v]),
            "unsupported_claims_accepted":sum(x["false_support"] for x in v),
            "supported_claims_missed":sum(x["missed"] for x in v),
            "unresolved_items":sum(x["unresolved"] for x in v),
        } for arm,v in by_arm.items()
    }
    return {
        "status":"EXPLORATORY DESCRIPTIVE HUMAN PILOT ONLY",
        "claims_authorized":True, "representative_accuracy_claim_authorized":False,
        "causal_effect_claim_authorized":False,
        "reviewer_codes_count":len(groups),
        "both_arm_reviewers":len(valid_reviewers),
        "tasks":len(rows),"completed_tasks":len(clean),
        "incomplete_tasks":noncompleted,
        "conditions":metrics,
        "descriptive_median_time_delta_percent":round(100*(m-a)/m,2),
        "paired_reviewer_median_time_deltas_percent":paired,
        "limitations":[
            "Reviewer assignment and difficulty balance must be confirmed by facilitator",
            "Small convenience sample is exploratory, not a population experiment",
            "Comparing group medians is not a causal treatment-effect estimate",
            "Synthetic CV expectations require separate human adjudication",
            "All raw rows, negative outcomes and incomplete tasks must be retained",
        ],
    }

def main():
    file=Path(sys.argv[1] if len(sys.argv)>1 else
              "evaluation/reviewer_pilot_data_template.csv")
    result=evaluate(read_rows(file))
    print(json.dumps(result,indent=2))
    if result["status"].startswith("EXPLORATORY"):
        target=Path("artifacts/reviewer-pilot")/"aggregate-results.json"
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
