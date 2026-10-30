"""Public build provenance check: no model keys or private settings exposed."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
import app


class BuildInfoTests(unittest.TestCase):
    def test_missing_commit_fails_closed_to_unknown_not_a_fictional_sha(self):
        with patch.dict(os.environ, {"RENDER_GIT_COMMIT": "", "EVIDENCETRAIL_BUILD_SHA": "",
                                     "RENDER_GIT_BRANCH": ""}):
            with TestClient(app.app) as client:
                response = client.get("/build-info")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIsNone(result["source_commit"])
        self.assertFalse(result["source_provenance_available"])
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertNotIn("api_key", str(result).lower())

    def test_render_commit_and_branch_return_exact_deploy_fingerprint(self):
        sha = "ab" * 20
        with patch.dict(os.environ, {
            "RENDER_GIT_COMMIT": sha.upper(),
            "RENDER_GIT_BRANCH": "release/evidencetrail-judge-rc1-oct30",
            "EVIDENCETRAIL_BUILD_SHA": "cd" * 20,
        }):
            with TestClient(app.app) as client:
                result = client.get("/build-info").json()
        self.assertTrue(result["source_provenance_available"])
        self.assertEqual(result["source_commit"], sha)
        self.assertEqual(result["source_branch"], "release/evidencetrail-judge-rc1-oct30")
        self.assertEqual(result["saved_replay_route"], "/demo20/recorded-muse")

    def test_malformed_sha_is_not_treated_as_version_proof(self):
        with patch.dict(os.environ, {
            "RENDER_GIT_COMMIT": "some-text-not-a-commit",
            "EVIDENCETRAIL_BUILD_SHA": "",
        }):
            with TestClient(app.app) as client:
                result = client.get("/build-info").json()
        self.assertIsNone(result["source_commit"])
        self.assertFalse(result["source_provenance_available"])


if __name__ == "__main__":
    unittest.main()
