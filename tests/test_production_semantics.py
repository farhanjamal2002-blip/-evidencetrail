"""Fail-closed semantic invariants on actual verified findings (no Muse calls)."""
import unittest
from unittest.mock import patch
import app


def finding(status="supported", evidence_type="related", requirement="Led airline safety audits."):
    return {
        "id": "R1",
        "requirement": requirement,
        "status": status,
        "evidence_type": evidence_type,
        "certainty": "clear",
        "note": "This quote exists on the PDF page.",
        "evidence": [{"quote": "Led retail store safety audits.", "role": "supports", "page": 1}],
        "scope_boundary_review": {"final_status": status},
    }


class EvidenceInvariantTests(unittest.TestCase):
    def test_office_procurement_does_not_satisfy_semiconductor_requirement(self):
        row=finding(requirement="Negotiated semiconductor OSAT contracts.")
        with patch.object(app, "MOCK_PROVIDER_ENABLED", False):
            audit=app.enforce_evidence_status_invariants([row],[{
                "requirement":row["requirement"],"status":"supported","evidence_type":"related"
            }])
        self.assertEqual(row["status"],"not_found")
        self.assertEqual(row["evidence_type"],"related")
        self.assertEqual(row["certainty"],"ambiguous")
        self.assertEqual(row["muse_status"],"supported")
        self.assertEqual(row["raw_status"],"supported")
        self.assertEqual(row["effective_status"],"not_found")
        self.assertEqual(row["scope_boundary_review"]["final_status"],"not_found")
        self.assertEqual(len(row["evidence"]),1)
        self.assertEqual(audit["related_supported_demoted"],1)

    def test_retail_safety_does_not_satisfy_airline_safety_criteria(self):
        rows=[finding(requirement="Four years commercial airline safety audits."),
            finding(requirement="Airport runway and aircraft ground safety inspections.")]
        raw=[{"requirement":row["requirement"],"status":"supported"} for row in rows]
        with patch.object(app,"MOCK_PROVIDER_ENABLED",False):
            audit=app.enforce_evidence_status_invariants(rows,raw)
        self.assertTrue(all(r["effective_status"]=="not_found" for r in rows))
        self.assertEqual(audit["related_supported_demoted"],2)

    def test_direct_proof_preserves_positive_and_raw_receipt(self):
        row=finding(evidence_type="direct",requirement="Negotiated semiconductor OSAT contracts.")
        with patch.object(app,"MOCK_PROVIDER_ENABLED",False):
            audit=app.enforce_evidence_status_invariants([row],[{"requirement":row["requirement"],"status":"supported"}])
        self.assertEqual(row["status"],"supported")
        self.assertEqual(row["muse_status"],"supported")
        self.assertEqual(row["effective_status"],"supported")
        self.assertEqual(audit["related_supported_demoted"],0)

    def test_conflict_keeps_conflict(self):
        row=finding(status="conflicting",evidence_type="conflicting")
        with patch.object(app,"MOCK_PROVIDER_ENABLED",False):
            app.enforce_evidence_status_invariants([row],[{"requirement":row["requirement"],"status":"conflicting"}])
        self.assertEqual(row["status"],"conflicting")
        self.assertEqual(row["raw_status"],"conflicting")

    def test_never_fabricates_raw_model_label_if_not_supplied(self):
        row=finding()
        with patch.object(app,"MOCK_PROVIDER_ENABLED",False):
            app.enforce_evidence_status_invariants([row],[])
        self.assertNotIn("raw_status",row)
        self.assertNotIn("muse_status",row)
        self.assertEqual(row["effective_status"],"not_found")

    def test_mock_does_not_claim_real_muse_model_label(self):
        row=finding()
        with patch.object(app,"MOCK_PROVIDER_ENABLED",True):
            app.enforce_evidence_status_invariants([row],[{"requirement":row["requirement"],"status":"supported"}])
        self.assertNotIn("raw_status",row)
        self.assertNotIn("muse_status",row)
        self.assertEqual(row["status"],"not_found")


if __name__=="__main__":
    unittest.main()
