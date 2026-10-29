"""Source-first safety tests: two quotes do not automatically mean CV conflict."""
import unittest
from copy import deepcopy
from semantic_review import clarify_verified_findings

def row(requirement, pairs, flags=None):
    return {
        "requirement":requirement,
        "status":"conflicting","effective_status":"conflicting","raw_status":"conflicting",
        "evidence_type":"conflicting","timeline_review_flags":flags or [],
        "evidence":[{"quote":q,"role":role,"page":1} for q,role in pairs],
    }

class MultiQuoteScopeTests(unittest.TestCase):
    def test_two_limiting_passages_are_not_opposing_cv_claims(self):
        f=row("Personally negotiated and finalized supplier contract terms.",[
          ("I prepared negotiation notes for senior procurement staff.","supports"),
          ("The procurement director negotiated and signed all contract terms.","contradicts")
        ])
        before=deepcopy(f["evidence"])
        a=clarify_verified_findings([f])
        self.assertEqual(a["multi_quote_scope_clarifications"],1)
        self.assertEqual(f["status"],"not_found")
        self.assertEqual(f["raw_status"],"conflicting")
        self.assertEqual(f["evidence"],before)
        self.assertEqual(f["review_reason_code"],"multi_quote_scope_not_internal_contradiction")
        self.assertNotEqual(f["status"],"supported")
    def test_two_negatives_do_not_prove_cv_self_contradiction(self):
        f=row("Configured AWS Glue jobs in production.",[
            ("I viewed the Glue dashboard but had no permission to configure.","contradicts"),
            ("Another team deployed the jobs; I merely checked logs.","contradicts")
        ])
        clarify_verified_findings([f])
        self.assertEqual(f["status"],"not_found")
        self.assertEqual(f["evidence_type"],"unsupported")
    def test_real_opposing_personal_negotiation_claims_preserved(self):
        f=row("Personally led supplier price negotiations and commercial contracts.",[
            ("I personally led supplier commercial negotiations.","supports"),
            ("I never led contract negotiations, my manager did.","contradicts"),
        ])
        a=clarify_verified_findings([f])
        self.assertEqual(f["status"],"conflicting")
        self.assertEqual(a["multi_quote_discrepancies_retained"],1)
    def test_direct_deployed_python_and_explicit_cv_denial_preserved(self):
        f=row("Developed and deployed production Python ETL pipelines.",[
            ("I wrote Python ingestion tasks and deployed them to the production scheduler.","supports"),
            ("In a signed form I had never deployed a Python ETL pipeline to production.","contradicts"),
        ])
        clarify_verified_findings([f])
        self.assertEqual(f["status"],"conflicting")
    def test_lead_audit_and_separate_explicit_denial_preserved(self):
        f=row("Personally led hospital infection-control audits.",[
            ("I was the lead auditor on hospital infection-control rounds.","supports"),
            ("The signed declaration states I did not lead hospital infection-control audits.","contradicts"),
        ])
        clarify_verified_findings([f])
        self.assertEqual(f["status"],"conflicting")
    def test_timeline_red_flags_are_retained_even_if_quotes_are_scope_only(self):
        f=row("Five years of financial controls.",[
            ("I helped reconcile 2024 invoices.","supports"),
            ("The controller approved reconciliations.","contradicts")
        ],flags=[{"code":"contradictory_employment_dates","source":"independent_date_check"}])
        clarify_verified_findings([f])
        self.assertEqual(f["status"],"conflicting")
    def test_unknown_requirement_is_not_cleared_by_heuristic(self):
        f=row("",[
            ("I managed the supplier contracts.","supports"),
            ("I did not manage supplier contracts.","contradicts"),
        ])
        clarify_verified_findings([f])
        self.assertEqual(f["status"],"conflicting")
    def test_local_correction_idempotent_and_source_quotes_stable(self):
        f=row("Authored and deployed SIEM detection rules in production.",[
            ("I read incident dashboard alerts.","supports"),
            ("The engineering team authored all rules.","contradicts"),
        ])
        original=deepcopy(f["evidence"])
        clarify_verified_findings([f]);once=deepcopy(f)
        clarify_verified_findings([f])
        self.assertEqual(f,once)
        self.assertEqual(f["evidence"],original)

if __name__=="__main__":unittest.main()
