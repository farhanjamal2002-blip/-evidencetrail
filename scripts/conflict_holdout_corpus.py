"""Separately authored, locked two-page fictional CV holdout.

Five NEW job families, four styles each, 80 predetermined requirement labels.
No references to the previous evaluation's sectors, evidence text or gold labels.
The cases are synthetic (not independently annotated by hiring experts).
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import fitz

from scripts.hard_cv_corpus import render_pdf

ROLES = [
    {
        "code": "aviation",
        "title": "Airline Turnaround Operations Supervisor",
        "criteria": [
            "Personally signed off flight turnaround load sheets.",
            "Led airline ground-safety occurrence investigations.",
            "Configured reservation inventory rules in Amadeus.",
            "Delivered practical de-icing safety training to ground crews.",
        ],
        "direct": [
            "I checked aircraft weights and signed the final turnaround load sheet before dispatch for every assigned departure.",
            "I led two ground-safety occurrence investigations, interviewed witnesses and submitted corrective findings.",
            "I personally configured Amadeus reservation-inventory rules for the airline's seasonal schedule.",
            "I delivered hands-on de-icing safety drills to apron staff and documented individual assessments.",
        ],
        "adjacent": [
            "I gathered load-sheet documents, while a licensed dispatcher performed the final sign-off.",
            "I logged ground incidents in a spreadsheet; an aviation safety officer ran the investigations.",
            "I checked flight inventory displays, but system administrators controlled Amadeus configuration.",
            "I distributed de-icing training timetables; instructors delivered the practical sessions.",
        ],
        "denial": "For this same job I confirmed in my written duty statement that I never signed or approved a turnaround load sheet.",
        "keywords": "Load sheet, air safety, Amadeus configuration and de-icing were topics in an online awareness course.",
    },
    {
        "code": "construction",
        "title": "Construction Project Controls Manager",
        "criteria": [
            "Personally drafted and approved construction change orders.",
            "Updated the live critical-path schedule in Primavera P6.",
            "Led on-site nonconformance corrective-action closures.",
            "Issued formal subcontractor payment certificates.",
        ],
        "direct": [
            "I drafted contract change orders for three site variations and approved them under delegated project authority.",
            "I updated the live Primavera P6 critical-path schedule each Friday and issued revised baseline reports.",
            "I chaired site nonconformance investigations, assigned rework and confirmed signed closure.",
            "I prepared and issued certified subcontractor payment approvals after measuring completed works.",
        ],
        "adjacent": [
            "I logged proposed site variations; the commercial manager drafted and approved every change order.",
            "I read printed P6 schedule reports, while the planning engineer edited the live critical path.",
            "I photographed defective work but the quality engineer led and closed all nonconformances.",
            "I collated subcontractor invoices for review; a quantity surveyor issued payment certificates.",
        ],
        "denial": "I certify that I did not draft or approve any site change orders in the employment period above.",
        "keywords": "Coursework covered change orders, Primavera P6, NCR closures and valuation certificates.",
    },
    {
        "code": "marketing",
        "title": "Digital Campaign Operations Manager",
        "criteria": [
            "Personally administered production Google Ads campaign budgets.",
            "Implemented GA4 event tracking using Google Tag Manager.",
            "Led controlled landing-page A/B tests with outcome analysis.",
            "Negotiated and signed paid influencer partnership agreements.",
        ],
        "direct": [
            "I owned the live Google Ads account budget and changed daily campaign bids within the signed spending cap.",
            "I configured GA4 conversion events inside Google Tag Manager and published the production container.",
            "I designed two landing-page A/B tests, set exposure rules and interpreted the purchase-conversion outcomes.",
            "I negotiated commercial terms and signed influencer partnership agreements for the product launch.",
        ],
        "adjacent": [
            "I exported weekly Google Ads spend charts; the acquisition director controlled campaign budgets.",
            "I read GA4 dashboards but an analytics contractor installed all Tag Manager events.",
            "I proposed landing-page copy; a growth analyst configured and interpreted A/B experiments.",
            "I located influencer contact details and booked calls; a brand director signed all agreements.",
        ],
        "denial": "My documented access was read-only and I never administered a production Google Ads budget during this role.",
        "keywords": "Training handouts mentioned Google Ads, GA4, Tag Manager, A/B testing and influencer agreements.",
    },
    {
        "code": "laboratory",
        "title": "Pharmaceutical Quality Laboratory Lead",
        "criteria": [
            "Validated HPLC assays for pharmaceutical product release.",
            "Approved GMP batch-deviation corrective actions.",
            "Authored ISO 17025 method uncertainty reports.",
            "Led environmental monitoring excursion investigations.",
        ],
        "direct": [
            "I designed and executed HPLC assay validation protocols and signed the analytical method validation report for product release.",
            "I investigated GMP batch deviations, approved the written CAPA plan and signed its effectiveness review.",
            "I authored uncertainty-of-measurement reports for ISO 17025 analytical methods and issued signed reports.",
            "I led investigation of environmental monitoring excursions, documented root cause and approved final closure.",
        ],
        "adjacent": [
            "I filed assay chromatograms; the validation scientist designed and signed HPLC release protocols.",
            "I entered deviation events into the quality log but a qualified person approved CAPA decisions.",
            "I transcribed uncertainty figures into templates; laboratory statisticians authored ISO 17025 reports.",
            "I collected environmental monitoring swabs; the microbiology manager led excursions and corrective reviews.",
        ],
        "denial": "The signed employment scope confirms I never validated an HPLC assay for product release here.",
        "keywords": "My classroom syllabus included HPLC validation, GMP CAPA, ISO 17025 uncertainty and EM excursions.",
    },
    {
        "code": "customersuccess",
        "title": "Enterprise SaaS Customer Success Director",
        "criteria": [
            "Personally negotiated multi-year enterprise software renewals.",
            "Created and deployed Salesforce Flow automations in production.",
            "Led executive quarterly business review presentations.",
            "Owned escalations for live enterprise service outages.",
        ],
        "direct": [
            "I negotiated the three-year renewal price and executed the enterprise software contract with the customer sponsor.",
            "I built Salesforce Flow automations, tested each rule and published them into the live CRM organisation.",
            "I led the quarterly business review with the client COO, presenting adoption results and the next delivery plan.",
            "I owned the enterprise outage escalation bridge, coordinated engineering response and issued customer updates.",
        ],
        "adjacent": [
            "I prepared renewal briefing notes; the account executive negotiated and executed the contract.",
            "I submitted Salesforce automation requests; the CRM admin built and deployed the flows.",
            "I booked executive quarterly review meetings; my director presented the business review.",
            "I monitored outage support tickets but the incident commander owned service escalation decisions.",
        ],
        "denial": "Despite the summary claim, I did not negotiate or execute any multi-year customer renewal in that position.",
        "keywords": "The onboarding workbook contained words such as renewals, Salesforce Flow, QBR and outage escalations.",
    },
]

ARCHETYPES = ("scope_only","different_owner","opposing_cv_claims","keyword_noise")
REFERENCE = {
    "scope_only": ["not_found","not_found","not_found","supported"],
    "different_owner": ["not_found","supported","not_found","not_found"],
    "opposing_cv_claims": ["conflicting","supported","not_found","supported"],
    "keyword_noise": ["not_found","not_found","not_found","not_found"],
}

def build_case(role_idx: int, style_idx: int) -> dict:
    role = ROLES[role_idx]
    style = ARCHETYPES[style_idx]
    direct, adjacent = role["direct"],role["adjacent"]
    if style == "scope_only":
        pages = [
            ["ROLE AND EMPLOYMENT", "2020-2026: Crescent Field Services, Operations Coordinator.",
             "My support work did not include the authorisations held by the full department.",
             adjacent[0], adjacent[1], "These are first-person descriptions of the tasks I actually performed."],
            ["SELECTED ASSIGNMENTS AND SIGNATURES", adjacent[2], direct[3],
             "Only the fourth responsibility listed in this section was executed directly by me.",
             "Training and team outcomes should not be attributed to a single individual."],
        ]
    elif style == "different_owner":
        pages = [
            ["CURRENT DUTIES", "2022-2026: Harbourgate Systems, Senior Associate.",
             "The employer offered services beyond my own delegated remit.",
             adjacent[0], direct[1], "I worked with specialists but did not take their approval authority."],
            ["OTHER TEAM DELIVERABLES", adjacent[2], adjacent[3],
             "Team-wide results below are not personal authority claims.",
             "A supervisor, administrator or specialist led the excluded tasks."],
        ]
    elif style == "opposing_cv_claims":
        pages = [
            ["CAREER ACHIEVEMENTS", "2021-2026: Meridian Group, Department Lead.",
             "The following accomplishment is a claim about my personal duties.",
             direct[0], direct[1], "These responsibilities relate to the same employer and dates."],
            ["SIGNED RESPONSIBILITY RECORD", "The signed statement refers to that exact job and period.",
             role["denial"], direct[3], adjacent[2],
             "The two different accounts of the first responsibility require clarification."],
        ]
    else:
        pages = [
            ["TRAINING-HEAVY PROFESSIONAL SUMMARY", "2023-2026: Silverline Office Services, Support Associate.",
             role["keywords"], "I recognise all four technical expressions, but course exposure is not operational ownership.",
             adjacent[0], adjacent[1]],
            ["PRACTICAL TASKS AND LIMITS", adjacent[2], adjacent[3],
             "The professional specialists, not me, were responsible for these senior duties.",
             "The CV describes observation, coordination and coursework, not authorisation."],
        ]
    expected = list(REFERENCE[style])
    anchors=[]
    for i,status in enumerate(expected):
        if status=="supported":
            anchors.append({"requirement_index":i,"status":status,"anchor":direct[i]})
        elif status=="conflicting":
            anchors.append({"requirement_index":i,"status":status,"anchor":direct[i],
                            "opposing_anchor":role["denial"]})
        else:
            anchors.append({"requirement_index":i,"status":status,"anchor":adjacent[i]})
    return {
        "id":f"HOLD-{role_idx+1:02d}-{style_idx+1:02d}",
        "sector":role["code"],"archetype":style,"job_title":role["title"],
        "criteria":list(role["criteria"]),"pages":deepcopy(pages),
        "expected":expected,"oracle_evidence":anchors,
        "source_type":"independently authored synthetic hiring CV",
    }

def build_all_cases() -> list[dict]:
    return [build_case(a,b) for a in range(len(ROLES)) for b in range(len(ARCHETYPES))]

def verify_reference(case: dict) -> list[str]:
    errs=[]
    raw="\n".join(t for page in case["pages"] for t in page)
    if any(not x.isascii() for page in case["pages"] for x in page):
        errs.append("non-ascii text")
    with fitz.open(stream=render_pdf(case),filetype="pdf") as doc:
        if len(doc)!=2:
            errs.append("wrong page count")
        text="\n".join(page.get_text() for page in doc)
        if len(text)<600:
            errs.append("too little PDF content")
    if len(case["criteria"])!=4 or len(case["expected"])!=4:
        errs.append("incorrect rubric cardinality")
    for item in case["oracle_evidence"]:
        for name in ("anchor","opposing_anchor"):
            v=item.get(name)
            if v and v not in raw:
                errs.append("missing "+name+" for "+str(item["requirement_index"]))
        if item["status"]=="conflicting" and not item.get("opposing_anchor"):
            errs.append("missing contradicting source")
    return errs

def corpus_manifest() -> dict:
    items=build_all_cases()
    assert len(items)==20 and len(set(c["id"] for c in items))==20
    return {
        "schema":"evidencetrail/separate-holdout-fictional-cv/v1",
        "cases":len(items),"criterion_instances":sum(len(c["expected"]) for c in items),
        "sectors":len(ROLES),
        "status_distribution":{
            kind:sum(kind==status for c in items for status in c["expected"])
            for kind in ("supported","not_found","conflicting")
        },
        "archetypes":{style:sum(c["archetype"]==style for c in items) for style in ARCHETYPES},
        "pdf_sha256_by_case":{
            c["id"]:hashlib.sha256(render_pdf(c)).hexdigest() for c in items
        },
        "invalid_references":{c["id"]:verify_reference(c) for c in items},
        "caveat":"Newly authored two-page fictional cases, not independent recruiter judgments or real-world population accuracy.",
    }
