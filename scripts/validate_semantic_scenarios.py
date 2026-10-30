"""Independent preflight on synthetic truth labels before any model comparison.

This is a minimum oracle-consistency audit, not a replacement for a human
domain expert. It catches a gold label that claims a timeline contradiction
but supplies no dates. Never silently change an expected label after viewing
a model's output.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from scripts.semantic_policy_benchmark_1000 import create_case

DATE=re.compile(r"\b(?:19|20)\d{2}\b")
def oracle_defects(case:dict)->list[str]:
    errors=[]
    cv=case["cv_text"]
    finding=case["finding"]
    for ev in finding.get("evidence") or []:
        if ev["quote"] not in cv: errors.append("synthetic quote not in CV")
    if case["family"]=="explicit_timeline_discrepancy":
        years=DATE.findall(cv)
        if len(years)<2:
            errors.append("timeline reference expects conflict but no two dated claims exist")
    if case["family"]=="opposing_cv_claims":
        if len(finding["evidence"])<2:
            errors.append("two incompatible source statements not present")
    if case["family"]=="missed_direct":
        if not finding["evidence"] or case["expected"]!="supported":
            errors.append("direct-support false-negative oracle not documented")
    return errors

def audit():
    rows=[]
    for r in range(10):
        for family in range(10):
            for v in range(10):
                case=create_case(r,family,v)
                reasons=oracle_defects(case)
                if reasons:rows.append({"id":case["id"],"family":case["family"],"reasons":reasons})
    return {
        "total":1000,"flagged":len(rows),
        "flagged_by_family":{f:sum(x["family"]==f for x in rows)
                             for f in sorted({x["family"] for x in rows})},
        "examples":rows[:12],
        "disclosure":"This is fixture consistency validation; no Muse requests or human truth annotation.",
    }
if __name__=="__main__":
    result=audit()
    out=Path("artifacts/semantic-benchmark")
    out.mkdir(parents=True,exist_ok=True)
    (out/"oracle_quality.json").write_text(json.dumps(result,indent=2)+"\n")
    print("SEMANTIC_ORACLE_AUDIT="+json.dumps(result),flush=True)
