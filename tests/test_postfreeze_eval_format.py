"""The evaluation format must succeed BEFORE consuming any real provider credits."""
import unittest
from scripts.postfreeze_cv_corpus import cases
from scripts.postfreeze_eval_format import format_criteria

class FormatPreflight(unittest.TestCase):
    def test_all_sixteen_synthetic_cases_format_after_fake_response(self):
        for case in cases():
            fake=[
                {"raw_status":s,"status":s,"evidence_type":"direct" if s=="supported" else "unsupported",
                 "evidence":[]}
                for s in case["expected"]
            ]
            result=format_criteria(case,fake)
            self.assertEqual(len(result),len(case["criteria"]))
            self.assertTrue(all(x["final_correct"] for x in result))

    def test_missing_responses_become_explicit_failures_not_exceptions(self):
        for case in cases():
            result=format_criteria(case,[])
            self.assertEqual(len(result),3)
            self.assertFalse(any(x["final_correct"] for x in result))
            self.assertTrue(all(x["final"] is None for x in result))

    def test_rejects_reference_length_mismatch_before_model_work(self):
        c=cases()[0].copy()
        c["expected"]=c["expected"][:2]
        with self.assertRaises(ValueError):
            format_criteria(c,[])

if __name__=="__main__":unittest.main()
