"""Offline unit tests of anonymous judge deployment-parity gate."""
import unittest
from unittest.mock import patch
from scripts import public_demo_release_probe as probe


class JudgePublicParityTests(unittest.TestCase):
    def setUp(self):
        self.sha = "ab" * 20

    def test_repeated_public_unavailability_is_a_hard_release_blocker(self):
        with patch.object(probe, "EXPECTED_SHA", self.sha), \
             patch.object(probe, "fetch_json", return_value=(503, None, "HTTP 503")) as fetch, \
             patch.object(probe.time, "sleep"):
            result = probe.run()
        self.assertFalse(result["passed"])
        self.assertFalse(result["health_ok"])
        self.assertEqual(fetch.call_count, 6)
        self.assertEqual(result["model_calls"], 0)
        self.assertIn("Public /health", result["blockers"][0])

    def test_healthy_but_stale_commit_never_passes(self):
        values = [
            (200, {"status": "ok"}, None),
            (200, {"source_provenance_available": True, "source_commit": "cd" * 20,
                   "judge_demo_mode": "mock_only"}, None),
            (200, {"total": 20, "live_muse_configured": False}, None),
            (200, {"results": [
                {"provider_mode": "muse", "receipt": "historical-meta-id",
                 "analysis_calls": 1} for _ in range(20)
            ]}, None),
        ]
        with patch.object(probe, "EXPECTED_SHA", self.sha), \
             patch.object(probe, "fetch_json", side_effect=values):
            result = probe.run()
        self.assertFalse(result["passed"])
        self.assertTrue(any("Stale deployed commit" in b for b in result["blockers"]))
        self.assertEqual(result["saved_genuine_model_responses"], 20)

    def test_matching_mock_only_build_and_authentic_saved_replay_can_pass(self):
        values = [
            (200, {"status": "ok"}, None),
            (200, {"source_provenance_available": True, "source_commit": self.sha,
                   "judge_demo_mode": "mock_only"}, None),
            (200, {"total": 20, "live_muse_configured": False}, None),
            (200, {"results": [
                {"provider_mode": "muse", "receipt": "historical-provider-id",
                 "analysis_calls": 1} for _ in range(20)
            ]}, None),
        ]
        with patch.object(probe, "EXPECTED_SHA", self.sha), \
             patch.object(probe, "fetch_json", side_effect=values):
            result = probe.run()
        self.assertTrue(result["passed"], result["blockers"])
        self.assertEqual(result["deployed_sha"], self.sha)
        self.assertEqual(result["model_calls"], 0)

    def test_unknown_version_or_live_public_muse_is_blocked(self):
        values = [
            (200, {"status": "ok"}, None),
            (200, {"source_provenance_available": False, "source_commit": None,
                   "judge_demo_mode": "review_server_configuration"}, None),
            (200, {"total": 20, "live_muse_configured": True}, None),
            (503, None, "HTTP 503"),
        ]
        with patch.object(probe, "EXPECTED_SHA", self.sha), \
             patch.object(probe, "fetch_json", side_effect=values):
            result = probe.run()
        self.assertFalse(result["passed"])
        self.assertGreaterEqual(len(result["blockers"]), 3)


if __name__ == "__main__":
    unittest.main()
