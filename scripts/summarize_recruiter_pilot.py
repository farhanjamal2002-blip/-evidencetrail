"""Human reviewer pilot reporting: never estimate savings without observed data.

Input is a JSON array, supplied *after* voluntary reviewer sessions, with
actual task records. No test fixture is treated as human study evidence.
Records require same predefined 24 assignments and all 4 coded reviewers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.prepare_recruiter_pilot_packets import assignments

OUT=Path("artifacts/recruiter-human-pilot")
ARMS=("manual","assisted")


def report(observations: list[dict] | None) -> dict:
    known={(r["reviewer_code"],r["candidate_id"]):r for r in assignments()}
    if observations is None:
        return {
            "status":"NOT MEASURED",
            "human_tasks_completed":0,
            "false_supported_counts":None,
            "missed_supported_counts":None,
            "median_time_saved_fraction":None,
            "reason":"No genuine human reviewer observations supplied",
            "limitations":["4 planned volunteers only; small convenience pilot"],
        }
    if not isinstance(observations,list):
        raise ValueError("Observations must be a JSON list")
    seen=set()
    by_arm={arm:[] for arm in ARMS}
    incomplete=[]
    for obs in observations:
        if not isinstance(obs,dict):
            raise ValueError("Each observation must be an object")
        key=(obs.get("reviewer_code"),obs.get("candidate_id"))
        if key not in known or key in seen:
            raise ValueError("Unexpected or duplicate reviewer/candidate assignment: "+str(key))
        seen.add(key)
        arm=known[key]["condition"]
        if obs.get("condition")!=arm:
            raise ValueError("Condition does not match preregistered assignment")
        if obs.get("completed") is not True:
            incomplete.append(key)
            continue
        value=obs.get("active_seconds")
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not 10<=value<=360:
            raise ValueError("Completed tasks need plausible stopwatch seconds (10–360)")
        findings=obs.get("reviewer_findings")
        if not isinstance(findings,list) or len(findings)!=4 or not all(
            x in ("supported","not_found","conflicting","uncertain") for x in findings
        ):
            raise ValueError("Four original reviewer labels are required")
        by_arm[arm].append({"seconds":float(value),"id":key,
                            "adjudication":obs.get("independent_adjudication")})
    if set(known)!=seen:
        raise ValueError("Missing predeclared assignments; partial pilot must not be presented as complete")
    manual=[r["seconds"] for r in by_arm["manual"]]
    assisted=[r["seconds"] for r in by_arm["assisted"]]
    if not manual or not assisted:
        raise ValueError("Both study arms need completed tasks")
    manual_med=median(manual)
    assisted_med=median(assisted)
    # Only errors adjudicated independently after submission are countable.
    adjudicated={}
    for arm,items in by_arm.items():
        validated=[r["adjudication"] for r in items
                   if isinstance(r["adjudication"],dict) and
                   r["adjudication"].get("adjudicator_count",0)>=2 and
                   isinstance(r["adjudication"].get("false_supported"),int) and
                   isinstance(r["adjudication"].get("missed_supported"),int)]
        adjudicated[arm]={
            "adjudicated_tasks":len(validated),
            "false_supported_count":sum(v["false_supported"] for v in validated) if len(validated)==len(items) else None,
            "missed_supported_count":sum(v["missed_supported"] for v in validated) if len(validated)==len(items) else None,
        }
    return {
        "status":"EXPLORATORY HUMAN RESULTS — NOT GENERALIZABLE",
        "reviewers":len({x[0] for x in seen}),
        "assigned_tasks":len(known),
        "completed_tasks":len(manual)+len(assisted),
        "incomplete_tasks":len(incomplete),
        "manual_median_active_seconds":manual_med,
        "assisted_median_active_seconds":assisted_med,
        "median_time_saved_fraction":round((manual_med-assisted_med)/manual_med,3),
        "per_arm_count":{"manual":len(manual),"assisted":len(assisted)},
        "independent_evidence_adjudication":adjudicated,
        "limitations":[
            "Four volunteer convenience reviewers on fictional CVs",
            "Unblinded participants and small N; no formal causal evidence",
            "Reviewers each see different but matched CVs across conditions",
            "Time includes PDF/app navigation, unlike pure model latency",
            "Unadjudicated evidence error outcomes intentionally omitted",
        ],
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--observations",type=Path)
    args=parser.parse_args()
    observations=json.loads(args.observations.read_text()) if args.observations else None
    result=report(observations)
    OUT.mkdir(exist_ok=True,parents=True)
    (OUT/"pilot-impact-summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
