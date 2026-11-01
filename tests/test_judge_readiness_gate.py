"""The judge preflight must reject claims unsupported by actual receipts."""
from __future__ import annotations

import unittest

from scripts.judge_readiness_gate import report


class JudgeReadinessGateTests(unittest.TestCase):
    def test_saved_muse_receipts_and_demo_anchors_are_honest(self):
        r = report()
        self.assertTrue(r["local_preflight_passed"], r["errors"])
        self.assertEqual(r["fictional_cv_count"], 20)
        self.assertEqual(r["requirement_judgments"], 80)
        self.assertEqual(r["model_receipts_in_historical_record"], 20)
        self.assertEqual(r["model_calls_when_running_this_preflight"], 0)
        self.assertTrue(r["demonstrable_anchors"]["ET-003"]["corrections"])
        self.assertTrue(r["demonstrable_anchors"]["ET-015"]["no_claim_of_external_truth"])
        self.assertTrue(r["demonstrable_anchors"]["ET-019"]["not_proof_of_a_live_image_input_to_muse"])

    def test_do_not_claim_blocked_quote_in_old_replay(self):
        r = report()
        self.assertEqual(r["quote_counters"]["excluded_by_page_check"], 0)
        self.assertGreater(r["quote_counters"]["source_checked"], 0)
        self.assertLessEqual(r["quote_counters"]["retained_individual_citations"],
                             r["quote_counters"]["source_checked"])

    def test_local_preflight_is_not_public_release_or_accuracy_evidence(self):
        r = report()
        gates = " ".join(r["external_gates_not_proven_here"])
        for phrase in ("deployed public URL", "time savings", "judge video",
                       "image-input API call", "registered track", "real-world"):
            self.assertIn(phrase, gates)


if __name__ == "__main__":
    unittest.main()
