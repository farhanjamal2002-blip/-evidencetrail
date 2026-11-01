"""100 blind Meta document-semantic judgments in ten bounded API calls.

Each batch contains TEN short, fictional CV/JD situations. The model sees no
reference labels, no simulated initial labels and no EvidenceTrail output.
This is independent QUERY BLINDING, not independent MODEL FAMILY nor human gold.
No retries and no real candidate data. Report errors instead of skipping cases.
"""
import json
import re
import statistics
import time
from pathlib import Path
import app
from scripts.semantic_policy_benchmark_1000 import create_case
from scripts.validate_semantic_scenarios import oracle_defects

assert app.ANALYSIS_PROVIDER=="muse" and app.MUSE_PROVIDER_ENABLED
assert app.configured_model_api_key()
OUT=Path("artifacts/100-blind-meta")
OUT.mkdir(parents=True,exist_ok=True)
client=app.get_muse_client(app.configured_model_api_key())
RESULTS=[];BATCHES=[];ERRORS=[]
FENCE=chr(96)*3
for domain_index in range(10):
    cases=[create_case(domain_index,category,(domain_index+7)%10) for category in range(10)]
    assert all(not oracle_defects(x) for x in cases)
    public_cases=[{"id":x["id"],"job_requirement":x["job_requirement"],
                   "cv_text":x["cv_text"]} for x in cases]
    marker=OUT/(f"batch-{domain_index:02}.attempt")
    assert not marker.exists(),"No retries allowed"
    marker.write_text("one inference attempt\n")
    instruction=(
        "You are independently classifying document evidence for a fictional "
        "job review. For EACH supplied case return status supported ONLY if "
        "the CV directly establishes the exact job criterion; conflicting ONLY "
        "if two incompatible CV statements exist; otherwise not_found. "
        "One CV sentence saying the applicant did not perform a task is "
        "NOT internal contradiction. A related task is NOT exact direct proof. "
        "Output a JSON object exactly shaped as "
        '{"cases":[{"id":"...","status":"supported|not_found|conflicting",'
        '"source_quote":"verbatim source phrase or empty string"}]}. '
        "Preserve all IDs; no scores or hiring decisions. "
        "Do not infer missing qualifications as absent in real life."
    )
    start=time.monotonic()
    row={"domain_index":domain_index,"cases_submitted":len(cases)}
    try:
        response=client.chat.completions.create(
            model=app.MODEL_ID,
            messages=[
                {"role":"developer","content":instruction},
                {"role":"user","content":json.dumps({"cases":public_cases},ensure_ascii=False)},
            ],
            reasoning_effort="minimal",
            max_completion_tokens=2000,
        )
        row["seconds"]=round(time.monotonic()-start,3)
        row["receipt"]=getattr(response,"id",None)
        value=response.choices[0].message.content
        if not isinstance(value,str):raise ValueError("No readable model text")
        value=value.strip()
        if value.startswith(FENCE):
            value=re.sub(r"^"+FENCE+r"(?:json)?\s*|\s*"+FENCE+r"$","",value)
        decoded=json.loads(value)
        assessments=decoded.get("cases")
        if not isinstance(assessments,list):raise ValueError("No cases array")
        indexed={}
        for entry in assessments:
            if not isinstance(entry,dict):continue
            cid=entry.get("id")
            if not isinstance(cid,str) or cid in indexed:
                raise ValueError("Duplicate or invalid model case ID")
            indexed[cid]=entry
        expected_ids={x["id"] for x in cases}
        if set(indexed)!=expected_ids:
            raise ValueError("Missing or unexpected model case IDs")
        for case in cases:
            item=indexed[case["id"]]
            label=item.get("status")
            if label not in {"supported","not_found","conflicting"}:
                raise ValueError("Invalid model status")
            quote=item.get("source_quote") or ""
            grounded=isinstance(quote,str) and (not quote or quote in case["cv_text"])
            outcome={
                "id":case["id"],"domain":case["domain"],
                "family":case["family"],"predeclared_reference":case["expected"],
                "blind_meta_status":label,
                "correct":label==case["expected"],
                "quote_supplied":bool(quote),
                "quote_grounded_if_supplied":grounded,
            }
            RESULTS.append(outcome)
            if not grounded:
                ERRORS.append({"id":case["id"],"kind":"fabricated_source_quote"})
        row["parsed"]=len(cases)
        row["correct"]=sum(x["correct"] for x in RESULTS[-10:])
        row["grounded_quotes"]=sum(x["quote_supplied"] and x["quote_grounded_if_supplied"] for x in RESULTS[-10:])
    except Exception as exc:
        ERRORS.append({"batch":domain_index,"kind":type(exc).__name__})
        row["error_kind"]=type(exc).__name__
    BATCHES.append(row)
    print("BLIND_META_BATCH="+json.dumps({k:v for k,v in row.items() if k!="receipt"}),flush=True)

families={}
for family in sorted({x["family"] for x in RESULTS}):
    r=[x for x in RESULTS if x["family"]==family]
    families[family]={"assessed":len(r),"reference_matches":sum(x["correct"] for x in r)}
summary={
    "fictional_cases_requested":100,
    "cases_successfully_assessed":len(RESULTS),
    "genuine_meta_calls_attempted":len(BATCHES),
    "authentic_provider_receipts":sum(isinstance(x.get("receipt"),str) and bool(x.get("receipt")) for x in BATCHES),
    "reference_matches":sum(x["correct"] for x in RESULTS),
    "source_quotes_grounded_when_supplied":sum(x["quote_supplied"] and x["quote_grounded_if_supplied"] for x in RESULTS),
    "source_quotes_supplied":sum(x["quote_supplied"] for x in RESULTS),
    "by_family":families,
    "errors":ERRORS,
    "api_median_batch_seconds":round(statistics.median(x["seconds"] for x in BATCHES if "seconds" in x),2) if any("seconds" in x for x in BATCHES) else None,
    "disclosure":"The same Muse model family independently reinterprets synthetic documents; these are blind requests, NOT independent human judgments, and not 100 end-to-end CV runs.",
}
(OUT/"report.json").write_text(json.dumps({"summary":summary,"batches":BATCHES,"cases":RESULTS},indent=2)+"\n")
print("BLIND_META_100_SUMMARY="+json.dumps(summary),flush=True)
if ERRORS or len(RESULTS)!=100:raise SystemExit(1)
