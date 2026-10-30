"""Strict no-cost paired robustness metrics; no model inference occurs here.

The challenge pairs are frozen author-created fictional CVs. This process
reports genuine Muse outputs ONLY when both variants have authentic provider
response IDs and matching challenge IDs. Until then no model accuracy or
real-world robustness result is emitted. A mock result is never accepted as
a genuine research run.
"""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

CORPUS=Path("evaluation/RESEARCH_METAMORPHIC_PAIRS.json")
INPUT=Path("evaluation/research_metamorphic_predictions.jsonl")
OUT=Path("artifacts/academic-methods/metamorphic_report.json")
VALID={"supported","not_found","conflicting"}
ROLES={"baseline","variant"}

def load_corpus(path=CORPUS):
    raw=path.read_bytes()
    data=json.loads(raw)
    rows=data.get("pairs") or []
    if data.get("reference_provenance")!="author_labelled_synthetic" or len(rows)!=12:
        raise ValueError("Frozen challenge missing or provenance changed")
    seen=set()
    for p in rows:
        if p.get("id") in seen:
            raise ValueError("Duplicate challenge ID")
        seen.add(p["id"])
        if p["expected_relation"] not in ("invariant","must_change"):
            raise ValueError("Invalid expected relation")
        for k in ROLES:
            if p[k]["authored_reference"] not in VALID or not p[k]["cv_text"]:
                raise ValueError("Invalid authored reference")
        same=p["baseline"]["authored_reference"]==p["variant"]["authored_reference"]
        if same!=(p["expected_relation"]=="invariant"):
            raise ValueError("Authored relation inconsistent with reference labels")
    return rows,hashlib.sha256(raw).hexdigest()

def load_predictions(path=INPUT):
    if not path.exists():
        return []
    rows=[]
    for n,line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.strip():
            continue
        try: obj=json.loads(line)
        except ValueError as exc: raise ValueError(f"Malformed JSON row {n}") from exc
        rows.append(obj)
    return rows

def evaluate(predictions, corpus, corpus_sha):
    if not predictions:
        return {"status":"NO REPRODUCIBLE METAMORPHIC RUN YET",
                "model_results_measured":False,
                "author_declared_pairs":len(corpus),
                "challenge_sha256":corpus_sha,
                "completed_pairs":0,
                "new_model_calls_in_metric_runner":0,
                "unmeasured_pairs":[p["id"] for p in corpus]}
    allowed={p["id"]:p for p in corpus}
    by_id={}
    for row in predictions:
        if not isinstance(row,dict) or row.get("pair_id") not in allowed:
            raise ValueError("Unexpected challenge ID or malformed row")
        role=row.get("role")
        if role not in ROLES:
            raise ValueError("Invalid variant role")
        key=(row["pair_id"],role)
        if key in by_id:
            raise ValueError("Repeated model result (potential selective retry or cherry-picking)")
        if row.get("provider_mode")!="muse" or not isinstance(row.get("provider_response_id"),str) or not row["provider_response_id"].strip():
            raise ValueError("Genuine Meta mode and nonempty provider receipt required")
        if row.get("corpus_sha256") != corpus_sha:
            raise ValueError("Corpus fingerprint mismatch")
        if row.get("predicted_status") not in VALID:
            raise ValueError("Unsupported/invalid predicted evidence label")
        if type(row.get("source_quote_located")) is not bool:
            raise ValueError("Source location check must be explicit boolean")
        if type(row.get("analysis_calls")) is not int or row["analysis_calls"]!=1:
            raise ValueError("One authentic provider request expected for each variant")
        if type(row.get("cited_page")) is not int or row["cited_page"]<0:
            raise ValueError("Cited page requires 0 for absent or positive integer")
        if row["source_quote_located"] and row["cited_page"]==0:
            raise ValueError("Located quote requires a cited page")
        by_id[key]=row
    if len(by_id) != len(corpus)*2:
        incomplete=[p["id"] for p in corpus if
                    (p["id"],"baseline") not in by_id or (p["id"],"variant") not in by_id]
        return {"status":"PARTIAL GENUINE MODEL PREDICTIONS — NO COMPLETED BENCHMARK CLAIM",
                "model_results_measured":False,
                "challenge_sha256":corpus_sha,
                "recorded_variants":len(by_id),
                "completed_pairs":len(corpus)-len(incomplete),
                "unmeasured_pairs":incomplete,
                "new_model_calls_in_metric_runner":0}
    outcomes=[]
    for p in corpus:
        a=by_id[(p["id"],"baseline")]
        b=by_id[(p["id"],"variant")]
        predicted_invariant=(a["predicted_status"]==b["predicted_status"])
        expected_invariant=(p["expected_relation"]=="invariant")
        correct_count=sum(
            r["predicted_status"]==p[k]["authored_reference"]
            for k,r in (("baseline",a),("variant",b))
        )
        outcomes.append({
            "pair_id":p["id"],
            "factor":p["single_change_factor"],
            "expected_relation":p["expected_relation"],
            "predicted_relation":"invariant" if predicted_invariant else "changed",
            "relationship_matches_author_expectation":predicted_invariant==expected_invariant,
            "variant_labels_matching_author_reference":correct_count,
            "variant_count":2,
            "source_quotes_located":sum(r["source_quote_located"] for r in (a,b)),
            "source_location_not_equivalent_to_semantic_support":True,
        })
    by_factor=defaultdict(list)
    for outcome in outcomes:
        by_factor[outcome["factor"]].append(outcome)
    return {
        "status":"SMALL PREDECLARED SYNTHETIC PAIR EVALUATION (NOT REAL-WORLD ACCURACY)",
        "model_results_measured":True,
        "challenge_sha256":corpus_sha,
        "pairs":len(outcomes),
        "genuine_provider_records":len(predictions),
        "relation_matches_author_expectation":sum(x["relationship_matches_author_expectation"] for x in outcomes),
        "variant_label_matches_author_reference":sum(x["variant_labels_matching_author_reference"] for x in outcomes),
        "source_quotes_located":sum(x["source_quotes_located"] for x in outcomes),
        "by_change_factor":[{"factor":key,
                             "pairs":len(v),
                             "relation_matches_author_expectation":sum(x["relationship_matches_author_expectation"] for x in v)}
                            for key,v in sorted(by_factor.items())],
        "per_pair":outcomes,
        "new_model_calls_in_metric_runner":0,
        "limitations":[
            "Author-defined fictional CV labels; not independent or real-world hiring data",
            "Pair invariance is not equivalent to per-criterion correctness",
            "Located page quotes are not automatically semantically sufficient",
            "Do not infer hiring fairness from changing two fictional names",
            "No multi-pass selective retries; failures must be retained",
        ],
    }

def main():
    corpus,sha=load_corpus()
    report=evaluate(load_predictions(),corpus,sha)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="per_pair"},indent=2))

if __name__=="__main__":
    main()
