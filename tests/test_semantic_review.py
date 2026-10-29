"""Fail-closed post-quote verification semantics, no model call or fabricated claims."""
import unittest
from copy import deepcopy
from fastapi.testclient import TestClient
import app
import demo20_workflow as demo
from semantic_review import clarify_verified_findings


def row(quotes, status="conflicting", evidence_type="conflicting", flags=None):
    return {
        "id": "R1", "status": status, "effective_status":status,
        "evidence_type": evidence_type, "raw_status": status, "muse_status": status,
        "note":"Original Muse explanation.", "certainty":"clear",
        "evidence":[{"quote":q,"page":1,"role":role} for q,role in quotes],
        "timeline_review_flags":flags or [],
    }


class SemanticCalibrationTests(unittest.TestCase):
    def test_single_explicit_scope_limit_is_not_internal_cv_contradiction(self):
        finding=row([("Used warehouse management system, not SAP procurement.", "contradicts")])
        result=clarify_verified_findings([finding])
        self.assertEqual(result["single_scope_limits_clarified"],1)
        self.assertEqual(finding["status"],"not_found")
        self.assertEqual(finding["effective_status"],"not_found")
        self.assertEqual(finding["raw_status"],"conflicting")
        self.assertEqual(finding["muse_status"],"conflicting")
        self.assertEqual(finding["review_label"],"Scope not established")
        self.assertEqual(finding["evidence"][0]["display_role"],"scope_context")
        self.assertEqual(len(finding["evidence"]),1)
        self.assertEqual(app.judge_facing_evidence_status(finding),"Scope not established")

    def test_absence_statement_is_not_self_contradiction(self):
        f=row([("No employer negotiation or job-duration evidence was reported.","contradicts")])
        result=clarify_verified_findings([f])
        self.assertEqual(result["document_absences_clarified"],1)
        self.assertEqual(f["review_label"],"Not documented in this CV")
        self.assertEqual(app.judge_facing_evidence_status(f),"Not documented")

    def test_multiple_opposing_claims_remain_for_human_review(self):
        f=row([("I led all supplier contracts.","supports"),
               ("I never led supplier contracts.","contradicts")])
        result=clarify_verified_findings([f])
        self.assertEqual(result["multi_quote_discrepancies_retained"],1)
        self.assertEqual(f["status"],"conflicting")
        self.assertEqual(f["review_label"],"Discrepancy to clarify")
        self.assertEqual(len(f["evidence"]),2)

    def test_two_verified_scope_limits_are_not_internal_contradictions(self):
        f=row([
            ("I assembled supplier comparison notes; my manager negotiated the contracts.", "contradicts"),
            ("I had no authority to approve the supplier contracts.", "contradicts"),
        ])
        before=deepcopy(f["evidence"])
        counts=clarify_verified_findings([f])
        self.assertEqual(f["status"],"not_found")
        self.assertEqual(f["raw_status"],"conflicting")
        self.assertEqual(f["review_reason_code"],"explicit_scope_limit_not_contradiction")
        self.assertEqual(counts["multi_scope_limits_clarified"],1)
        self.assertEqual([q["quote"] for q in f["evidence"]],
                         [q["quote"] for q in before])
        self.assertEqual([q["role"] for q in f["evidence"]],["contradicts","contradicts"])
        self.assertEqual([q["display_role"] for q in f["evidence"]],["scope_context","scope_context"])

    def test_five_distinct_genuine_cv_contradictions_survive(self):
        from scripts.hard_cv_corpus import SECTORS
        self.assertEqual(len(SECTORS),5)
        for sector in SECTORS:
            with self.subTest(sector=sector["code"]):
                f=row([(sector["direct"][0],"supports"),
                       (sector["denial"],"contradicts")])
                quotes=deepcopy(f["evidence"])
                clarify_verified_findings([f])
                self.assertEqual(f["status"],"conflicting")
                self.assertEqual(f["review_reason_code"],"multi_claim_or_timeline_discrepancy")
                self.assertEqual(f["evidence"],quotes)

    def test_independent_timeline_issue_retained_even_with_two_limits(self):
        f=row([("I did not approve vendor contracts.","contradicts"),
               ("My manager signed all vendor agreements.","contradicts")],
              flags=[{"code":"independently_verified_duration_gap"}])
        clarify_verified_findings([f])
        self.assertEqual(f["status"],"conflicting")

    def test_local_timeline_flags_prevent_false_clearance(self):
        f=row([("Only documented role was 2022 to 2026.","contradicts")],flags=[{"code":"duration_gap"}])
        clarify_verified_findings([f])
        self.assertEqual(f["status"],"conflicting")
        self.assertEqual(f["review_label"],"Discrepancy to clarify")

    def test_related_evidence_is_visible_but_not_proof(self):
        f=row([("Processed SAP procurement data without specifying MM.","supports")],status="not_found",evidence_type="related")
        before=deepcopy(f["evidence"])
        counts=clarify_verified_findings([f])
        self.assertEqual(counts["related_context_labeled"],1)
        self.assertEqual(f["status"],"not_found")
        self.assertEqual(f["evidence_type"],"related")
        self.assertEqual(f["evidence"],before)
        self.assertIn("exact requirement unproven",f["review_label"])
        self.assertEqual(app.judge_facing_evidence_status(f),"Related")

    def test_no_verified_citation_does_not_demote_model_or_invent_source(self):
        f=row([("not a checked page","contradicts")])
        f["evidence"][0]["page"]=0
        clarify_verified_findings([f])
        self.assertEqual(f["status"],"conflicting")
        self.assertEqual(f["raw_status"],"conflicting")
        self.assertEqual(f["evidence"][0]["page"],0)

    def test_never_creates_positive_status_or_new_quote(self):
        f=row([("Did not operate SAP MM.","contradicts")])
        once=deepcopy(f)
        clarify_verified_findings([f])
        quote=deepcopy(f["evidence"])
        clarify_verified_findings([f])
        self.assertEqual(f["status"],"not_found")
        self.assertEqual(f["evidence"],quote)
        self.assertEqual(f["raw_status"],once["raw_status"])

    def test_genuine_recording_is_immutable_and_calibration_is_local(self):
        demo._load_verified_recording.cache_clear()
        raw=deepcopy(demo._load_verified_recording())
        with TestClient(app.app) as client:
            response=client.get("/demo20/recorded-muse")
            self.assertEqual(response.status_code,200,response.text[:300])
            actual=response.json()
        self.assertEqual(actual["presentation_calibration"]["model_calls"],0)
        self.assertTrue(actual["presentation_calibration"]["source_recording_unchanged"])
        self.assertEqual(raw,demo._load_verified_recording())
        self.assertEqual(len(actual["results"]),20)
        self.assertEqual(actual["successful_quotes"],raw["successful_quotes"])
        count=0
        for source, calibrated in zip(raw["results"],actual["results"]):
            self.assertEqual(source["receipt"],calibrated["receipt"])
            self.assertEqual(source["cv_sha256"],calibrated["cv_sha256"])
            for previous,item in zip(source["requirements"],calibrated["requirements"]):
                self.assertEqual(previous["raw_status"],item["raw_status"])
                self.assertEqual(previous["evidence"],[
                    {key:v for key,v in quote.items() if key not in ("display_role","evidence_type")}
                    for quote in item["evidence"]
                ])
                self.assertNotEqual(item["status"],"supported") if previous["status"]!="supported" else None
                if previous["status"]=="conflicting" and len(previous["evidence"])==1:
                    self.assertEqual(item["status"],"not_found")
                    count+=1
        self.assertEqual(count,33)
        self.assertEqual(sum(x["status"]=="conflicting" for candidate in actual["results"] for x in candidate["requirements"]),3)
        self.assertEqual(actual["presentation_calibration"]["counts"]["single_scope_limits_clarified"]
                         + actual["presentation_calibration"]["counts"]["document_absences_clarified"],33)


if __name__=="__main__":
    unittest.main()
