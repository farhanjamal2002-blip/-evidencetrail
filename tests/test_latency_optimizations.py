import base64
import io
import os
import unittest
from collections import Counter
from unittest.mock import patch

import pymupdf as fitz
from PIL import Image
from fastapi.testclient import TestClient

os.environ["EVIDENCETRAIL_PROVIDER"] = "mock"
os.environ["MAX_ANALYSES_PER_HOUR_PER_IP"] = "1000"
os.environ["MAX_ANALYSES_PER_PROCESS"] = "1000"

import app


class LatencyOptimizationTests(unittest.TestCase):
    def test_large_app_responses_use_gzip_when_the_client_supports_it(self):
        with TestClient(app.app) as client:
            response = client.get("/", headers={"Accept-Encoding": "gzip"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-encoding"), "gzip")
        self.assertLess(
            int(response.headers["content-length"]),
            len(response.content),
        )
        self.assertIn("EvidenceTrail", response.text)

    def test_fast_native_extraction_preserves_layout_prompt_and_quote_boxes(self):
        document = fitz.open()
        page = document.new_page(width=612, height=792)
        page.insert_text((54, 78), "EXPERIENCE")
        page.insert_text((54, 108), "Supplier Contracts Manager")
        page.insert_text((54, 130), "Negotiated supply agreements for four years")
        page.insert_text((360, 78), "TOOLS")
        page.insert_text((360, 108), "SAP Ariba")
        page.insert_text((360, 130), "Oracle ERP")
        pdf_bytes = document.tobytes()
        document.close()

        sorted_pages = app.extract_pdf(pdf_bytes, sort_native_text=True)
        extraction_timings = {}
        fast_pages = app.extract_pdf(
            pdf_bytes,
            sort_native_text=False,
            timing_collector=extraction_timings,
        )

        self.assertEqual(
            app.format_cv_text_for_model(fast_pages),
            app.format_cv_text_for_model(sorted_pages),
        )
        word_signature = lambda page: Counter(
            (
                word["text"],
                tuple(round(float(value), 2) for value in word["bbox"]),
            )
            for word in page["words"]
        )
        self.assertEqual(word_signature(fast_pages[0]), word_signature(sorted_pages[0]))
        expected_quote = "Negotiated supply agreements for four years"
        self.assertEqual(
            app.locate_quote(expected_quote, fast_pages, 1),
            app.locate_quote(expected_quote, sorted_pages, 1),
        )
        self.assertIn("pdf_native_text_extraction_ms", extraction_timings)
        self.assertIn("pdf_word_bbox_processing_ms", extraction_timings)
        self.assertIn("pdf_ocr_detection_ms", extraction_timings)

    def test_page_previews_open_the_pdf_once_for_multiple_pages(self):
        document = fitz.open()
        for page_number in range(3):
            page = document.new_page(width=612, height=792)
            page.insert_text((72, 100), f"Verified source line {page_number + 1}")
        pdf_bytes = document.tobytes()
        document.close()
        marks = {
            page_number: [{"role": "supports", "boxes": [[70, 85, 250, 110]]}]
            for page_number in (1, 2, 3)
        }

        original_open = fitz.open
        preview_timings = {}
        with patch.object(app.fitz, "open", wraps=original_open) as open_pdf:
            previews = app.page_previews(
                pdf_bytes, marks, timing_collector=preview_timings
            )

        self.assertEqual(open_pdf.call_count, 1)
        self.assertEqual(set(previews), {1, 2, 3})
        self.assertIn("preview_pdf_open_ms", preview_timings)
        self.assertIn("preview_page_raster_ms", preview_timings)
        self.assertIn("preview_pixmap_to_rgb_ms", preview_timings)
        self.assertIn("preview_highlight_draw_ms", preview_timings)
        self.assertIn("preview_jpeg_encode_ms", preview_timings)
        self.assertIn("preview_base64_encode_ms", preview_timings)
        self.assertTrue(all(value.startswith("data:image/jpeg;base64,") for value in previews.values()))
        for preview in previews.values():
            encoded = preview.split(",", 1)[1]
            with Image.open(io.BytesIO(base64.b64decode(encoded))) as image:
                self.assertLessEqual(
                    max(image.size), app.REPORT_PREVIEW_MAX_SIDE_PX
                )

    def test_direct_pixmap_conversion_matches_png_rgb_pixels(self):
        document = fitz.open()
        page = document.new_page(width=612, height=792)
        page.insert_text((72, 100), "RGB pixel equivalence check")
        pixmap = page.get_pixmap(colorspace=fitz.csRGB, alpha=False)

        direct = app._pixmap_to_rgb_image(pixmap)
        reference = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")

        self.assertEqual(direct.size, reference.size)
        self.assertEqual(direct.tobytes(), reference.tobytes())
        document.close()

    def test_ocr_language_is_resolved_once_per_process(self):
        app.ocr_language.cache_clear()
        try:
            with patch.object(
                app.pytesseract,
                "get_languages",
                return_value=["eng", "ara"],
            ) as get_languages:
                self.assertEqual(app.ocr_language(), "eng+ara")
                self.assertEqual(app.ocr_language(), "eng+ara")
                get_languages.assert_called_once_with(config="")
        finally:
            app.ocr_language.cache_clear()

    def test_quote_lookup_prefers_and_caches_the_cited_page(self):
        document = fitz.open()
        first = document.new_page(width=612, height=792)
        first.insert_text((72, 100), "A different supplier record appears here")
        second = document.new_page(width=612, height=792)
        second.insert_text((72, 100), "Supplier contract evidence for two years")
        pdf_bytes = document.tobytes()
        document.close()
        pages = app.extract_pdf(pdf_bytes)

        with patch.object(app, "reading_order_streams", wraps=app.reading_order_streams) as group_page:
            located = app.locate_quote("Supplier contract evidence for two years", pages, 2)
            self.assertEqual(located["page"], 2)
            group_page.assert_called_once()
            app.locate_quote("Supplier contract evidence for two years", pages, 2)
            group_page.assert_called_once()

        recovered = app.locate_quote("Supplier contract evidence for two years", pages, 1)
        self.assertEqual(recovered["page"], 2)


if __name__ == "__main__":
    unittest.main()
