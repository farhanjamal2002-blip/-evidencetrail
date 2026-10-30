"""Academic-inspired evaluation must not launder weak evidence into claims."""
import unittest

from scripts.academic_evidence_metrics import evaluate

def case(ident, gold, pred, *, domain="fictional_cv",
         provenance="author_labelled_synthetic",
         pages=None, cited=None, spans=None, retrieved=None,
         source_verified=False, attribution="not_assessed", assessed=False):
    return {
        "document_id":ident,
        "criterion_id":"R1",
        "domain":domain,
        "reference_provenance":provenance,
        "gold_status":gold,
        "predicted_status":pred,
        "source_verified":source_verified,
        "gold_pages":pages if pages is not None else [],
        "cited_pages":cited if cited is not None else [],
        "gold_span_ids":spans if spans is not None else [],
        "pred_span_ids":retrieved if retrieved is not None else [],
        "semantic_attribution":attribution,
        "attribution_human_reviewed":assessed,
    }

class AcademicEvidenceMetricTests(unittest.TestCase):
    def test_empty_inputs_cannot_claim_academic_validation(self):
        r=evaluate([])
        self.assertFalse(r["claims_authorized"])
        self.assertEqual(r["domain_results"],[])
        self.assertIn("NO ACADEMIC",r["status"])

    def test_false_support_missed_support_and_abstention_are_separate(self):
        rows=[
            case("D1","supported","supported",pages=[1],cited=[1],
                 spans=["s1"],retrieved=["s1"],source_verified=True),
            case("D2","supported","review_required",pages=[2],cited=[]),
            case("D3","not_found","supported",pages=[],cited=[]),
            case("D4","conflicting","conflicting",pages=[1,2],cited=[2],
                 spans=["a","b"],retrieved=["b"],source_verified=True),
            case("D5","refuted","supported",pages=[3],cited=[3],
                 source_verified=True),
        ]
        r=evaluate(rows)
        self.assertTrue(r["no_pooled_accuracy"])
        m=r["domain_results"][0]
        self.assertEqual(m["false_support"]["errors"],2)
        self.assertEqual(m["false_support"]["gold_not_supported"],3)
        self.assertEqual(m["missed_documented_support"]["errors"],1)
        self.assertEqual(m["missed_documented_support"]["gold_supported"],2)
        self.assertEqual(m["review_required"]["count"],1)
        self.assertTrue(m["review_required"]["not_equivalent_to_not_found"])
        self.assertEqual(m["source_pages"]["matched"],3)
        self.assertEqual(m["source_pages"]["gold"],5)
        self.assertEqual(m["evidence_span_ids"]["matched"],2)
        self.assertEqual(m["evidence_span_ids"]["gold"],3)

    def test_contract_refutation_cannot_masquerade_as_cv_conflicting(self):
        with self.assertRaisesRegex(ValueError,"ContractNLI contradiction"):
            evaluate([case("C1","refuted","conflicting",
                           domain="contract_nli_transfer",
                           provenance="published_external_gold")])
        result=evaluate([case("C1","refuted","refuted",
                              domain="contract_nli_transfer",
                              provenance="published_external_gold")])
        self.assertIsNone(result["domain_results"][0]["macro_f1_all_comparable_labels"])

    def test_verified_quote_cannot_be_groundless(self):
        with self.assertRaisesRegex(ValueError,"Verified page citation"):
            evaluate([case("D1","supported","supported",source_verified=True)])

    def test_ais_like_attribution_requires_a_real_human_judgement(self):
        with self.assertRaisesRegex(ValueError,"not human AIS"):
            evaluate([case("D1","supported","supported",cited=[1],
                           attribution="supported",assessed=False)])
        r=evaluate([case("D1","supported","supported",pages=[1],cited=[1],
                         attribution="supported",assessed=True)])
        self.assertEqual(r["domain_results"][0]["human_semantic_attribution"]["assessed"],1)

    def test_joint_strict_support_requires_status_page_span_source_and_human_semantics(self):
        rows=[
            case("J1","supported","supported",pages=[1,2],cited=[1,2],
                 spans=["s1","s2"],retrieved=["s1","s2"],source_verified=True,
                 attribution="supported",assessed=True),
            case("J2","supported","not_found",pages=[1],cited=[1],
                 spans=["s1"],retrieved=["s1"],source_verified=True,
                 attribution="supported",assessed=True),
            case("J3","supported","supported",pages=[1,2],cited=[1],
                 spans=["s1","s2"],retrieved=["s1"],source_verified=True,
                 attribution="supported",assessed=True),
            case("J4","supported","supported",pages=[1],cited=[1],
                 spans=["s1"],retrieved=["s1"],source_verified=True,
                 attribution="unsupported",assessed=True),
            case("J5","supported","supported",pages=[1],cited=[1],
                 spans=["s1"],retrieved=["s1"],source_verified=True),
        ]
        metric=evaluate(rows)["domain_results"][0]["joint_supported_answer_and_evidence"]
        self.assertEqual(metric["passed"],1)
        self.assertEqual(metric["human_assessed_supported_gold"],4)
        self.assertEqual(metric["unassessed_or_missing_gold_spans"],1)
        self.assertEqual(metric["rate"],0.25)
        self.assertTrue(metric["adapted_from_citevqa_not_a_citevqa_benchmark_score"])

    def test_no_cross_domain_pooled_accuracy_or_synthetic_gold_masquerade(self):
        rows=[
            case("S1","supported","supported"),
            case("X1","not_found","not_found",domain="qasper_transfer",
                 provenance="published_external_gold"),
        ]
        r=evaluate(rows)
        self.assertEqual(r["domains"],2)
        self.assertTrue(r["no_pooled_accuracy"])
        with self.assertRaisesRegex(ValueError,"Transfer metrics"):
            evaluate([case("X2","supported","supported",
                           domain="qasper_transfer")])

    def test_duplicate_references_or_invented_source_pages_fail(self):
        row=case("D1","supported","supported",pages=[1],cited=[1])
        with self.assertRaisesRegex(ValueError,"Duplicate document"):
            evaluate([row,row])
        row2=case("D2","supported","supported",pages=[1],
                  cited=[1,1])
        with self.assertRaisesRegex(ValueError,"duplicates"):
            evaluate([row2])
        row3=case("D3","supported","supported",pages=[1],
                  cited=[0])
        with self.assertRaisesRegex(ValueError,"positive integer"):
            evaluate([row3])


if __name__=="__main__":
    unittest.main()
