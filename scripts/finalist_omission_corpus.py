"""Predeclared new fictional CV tests; never treat these as unbiased real-world labels.

These cases intentionally include missed-support risk, scope limits, apparent
contradictions, unusual wordings, and one OCR-only source page. No API keys.
"""
from dataclasses import dataclass
import hashlib
import json

import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont
import io


@dataclass(frozen=True)
class Case:
    id: str
    family: str
    requirement: str
    cv_text: str
    reference: str
    trap: str
    scanned: bool = False


CASES: tuple[Case, ...] = (
    Case("U01","Procurement","Personally negotiated supplier contract terms",
         "I negotiated prices and terms directly with supplier representatives for 14 purchase agreements.",
         "supported","explicit first-person action"),
    Case("U02","Procurement","Personally negotiated supplier contract terms",
         "I prepared comparison sheets for the procurement director, who alone negotiated and signed all supplier contracts.",
         "not_found","assistant versus owner"),
    Case("U03","Procurement","Personally negotiated supplier contract terms",
         "In 2023 I personally negotiated contract prices. Later clarification: I never negotiated supplier terms in 2023; the director did.",
         "conflicting","explicit opposing first-person claims"),
    Case("U04","Cloud","Operated production Kubernetes clusters",
         "I administered production Kubernetes clusters, managed rollout policies and recovered failed pods.",
         "supported","explicit technical ownership"),
    Case("U05","Cloud","Operated production Kubernetes clusters",
         "I viewed Kubernetes dashboards and reported alerts. The platform team administered the production clusters.",
         "not_found","mere observation"),
    Case("U06","Cloud","Operated production Kubernetes clusters",
         "I was a member of a cloud operations team; our group operated Kubernetes clusters. My individual work was invoice reconciliation.",
         "not_found","group claim versus personal role"),
    Case("U07","Data Engineering","Built scheduled Apache Airflow pipelines",
         "I authored DAGs in Apache Airflow to orchestrate nightly warehouse transformations.",
         "supported","paraphrase pipelines as DAGs"),
    Case("U08","Data Engineering","Built scheduled Apache Airflow pipelines",
         "My colleague operated Airflow. I exclusively maintained spreadsheet reporting and did not develop any DAGs.",
         "not_found","other person owns claimed capability"),
    Case("U09","Cybersecurity","Led incident response investigations",
         "I served as incident commander and directed containment during two ransomware incidents.",
         "supported","semantic ownership with synonym"),
    Case("U10","Cybersecurity","Led incident response investigations",
         "I received incident-response notifications but the SOC led investigation and containment.",
         "not_found","observed not led"),
    Case("U11","Clinical Laboratory","Personally performed quantitative PCR assays",
         "As a lab technician I ran qPCR assays on patient samples and recorded cycle threshold measurements.",
         "supported","qPCR synonym"),
    Case("U12","Clinical Laboratory","Personally performed quantitative PCR assays",
         "I accessioned samples and prepared collection tubes. The molecular team alone performed quantitative PCR assays.",
         "not_found","supporting laboratory work"),
    Case("U13","Construction","Owned project cost forecasting",
         "I maintained the cost-to-complete forecast and presented monthly variance projections to the project director.",
         "supported","forecast synonym"),
    Case("U14","Construction","Owned project cost forecasting",
         "I received the project cost forecast from the controls engineer and uploaded it to the shared drive.",
         "not_found","received versus created"),
    Case("U15","Marketing","Controlled paid search advertising budgets",
         "I allocated Google Ads budget, changed daily bid caps and approved paid search spending.",
         "supported","clear budget authority"),
    Case("U16","Marketing","Controlled paid search advertising budgets",
         "I wrote paid search ad copy. The external agency exclusively controlled campaign budgets and bids.",
         "not_found","creative versus budget owner"),
    Case("U17","Finance","Prepared consolidated IFRS financial statements",
         "I prepared IFRS consolidated financial statements for three subsidiaries and reconciled intercompany balances.",
         "supported","direct source support"),
    Case("U18","Finance","Prepared consolidated IFRS financial statements",
         "I reviewed the group accounts after the controller consolidated them. I never prepared consolidated statements.",
         "not_found","reviewer versus producer"),
    Case("U19","Airport Operations","Coordinated aircraft turnaround ground teams",
         "I coordinated baggage and ramp crews during aircraft turnarounds, assigning teams and resolving gate delays.",
         "supported","direct aviation role"),
    Case("U20","Airport Operations","Coordinated aircraft turnaround ground teams",
         "I worked in airport passenger check-in. Ground turnaround crews were managed by a different department.",
         "not_found","adjacent airport role"),
    Case("U21","Customer Success","Personally managed enterprise SaaS renewals",
         "I led contract renewal discussions and signed the renewal paperwork for six enterprise SaaS accounts.",
         "supported","enterprise account ownership"),
    Case("U22","Customer Success","Personally managed enterprise SaaS renewals",
         "Our team retained SaaS customers, while I handled support tickets; account managers owned renewals.",
         "not_found","team claim without individual action"),
    Case("U23","Public Health","Designed a vaccination outreach program",
         "I designed a mobile vaccination outreach program serving rural clinics and coordinated implementation.",
         "supported","low-resolution OCR page",True),
    Case("U24","Public Health","Designed a vaccination outreach program",
         "I distributed the program flyers after the district officer designed the vaccination outreach plan.",
         "not_found","contributor not author",True),
)


def make_cv_pdf(case: Case) -> bytes:
    doc = fitz.open()
    try:
        if not case.scanned:
            page = doc.new_page(width=612,height=792)
            lines = ["FICTIONAL CV — " + case.id,
                     "All names and claims below are synthetic.", "",
                     "PROFESSIONAL EXPERIENCE", case.cv_text]
            for i, line in enumerate(lines[:-1]):
                page.insert_text((50, 60 + i * 24), line, fontsize=11)
            rect=fitz.Rect(50,185,560,450)
            if page.insert_textbox(rect, case.cv_text,fontsize=11,lineheight=1.4)<0:
                raise ValueError("Could not fit fictional CV: "+case.id)
        else:
            image=Image.new("RGB",(1250,1550),"white")
            draw=ImageDraw.Draw(image)
            font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",25)
            draw.text((85,105),"FICTIONAL CV — "+case.id,fill="black",font=font)
            draw.text((85,160),"All claims are synthetic.",fill="black",font=font)
            # Wrap into consistent 78-character lines to avoid image clipping.
            words=case.cv_text.split()
            chunks=[]; current=""
            for word in words:
                candidate=(current+" "+word).strip()
                if len(candidate)>73 and current:
                    chunks.append(current);current=word
                else:current=candidate
            if current:chunks.append(current)
            for i,text in enumerate(chunks):
                draw.text((85,270+i*48),text,fill="black",font=font)
            image_data=io.BytesIO();image.save(image_data,format="PNG")
            page=doc.new_page(width=612,height=792)
            page.insert_image(page.rect,stream=image_data.getvalue())
        return doc.tobytes(garbage=4,deflate=True)
    finally:
        doc.close()


def manifest_hash() -> str:
    body=json.dumps([vars(c) for c in CASES],sort_keys=True,ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
