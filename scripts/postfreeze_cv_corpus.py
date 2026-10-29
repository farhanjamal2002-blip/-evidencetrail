"""Post-prompt-freeze challenge: sixteen new, two-page fictional CVs.
The expected labels are encoded here BEFORE any inference. Four different
sectors, four writing styles, three requirements each. This is a synthetic
source-quality test, not independent recruiter annotation or a real CV study.
"""
import hashlib
import json
import textwrap
import fitz

DOMAINS=[
  {
   "name":"renewable_energy",
   "job":"Solar Commissioning Supervisor",
   "requirements":[
     "Personally commissioned grid-connected solar inverter systems.",
     "Configured high-voltage protection relays.",
     "Signed off utility grid acceptance certificates.",
   ],
   "direct":[
     "At an eighty-megawatt solar site, I energized and accepted the inverter stations after testing the start-up sequence.",
     "I programmed trip thresholds and protection logic in the substation's 33-kilovolt relays.",
     "I was the authorized signatory who approved the utility's final grid-connection acceptance certificate.",
   ],
   "related":[
     "I maintained the inverter commissioning tracker; licensed electrical engineers performed the energization.",
     "I transcribed relay settings from engineers' notes; I did not configure the protective devices.",
     "I gathered documents for the grid handover; a separate authorized manager signed the acceptance certificate.",
   ],
   "denial":"My signed duties declaration confirms I did not energize or commission solar inverter systems.",
   "noise":"I completed webinar modules covering inverters, protection relays and grid codes.",
  },
  {
   "name":"learning_design",
   "job":"School Curriculum and Assessment Lead",
   "requirements":[
     "Designed a standards-aligned secondary mathematics curriculum.",
     "Led structured classroom observation and coaching reviews.",
     "Evaluated learning progress with pre- and post-intervention tests.",
   ],
   "direct":[
     "I built the algebra and geometry teaching sequence and mapped each unit's outcomes to the national curriculum competencies.",
     "I observed twelve lessons using a classroom rubric, chaired feedback conversations and coached teachers on improvements.",
     "I compared student assessments before and after our tutoring intervention and reported changes by learning outcome.",
   ],
   "related":[
     "I formatted the algebra curriculum templates after teachers had developed and approved all content.",
     "I organized the principal's lesson-observation schedule but never evaluated teachers or led coaching.",
     "I typed student test results into a spreadsheet; an education researcher performed pre/post analysis.",
   ],
   "denial":"The role-scope addendum says I never designed or approved secondary mathematics curriculum content.",
   "noise":"Training completed in learning standards, observation rubrics, mathematics and test-score reporting.",
  },
  {
   "name":"maritime_operations",
   "job":"Port and Fleet Operations Manager",
   "requirements":[
     "Directed dry-dock maintenance work on commercial vessels.",
     "Approved dangerous-goods cargo declarations.",
     "Coordinated ship-to-shore oil-spill containment response.",
   ],
   "direct":[
     "I scheduled the dry-dock repair window for two cargo vessels and directed the contractor work packages through completion.",
     "I reviewed and authorized the dangerous-goods manifest declarations before the hazardous cargo entered the terminal.",
     "When an oil leak occurred alongside the quay, I coordinated containment booms, tugs and port authority notifications.",
   ],
   "related":[
     "I filed dry-dock contractor invoices; marine engineers directed the maintenance work.",
     "I scanned dangerous-goods paperwork; the chief cargo officer alone approved the declarations.",
     "I attended oil-spill drills as an observer; port emergency staff coordinated actual containment.",
   ],
   "denial":"I explicitly confirm that I did not direct any commercial-vessel dry-dock maintenance.",
   "noise":"Completed awareness courses for dry docking, hazardous cargo and spill response.",
  },
  {
   "name":"manufacturing_quality",
   "job":"Manufacturing Quality Engineer",
   "requirements":[
     "Led root-cause investigations into manufacturing defects.",
     "Performed ultrasonic examinations of production welds.",
     "Approved closure of ISO 9001 nonconformance actions.",
   ],
   "direct":[
     "I chaired the eight-discipline defect investigation, tested likely causes and signed the root-cause corrective action report.",
     "I personally inspected production welds using calibrated ultrasonic equipment and recorded the indication maps.",
     "I audited the corrective-action evidence and signed the closeout approval for ISO 9001 manufacturing nonconformities.",
   ],
   "related":[
     "I gathered photographs for defect investigations; the quality manager determined the root cause.",
     "I logged ultrasonic inspection appointments; qualified inspectors conducted all weld examinations.",
     "I maintained the ISO 9001 action tracker; certification managers alone approved closure.",
   ],
   "denial":"My signed job scope says I did not lead manufacturing defect root-cause investigations.",
   "noise":"Awareness courses in root cause analysis, ultrasound testing and ISO 9001 quality processes.",
  },
]
STYLES=("buried_direct","explicit_role_boundaries","contradictory_attestation","training_keyword_noise")
REFERENCES={
 "buried_direct":["supported","supported","supported"],
 "explicit_role_boundaries":["not_found","not_found","not_found"],
 "contradictory_attestation":["conflicting","supported","not_found"],
 "training_keyword_noise":["not_found","not_found","not_found"],
}

def cases():
    output=[]
    for i,d in enumerate(DOMAINS):
        for j,style in enumerate(STYLES):
            if style=="buried_direct":
                pages=[
                  ["CAREER RECORD","Operations specialist, 2021-2026","Managed shift handovers and documentation quality.",
                   "I also handled routine vendor communications, staff logistics and purchase requisitions.",
                   "Work summary: responsibilities are described in the annex."],
                  ["PROJECT ANNEX - COMPLETED ASSIGNMENTS",
                   d["direct"][0],d["direct"][1],d["direct"][2],
                   "All source claims above relate to tasks I personally performed."],
                ]
            elif style=="explicit_role_boundaries":
                pages=[
                  ["PROFESSIONAL HISTORY","Project administrator, 2020-2026",
                   "I worked alongside specialists; the exact boundaries of my assigned tasks follow.",
                   d["related"][0],d["related"][1]],
                  ["JOB-SCOPE STATEMENT",d["related"][2],
                   "I am documenting actual tasks, not claiming responsibility for managers' decisions.",
                   d["noise"]],
                ]
            elif style=="contradictory_attestation":
                pages=[
                  ["PROFILE AND ASSIGNMENTS","Team supervisor, 2022-2026",
                   "My role summary is intended to describe my own responsibilities.",
                   d["direct"][0],d["direct"][1]],
                  ["ADDITIONAL SIGNED SCOPE STATEMENT",d["denial"],
                   "This statement concerns the same engagement described in the career summary.",
                   "Additional work involved training new colleagues and maintaining shift records."],
                ]
            else:
                pages=[
                  ["COURSES AND AREAS OF INTEREST","Administrative assistant, 2023-2026",
                   d["noise"],"I read introductory manuals and watched training recordings.",
                   "My actual job was scheduling visitor access, handling timesheets and filing receipts."],
                  ["WORK HISTORY - RESPONSIBILITY DETAILS",d["related"][0],d["related"][1],d["related"][2],
                   "The cited specialist tasks were the responsibility of other people."],
                ]
            output.append({
              "id":f"POST-{i+1:02d}-{j+1:02d}",
              "domain":d["name"],"style":style,"job":d["job"],
              "criteria":list(d["requirements"]),"expected":list(REFERENCES[style]),
              "pages":pages,
            })
    return output

def render_pdf(c):
    doc=fitz.open()
    for num,segments in enumerate(c["pages"],1):
        page=doc.new_page(width=612,height=792)
        page.insert_text((45,44),f"FICTIONAL RESUME {c['id']} - PAGE {num}",fontsize=11)
        y=82
        for chunk in segments:
            assert chunk.isascii(),(c["id"],chunk)
            for line in textwrap.wrap(chunk,width=82,break_long_words=False) or [""]:
                page.insert_text((45,y),line,fontsize=9.5)
                y+=20
        assert y<755,(c["id"],num,y)
    data=doc.tobytes(garbage=4,deflate=True)
    doc.close()
    return data

def manifest():
    cs=cases()
    assert len(cs)==16 and len({x["id"] for x in cs})==16
    hashes={}
    for c in cs:
        pdf=render_pdf(c)
        with fitz.open(stream=pdf,filetype="pdf") as doc:
            assert len(doc)==2
            assert all(len(p.get_text("text"))>100 for p in doc)
        hashes[c["id"]]=hashlib.sha256(pdf).hexdigest()
    return {
      "schema":"evidencetrail/postfreeze-synthetic-challenge/v1",
      "cases":len(cs),"requirements":sum(len(c["criteria"]) for c in cs),
      "sectors":[d["name"] for d in DOMAINS],
      "styles":list(STYLES),
      "reference_distribution":{k:sum(s==k for c in cs for s in c["expected"])
                                 for k in ("supported","not_found","conflicting")},
      "sha256":hashes,
      "limitations":"New after prompt freeze, but still model-author-created synthetic references, not independent expert labels.",
    }
