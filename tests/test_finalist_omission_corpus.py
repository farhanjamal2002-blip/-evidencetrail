"""Corpus is predeclared before evaluation; no exposed user data or API calls."""
import unittest
import pymupdf as fitz
from scripts.finalist_omission_corpus import CASES, make_cv_pdf, manifest_hash


class NewFictionalCorpusTests(unittest.TestCase):
    def test_cases_are_nonduplicated_and_both_directions_present(self):
        self.assertEqual(len(CASES),24)
        self.assertEqual(len({x.id for x in CASES}),24)
        self.assertGreaterEqual(len({x.family for x in CASES}),9)
        self.assertGreaterEqual(sum(x.reference=="supported" for x in CASES),9)
        self.assertGreaterEqual(sum(x.reference=="not_found" for x in CASES),9)
        self.assertTrue(any(x.reference=="conflicting" for x in CASES))
        self.assertEqual(len(manifest_hash()),64)

    def test_each_pdf_is_readable_and_scans_are_truly_image_only(self):
        for case in CASES:
            with self.subTest(case=case.id):
                source=make_cv_pdf(case)
                with fitz.open(stream=source,filetype="pdf") as doc:
                    self.assertEqual(len(doc),1)
                    text=doc[0].get_text()
                    self.assertEqual(bool(text.strip()),not case.scanned)
                    if case.scanned:
                        self.assertTrue(doc[0].get_images())


if __name__=="__main__":
    unittest.main()
