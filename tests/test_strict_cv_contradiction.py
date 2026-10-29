"""Conservatively disambiguate JOB-vs-CV gaps from CV-internal contradictions.

All quotations are assumed verified by the existing PDF-source layer.
No model calls, no CV scores, no automatic human hiring decisions.
"""
import unittest
from copy import deepcopy
from semantic_review import clarify_verified_findings


def finding(requirement, affirmative, denial):
    return {
        "id":"R1","requirement":requirement,
        "status":"conflicting","effective_status":"conflicting",
        "raw_status":"conflicting","muse_status":"conflicting",
        "evidence_type":"conflicting","timeline_review_flags":[],
        "evidence":[
            {"page":1,"quote":affirmative,"role":"supports"},
            {"page":2,"quote":denial,"role":"contradicts"},
        ],
    }


class StrictConflictSemantics(unittest.TestCase):
    def test_negotiation_prep_is_not_personal_negotiation_claim(self):
        r=finding("Personally negotiated and finalized supplier contract terms.",
            "I prepared negotiation notes for the director and attended discussions.",
            "I never negotiated or finalized supplier contracts personally.")
        source=deepcopy(r["evidence"])
        clarify_verified_findings([r])
        self.assertEqual(r["status"],"not_found")
        self.assertEqual(r["review_reason_code"],"multi_quote_scope_not_internal_contradiction")
        self.assertEqual(r["raw_status"],"conflicting")
        self.assertEqual(r["evidence"],source)

    def test_handled_is_not_led_substring(self):
        r=finding("Led incident response for confirmed security breaches.",
            "I handled incident response tracking sheets during alerts.",
            "I never led incident response and had no incident command responsibility.")
        clarify_verified_findings([r])
        self.assertEqual(r["status"],"not_found")

    def test_siEM_rule_reader_is_not_rule_author(self):
        r=finding("Authored and deployed SIEM detection rules in production.",
            "I reviewed SIEM rule logs and wrote incident notes.",
            "I never authored any SIEM detections; another team owned all deployment.")
        clarify_verified_findings([r])
        self.assertEqual(r["status"],"not_found")

    def test_genuinely_opposing_negotiator_claims_are_kept(self):
        r=finding("Personally negotiated supplier contract terms.",
            "I personally negotiated pricing for the vendor renewal.",
            "I never personally negotiated any supplier contract terms.")
        clarify_verified_findings([r])
        self.assertEqual(r["status"],"conflicting")
        self.assertEqual(r["review_reason_code"],"multi_claim_or_timeline_discrepancy")

    def test_true_cv_first_person_led_and_denial_is_kept(self):
        r=finding("Led incident response for confirmed security breaches.",
            "I led the security breach response and signed the final report.",
            "I never led a security breach response.")
        clarify_verified_findings([r])
        self.assertEqual(r["status"],"conflicting")

    def test_real_attested_ownership_and_denial_is_kept(self):
        r=finding("Personally negotiated and finalized supplier contract terms.",
            "I was the final commercial negotiator and signed the agreed terms.",
            "I never acted as negotiator for a supplier agreement.")
        clarify_verified_findings([r])
        self.assertEqual(r["status"],"conflicting")

    def test_never_override_verified_timeline_flag(self):
        r=finding("Led incident response for confirmed security breaches.",
            "I handled an incident tracker and never commanded the response.",
            "I did not lead the investigation.")
        r["timeline_review_flags"]=[{"code":"verified_incompatible_dates"}]
        clarify_verified_findings([r])
        self.assertEqual(r["status"],"conflicting")

    def test_no_new_support_from_document_gap(self):
        r=finding("Configured AWS Glue jobs in production.",
            "I watched AWS Glue dashboards and wrote training notes.",
            "I did not configure the Glue jobs and was not granted deployment permissions.")
        clarify_verified_findings([r])
        self.assertEqual(r["status"],"not_found")
        self.assertNotEqual(r["status"],"supported")


if __name__=="__main__":
    unittest.main()
