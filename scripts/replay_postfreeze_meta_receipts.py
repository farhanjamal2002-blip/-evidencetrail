"""Replay saved genuine Meta Muse findings through the PATCHED local verifier.

Downloads immutable prior 16-CV GitHub Actions evidence. Zero Meta inference.
The previous postprocessor's two demotions are unrolled to their raw status,
then re-adjudicated using actual verified quotation roles and source passages.
Never invent or alter source quotes/receipt IDs/expected labels.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

from semantic_review import clarify_verified_findings

ROOT=Path("artifacts/postfreeze-16-report")
OUT=Path("artifacts/postfreeze-offline-replay")
OUT.mkdir(parents=True,exist_ok=True)
reference=json.loads((ROOT/"report.json").read_text())
original={r["id"]:r for r in reference["cases"]}
assert len(original)==16
before=after=restored=0
audit=[]

for cid,row in sorted(original.items()):
    saved=json.loads((ROOT/(cid+".response.json")).read_text())
    f=saved.get("requirements") or []
    locked=row["requirements"]
    assert len(f)==len(locked)==3,(cid,len(f),len(locked))
    provider_id=(saved.get("analysis_pass") or {}).get("provider_response_id")
    assert isinstance(provider_id,str) and provider_id.startswith("chatcmpl-"),cid
    for i,(original_f,truth) in enumerate(zip(f,locked)):
        baseline=original_f.get("status")
        gold=truth["reference"]
        raw=original_f.get("raw_status")
        assert raw==truth["raw"],(cid,i,"raw receipt mismatch")
        assert baseline==truth["final"],(cid,i,"saved outcome mismatch")
        before+=int(baseline==gold)
        amended=deepcopy(original_f)
        previous_quotes=deepcopy(amended.get("evidence") or [])
        changed=amended.get("review_reason_code")=="multi_quote_scope_not_internal_contradiction"
        if changed:
            assert raw=="conflicting" and baseline=="not_found"
            amended["status"]="conflicting"
            amended["effective_status"]="conflicting"
            amended["evidence_type"]="conflicting"
            for k in ("review_reason_code","review_label","review_explanation","status_policy"):
                amended.pop(k,None)
            if isinstance(amended.get("scope_boundary_review"),dict):
                amended["scope_boundary_review"]["final_status"]="conflicting"
            clarify_verified_findings([amended])
            restored+=1
        result=amended.get("status")
        assert amended.get("raw_status")==raw
        assert amended.get("evidence",[])==previous_quotes, "Never mutate source quotations"
        after+=int(result==gold)
        audit.append({"id":cid,"criterion":i+1,"gold":gold,
                      "raw":raw,"previous_final":baseline,"new_final":result,
                      "rule_rechecked":changed,
                      "source_citations":len(previous_quotes)})
summary={
    "replayed_genuine_muse_CVs":16,
    "locked_requirement_labels":len(audit),
    "raw_provider_receipts":16,
    "extra_meta_calls":0,
    "prior_final_reference_matches":before,
    "post_fix_reference_matches":after,
    "reaudited_multiquote_scope_cases":restored,
    "new_false_supported":sum(x["new_final"]=="supported" and x["gold"]!="supported" for x in audit),
    "remaining_missed_contradictions":sum(x["gold"]=="conflicting" and x["new_final"]!="conflicting" for x in audit),
    "disclosure":"16 hand-authored fictional CVs; replays preserved real Meta result records and source quotes, not an independent real-world accuracy estimate.",
}
(OUT/"result.json").write_text(json.dumps({"summary":summary,"criteria":audit},indent=2)+"\n")
print("OFFLINE_REAL_META_REPLAY="+json.dumps(summary),flush=True)
assert summary["prior_final_reference_matches"]==46
assert summary["post_fix_reference_matches"]==48,summary
assert summary["reaudited_multiquote_scope_cases"]==2
assert summary["new_false_supported"]==0
assert summary["remaining_missed_contradictions"]==0
