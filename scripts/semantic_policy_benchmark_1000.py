"""EvidenceTrail semantic-policy simulation, NOT a 1,000-call Muse benchmark.

1,000 synthetic, human-specified evidence situations (10 roles x 10 failure
classes x 10 surface variants) provide an independently written expected status.
Some intentionally injected "Muse-like" model proposals are wrong. We assess
real production post-verification guards, not how frequently Muse makes mistakes.
No Meta requests, no real applicant records, no claims of independent field accuracy.
"""
from __future__ import annotations

from collections import Counter,defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import time
from typing import Any

import app
from semantic_review import clarify_verified_findings

ROLES = [
    ("procurement","personally negotiated supplier contract terms","prepared negotiation notes"),
    ("software","deployed production Python applications","reviewed Python tutorials"),
    ("finance","signed off monthly financial reconciliations","prepared reconciliation drafts"),
    ("logistics","personally coordinated GCC cross-border shipments","organized domestic dispatch logs"),
    ("aviation","performed aircraft safety audits","assisted with airport office checklists"),
    ("healthcare","conducted clinical compliance audits","filed clinic compliance records"),
    ("construction","supervised foundation structural inspections","collected engineering site notes"),
    ("security","led incident response investigations","forwarded security alerts"),
    ("analytics","designed production SQL data pipelines","formatted existing spreadsheet reports"),
    ("support","managed escalated customer incidents","answered routine customer questions"),
]
VARIANTS = [
    ("I","and maintained traceable records."),
    ("My role","under the documented team process."),
    ("During a contract","according to assigned duties."),
    ("In a prior position","with direct responsibility noted."),
    ("Across a project","as described in project notes."),
    ("On a team","with role boundaries explained."),
    ("For an employer","within the relevant business unit."),
    ("In the review period","during the stated engagement."),
    ("In my work","with responsibility separated from assistance."),
    ("For the assignment","without assuming other team members' tasks."),
]
CLASSES = (
    "direct_correct",
    "related_overstated",
    "unsupported_overstated",
    "one_scope_not_conflict",
    "document_absence_not_conflict",
    "opposing_cv_claims",
    "explicit_timeline_discrepancy",
    "related_context_unproven",
    "missing_no_evidence",
    "missed_direct",
)

def quote(text,role="supports"):
    return {"quote":text,"page":1,"role":role}

def create_case(role_index:int,case_index:int,variant_index:int)->dict[str,Any]:
    role,direct,related=ROLES[role_index]
    intro,ending=VARIANTS[variant_index]
    prefix=f"{intro} {direct}"
    direct_text=f"{prefix} {ending}"
    adjacent_text=f"{intro} {related} {ending}"
    limited_text=f"{intro} supported the team; I did not personally {direct}. {ending}"
    missing_text=f"{intro} reported no documentary evidence for {direct}. {ending}"
    opposing_text=f"{intro} personally {direct}. {ending}"
    denial_text=f"{intro} never personally {direct}. {ending}"
    label=CLASSES[case_index]
    expected="not_found"
    status="not_found"
    evidence_type="unsupported"
    evidence=[]
    flags=[]
    if label=="direct_correct":
        status="supported";evidence_type="direct";evidence=[quote(direct_text)];expected="supported"
    elif label=="related_overstated":
        status="supported";evidence_type="related";evidence=[quote(adjacent_text)]
    elif label=="unsupported_overstated":
        status="supported";evidence_type="unsupported";evidence=[]
    elif label=="one_scope_not_conflict":
        status="conflicting";evidence_type="conflicting";evidence=[quote(limited_text,"contradicts")]
    elif label=="document_absence_not_conflict":
        status="conflicting";evidence_type="conflicting";evidence=[quote(missing_text,"contradicts")]
    elif label=="opposing_cv_claims":
        status="conflicting";evidence_type="conflicting";evidence=[quote(opposing_text),quote(denial_text,"contradicts")];expected="conflicting"
    elif label=="explicit_timeline_discrepancy":
        status="conflicting";evidence_type="conflicting";evidence=[quote(denial_text,"contradicts")]
        flags=[{"code":"duration_discrepancy","source":"independent_date_audit"}];expected="conflicting"
    elif label=="related_context_unproven":
        status="not_found";evidence_type="related";evidence=[quote(adjacent_text)]
    elif label=="missing_no_evidence":
        status="not_found";evidence_type="unsupported"
    elif label=="missed_direct":
        status="not_found";evidence_type="direct";evidence=[quote(direct_text)];expected="supported"
    else:raise ValueError(label)
    requirement=f"Must have {direct}."
    cv_passages=[q["quote"] for q in evidence]
    if not cv_passages:cv_passages=[f"{intro} worked at a {role} workplace. {ending}"]
    return {
      "id":f"SIM-{role_index:02}-{case_index:02}-{variant_index:02}",
      "domain":role,"family":label,"variant":variant_index,
      "job_requirement":requirement,
      "cv_text":"\n".join(cv_passages),
      "expected":expected,
      "raw_proposal":status,
      "finding":{
        "id":"R1","requirement":requirement,
        "status":status,"effective_status":status,
        "raw_status":status,"muse_status":status,
        "evidence_type":evidence_type,"evidence":evidence,
        "timeline_review_flags":flags,"certainty":"clear",
        "note":"Controlled simulation — not a real Meta response.",
      }
    }

def run_suite()->dict[str,Any]:
    cases=[create_case(r,c,v) for r in range(10) for c in range(10) for v in range(10)]
    assert len(cases)==1000 and len({x["id"] for x in cases})==1000
    before=deepcopy(cases)
    errors=[];diagnostics=[];family=defaultdict(lambda:Counter())
    confusion_raw=Counter();confusion_final=Counter()
    timings=[]
    for case in cases:
        original=case["finding"]
        # Test passes in grounded-source quotes deliberately constructed above.
        # This intentionally does NOT test PDF byte verification or independent
        # semantic ability of Muse. The model-like proposal is controlled input.
        for evidence in original["evidence"]:
            if evidence["quote"] not in case["cv_text"]:
                errors.append([case["id"],"Ungrounded synthetic quote"])
        row=deepcopy(original)
        start=time.perf_counter()
        app.enforce_evidence_status_invariants([row],[{"requirement":case["job_requirement"],"status":original["raw_status"]}])
        clarify_verified_findings([row])
        timings.append((time.perf_counter()-start)*1000)
        actual=row["status"];gold=case["expected"];raw=original["raw_status"]
        confusion_raw[(gold,raw)]+=1
        confusion_final[(gold,actual)]+=1
        family[case["family"]]["count"]+=1
        family[case["family"]]["raw_correct"]+=int(gold==raw)
        family[case["family"]]["final_correct"]+=int(gold==actual)
        family[case["family"]]["changed"]+=int(raw!=actual)
        if raw != row.get("raw_status"):
            errors.append([case["id"],"Provider proposal was overwritten"])
        if gold!=actual:
            diagnostics.append({
                "id":case["id"],"family":case["family"],
                "gold":gold,"raw":raw,"final":actual,
                "failure_kind":"false_positive" if actual=="supported" else
                    "false_negative" if gold=="supported" else "other",
            })
    assert not errors,errors[:4]
    assert cases==before,"Input scenarios must remain untouched"
    final_correct=sum(v for (gold,pred),v in confusion_final.items() if gold==pred)
    raw_correct=sum(v for (gold,pred),v in confusion_raw.items() if gold==pred)
    # No percentages on applicant UI. This *technical evaluation* tracks accuracy.
    output={
        "schema":"evidencetrail/synthetic-semantic-policy-benchmark/v1",
        "scenarios":1000,"domains":len(ROLES),"families":list(CLASSES),"variants_per_family_domain":10,
        "oracle":"pre-authored synthetic class status; not an independent recruiter annotation",
        "muse_requests":0,"model_proposals":"deliberately injected controlled Muse-shaped statuses; NOT genuine Meta outputs",
        "raw_correct":raw_correct,"final_correct":final_correct,
        "raw_accuracy":round(raw_correct/1000,4),"final_accuracy":round(final_correct/1000,4),
        "new_errors":sum(v for k,v in confusion_final.items() if k[0]!=k[1]),
        "raw_confusion":{f"{g}->{p}":n for (g,p),n in sorted(confusion_raw.items())},
        "final_confusion":{f"{g}->{p}":n for (g,p),n in sorted(confusion_final.items())},
        "families":{k:dict(v) for k,v in sorted(family.items())},
        "failures":diagnostics,
        "failures_by_family":dict(Counter(x["family"] for x in diagnostics)),
        "per_item_guard_latency_ms_p50":round(sorted(timings)[len(timings)//2],4),
        "per_item_guard_latency_ms_p95":round(sorted(timings)[int(len(timings)*.95)],4),
        "warning":"These are intentionally templated policy unit scenarios, not 1,000 independent CVs or real Muse calls. This quantifies guard behavior under injected errors, not production semantic accuracy.",
    }
    assert sum(v["count"] for v in family.values())==1000
    return output

if __name__=="__main__":
    result=run_suite()
    out=Path("artifacts/semantic-benchmark")
    out.mkdir(parents=True,exist_ok=True)
    (out/"policy_1000.json").write_text(json.dumps(result,indent=2)+"\n")
    summary={key:result[key] for key in (
        "scenarios","domains","raw_correct","final_correct","raw_accuracy",
        "final_accuracy","failures_by_family","muse_requests",
        "per_item_guard_latency_ms_p50","per_item_guard_latency_ms_p95")}
    print("SEMANTIC_POLICY_BENCHMARK="+json.dumps(summary),flush=True)
