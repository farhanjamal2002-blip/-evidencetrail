"""Actual source-linked quote snap on immutable fictional CVs."""
import unittest
import fitz
from fastapi.testclient import TestClient
import app
from demo20_workflow import _load_verified_recording,make_cv_pdf
from pdf_quote_geometry import locate_quote_geometry

class QuoteGeometryTests(unittest.TestCase):
    def test_page_image_bytes_and_guards(self):
        with TestClient(app.app) as client:
            resp=client.get("/demo20/cv/ET-005/page/1.png")
            self.assertEqual(resp.status_code,200,resp.text[:100] if resp.status_code!=200 else "")
            self.assertTrue(resp.content.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertEqual(resp.headers["content-type"],"image/png")
            self.assertEqual(client.get("/demo20/cv/ET-005/page/2.png").status_code,404)
            self.assertEqual(client.get("/demo20/cv/ET-099/page/1.png").status_code,404)
            self.assertEqual(client.get("/demo20/cv/ET-019/page/1.png?dpi=9999").status_code,200)

    def test_normalized_coordinates_are_actual_page_geometry(self):
        with fitz.open(stream=make_cv_pdf("ET-005"),filetype="pdf") as doc:
            quote="Prepared negotiation notes, but a director led supplier contract negotiations."
            r=locate_quote_geometry(doc[0],quote)
            self.assertIn(r["match_method"],("pymupdf_search_for","normalized_word_span"))
            self.assertTrue(r["bounding_boxes"])
            self.assertEqual(r["page_dimensions"],{"width":612.0,"height":792.0})
            for b in r["bounding_boxes"]:
                self.assertTrue(all(0<=b[k]<=1 for k in ("norm_x","norm_y","norm_w","norm_h")))
                self.assertAlmostEqual(b["x0"],b["norm_x"]*612,delta=.02)
                self.assertAlmostEqual(b["y0"],b["norm_y"]*792,delta=.02)

    def test_ocr_refuses_to_invent_character_geometry(self):
        with fitz.open(stream=make_cv_pdf("ET-019"),filetype="pdf") as doc:
            r=locate_quote_geometry(doc[0],"Raised SAP MM purchase orders.",is_ocr_page=True)
            self.assertEqual(r["match_method"],"ocr_page_level_only")
            self.assertIsNone(r["bounding_boxes"])
            self.assertIsNone(r["char_span"])

    def test_unmatched_passage_never_gets_highlight(self):
        with fitz.open(stream=make_cv_pdf("ET-005"),filetype="pdf") as doc:
            r=locate_quote_geometry(doc[0],"An entirely fabricated source passage that does not exist.")
            self.assertEqual(r["match_method"],"page_verified_no_bbox")
            self.assertIsNone(r["bounding_boxes"])

    def test_all_real_recorded_citations_measured_without_meta_call(self):
        original=_load_verified_recording()
        with TestClient(app.app) as client:
            response=client.get("/demo20/recorded-muse")
        self.assertEqual(response.status_code,200)
        data=response.json()
        total=located=ocr=unlocated=0
        for row in data["results"]:
            self.assertTrue(row["receipt"])
            for req in row["verification_receipt"]["requirements"]:
                for ev in req["quote_citations"]:
                    total+=1
                    if ev["bounding_boxes"]:
                        located+=1
                        self.assertIn(ev["match_method"],("pymupdf_search_for","normalized_word_span"))
                    elif ev["match_method"]=="ocr_page_level_only":
                        ocr+=1
                    else:unlocated+=1
        self.assertEqual(total,71)
        self.assertEqual(located,62)
        self.assertEqual(ocr,9)
        self.assertEqual(unlocated,0)
        # The original historical audit counted 76 verifications but saved only
        # 71 surviving individual quotes; no missing geometry is fabricated.
        self.assertEqual(sum(r["quote_audit"]["verified"] for r in original["results"]),76)

if __name__=="__main__":unittest.main()
