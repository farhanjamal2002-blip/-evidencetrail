"""Reproducible counterbalanced fictional recruiter pilot assignment generator.

Produces a study packet, NOT observed results. Uses 12 existing synthetic CVs
in six matched difficulty pairs; four volunteer reviewers see six CVs each
(three manual, three assisted). Each CV is shown to 2 different reviewers,
once in each condition. No reviewer ever sees the same CV in both conditions.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT=Path("artifacts/recruiter-human-pilot")
PAIRS=[
    ("ET-001","ET-002","Direct documented evidence"),
    ("ET-005","ET-006","Adjacent responsibility / role scope"),
    ("ET-008","ET-009","Partial evidence"),
    ("ET-013","ET-014","Keyword-only / no employment evidence"),
    ("ET-015","ET-016","Conflicting CV statements"),
    ("ET-019","ET-020","Image-only scanned CV"),
]
CRITERIA=[
    "Documented supplier procurement experience of at least eight years",
    "Personally led supplier price negotiations and commercial contracts",
    "Personally used SAP MM for purchase orders and procurement records",
    "Personally coordinated GCC cross-border supplier shipments",
]
BASE="https://evidencetrail-judge-rc1-2026.onrender.com"


def assignments():
    rows=[]
    for reviewer in range(4):
        for group,(left,right,label) in enumerate(PAIRS):
            chosen_left=(reviewer % 2)==(group % 2)
            candidate=left if chosen_left else right
            assisted=(reviewer in (0,3)) != (group % 2 == 0)
            condition="assisted" if assisted else "manual"
            rows.append({
                "reviewer_code":f"R{reviewer+1:02d}",
                "task_order":group+1,
                "case_pair":group+1,
                "difficulty":label,
                "condition":condition,
                "candidate_id":candidate,
                "source_pdf":f"{BASE}/demo20/cv/{candidate}",
                "assisted_inbox":f"{BASE}/demo20",
                "criteria":CRITERIA,
                "session_minutes_max":6,
                "record_seconds_including_navigation":True,
                "reference_scores_available_to_reviewer":False,
            })
    assert len(rows)==24
    for reviewer in range(4):
        mine=[r for r in rows if r["reviewer_code"]==f"R{reviewer+1:02d}"]
        assert len(mine)==6 and len({r["candidate_id"] for r in mine})==6
        assert sorted(r["condition"] for r in mine)==["assisted"]*3+["manual"]*3
    for a,b,_ in PAIRS:
        for ident in (a,b):
            present=[r for r in rows if r["candidate_id"]==ident]
            assert len(present)==2 and {r["condition"] for r in present}=={
                "assisted","manual"
            }
    return rows


def packet():
    rows=assignments()
    body=[
        "# EvidenceTrail — exploratory human reviewer pilot",
        "**These are assignments, not results.** All CVs are fictional. "
        "Reviewers must voluntarily agree. Do not use actual applicant data.",
        "Compare active review time and evidence-judgment errors, not candidate rank.",
        "Show the four job criteria verbatim in both conditions. Do not reveal "
        "author-written reference expectations to reviewers.",
        "**Manual:** open only the linked PDF; fill a four-row blank worksheet "
        "with Supported / Not found / Conflicting / Uncertain and a source page.",
        "**Assisted:** open EvidenceTrail's saved genuine Muse inbox, search "
        "for the assigned CV, inspect the original PDF and fill the same worksheet. "
        "Disagreement with the AI is explicitly allowed.",
        "Measure active seconds from opening an applicant until worksheet "
        "completion, including reading/navigating the source. Log timeouts.",
        "Keep reviewer identity coded; do not collect names or personal emails.",
        "Reverse the task order for R02 and R04 to mitigate order effects; "
        "do not change which task has which assigned condition.",
        "Only 4 convenience reviewers are proposed here. Do not generalize "
        "their results to recruitment populations or claim precision.",
    ]
    sections=["\n\n".join(body)]
    for reviewer in ("R01","R02","R03","R04"):
        mine=[r for r in rows if r["reviewer_code"]==reviewer]
        if reviewer in ("R02","R04"):
            mine=list(reversed(mine))
        sections.append("\n## "+reviewer+" — six tasks\n")
        for ordinal,r in enumerate(mine,start=1):
            sections.append(
                f"**Task {ordinal} / pair {r['case_pair']} — {r['difficulty']}**: "
                f"{r['condition'].upper()} — fictional {r['candidate_id']}\n\n"
                f"Original PDF: {r['source_pdf']}\n\n"
                + (f"Assisted inbox: {r['assisted_inbox']} (search {r['candidate_id']})\n\n"
                    if r["condition"]=="assisted" else "")
                + "Time: ____ seconds. Requirement classifications: "
                  "R1 ____ R2 ____ R3 ____ R4 ____. "
                  "Source pages: ____. Notes: ____.\n"
            )
    sections.append(
        "\n## Results logging\n\n"
        "Fields: reviewer_code, candidate_id, condition, task_order, "
        "active_seconds, completed, reviewer_findings, notes. "
        "Independently adjudicated errors must be added only after two people "
        "compare each completed worksheet against the original fictional PDF; "
        "never auto-copy author-generated reference labels."
    )
    return "\n".join(sections),rows


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    markdown, rows=packet()
    (OUT/"reviewer-task-packets.md").write_text(markdown+"\n",encoding="utf-8")
    (OUT/"assignments.json").write_text(json.dumps(rows,indent=2)+"\n")
    print(json.dumps({
        "reviewer_slots":4,"total_tasks":len(rows),
        "distinct_fictional_CVs":len({r["candidate_id"] for r in rows}),
        "human_results_collected":0,"meta_model_calls":0,
        "outputs":["reviewer-task-packets.md","assignments.json"],
    },indent=2))


if __name__=="__main__":
    main()
