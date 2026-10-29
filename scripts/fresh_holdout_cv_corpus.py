"""A fresh, post-fix holdout of 8 manually authored two-page fictional CVs.

Four sectors absent from prior development corpus. Each criterion and reference
label is predeclared without running Meta. NEVER tune semantic_review.py against
this set then claim it remains a held-out evaluation.
"""
import hashlib
import json
import textwrap
import fitz

CASES=[
{
"id":"HOLD-PH-1","sector":"pharmaceutical distribution",
"role":"Pharmaceutical Distribution Quality Supervisor",
"criteria":[
"Investigated cold-chain temperature excursions affecting medicine shipments.",
"Led WHO GDP audit readiness inspections for distribution operations.",
"Used ERP batch traceability to investigate medicine product recalls.",
"Approved corrective action plans for pharmaceutical distribution deviations.",
],
"expected":["supported","supported","not_found","supported"],
"pages":[
["PROFILE: 2019-2026 | distribution quality operations",
"Managed warehouse quality checks, carrier communications and exception logs.",
"On evening shifts I personally investigated temperature excursions for insulin shipments, cross-checking logger records, carrier handoffs and quarantine decisions.",
"Separately completed regular packaging checks and dock audits.",
"Training keywords include batch tracking, ERP, WHO GDP and product recall management."],
["PRINCIPAL ASSIGNMENTS",
"I led WHO Good Distribution Practice inspection-readiness walkthroughs of the wholesale site and owned the resulting audit checklist.",
"The company ERP batch recall-tracing console was accessible to our recall specialist; my role was to send their status emails, not to conduct recall traceability investigations.",
"I signed off distribution deviation CAPA plans after reviewing the evidence and risk assessment.",
"Note: these descriptions distinguish work performed from systems I merely observed."],
],
"anchors":["I personally investigated temperature excursions","I led WHO Good Distribution Practice inspection-readiness walkthroughs",None,"I signed off distribution deviation CAPA plans"],
},
{
"id":"HOLD-PH-2","sector":"pharmaceutical distribution",
"role":"Medicine Warehouse Program Assistant",
"criteria":[
"Investigated cold-chain temperature excursions affecting medicine shipments.",
"Led WHO GDP audit readiness inspections for distribution operations.",
"Used ERP batch traceability to investigate medicine product recalls.",
"Approved corrective action plans for pharmaceutical distribution deviations.",
],
"expected":["not_found","not_found","conflicting","not_found"],
"pages":[
["CAREER OUTLINE: 2022-2026",
"Attended temperature-control seminars and forwarded freezer alarms to the authorized investigation team.",
"A supervising pharmacist conducted every temperature excursion investigation; I maintained the contact roster.",
"WHO GDP was covered in a training presentation. I photographed audit evidence while a quality officer led readiness inspections.",
"CV SUMMARY: I personally used our ERP batch tracing records to lead recall investigations."],
["RESPONSIBILITY DECLARATION",
"For the same job and period, I never had ERP access and never used batch traceability to investigate medicine recalls.",
"My work was dispatch scheduling, document filing and shipment status calls.",
"CAPA approvals were signed by the responsible pharmacist; I did not review or approve deviation action plans.",
"The CV summary and responsibility declaration give incompatible accounts of my ERP recall duties."],
],
"anchors":[None,None,["I personally used our ERP batch tracing records","I never had ERP access"],None],
},
{
"id":"HOLD-RE-1","sector":"renewable power",
"role":"Solar Power Commissioning Engineer",
"criteria":[
"Commissioned grid-connected solar inverters at an operating plant.",
"Configured SCADA telemetry and alarms for an operating power site.",
"Approved site lockout-tagout procedures for high-voltage equipment.",
"Negotiated commercial EPC change order terms with contractors.",
],
"expected":["supported","not_found","supported","not_found"],
"pages":[
["ENGINEERING HISTORY",
"During site acceptance I personally energized and commissioned grid-tied solar inverters after protective relay checks and witnessed acceptance tests.",
"2021-2026: commissioning engineer, operations handovers and maintenance documentation.",
"Installed sensor cables and recorded SCADA display screenshots, while the controls contractor configured all telemetry points and alarms.",
"I completed inverter commissioning checklists and issued punch list actions."],
["SAFETY AND COMMERCIAL TASKS",
"I was the designated approver for HV electrical lockout-tagout isolation procedures and signed the work-permit release.",
"Contract variations were written by project finance. I provided engineering measurements; the EPC commercial director alone negotiated prices and terms.",
"Additional modules completed: SCADA programming, change management, commissioning and safety law.",
"Training does not establish personal responsibility for those other tasks."],
],
"anchors":["I personally energized and commissioned grid-tied solar inverters",None,"I was the designated approver for HV electrical lockout-tagout isolation procedures",None],
},
{
"id":"HOLD-RE-2","sector":"renewable power",
"role":"Renewable Site Controls Technician",
"criteria":[
"Commissioned grid-connected solar inverters at an operating plant.",
"Configured SCADA telemetry and alarms for an operating power site.",
"Approved site lockout-tagout procedures for high-voltage equipment.",
"Negotiated commercial EPC change order terms with contractors.",
],
"expected":["not_found","conflicting","not_found","supported"],
"pages":[
["PROJECT LOG",
"Helped prepare plant acceptance photographs, but a vendor commissioning specialist started and signed off the grid-connected inverters.",
"I wrote and deployed SCADA telemetry points and configured live production alarms at the operating site.",
"The site commissioning log was created by my supervisor.",
"I attended high-voltage lockout training and signed attendance sheets, not approval forms."],
["SIGNED TASK SCOPE",
"For the same assignment, I never configured SCADA telemetry or alarms in production; the controls supplier completed all those changes.",
"Only the electrical authorized person approved high-voltage isolation procedures.",
"Separately, I personally negotiated and settled an EPC contractor change-order pricing amendment, documenting the agreed terms.",
"These two SCADA descriptions are mutually inconsistent in the source document."],
],
"anchors":[None,["I wrote and deployed SCADA telemetry points","I never configured SCADA telemetry"],None,"I personally negotiated and settled an EPC contractor change-order"],
},
{
"id":"HOLD-LE-1","sector":"legal operations",
"role":"Commercial Disputes Associate",
"criteria":[
"Drafted commercial arbitration submissions for filing.",
"Led e-discovery document collection and privilege review.",
"Negotiated software licensing agreements with vendors.",
"Filed pleadings in Dubai courts.",
],
"expected":["supported","supported","not_found","not_found"],
"pages":[
["COMMERCIAL DISPUTES PRACTICE 2020-2026",
"I drafted the statement of claim and written submissions for an international commercial arbitration; the managing partner approved final filing.",
"Tracked arbitration deadlines and liaised with document production vendors.",
"I led the e-discovery collection process, instructed custodians and personally decided the initial privilege-tagging review.",
"Participated in hearings as a legal team researcher."],
["ADJACENT WORK NOT OWNED",
"Software licence negotiations were conducted by the technology procurement lawyer; I extracted clauses and prepared redline comparisons only.",
"I prepared Dubai court research memos but never filed pleadings. Court filings were handled by local litigation counsel.",
"Training included software licensing, court procedure and arbitration drafting.",
"Responsibility boundaries apply to this same period of employment."],
],
"anchors":["I drafted the statement of claim and written submissions","I led the e-discovery collection process",None,None],
},
{
"id":"HOLD-LE-2","sector":"legal operations",
"role":"Litigation Administrative Specialist",
"criteria":[
"Drafted commercial arbitration submissions for filing.",
"Led e-discovery document collection and privilege review.",
"Negotiated software licensing agreements with vendors.",
"Filed pleadings in Dubai courts.",
],
"expected":["not_found","not_found","conflicting","supported"],
"pages":[
["RESPONSIBILITY SUMMARY",
"Prepared indexed bundles and references for arbitration submissions; qualified counsel drafted all pleadings.",
"Distributed e-discovery legal holds while senior associates led the collection and privilege decisions.",
"Commercial licence negotiating authority: I personally negotiated and finalized SaaS vendor pricing, liability language and renewal terms.",
"2023-2026: case coordinator at regional legal services group."],
["ATTESTATION AND COURT WORK",
"In a formal role attestation for that same job, I wrote that I have never negotiated any software licence terms with a vendor.",
"I completed Dubai court electronic filing of civil pleadings through the designated filing account, retained stamped receipts and submitted them to counsel.",
"The licence responsibility summary and signed attestation are incompatible claims.",
"Certificates attended: e-discovery, arbitration, software procurement."],
],
"anchors":[None,None,["I personally negotiated and finalized SaaS vendor pricing","I have never negotiated any software licence terms"],"I completed Dubai court electronic filing of civil pleadings"],
},
{
"id":"HOLD-ED-1","sector":"education technology",
"role":"Learning Technology Coordinator",
"criteria":[
"Built and published Moodle LMS courses for staff training.",
"Led teacher curriculum assessment reviews.",
"Developed individual education support plans for students.",
"Audited examination moderation and grading consistency.",
],
"expected":["supported","supported","supported","not_found"],
"pages":[
["LEARNING DESIGN PORTFOLIO",
"I assembled Moodle learning modules with quizzes and rubrics and personally published the courses on the staff training LMS.",
"During the academic year I led the curriculum assessment review meetings for the science faculty and signed the review findings.",
"Prior role: teaching assistant from 2019 to 2022, then coordinator 2022-2026.",
"Reviewed student learning adjustments with colleagues and documented agreed outcomes."],
["STUDENT SUPPORT AND ASSESSMENT",
"I wrote and implemented individual student education support plans, including accommodation goals and review dates.",
"Exam moderation audits were conducted by the examinations office. I merely circulated the moderation calendar and collected teacher signatures.",
"Familiar with external grading benchmarks and standardization; completed a webinar.",
"Assessment review leadership differs from performing exam moderation audits."],
],
"anchors":["personally published the courses on the staff training LMS","I led the curriculum assessment review meetings","I wrote and implemented individual student education support plans",None],
},
{
"id":"HOLD-ED-2","sector":"education technology",
"role":"Digital School Services Assistant",
"criteria":[
"Built and published Moodle LMS courses for staff training.",
"Led teacher curriculum assessment reviews.",
"Developed individual education support plans for students.",
"Audited examination moderation and grading consistency.",
],
"expected":["not_found","not_found","not_found","conflicting"],
"pages":[
["PROFILE AND SKILLS",
"Used Moodle to upload attachments into courses that the learning designer built and published.",
"Took minutes at teacher curriculum meetings; the department lead chaired assessment review.",
"Assigned appointment times for student support meetings, but SEN coordinators wrote and approved all individual education plans.",
"Learning technology, student accommodation, exam moderation and quality assurance are familiar terminology."],
["SCHOOL OPERATIONS DECLARATION",
"My achievements statement reports: I personally audited external exam moderation and grading consistency across the school.",
"The declaration for that same academic year says I never performed any examination moderation audit, even as a supporting reviewer.",
"I booked rooms, printed examination rosters and attended briefing sessions.",
"These are two mutually incompatible claims about exam-audit ownership."],
],
"anchors":[None,None,None,["I personally audited external exam moderation","I never performed any examination moderation audit"]],
},
]

def pdf_for_case(case:dict)->bytes:
    doc=fitz.open()
    for page_no,lines in enumerate(case["pages"],1):
        page=doc.new_page(width=612,height=792)
        page.insert_text((54,48),f"FICTIONAL TEST CV {case['id']} - PAGE {page_no}",fontsize=12)
        y=87
        for p in lines:
            assert p.isascii(),case["id"]
            for line in textwrap.wrap(p,87,break_long_words=False,break_on_hyphens=False):
                page.insert_text((54,y),line,fontsize=9.3)
                y+=19
    content=doc.tobytes(garbage=4,deflate=True)
    doc.close()
    return content

def manifest()->dict:
    ids=[x["id"] for x in CASES]
    issues=[]
    for case in CASES:
        with fitz.open(stream=pdf_for_case(case),filetype="pdf") as pdf:
            if len(pdf)!=2:issues.append((case["id"],"pages"))
            source="\n".join("\n".join(p) for p in case["pages"])
            if len(source)<450:issues.append((case["id"],"document too short"))
            if len(case["criteria"])!=4 or len(case["expected"])!=4 or len(case["anchors"])!=4:
                issues.append((case["id"],"rubric mismatch"))
            for i,label in enumerate(case["expected"]):
                anchors=case["anchors"][i]
                if label=="supported" and not isinstance(anchors,str):issues.append((case["id"],i,"missing support quote"))
                if label=="conflicting" and (not isinstance(anchors,list) or len(anchors)!=2):
                    issues.append((case["id"],i,"missing opposing quotes"))
                for quote in ([anchors] if isinstance(anchors,str) else anchors or []):
                    if quote not in source:issues.append((case["id"],i,"reference anchor not in authored CV"))
    return {
        "schema":"evidencetrail/unseen-holdout-v1",
        "cases":len(CASES),"criterion_instances":len(CASES)*4,
        "status_distribution":{s:sum(q==s for c in CASES for q in c["expected"]) for s in ("supported","not_found","conflicting")},
        "sources_sha256":{c["id"]:hashlib.sha256(pdf_for_case(c)).hexdigest() for c in CASES},
        "issues":issues,
        "limitations":"Manually authored fictional reference labels, structurally varied from first development corpus but not external human annotation.",
    }
