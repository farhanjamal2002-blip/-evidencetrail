"""Local multimodal image intake must preserve independent PDF checks."""
from __future__ import annotations
import io
import unittest

import pymupdf as fitz
from PIL import Image
from fastapi.testclient import TestClient

from multimodal_intake import prepare_cv, media_kind, optional_meta_vision_parts
import app
import demo20_workflow


class MultimodalIntakeTests(unittest.TestCase):
    def test_png_and_jpeg_become_source_checkable_one_page_pdfs(self):
        image=Image.new("RGB",(750,1200),"white")
        for fmt in ("PNG","JPEG"):
            with self.subTest(fmt=fmt):
                stream=io.BytesIO();image.save(stream,format=fmt)
                prepared=prepare_cv(stream.getvalue(),max_bytes=3_000_000)
                self.assertTrue(prepared.converted_image_to_pdf)
                self.assertNotEqual(prepared.original_sha256,prepared.normalized_sha256)
                with fitz.open(stream=prepared.pdf_bytes,filetype="pdf") as doc:
                    self.assertEqual(len(doc),1)
                    self.assertGreaterEqual(len(doc[0].get_images()),1)
                    self.assertFalse(doc[0].get_text().strip())

    def test_rejects_oversized_dimensions_and_spoofed_file(self):
        stream=io.BytesIO()
        Image.new("RGB",(4000,4000),"white").save(stream,format="PNG")
        with self.assertRaisesRegex(ValueError,"dimensions"):
            prepare_cv(stream.getvalue(),max_bytes=3_000_000)
        for blob in (b"",b"PK\x03\x04 zip",b"<script>alert(1)</script>"):
            with self.assertRaises(ValueError):
                prepare_cv(blob,max_bytes=3_000_000)
        self.assertEqual(media_kind(b"%PDF-1.7\n"),"application/pdf")

    def test_meta_visual_parts_are_bounded_and_page_labelled(self):
        with fitz.open(stream=demo20_workflow.make_cv_pdf("ET-019"),filetype="pdf") as doc:
            self.assertEqual(len(doc),1)
        pdf=demo20_workflow.make_cv_pdf("ET-019")
        parts=optional_meta_vision_parts(pdf,[1,1,999,True])
        self.assertEqual([x["type"] for x in parts],["text","image_url"])
        self.assertIn("PDF page 1",parts[0]["text"])
        self.assertTrue(parts[1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))
        self.assertLess(len(parts[1]["image_url"]["url"]),1_300_000)
        self.assertEqual(optional_meta_vision_parts(pdf,[]),[])

    def test_vision_fails_closed_without_flag_and_still_requires_consent(self):
        if app.ANALYSIS_PROVIDER!="mock":
            self.skipTest("This fails closed in mock mode")
        with TestClient(app.app) as client:
            response=client.post("/api/analyze",data={
                "job_description":"Position: Supply Lead",
                "consent":"true","visual_review":"true",
            },files={"cv":("sample.pdf",demo20_workflow.make_cv_pdf("ET-019"),"application/pdf")})
        self.assertEqual(response.status_code,400)
        self.assertIn("disabled",response.json()["detail"])

    def test_pdf_normalization_preserves_original_hash_and_bytes(self):
        sample=demo20_workflow.make_cv_pdf("ET-001")
        prepared=prepare_cv(sample,max_bytes=3_000_000)
        self.assertFalse(prepared.converted_image_to_pdf)
        self.assertEqual(prepared.pdf_bytes,sample)
        self.assertEqual(prepared.original_sha256,prepared.normalized_sha256)

    def test_image_upload_uses_existing_analysis_ocr_and_verification(self):
        if app.ANALYSIS_PROVIDER!="mock":
            self.skipTest("CI verifies upload in mock mode")
        source=demo20_workflow.make_cv_pdf("ET-001")
        with fitz.open(stream=source,filetype="pdf") as document:
            screenshot=document[0].get_pixmap(dpi=180).tobytes("png")
        with TestClient(app.app) as client:
            row=client.get("/demo20/manifest").json()
            response=client.post(
                "/api/analyze",
                data={"job_description":row["job_description"],
                      "consent":"true",
                      "locked_rubric_json":__import__("json").dumps(list(row["criteria"].values()))},
                files={"cv":("scanned-cv.png",screenshot,"image/png")},
            )
        self.assertEqual(response.status_code,200,response.text[:600])
        result=response.json()
        self.assertEqual(result["input_document"]["original_media_type"],"image/png")
        self.assertTrue(result["input_document"]["locally_converted_image"])
        self.assertEqual(result["input_document"]["vision_model_calls"],0)
        self.assertEqual(result["analysis_calls"],0)
        self.assertTrue(result["ocr_pages"])
        self.assertEqual(len(result["requirements"]),4)


if __name__=="__main__":
    unittest.main()
