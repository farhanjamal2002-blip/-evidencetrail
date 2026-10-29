"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const C=require("../static/coverage_matrix.js");
const direct={status:"supported",evidence_type:"direct"};
const related={status:"not_found",evidence_type:"related"};
const limited={status:"not_found",evidence_type:"unsupported",review_reason_code:"explicit_scope_limit_not_contradiction"};
const absent={status:"not_found",evidence_type:"unsupported",review_reason_code:"document_absence_not_contradiction"};
const missing={status:"not_found",evidence_type:"unsupported"};
const conflict={status:"conflicting",evidence_type:"conflicting"};
const r=(...requirements)=>({requirements});
const row=(id,state="ready")=>({id,state});
const coverage=(value)=>C.coverage(value,4);

test("all four directly documented -> complete (not candidate worth)",()=>{
 const v=coverage(r(direct,direct,direct,direct));
 assert.equal(v.group,"complete");
 assert.deepEqual(v.signals,["direct","direct","direct","direct"]);
 assert.equal(v.counts.direct,4);
});
test("related work and explicit scope limits are never direct proof",()=>{
 const v=coverage(r(direct,related,limited,absent));
 assert.equal(v.group,"partial");
 assert.deepEqual(v.signals,["direct","related","related","related"]);
 assert.equal(v.counts.direct,1);
});
test("unknown qualifications remain missing, not a negative candidate decision",()=>{
 const v=coverage(r(missing,missing,missing,missing));
 assert.equal(v.group,"attention");
 assert.equal(v.counts.missing,4);
 assert.equal("recommendation" in v,false);
});
test("any documented discrepancy requires human clarification regardless of other coverage",()=>{
 const v=coverage(r(direct,direct,direct,conflict));
 assert.equal(v.group,"attention");
 assert.equal(v.signals[3],"discrepancy");
});
test("related-only evidence is partial rather than failed",()=>{
 assert.equal(coverage(r(related,related,related,related)).group,"partial");
});
test("truncated or malformed model outcomes cannot count as complete",()=>{
 const v=coverage(r(direct,direct),4);
 assert.equal(v.count,4);
 assert.deepEqual(v.signals,["direct","direct","missing","missing"]);
 assert.equal(v.group,"partial");
});
test("unverified or missing CV analysis stays in a separate pending group",()=>{
 assert.equal(C.groupFor(row("ET-001","not_analyzed"),undefined,4),"pending");
 assert.equal(C.groupFor(row("ET-001","failed"),null,4),"failed");
 assert.equal(C.coverage({requirements:[]},4).group,"attention");
});
test("conflicting outranks misleading related evidence for attention category",()=>{
 assert.equal(coverage(r(related,conflict,direct,direct)).group,"attention");
});
test("sort groups deterministically and preserve original arrival order within each",()=>{
 const incoming=[row("F","failed"),row("A"),row("P1"),row("C2"),row("P2"),row("C1"),row("U","not_analyzed")];
 const results=new Map([
  ["A",r(conflict,missing,missing,missing)],
  ["P1",r(direct,related,missing,missing)],
  ["C2",r(direct,direct,direct,direct)],
  ["P2",r(related,direct,missing,missing)],
  ["C1",r(direct,direct,direct,direct)]
 ]);
 const ordered=C.sortStable(incoming,results,4);
 assert.deepEqual(ordered.map(x=>x.row.id),["C2","C1","P1","P2","A","U","F"]);
 assert.deepEqual(ordered.map(x=>x.group),["complete","complete","partial","partial","attention","pending","failed"]);
 assert.deepEqual(incoming.map(x=>x.id),["F","A","P1","C2","P2","C1","U"]);
});
test("classification does not modify raw provider source or invent model calls",()=>{
 const input=r({status:"not_found",raw_status:"conflicting",evidence_type:"related"},direct,missing,missing);
 const original=JSON.stringify(input);
 const v=coverage(input);
 assert.equal(v.group,"partial");
 assert.equal(JSON.stringify(input),original);
 assert.equal("score" in v,false);
});
test("historic genuine Muse replay is processable without any model call",()=>{
 const file=path.join(__dirname,"..","data","demo20_muse_replay.json");
 const saved=JSON.parse(fs.readFileSync(file,"utf8"));
 assert.equal(saved.results.length,20);
 assert.equal(saved.fictional_only,true);
 const counts={complete:0,partial:0,attention:0};
 for(const item of saved.results){
  assert.ok(item.receipt);
  assert.equal(item.requirements.length,4);
  const bucket=coverage(item);
  assert.equal(bucket.signals.length,4);
  counts[bucket.group]++;
 }
 assert.equal(Object.values(counts).reduce((a,b)=>a+b,0),20);
});
