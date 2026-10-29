"""Pure evaluator formatter; no Meta calls. Never hardcode criterion count."""
from __future__ import annotations
from typing import Any

def format_criteria(case:dict[str,Any], findings:list[dict[str,Any]])->list[dict[str,Any]]:
    required=case["criteria"]
    expected=case["expected"]
    if len(required)!=len(expected):
        raise ValueError("Reference label count does not match approved requirements")
    if not isinstance(findings,list):
        findings=[]
    rows=[]
    for i,gold in enumerate(expected):
        actual=findings[i] if i<len(findings) and isinstance(findings[i],dict) else {}
        evidence=actual.get("evidence") or []
        rows.append({
            "index":i+1,"reference":gold,
            "raw":actual.get("raw_status"),
            "final":actual.get("status"),
            "evidence_type":actual.get("evidence_type"),
            "citation_count":len(evidence) if isinstance(evidence,list) else 0,
            "reason_code":actual.get("review_reason_code"),
            "raw_correct":actual.get("raw_status")==gold,
            "final_correct":actual.get("status")==gold,
        })
    return rows
