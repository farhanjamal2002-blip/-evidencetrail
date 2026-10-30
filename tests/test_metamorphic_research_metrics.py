"""Research-pair integrity tests use FAKE ID strings inside unit tests only.

These are tests for the evaluator, not actual Muse calls or outcome claims.
"""
import unittest
from copy import deepcopy
from scripts.metamorphic_research_metrics import load_corpus,evaluate

class ResearchPairMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus,cls.sha=load_corpus()

    def rows(self):
        data=[]
        for case in self.corpus:
            for role in ("baseline","variant"):
                data.append({
                    "pair_id":case["id"],
                    "role":role,
                    "provider_mode":"muse",
                    # Contrived marker for validator unit-testing ONLY,
                    # NEVER published as an authentic Meta response.
                    "provider_response_id":"UNIT_TEST_FAKE_RECEIPT_"+case["id"]+"_"+role,
                    "corpus_sha256":self.sha,
                    "analysis_calls":1,
                    "source_quote_located":False,
                    "cited_page":0,
                    "predicted_status":case[role]["authored_reference"],
                })
        return data

    def test_frozen_author_corpus_and_empty_results_are_honest(self):
        self.assertEqual(len(self.corpus),12)
        r=evaluate([],self.corpus,self.sha)
        self.assertFalse(r["model_results_measured"])
        self.assertEqual(r["completed_pairs"],0)
        self.assertEqual(len(r["unmeasured_pairs"]),12)

    def test_partial_results_cannot_be_reported_as_benchmark(self):
        r=evaluate(self.rows()[:5],self.corpus,self.sha)
        self.assertFalse(r["model_results_measured"])
        self.assertIn("PARTIAL",r["status"])
        self.assertLess(r["completed_pairs"],12)

    def test_dedup_prevents_cherry_picking_retries(self):
        rows=self.rows()
        with self.assertRaisesRegex(ValueError,"Repeated model result"):
            evaluate(rows+[deepcopy(rows[0])],self.corpus,self.sha)

    def test_fake_or_wrong_provider_configuration_is_rejected(self):
        for key,value,substring in [
            ("provider_mode","mock","Muse mode"),
            ("provider_response_id","","Genuine Meta"),
            ("corpus_sha256","0"*64,"fingerprint"),
            ("source_quote_located","yes","boolean"),
            ("analysis_calls",2,"One authentic"),
        ]:
            rows=self.rows()
            rows[0][key]=value
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError,substring):
                    evaluate(rows,self.corpus,self.sha)

    def test_perfectly_matching_contrived_unit_test_values_are_not_real_results(self):
        # Mathematical smoke test only. THESE ARE ARTIFICIAL UNIT-TEST VALUES,
        # not actual model outputs or a benchmark result.
        r=evaluate(self.rows(),self.corpus,self.sha)
        self.assertEqual(r["pairs"],12)
        self.assertEqual(r["self_reported_muse_records"],24)
        self.assertEqual(r["relation_matches_author_expectation"],12)
        self.assertEqual(r["variant_label_matches_author_reference"],24)
        self.assertEqual(r["source_quotes_located"],0)
        self.assertEqual(r["new_model_calls_in_metric_runner"],0)

    def test_invariant_violation_is_detected_with_actual_pair_denominator(self):
        rows=self.rows()
        for row in rows:
            if row["pair_id"]=="M01" and row["role"]=="variant":
                row["predicted_status"]="not_found"
        report=evaluate(rows,self.corpus,self.sha)
        self.assertEqual(report["relation_matches_author_expectation"],11)
        self.assertEqual(report["variant_label_matches_author_reference"],23)

if __name__=="__main__":
    unittest.main()
