"""Sanity checks for 1000 distinct, hand-specified policy situations.

The benchmark MUST disclose that its Muse-shaped proposals are injected and
not real Meta calls. Do not present it as a 1000-CV semantic generalization score.
"""
import unittest
from scripts.semantic_policy_benchmark_1000 import create_case,run_suite

class LargePolicyEvaluation(unittest.TestCase):
    def test_exactly_one_thousand_cross_role_scenarios(self):
        all_cases=[create_case(r,c,v) for r in range(10) for c in range(10) for v in range(10)]
        self.assertEqual(len(all_cases),1000)
        self.assertEqual(len({x["id"] for x in all_cases}),1000)
        self.assertEqual(len({x["domain"] for x in all_cases}),10)
        self.assertEqual(len({x["family"] for x in all_cases}),10)
        self.assertTrue(all(q["quote"] in c["cv_text"]
              for c in all_cases for q in c["finding"]["evidence"]))
    def test_actual_production_semantic_guards_and_failure_disclosure(self):
        result=run_suite()
        self.assertEqual(result["scenarios"],1000)
        self.assertEqual(result["muse_requests"],0)
        self.assertEqual(result["raw_correct"],500)
        self.assertEqual(result["final_correct"],900)
        self.assertEqual(result["failures_by_family"],{"missed_direct":100})
        self.assertIn("not 1,000 independent CVs",result["warning"])
        self.assertEqual(result["families"]["opposing_cv_claims"]["final_correct"],100)
        self.assertEqual(result["families"]["one_scope_not_conflict"]["final_correct"],100)
        self.assertEqual(result["families"]["document_absence_not_conflict"]["final_correct"],100)
    def test_scope_and_related_do_not_become_supported(self):
        outcome=run_suite()
        for name in ["one_scope_not_conflict","document_absence_not_conflict",
                     "related_context_unproven","related_overstated"]:
            self.assertEqual(outcome["families"][name]["final_correct"],100)

if __name__=="__main__": unittest.main()
