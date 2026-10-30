"""EvidenceTrail reproducible research-method metrics, no API calls or raw CVs.

Only evaluates real supplied reference/prediction JSONL records. Dataset
families and gold-label provenance are reported separately, never pooled.
This is a scoring harness, not an academic benchmark result.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

STATUS = {"supported", "not_found", "conflicting", "refuted"}
PREDICTION = STATUS | {"review_required"}
PROVENANCE = {"author_labelled_synthetic", "independent_blinded",
              "published_external_gold"}
DOMAINS = {"fictional_cv", "contract_nli_transfer", "qasper_transfer",
           "docvqa_transfer", "other_document_transfer"}
ATTRIBUTION = {"supported", "unsupported", "ambiguous", "not_assessed"}
EVIDENCE_FIELDS = ("gold_pages", "cited_pages", "gold_span_ids", "pred_span_ids")
EXAMPLE = "evaluation/academic_metric_inputs.jsonl"
OUT = "artifacts/academic-methods/metric_report.json"


def fraction(numerator: int, denominator: int):
    return round(numerator / denominator, 4) if denominator else None


def _list_unique(value, *, field, numeric=False):
    if not isinstance(value, list):
        raise ValueError(field + " must be a list")
    if numeric:
        if any(type(x) is not int or x < 1 for x in value):
            raise ValueError(field + " requires positive integer PDF pages")
    elif any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(field + " requires non-empty canonical span identifiers")
    if len(value) != len(set(value)):
        raise ValueError(field + " contains duplicates")
    return set(value)


def validate(row: dict, index: int) -> dict:
    if not isinstance(row, dict):
        raise ValueError(f"Row {index} must be an object")
    for key in ("document_id", "criterion_id"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            raise ValueError(f"Row {index} missing {key}")
    for key, choices in (
        ("domain", DOMAINS), ("reference_provenance", PROVENANCE),
        ("gold_status", STATUS), ("predicted_status", PREDICTION),
        ("semantic_attribution", ATTRIBUTION),
    ):
        if row.get(key) not in choices:
            raise ValueError(f"Row {index}: invalid {key}")
    if type(row.get("source_verified")) is not bool:
        raise ValueError(f"Row {index}: source_verified must be an actual boolean")
    if row["domain"] == "contract_nli_transfer" and (
        row["gold_status"] == "conflicting" or row["predicted_status"] == "conflicting"
    ):
        raise ValueError("ContractNLI contradiction is not EvidenceTrail internal conflict")
    if row["domain"] != "fictional_cv" and row["reference_provenance"] == "author_labelled_synthetic":
        raise ValueError("Transfer metrics require separately verified external reference provenance")
    if row["reference_provenance"] == "published_external_gold" and row["domain"] == "fictional_cv":
        raise ValueError("Fictional CV labels cannot masquerade as a published external benchmark")
    if row["semantic_attribution"] in {"supported", "unsupported"} and (
        row["reference_provenance"] == "author_labelled_synthetic"
        and not row.get("attribution_human_reviewed", False)
    ):
        raise ValueError("Author-labelled automatic checks are not human AIS annotations")
    if "attribution_human_reviewed" in row and type(row["attribution_human_reviewed"]) is not bool:
        raise ValueError("attribution_human_reviewed must be boolean")
    data = dict(row)
    for field in EVIDENCE_FIELDS:
        data[field] = _list_unique(row.get(field, []), field=field,
                                   numeric=field.endswith("pages"))
    if data["semantic_attribution"] != "not_assessed" and not data["cited_pages"]:
        raise ValueError("Semantic attribution cannot be assessed without cited source pages")
    if row["source_verified"] and not data["cited_pages"]:
        raise ValueError("Verified page citation cannot be true without an actual page")
    return data


def _metrics(rows: list[dict]):
    if not rows:
        return {"status": "NO ACADEMIC BENCHMARK DATA YET", "total": 0,
                "claims_authorized": False}
    ids=set()
    for i,row in enumerate(rows,1):
        key=(row["document_id"], row["criterion_id"])
        if key in ids:
            raise ValueError("Duplicate document and criterion in same dataset slice")
        ids.add(key)
    def count_gold(g):
        return sum(r["gold_status"] == g for r in rows)
    positives=count_gold("supported")
    negatives=len(rows)-positives
    false_supported=sum(r["predicted_status"]=="supported" and
                        r["gold_status"]!="supported" for r in rows)
    missed_supported=sum(r["gold_status"]=="supported" and
                         r["predicted_status"]!="supported" for r in rows)
    abstentions=sum(r["predicted_status"]=="review_required" for r in rows)
    confusion=Counter((r["gold_status"],r["predicted_status"]) for r in rows)
    tp_pages=pred_pages=gold_pages=0
    tp_spans=pred_spans=gold_spans=0
    support_count=unsafe_count=attribution_count=0
    joint_count=joint_pass=unassessed_supported=0
    for r in rows:
        gold=r["gold_pages"]; pred=r["cited_pages"]
        tp_pages += len(gold & pred)
        pred_pages += len(pred)
        gold_pages += len(gold)
        gs=r["gold_span_ids"]; ps=r["pred_span_ids"]
        tp_spans += len(gs & ps)
        gold_spans += len(gs)
        pred_spans += len(ps)
        if r["semantic_attribution"] in {"supported","unsupported"}:
            attribution_count += 1
            support_count += (r["semantic_attribution"]=="supported")
            unsafe_count += (r["semantic_attribution"]=="unsupported")
        if r["gold_status"] == "supported":
            human_labelled = r.get("attribution_human_reviewed", False) and r["semantic_attribution"] in {"supported", "unsupported", "ambiguous"}
            has_complete_gold = bool(r["gold_pages"]) and bool(r["gold_span_ids"])
            if not human_labelled or not has_complete_gold:
                unassessed_supported += 1
            else:
                joint_count += 1
                joint_pass += (
                    r["predicted_status"] == "supported"
                    and r["source_verified"]
                    and r["gold_pages"].issubset(r["cited_pages"])
                    and r["gold_span_ids"].issubset(r["pred_span_ids"])
                    and r["semantic_attribution"] == "supported"
                )
    per_class={}
    # Five-way prediction vocabulary: review_required is never silently
    # mapped to not_found, especially when legitimate evidence exists.
    for label in sorted(STATUS):
        tp=confusion[(label,label)]
        fp=sum(r["gold_status"]!=label and r["predicted_status"]==label for r in rows)
        fn=sum(r["gold_status"]==label and r["predicted_status"]!=label for r in rows)
        precision=fraction(tp,tp+fp)
        recall=fraction(tp,tp+fn)
        f1=fraction(2*tp,2*tp+fp+fn)
        per_class[label]={"support":count_gold(label),"tp":tp,
                          "fp":fp,"fn":fn,"precision":precision,
                          "recall":recall,"f1":f1}
    return {
        "status": "DESCRIPTIVE DATASET-SPECIFIC RESULTS",
        "claims_authorized": True,
        "total":len(rows),
        "unique_documents":len({r["document_id"] for r in rows}),
        "reference_provenance":rows[0]["reference_provenance"],
        "domain":rows[0]["domain"],
        "confusion":[{"gold":g,"predicted":p,"n":n} for (g,p),n
                     in sorted(confusion.items())],
        "false_support":{"errors":false_supported,"gold_not_supported":negatives,
                         "rate":fraction(false_supported,negatives)},
        "missed_documented_support":{"errors":missed_supported,
                                     "gold_supported":positives,
                                     "rate":fraction(missed_supported,positives)},
        "review_required":{"count":abstentions,"rate":fraction(abstentions,len(rows)),
                           "not_equivalent_to_not_found":True},
        "source_pages":{"matched":tp_pages,"predicted":pred_pages,"gold":gold_pages,
                        "precision":fraction(tp_pages,pred_pages),
                        "recall":fraction(tp_pages,gold_pages)},
        "evidence_span_ids":{"matched":tp_spans,"predicted":pred_spans,"gold":gold_spans,
                             "precision":fraction(tp_spans,pred_spans),
                             "recall":fraction(tp_spans,gold_spans)},
        "human_semantic_attribution":{"assessed":attribution_count,
                                      "supported":support_count,
                                      "unsupported":unsafe_count,
                                      "supported_fraction":fraction(support_count,attribution_count),
                                      "not_counted_when_unassessed":True},
        "joint_supported_answer_and_evidence":{
            "passed":joint_pass,
            "human_assessed_supported_gold":joint_count,
            "unassessed_or_missing_gold_spans":unassessed_supported,
            "rate":fraction(joint_pass,joint_count),
            "rule":"Correct supported label, source verification, all gold pages and spans cited, and human semantic attribution judged supported",
            "adapted_from_citevqa_not_a_citevqa_benchmark_score":True,
        },
        "per_class":per_class,
        "macro_f1_all_comparable_labels":(
            round(sum(per_class[x]["f1"] for x in ("supported","not_found","conflicting"))/3,4)
            if (rows[0]["domain"]=="fictional_cv" and all(
                per_class[x]["f1"] is not None for x in ("supported","not_found","conflicting")
            )) else None
        ),
        "known_limitations":[
            "Missing page evidence is not source-verification success",
            "Page overlap does not prove semantic entailment or external truth",
            "AIS-style support requires independently reviewed annotation",
            "Transfer research domains do not establish real-world hiring reliability",
            "CV criteria within one document are correlated; no simplistic confidence interval",
            "Do not claim a published-paper reproduction without original licensed data and split",
            "No candidate scores, automated decisions, or paid API calls are produced here"
        ],
    }


def evaluate(rows: list[dict]) -> dict:
    if not rows:
        return {"status": "NO ACADEMIC BENCHMARK DATA YET", "total": 0,
                "claims_authorized":False, "domain_results":[]}
    data=[validate(r,i) for i,r in enumerate(rows,1)]
    buckets=defaultdict(list)
    for r in data:
        buckets[(r["domain"],r["reference_provenance"])].append(r)
    # Keep domain and provenance separate, particularly author-built vs
    # independently adjudicated references. No misleading pooled headline.
    for (domain,provenance),group in buckets.items():
        keys=set()
        for r in group:
            key=(r["document_id"],r["criterion_id"])
            if key in keys:
                raise ValueError("Duplicate document + criterion in "+str((domain,provenance)))
            keys.add(key)
    results=[_metrics(group) for _,group in sorted(buckets.items())]
    return {"status":"SEPARATE RESEARCH-SLICE RESULTS",
            "claims_authorized":True,"domains":len(results),
            "total_examples":len(data),
            "no_pooled_accuracy":True,
            "new_meta_requests":0,
            "domain_results":results}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows=[]
    for i,line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError("Malformed JSONL line "+str(i)) from e
    return rows


def main():
    path=Path(sys.argv[1] if len(sys.argv)>1 else EXAMPLE)
    report=evaluate(read_jsonl(path))
    destination=Path(OUT)
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
