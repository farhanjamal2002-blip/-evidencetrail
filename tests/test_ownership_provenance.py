"""Frozen author-labelled source-ownership shadow diagnostic; no Meta API."""
import unittest
from copy import deepcopy
from ownership_provenance import ownership_warning, audit_verified_findings
from scripts.finalist_omission_corpus import CASES


class OwnershipProvenanceTests(unittest.TestCase):
    def test_no_automatic_candidate_decision_or_label(self):
        finding={
          "id":"R1","requirement":"Personally negotiated supplier contract terms",
          "status":"supported","raw_status":"supported",
          "evidence":[{"role":"supports","quote":
            "I prepared comparison sheets. The procurement director alone negotiated supplier contracts.",
            "page":1,"source_id":"R1-Q1"}],
        }
        original=deepcopy(finding)
        warnings=audit_verified_findings([finding])
        self.assertEqual(finding,original)
        self.assertEqual(len(warnings),1)
        self.assertTrue(warnings[0]["human_review_required"])
        self.assertIsNone(warnings[0]["asserted_qualification"])
        self.assertEqual(warnings[0]["page"],1)

    def test_malformed_or_unverified_citations_cannot_create_warning(self):
        for ev in [
            {"role":"supports","quote":"The director negotiated.","page":0},
            {"role":"supports","quote":"The director negotiated.","page":True},
            {"role":"unknown","quote":"The director negotiated.","page":1},
            {"role":"supports","quote":"","page":1},
        ]:
            self.assertEqual(audit_verified_findings([{
                "id":"R1","requirement":"Personally negotiated supplier contracts",
                "evidence":[ev],
            }]),[])

    def test_independent_first_person_support_cannot_be_overridden_by_team_mentions(self):
        examples=[
            ("Personally negotiated supplier contracts",
             "I personally negotiated supplier contracts alongside the procurement director."),
            ("Operated production Kubernetes clusters",
             "I administered production clusters. The wider platform team also handled incidents."),
            ("Designed vaccination outreach program",
             "I designed the vaccination outreach program; the district officer approved it."),
            ("Controlled paid search advertising budgets",
             "I allocated the advertising budget and the agency wrote ad copy."),
        ]
        for requirement,quote in examples:
            with self.subTest(quote=quote):
                self.assertIsNone(ownership_warning(requirement,quote))

    def test_shadow_flags_explicit_third_party_or_first_person_denial(self):
        examples=[
            ("Personally negotiated supplier contract terms",
             "I prepared comparison sheets for the director, who alone negotiated supplier contracts."),
            ("Operated production Kubernetes clusters",
             "I viewed Kubernetes dashboards. The platform team administered production clusters."),
            ("Built scheduled Apache Airflow pipelines",
             "My colleague operated Airflow. I only maintained spreadsheet reports."),
            ("Led incident response investigations",
             "I received notifications but the SOC led the investigations."),
            ("Prepared consolidated IFRS financial statements",
             "I reviewed the statements after the controller consolidated them."),
            ("Designed a vaccination outreach program",
             "I distributed the flyers after the district officer designed the outreach program."),
        ]
        for requirement,quote in examples:
            with self.subTest(quote=quote):
                self.assertIsNotNone(ownership_warning(requirement,quote))

    def test_historical_muse_citations_have_stable_criterion_identifiers(self):
        from demo20_workflow import _load_verified_recording
        from copy import deepcopy
        raw=_load_verified_recording()
        before=deepcopy(raw)
        known={"ET-005","ET-007","ET-015"}
        flagged={}
        for applicant in raw["results"]:
            warnings=audit_verified_findings(applicant["requirements"])
            if warnings:
                flagged[applicant["id"]]=warnings
                self.assertTrue(all(
                    str(w.get("requirement_id","")).startswith("R")
                    and w.get("page",0)>=1 for w in warnings
                ))
        self.assertTrue(known.issubset(flagged))
        self.assertEqual(raw,before,"Never alter immutable historical Meta results")

    def test_entire_author_frozen_corpus_reports_counts_without_relabeling(self):
        positive=[c for c in CASES if c.reference=="supported"]
        negative=[c for c in CASES if c.reference=="not_found"]
        flagged_positive=[c.id for c in positive
                          if ownership_warning(c.requirement,c.cv_text)]
        flagged_negative=[c.id for c in negative
                          if ownership_warning(c.requirement,c.cv_text)]
        # False alarms are release-blocking; incomplete coverage is disclosed.
        self.assertEqual(flagged_positive,[])
        self.assertGreaterEqual(len(flagged_negative),7)
        self.assertEqual(len(CASES),24)


if __name__=="__main__":
    unittest.main()
