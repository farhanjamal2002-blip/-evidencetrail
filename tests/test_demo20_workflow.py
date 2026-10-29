"""Fictional recruiter inbox: 20 real PDF bytes; no model calls or PII."""
import unittest

import fitz
from fastapi.testclient import TestClient

import app
import demo20_workflow as demo


class TwentyApplicantDemoTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app.app)

    def tearDown(self):
        self.client.close()

    def test_inbox_route_and_noindex(self):
        response=self.client.get("/demo20")
        self.assertEqual(response.status_code,200)
        self.assertIn('noindex',response.headers["x-robots-tag"])
        self.assertIn("20 FICTIONAL CVs",response.text)
        self.assertIn('id="analyze-five"',response.text)
        self.assertIn('id="consent"',response.text)

    def test_fixture_manifest_exactly_twenty_and_not_real_results(self):
        response=self.client.get("/demo20/manifest")
        self.assertEqual(response.status_code,200)
        data=response.json()
        self.assertEqual(data["total"],20)
        self.assertEqual([x["id"] for x in data["candidates"]],[f"ET-{i:03d}" for i in range(1,21)])
        self.assertEqual(len(data["criteria"]),4)
        self.assertTrue(all(x["processing_state"]=="not_analyzed" for x in data["candidates"]))
        self.assertFalse(data["automatic_hiring_decisions"])
        self.assertTrue(all("reference_only" in x and "muse_status" not in x for x in data["candidates"]))
        self.assertTrue(all(x["file_url"].startswith("/demo20/cv/") for x in data["candidates"]))

    def test_all_twenty_are_valid_pdfs_and_scans_are_image_only(self):
        self.assertEqual(len(demo.CASES),20)
        scans=[]
        for i in range(1,21):
            id=f"ET-{i:03d}"
            response=self.client.get(f"/demo20/cv/{id}")
            self.assertEqual(response.status_code,200,id)
            self.assertTrue(response.content.startswith(b"%PDF-"))
            self.assertIn("no-store",response.headers["cache-control"])
            with fitz.open(stream=response.content,filetype="pdf") as pdf:
                self.assertEqual(len(pdf),1,id)
                if not pdf[0].get_text().strip():
                    scans.append(id)
                else:
                    self.assertIn(id,pdf[0].get_text())
        self.assertEqual(scans,["ET-019","ET-020"])

    def test_invalid_id_paths_fail_closed(self):
        for id in ("../app.py","ET-021","ET-1","ET-000","ET-999","ET-018.pdf","%2E%2E%2Fapp.py"):
            response=self.client.get(f"/demo20/cv/{id}")
            self.assertIn(response.status_code,{404,422},id)

    def test_model_configuration_not_forged(self):
        data=self.client.get("/demo20/manifest").json()
        self.assertIn(data["provider_mode"],{"mock","muse"})
        self.assertIsInstance(data["live_muse_configured"],bool)
        self.assertNotIn("MODEL_API_KEY",str(data))
        self.assertIn("not actual Muse outcomes",data["disclosure"])

    def test_markers_for_security_and_conflicts(self):
        data=self.client.get("/demo20/manifest").json()["candidates"]
        self.assertEqual(sum(c["scan"] for c in data),2)
        self.assertTrue(any("INSTRUCTION TO THE AI SYSTEM" in " ".join(c["fixture_lines"]) for c in data))
        self.assertTrue(any(c["scenario"]=="Conflict" for c in data))
        self.assertTrue(any(c["scenario"]=="KeywordOnly" for c in data))
        self.assertTrue(any(c["scenario"]=="CareerSwitch" for c in data))

    def test_job_criteria_can_be_submitted_to_real_existing_analyze_endpoint_in_mock_mode(self):
        # Integration exercises real analysis on just a fictional PDF with
        # explicit consent, exact locked rubric and NO Muse requests.
        if app.ANALYSIS_PROVIDER!="mock":
            self.skipTest("CI runs this test in mock mode")
        row=self.client.get("/demo20/manifest").json()
        pdf=self.client.get("/demo20/cv/ET-001").content
        response=self.client.post("/api/analyze",
            data={"job_description":row["job_description"],"locked_rubric_json":__import__("json").dumps(list(row["criteria"].values())),"consent":"true"},
            files={"cv":("ET-001-fictional.pdf",pdf,"application/pdf")})
        self.assertEqual(response.status_code,200,response.text[:300])
        out=response.json()
        self.assertEqual(out["analysis_calls"],0)
        self.assertEqual(out["provider_mode"],"mock")
        self.assertEqual(len(out["requirements"]),4)
        self.assertEqual([x["requirement"] for x in out["requirements"]],list(row["criteria"].values()))


if __name__=="__main__":unittest.main()
