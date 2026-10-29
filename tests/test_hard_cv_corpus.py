"""Hard CV benchmark corpus locks its ground truth before using the model."""
import unittest
import fitz
from scripts.hard_cv_corpus import build_all_cases,corpus_manifest,render_pdf,verify_reference

class HardCVCorpusTests(unittest.TestCase):
    def test_20_documents_80_locked_criteria(self):
        manifest=corpus_manifest()
        self.assertEqual(manifest["cases"],20)
        self.assertEqual(manifest["criterion_instances"],80)
        self.assertEqual(manifest["sectors"],5)
        self.assertEqual(manifest["status_distribution"],{
            "supported":30,"not_found":45,"conflicting":5,
        })
        self.assertFalse(any(manifest["invalid_references"].values()),manifest["invalid_references"])
    def test_original_pdf_text_and_dual_source_conflicts(self):
        for case in build_all_cases():
            pdf=render_pdf(case)
            with fitz.open(stream=pdf,filetype="pdf") as doc:
                self.assertEqual(len(doc),2,case["id"])
                all_text="\n".join(page.get_text("text") for page in doc)
                self.assertGreater(len(all_text),500,case["id"])
                self.assertIn("FICTIONAL CV "+case["id"],all_text)
                self.assertFalse(verify_reference(case))
                for label in case["oracle_evidence"]:
                    if label["status"]=="conflicting":
                        self.assertTrue(label["anchor"])
                        self.assertTrue(label["opposing_anchor"])
                        self.assertNotEqual(label["anchor"],label["opposing_anchor"])
    def test_different_cv_styles_not_exact_duplicates(self):
        contents=["\n".join("\n".join(p) for p in c["pages"]) for c in build_all_cases()]
        self.assertEqual(len(contents),len(set(contents)))
        self.assertEqual(len(build_all_cases()),20)
if __name__=="__main__":unittest.main()
