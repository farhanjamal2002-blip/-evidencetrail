import unittest

from fastapi.testclient import TestClient

import app


class UnifiedDemoLoaderTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app.app)

    def test_manifest_and_all_five_downloads_are_fixed_fictional_pdfs(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn('id="load-unified-demo"', page.text)
        self.assertIn("Unified supplier-operations set · rubric v3", page.text)

        response = self.client.get("/demo/unified-inputs")
        self.assertEqual(response.status_code, 200)
        manifest = response.json()
        self.assertEqual(manifest["rubric_version"], "demo-v3")
        self.assertEqual(len(manifest["candidates"]), 5)
        self.assertNotIn("expected", manifest)
        self.assertEqual(
            [candidate["id"] for candidate in manifest["candidates"]],
            [
                "unified_c1_specific",
                "unified_c2_keyword_only",
                "unified_c3_career_switcher",
                "unified_c4_date_overlap",
                "unified_c5_scanned_two_column",
            ],
        )

        for candidate in manifest["candidates"]:
            with self.subTest(candidate=candidate["id"]):
                pdf = self.client.get(candidate["download_url"])
                self.assertEqual(pdf.status_code, 200)
                self.assertEqual(pdf.headers["content-type"], "application/pdf")
                self.assertTrue(pdf.content.startswith(b"%PDF-"))

    def test_loader_refuses_unknown_candidate_paths(self):
        response = self.client.get("/demo/unified-cv/not-a-fixture")
        self.assertEqual(response.status_code, 404)
        report = self.client.get("/demo/unified-report/not-a-fixture")
        self.assertEqual(report.status_code, 404)

    def test_frozen_muse_replay_contains_five_real_results_without_new_calls(self):
        response = self.client.get("/demo/unified-replay")
        self.assertEqual(response.status_code, 200)
        replay = response.json()
        self.assertEqual(replay["replay_mode"], "frozen_live_muse_results")
        self.assertFalse(replay["makes_model_request"])
        self.assertEqual(replay["model"], "muse-spark-1.3")
        self.assertEqual(replay["reasoning_effort"], "minimal")
        self.assertEqual(len(replay["results"]), 5)
        self.assertEqual(replay["analysis_calls"], 5)
        self.assertIn("five fictional CV PDFs", replay["disclosure"])

        scanned = next(
            item for item in replay["results"]
            if item["fixture_id"] == "unified_c5_scanned_two_column"
        )
        self.assertEqual(scanned["result"]["analysis_calls"], 1)
        self.assertEqual(scanned["result"]["ocr_pages"], [1])
        self.assertEqual(scanned["result"]["verification_audit"]["excluded"], 0)
        self.assertNotIn("pages", scanned["result"])
        self.assertNotIn("report_html", scanned["result"])
        self.assertEqual(
            scanned["report_url"],
            "/demo/unified-report/unified_c5_scanned_two_column",
        )
        report = self.client.get(scanned["report_url"])
        self.assertEqual(report.status_code, 200)
        self.assertTrue(report.text.lower().startswith("<!doctype html"))
        self.assertIn("src='data:image/jpeg;base64,", report.text)

        career_switcher = next(
            item for item in replay["results"]
            if item["fixture_id"] == "unified_c3_career_switcher"
        )
        self.assertEqual(career_switcher["result"]["analysis_calls"], 1)


if __name__ == "__main__":
    unittest.main()
