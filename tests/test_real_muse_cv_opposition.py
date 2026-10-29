"""Real, source-verified, fictional Muse citations from the post-freeze test.

Keep genuine two-passage CV contradictions; don't conflate an unmet job
requirement with contradictory applicant claims. No extra Muse calls.
"""
import unittest
from copy import deepcopy
from semantic_review import clarify_verified_findings, _first_action_synonyms


def row(requirement, supports, denial):
    return {
        "id":"R1","requirement":requirement,
        "status":"conflicting","effective_status":"conflicting",
        "raw_status":"conflicting","muse_status":"conflicting",
        "evidence_type":"conflicting",
        "timeline_review_flags":[],
        "evidence":[
            {"page":1,"role":"supports","quote":supports},
            {"page":2,"role":"contradicts","quote":denial},
        ],
    }


class TrueContradictionRecoveryTests(unittest.TestCase):
    def test_design_not_misparsed_as_signoff_and_real_conflict_preserved(self):
        self.assertIn("built",_first_action_synonyms(
            "Designed a standards-aligned secondary mathematics curriculum."))
        finding=row("Designed a standards-aligned secondary mathematics curriculum.",
            "I built the algebra and geometry teaching sequence and mapped each unit's outcomes to the national curriculum competencies.",
            "The role-scope addendum says I never designed or approved secondary mathematics curriculum content.")
        old=deepcopy(finding["evidence"])
        audit=clarify_verified_findings([finding])
        self.assertEqual(finding["status"],"conflicting")
        self.assertEqual(finding["raw_status"],"conflicting")
        self.assertEqual(finding["evidence"],old)
        self.assertEqual(audit["multi_quote_discrepancies_retained"],1)

    def test_chaired_is_direct_personal_leadership_and_preserves_real_conflict(self):
        finding=row("Led root-cause investigations into manufacturing defects.",
            "I chaired the eight-discipline defect investigation, tested likely causes and signed the root-cause corrective action report.",
            "My signed job scope says I did not lead manufacturing defect root-cause investigations.")
        audit=clarify_verified_findings([finding])
        self.assertEqual(finding["status"],"conflicting")
        self.assertEqual(finding["review_reason_code"],"multi_claim_or_timeline_discrepancy")
        self.assertEqual(audit["multi_quote_discrepancies_retained"],1)

    def test_just_tracking_a_process_does_not_make_cv_self_contradictory(self):
        finding=row("Led root-cause investigations into manufacturing defects.",
            "I handled investigation tracking notes and filed photographs for the quality manager.",
            "I did not lead the defect investigations; the quality manager owned the decisions.")
        clarify_verified_findings([finding])
        self.assertEqual(finding["status"],"not_found")
        self.assertEqual(finding["raw_status"],"conflicting")
        self.assertNotEqual(finding["status"],"supported")

    def test_genuine_personal_led_and_denial_still_conflicts(self):
        finding=row("Led incident response for confirmed security breaches.",
            "I led the security-breach incident investigation and signed the report.",
            "I never led a confirmed security breach response.")
        clarify_verified_findings([finding])
        self.assertEqual(finding["status"],"conflicting")

    def test_source_has_no_model_call_or_invented_quote(self):
        finding=row("Designed secondary mathematics curricula.",
            "I built a mathematics learning plan and aligned it to required standards.",
            "I never designed secondary maths curricula.")
        source=deepcopy(finding["evidence"])
        clarify_verified_findings([finding])
        self.assertEqual(source,finding["evidence"])


if __name__=="__main__": unittest.main()
