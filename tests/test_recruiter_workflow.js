const assert = require("node:assert/strict");
const test = require("node:test");
const wf = require("../static/recruiter-workflow.js");

const result = {
  requirements: [
    {id:"R1",requirement:"Personally negotiated supplier contracts",
     status:"not_found",evidence_type:"unsupported",certainty:"ambiguous",
     evidence:[{quote:"Manager negotiated contracts",page:2}],
     follow_up_question:"Which contract terms did you personally negotiate?"},
    {id:"R2",requirement:"SAP MM purchase orders",status:"supported",
     evidence_type:"direct",certainty:"clear",evidence:[{quote:"I issued purchase orders",page:1}]},
  ],
};

test("tasks originate only in unresolved evidence, never qualifications or automated decisions", () => {
  const task = wf.createFollowUp("ET-005",result,0,"2026-10-30T10:00:00Z");
  assert.equal(task.status,"draft");
  assert.equal(task.requirement_id,"R1");
  assert.match(task.question,/Which contract terms/);
  assert.equal(wf.createFollowUp("ET-001",{requirements:[
    {id:"R1",status:"supported",evidence_type:"direct",certainty:"clear"}
  ]},0),null);
});

test("manually marked sent is explicit; copying message does not send anything", () => {
  const draft=wf.createFollowUp("ET-005",result,0);
  assert.equal(draft.manually_marked_sent,false);
  assert.match(wf.messageFor(draft,"Procurement Lead"),/Hello,/);
  const updated=wf.updateFollowUp(draft,{status:"waiting_external"},"2026-10-30T10:01:00Z");
  assert.equal(updated.manually_marked_sent,true);
  assert.equal(draft.status,"draft");
  assert.equal(wf.reviewStage("ET-005",result,null,updated),"waiting_external");
  assert.equal(wf.reviewStage("ET-005",result,{action:"Hold"},updated),"human_decided");
});

test("follow-up revisions validate input and have no model dependency", () => {
  const draft=wf.createFollowUp("ET-005",result,0);
  assert.throws(()=>wf.updateFollowUp(draft,{status:"automatically_rejected"}),/Invalid/);
  assert.throws(()=>wf.updateFollowUp(draft,{question:""}),/question/);
  assert.equal(wf.updateFollowUp(draft,{comment:"Needs source clarification"}).comment,
    "Needs source clarification");
});

test("workflow CSV neutralizes spreadsheet formula injection", () => {
  const items=[{id:"ET-005"}];
  const results=new Map([["ET-005",{...result,saved_replay:true}]]);
  const followups=new Map([["ET-005",{...wf.createFollowUp("ET-005",result,0),
    question:'=HYPERLINK("https://example.invalid")'}]]);
  const csv=wf.exportWorkflowCsv(items,results,new Map(),followups);
  assert.match(csv,/"'=HYPERLINK/);
  assert.match(csv,/recorded_muse/);
  assert.equal(csv.split("\r\n").length,3);
});

test("review stages preserve received order and do not rank people", () => {
  const items=[{id:"a"},{id:"b"}],results=new Map([["b",result]]);
  const summary=wf.reviewSummary(items,results,new Map(),new Map());
  assert.equal(summary.awaiting_evidence,1);
  assert.equal(summary.needs_clarification,1);
  assert.equal(Object.values(summary).reduce((a,b)=>a+b,0),2);
});

test("interview prep is criteria-first and never scores or rejects applicants", () => {
  const kit=wf.buildInterviewKit("ET-005","Procurement Lead",result);
  assert.equal(kit.questions.length,2);
  assert.equal(kit.questions[0].source_pages[0],2);
  assert.match(kit.questions[0].question,/personal role/);
  assert.match(wf.interviewKitText(kit),/HUMAN INTERVIEW PREP/);
  assert.equal(wf.buildInterviewKit("ET-005","Role",null),null);
  assert.equal(kit.questions.some(q => "score" in q || "rank" in q),false);
});

test("candidate reply is self-attested, time stamped, and cannot silently become verified", () => {
 const task=wf.createFollowUp("ET-005",result,0,"2026-10-30T08:00:00Z");
 assert.throws(()=>wf.updateFollowUp(task,{status:"resolved"}),/actual reply/);
 const received=wf.updateFollowUp(task,{
   status:"resolved",
   candidate_reply:"I observed negotiations but never signed a supply agreement.",
 },"2026-10-30T08:10:00Z");
 assert.equal(received.status,"resolved");
 assert.equal(received.reply_source,"recruiter_pasted_external_candidate_message");
 assert.equal(received.reply_evidence_status,"candidate_self_attested_unverified");
 assert.equal(received.candidate_reply_received_at,"2026-10-30T08:10:00Z");
 assert.equal(task.status,"draft");
 assert.equal(result.requirements[0].status,"not_found");
 const map=new Map([["ET-005",received]]);
 const csv=wf.exportWorkflowCsv([{id:"ET-005"}],new Map([["ET-005",result]]),new Map(),map);
 assert.match(csv,/candidate_self_attested_unverified/);
 assert.match(csv,/I observed negotiations/);
 assert.equal(wf.reviewStage("ET-005",result,null,received),"clarification_received");
});

test("selected outreach is one message, politely asks all selected questions, makes no decisions", () => {
 const first=wf.clarificationFor(result,0);
 const copy=wf.messageForSelectedQuestions([first,{...first,requirement_index:1,question:"Can you confirm your purchase order access?"},first],"Procurement Lead");
 assert.match(copy,/1\. Which contract terms/);
 assert.match(copy,/2\. Can you confirm/);
 assert.match(copy,/rather than assume a missing/i);
 assert.equal(copy.includes(String.raw`\n`),false);
 assert.throws(()=>wf.messageForSelectedQuestions([],"Role"),/Select/);
});
