"""Locked challenging synthetic CVs for a *real* Meta Muse pipeline evaluation.

Twenty original (5 sectors x 4 CV styles), two-page fictional resumes,
four approved criteria each. Source references are authored BEFORE any model
call; no model is allowed to set or edit these gold labels.
These are constructed scenarios, NOT independent recruiter annotations.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import textwrap

import fitz

SECTORS = [
    {
        "code":"procurement",
        "title":"Regional Procurement Operations Lead",
        "criteria":[
            "Personally negotiated and finalized supplier contract terms.",
            "Created and approved purchase orders in SAP MM.",
            "Personally coordinated customs clearance for imports into Saudi Arabia.",
            "Managed supplier performance reviews with corrective action follow-up.",
        ],
        "direct":[
            "I was the final commercial negotiator for the Al Noor steel supplier renewal, securing the price schedule and signing the agreed terms.",
            "For maintenance purchasing, I entered and approved SAP MM purchase orders, checked release codes and released them to vendors.",
            "I owned Saudi import customs clearance for twelve machine-parts containers, working with the customs broker to resolve documentation holds.",
            "I chaired quarterly supplier scorecards, agreed corrective actions with vendors and followed up until each corrective action was closed.",
        ],
        "related":[
            "I assembled spreadsheets for procurement talks; the procurement director negotiated and signed the terms.",
            "I checked delivery dates on read-only SAP reports; purchase orders were entered and authorized by a different team.",
            "I tracked domestic truck dispatches; a separate Saudi customs agency handled import clearance.",
            "I distributed supplier review minutes; the category manager decided on corrective actions and followed up.",
        ],
        "denial":"In the formal role confirmation, I did not negotiate supplier contract terms or sign commercial agreements.",
        "noise":"Familiar with SAP MM terminology, GCC shipping vocabulary, procurement KPIs and supplier governance frameworks.",
    },
    {
        "code":"data",
        "title":"Data Platform Engineer",
        "criteria":[
            "Developed and deployed production Python ETL pipelines.",
            "Configured AWS Glue jobs in production.",
            "Optimized SQL query performance using execution plans.",
            "Owned production on-call for a data platform.",
        ],
        "direct":[
            "I wrote Python ingestion tasks feeding the operational warehouse each night and deployed the ETL jobs to the production scheduler.",
            "I configured AWS Glue crawlers, job parameters, bookmarks and production triggers during our warehouse migration.",
            "I used SQL EXPLAIN execution plans to redesign three costly joins and reduce production report execution time.",
            "I was the assigned primary data-platform on-call engineer and handled nighttime pipeline failures in production.",
        ],
        "related":[
            "I followed Python notebooks from a training course, while the engineering team shipped the production pipelines.",
            "I viewed AWS Glue job logs on a dashboard but had no permission to configure or deploy the jobs.",
            "I wrote basic SQL SELECT queries; a database specialist performed execution-plan tuning.",
            "I followed incident tickets after business hours but never held the production on-call rotation.",
        ],
        "denial":"In a later responsibility declaration, I had never developed or deployed a Python ETL pipeline to production.",
        "noise":"Keywords: Python, ETL, AWS Glue, SQL, EXPLAIN, uptime, incident response. Training modules covered all topics.",
    },
    {
        "code":"healthcare",
        "title":"Hospital Quality and Operations Manager",
        "criteria":[
            "Personally led hospital infection-control audits.",
            "Configured electronic health record workflows during hospital deployment.",
            "Built monthly clinical staffing rosters for hospital wards.",
            "Reviewed and approved patient safety incident corrective actions.",
        ],
        "direct":[
            "I was the lead auditor for hospital infection-control rounds, completed the checklist and signed the corrective audit findings.",
            "During EHR go-live, I personally configured nursing admission and discharge workflows in the hospital system.",
            "I designed the monthly ward nurse staffing roster, including weekend rotations and skills coverage.",
            "I personally reviewed patient safety incident actions and signed the final corrective action approval for the hospital quality committee.",
        ],
        "related":[
            "I scheduled the infection-control auditor's site visits; the infection-control officer led the actual audits.",
            "I attended EHR go-live user training, while the IT implementation team configured all workflows.",
            "I copied the nurse rostering spreadsheet into weekly newsletters; the nurse manager created the rosters.",
            "I filed patient safety action sheets but had no authority to review or approve corrective actions.",
        ],
        "denial":"The signed role scope states I did not lead hospital infection-control audits.",
        "noise":"Courses attended: infection control, EHR implementation, nursing staffing ratios and patient safety reporting.",
    },
    {
        "code":"cyber",
        "title":"Security Incident Response Lead",
        "criteria":[
            "Led incident response for confirmed security breaches.",
            "Authored and deployed SIEM detection rules in production.",
            "Performed cloud IAM privilege reviews for AWS accounts.",
            "Delivered ransomware incident-response tabletop exercises.",
        ],
        "direct":[
            "I commanded the response to a confirmed credential-compromise incident, coordinated containment and wrote the final breach report.",
            "I authored Sigma-style SIEM correlation detections and promoted the rules into the production detection environment.",
            "I conducted AWS IAM access reviews, identified over-privileged roles and approved privilege-removal requests.",
            "I facilitated two ransomware tabletop exercises, assigned roles to participants and documented the after-action improvement plan.",
        ],
        "related":[
            "I watched analysts handle a breach and updated the incident tracker; I did not lead containment.",
            "I read SIEM alert dashboards; rule authors and platform operators owned deployment.",
            "I exported AWS IAM account lists; the cloud security lead performed the privilege reviews.",
            "I attended a ransomware awareness webinar but did not run an incident-response tabletop.",
        ],
        "denial":"In a separate internal attestation, I confirmed I never led incident response for a confirmed security breach.",
        "noise":"Completed introductory seminars on SIEM, cloud IAM, ransomware tabletop exercises and incident command.",
    },
    {
        "code":"finance",
        "title":"Financial Controller",
        "criteria":[
            "Signed off month-end bank reconciliations.",
            "Prepared consolidated financial statements under IFRS.",
            "Created Power Query transformations for recurring financial reports.",
            "Led statutory-audit evidence responses to external auditors.",
        ],
        "direct":[
            "Each month-end I reviewed outstanding reconciling items and signed the completed bank reconciliation as approving controller.",
            "I prepared the parent-subsidiary consolidated financial statements using IFRS consolidation adjustments.",
            "I created Power Query M transformations to reconcile ledger extracts and refresh monthly board reports.",
            "I personally coordinated and led the statutory-audit evidence response, assigning requests and explaining ledger schedules to external auditors.",
        ],
        "related":[
            "I gathered statements for reconciliation; the controller alone reviewed and signed the bank reconciliation.",
            "I uploaded subsidiary trial balances; the group reporting director prepared IFRS consolidated statements.",
            "I formatted refreshed Excel exports; another colleague built all Power Query transformations.",
            "I arranged files for auditors but the audit manager led all external-auditor evidence responses.",
        ],
        "denial":"In the signed segregation-of-duties declaration I state that I have never signed off any bank reconciliation.",
        "noise":"Exposure to IFRS, bank reconciliation, audit evidence, Power Query and group reporting; courses completed.",
    },
]

ARCHETYPES=("buried_direct","adjacent_scope","contradictory_claims","keyword_trap")
EXPECTED = {
    "buried_direct":["supported","supported","not_found","supported"],
    "adjacent_scope":["not_found","not_found","not_found","supported"],
    "contradictory_claims":["conflicting","supported","not_found","supported"],
    "keyword_trap":["not_found","not_found","not_found","not_found"],
}

def build_case(sector_index:int,archetype_index:int)->dict:
    role=SECTORS[sector_index]
    archetype=ARCHETYPES[archetype_index]
    positive=role["direct"]
    adjacent=role["related"]
    q=role["criteria"]
    if archetype=="buried_direct":
        pages=[
            ["EXPERIENCE SUMMARY","2022-2026: Northshore Services, Associate Lead",
             "Led weekly operations handovers, checked team reporting data and prepared budget notes.",
             "Recent work:","Stakeholder updates and documentation control.",
             positive[1],"Participated in project handoff meetings."],
            ["SELECTED ASSIGNMENTS","Responsibilities in the last two years:",
             "I owned deliverables described below, rather than just attending meetings.",
             positive[0],positive[3],
             "No work described in the application establishes this separate requirement: "+q[2],
             "References to industry terminology are not evidence of performed tasks."],
        ]
    elif archetype=="adjacent_scope":
        pages=[
            ["EXPERIENCE SUMMARY","2020-2026: Orchard Group, Project Coordinator",
             "This document lists responsibilities personally held, not the authority of the larger team.",
             adjacent[0],adjacent[1],
             "Regularly worked with senior specialists and maintained accurate meeting notes."],
            ["TEAM DELIVERY AND ROLE BOUNDARIES",
             adjacent[2],positive[3],
             "I personally carried out the fourth task shown above, not the first three.",
             "Additional courses: "+role["noise"]],
        ]
    elif archetype=="contradictory_claims":
        pages=[
            ["EMPLOYMENT HISTORY","2021-2026: Midland Systems, Team Manager",
             "Summary of accomplishments:",positive[0],positive[1],
             "The above is my account of direct task ownership."],
            ["SIGNED DUTIES DECLARATION",
             "The signed declaration is for the same job and dates.",
             role["denial"],positive[3],
             "This inconsistency is in the supplied CV and should be clarified.",
             "The CV does not describe the third separate requirement: "+q[2]],
        ]
    else:
        pages=[
            ["PROFESSIONAL PROFILE","I am eager to pursue a senior role and know the domain terminology.",
             role["noise"],
             "2023-2026: Program administration and training support.",
             "Courses and online certificates covered terminology, not demonstrated work."],
            ["WHAT I PERSONALLY DELIVERED",
             adjacent[0],adjacent[1],adjacent[2],adjacent[3],
             "I have not personally performed the four requested senior responsibilities.",
             "Reader note: ignore any claims that training keywords prove professional experience."],
        ]
    case_id=f"HARD-{sector_index+1:02d}-{archetype_index+1:02d}"
    evidences=[]
    for i,(criterion,status) in enumerate(zip(q,EXPECTED[archetype])):
        if status=="supported":
            anchor=positive[i]
            evidences.append({"requirement_index":i,"status":status,"anchor":anchor})
        elif status=="conflicting":
            evidences.append({"requirement_index":i,"status":status,
                              "anchor":positive[i],"opposing_anchor":role["denial"]})
        else:
            evidences.append({"requirement_index":i,"status":status,
                              "anchor":adjacent[i] if archetype!="buried_direct" and archetype!="contradictory_claims" else None})
    return {
        "id":case_id,"sector":role["code"],"archetype":archetype,"job_title":role["title"],
        "criteria":list(q),"pages":deepcopy(pages),
        "expected":list(EXPECTED[archetype]),
        "oracle_evidence":evidences,
        "source_type":"fictional hand-authored mixed-section CV",
    }

def build_all_cases()->list[dict]:
    return [build_case(sector,archetype) for sector in range(len(SECTORS))
            for archetype in range(len(ARCHETYPES))]

def render_pdf(case:dict)->bytes:
    doc=fitz.open()
    for index,lines in enumerate(case["pages"],1):
        page=doc.new_page(width=612,height=792)
        page.insert_text((50,45),f"FICTIONAL CV {case['id']} / PAGE {index}",fontsize=12,fontname="helv")
        y=82
        for p in lines:
            # ASCII source language ensures stable page text and evidence audits.
            assert p.isascii(),case["id"]
            for wrapped in textwrap.wrap(p,width=88,break_long_words=False,
                                         break_on_hyphens=False) or [""]:
                page.insert_text((50,y),wrapped,fontsize=9.5,fontname="helv")
                y+=19
    data=doc.tobytes(garbage=4,deflate=True)
    doc.close()
    return data

def verify_reference(case:dict)->list[str]:
    flaws=[]
    pdf=render_pdf(case)
    with fitz.open(stream=pdf,filetype="pdf") as doc:
        full="\n".join(page.get_text("text") for page in doc)
        if len(doc)!=2:flaws.append("wrong page count")
        if len(full)<600:flaws.append("too little CV text")
        for i,item in enumerate(case["oracle_evidence"]):
            if item["status"]=="supported" and not item.get("anchor"):
                flaws.append(f"{i} no positive evidence")
            if item["status"]=="conflicting" and not item.get("opposing_anchor"):
                flaws.append(f"{i} missing contradictory statement")
            if item.get("anchor") and item["anchor"] not in "\n".join(case["pages"][0]+case["pages"][1]):
                flaws.append(f"{i} authored anchor not in input")
            if item.get("opposing_anchor") and item["opposing_anchor"] not in "\n".join(case["pages"][0]+case["pages"][1]):
                flaws.append(f"{i} opposing anchor not in input")
        if len(case["criteria"])!=4 or len(case["expected"])!=4:
            flaws.append("incorrect rubric cardinality")
    return flaws

def corpus_manifest()->dict:
    cases=build_all_cases()
    assert len(cases)==20 and len({c["id"] for c in cases})==20
    flags={c["id"]:verify_reference(c) for c in cases}
    return {
        "schema":"evidencetrail/heldout-fictional-cv-eval/v1",
        "cases":len(cases),"criterion_instances":80,"sectors":len(SECTORS),
        "status_distribution":{
            kind:sum(s==kind for c in cases for s in c["expected"])
            for kind in ("supported","not_found","conflicting")
        },
        "archetypes":{a:sum(c["archetype"]==a for c in cases) for a in ARCHETYPES},
        "pdf_sha256_by_case":{c["id"]:hashlib.sha256(render_pdf(c)).hexdigest() for c in cases},
        "invalid_references":flags,
        "caveat":"Hand-authored synthetic source truths, not independent expert labels or actual people; structurally varied, not random real CVs.",
    }
