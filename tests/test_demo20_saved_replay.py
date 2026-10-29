"""Judge-visible authentic replay: no API call and never fabricate provenance."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
import app
import demo20_workflow as demo

class SavedMuseDemoTests(unittest.TestCase):
    def test_replay_missing_file_is_not_faked(self):
        demo._load_verified_recording.cache_clear()
        original=Path.is_file
        with patch.object(Path,"is_file",autospec=True,side_effect=lambda p: False if p.name=="demo20_muse_replay.json" else original(p)):
            with TestClient(app.app) as client:
                response=client.get("/demo20/recorded-muse")
                self.assertEqual(response.status_code,404)
                self.assertIn("no genuine recorded",response.text.lower())

    def test_published_replay_is_authentic_complete_and_sha_consistent(self):
        path=demo.BASE/"data"/"demo20_muse_replay.json"
        if not path.exists():
            self.skipTest("No genuine provider recording has been published yet")
        demo._load_verified_recording.cache_clear()
        with TestClient(app.app) as client:
            response=client.get("/demo20/recorded-muse")
        self.assertEqual(response.status_code,200,response.text[:400])
        data=response.json()
        self.assertTrue(data["fictional_only"])
        self.assertGreaterEqual(data["completed"],5)
        self.assertEqual(len(data["results"]),data["completed"])
        self.assertTrue(all(x["provider_mode"]=="muse" and x["receipt"] for x in data["results"]))
        self.assertTrue(all(len(x["requirements"])==4 for x in data["results"]))
        self.assertTrue(all(q["status"]!="supported" or q["evidence_type"]=="direct" for x in data["results"] for q in x["requirements"]))

if __name__=="__main__":unittest.main()
