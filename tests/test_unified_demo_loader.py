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

        response = self.client.get("/demo/unified-inputs")
        self.assertEqual(response.status_code, 200)
        manifest = response.json()
        self.assertEqual(manifest["rubric_version"], "demo-v1")
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


if __name__ == "__main__":
    unittest.main()
