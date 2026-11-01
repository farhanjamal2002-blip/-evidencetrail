"""Source-based receipt audit: unknown ≠ passed; genuine Meta receipts unchanged."""
from __future__ import annotations
import unittest
from copy import deepcopy
from fastapi.testclient import TestClient
import app
import demo20_workflow as demo
from verification_receipt import build_verification_receipt


class ReceiptTests(unittest.TestCase):
    def test_real_saved_replay_20_cv_receipts_immutable_and_no_new_calls(self):
        raw=deepcopy(demo._load_verified_recording())
        with TestClient(app.app) as client:
            response=client.get("/demo20/recorded-muse")
        self.assertEqual(response.status_code,200,response.text[:300])
        published=response.json()
        self.assertEqual(len(published["results"]),20)
        self.assertEqual(published["successful_quotes"],raw["successful_quotes"])
        self.assertEqual(demo._load_verified_recording(),raw)
        corrections=0
        for old,new in zip(raw["results"],published["results"]):
            receipt=new["verification_receipt"]
            self.assertEqual(receipt["schema"],"evidencetrail/verification-receipt/v1")
            self.assertEqual(receipt["provider"]["response_id"],old["receipt"])
            self.assertEqual(receipt["provider"]["source"],"saved_authentic_replay")
            self.assertEqual(receipt["provider"]["additional_model_calls_for_receipt"],0)
            self.assertTrue(receipt["provider"]["real_muse_response"])
            self.assertEqual(receipt["document"]["cv_sha256"],old["cv_sha256"])
            self.assertTrue(receipt["quote_grounding"]["aggregate_source_audit_consistent"])
            self.assertEqual(receipt["quote_grounding"]["verified"],old["quote_audit"]["verified"])
            self.assertEqual(len(receipt["requirements"]),4)
            self.assertEqual(sum(x["override_applied"] for x in receipt["requirements"]),
                             receipt["semantic_overrides"]["raw_vs_verified_status_changes"])
            corrections+=receipt["semantic_overrides"]["raw_vs_verified_status_changes"]
            for criterion,source in zip(receipt["requirements"],old["requirements"]):
                self.assertEqual(criterion["raw_muse_status"],source["raw_status"])
                for citation in criterion["quote_citations"]:
                    self.assertTrue(citation["source_verified"])
                    self.assertIn(citation["match_method"],(
                        "pymupdf_search_for","normalized_word_span","ocr_page_level_only"
                    ))
                    if citation["match_method"]=="ocr_page_level_only":
                        self.assertIsNone(citation["char_span"])
                        self.assertIsNone(citation["bounding_boxes"])
                    else:
                        self.assertTrue(citation["bounding_boxes"])
                    self.assertEqual(citation["page_dimensions"],{
                        "width":612.0,"height":792.0
                    })
                    self.assertTrue(citation["page"]>=1)
        # 33 new scope-only clarifications + 8 pre-existing verifier gates.
        # Both are genuine raw-to-final deltas; never claim all 41 are the same rule.
        self.assertEqual(corrections,41)
        self.assertEqual(
            published["presentation_calibration"]["counts"]["single_scope_limits_clarified"]
            + published["presentation_calibration"]["counts"]["document_absences_clarified"],
            33,
        )

    def test_real_fictional_scan_and_injection_fixture_do_not_overclaim(self):
        with TestClient(app.app) as client:
            rows={r["id"]:r for r in client.get("/demo20/recorded-muse").json()["results"]}
        scan=rows["ET-019"]["verification_receipt"]
        self.assertEqual(scan["document"]["extraction_mode"],"tesseract_ocr_used")
        self.assertEqual(scan["document"]["ocr_pages"],[1])
        attack=rows["ET-018"]["verification_receipt"]["input_guardrails"]
        self.assertEqual(attack["prompt_injection_scan"]["status"],"not_recorded")
        self.assertEqual(attack["hidden_text_scan"]["status"],"not_recorded")
        self.assertEqual(attack["input_sanitization_check"]["status"],"not_recorded")
        self.assertEqual(rows["ET-018"]["verification_receipt"]["timeline"]["status"],"not_recorded")

    def test_genuine_scope_limit_shows_actual_model_override_not_fabricated_reasoning(self):
        with TestClient(app.app) as client:
            result={r["id"]:r for r in client.get("/demo20/recorded-muse").json()["results"]}
        q=result["ET-008"]["verification_receipt"]["requirements"][2]
        self.assertEqual(q["raw_muse_status"],"conflicting")
        self.assertEqual(q["verified_status"],"not_found")
        self.assertTrue(q["override_applied"])
        self.assertEqual(q["override_reason_code"],"explicit_scope_limit_not_contradiction")
        self.assertEqual(q["quote_citations"][0]["page"],1)
        q15=result["ET-015"]["verification_receipt"]["requirements"][1]
        self.assertFalse(q15["override_applied"])
        self.assertEqual(q15["verified_status"],"conflicting")

    def test_unknown_audits_are_never_inferred_as_security_pass(self):
        payload={
            "provider_mode":"muse","model":"muse-spark-1.3",
            "requirements":[{"requirement":"SAP","raw_status":"supported",
                "status":"not_found","evidence_type":"unsupported",
                "evidence":[{"quote":"Not SAP.","page":1}]}],
            "quote_audit":{"proposed":1,"verified":0,"excluded":1},
            "verification_audit":{},
            "ocr_pages":[],
        }
        receipt=build_verification_receipt(payload)
        self.assertEqual(receipt["quote_grounding"]["aggregate_source_audit_consistent"],False)
        self.assertIsNone(receipt["requirements"][0]["quote_citations"][0]["source_verified"])
        self.assertFalse(receipt["provider"]["real_muse_response"])
        self.assertTrue(receipt["requirements"][0]["override_applied"])
        self.assertEqual(receipt["input_guardrails"]["prompt_injection_scan"]["status"],"not_recorded")

if __name__=="__main__":
    unittest.main()
