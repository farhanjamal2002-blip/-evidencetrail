"""Validate all never-before-used fictional CV source reference labels before inference."""
import unittest
import fitz
from scripts.fresh_holdout_cv_corpus import CASES,manifest,pdf_for_case

class FreshHoldoutTests(unittest.TestCase):
 def test_eight_two_page_documents_with_locked_references(self):
  m=manifest()
  self.assertEqual(m["cases"],8)
  self.assertEqual(m["criterion_instances"],32)
  self.assertEqual(m["status_distribution"],{"supported":12,"not_found":16,"conflicting":4})
  self.assertEqual(m["issues"],[])
  self.assertEqual(len(set(m["sources_sha256"].values())),8)
 def test_source_pdf_extraction_and_anchors(self):
  for case in CASES:
   with fitz.open(stream=pdf_for_case(case),filetype="pdf") as d:
    self.assertEqual(len(d),2)
    pages="\n".join(p.get_text("text") for p in d)
    self.assertIn(case["id"],pages)
    self.assertGreater(len(pages),450)
   written="\n".join("\n".join(p) for p in case["pages"])
   for label,anchor in zip(case["expected"],case["anchors"]):
    if label=="supported":self.assertTrue(isinstance(anchor,str) and anchor in written)
    if label=="conflicting":
     self.assertTrue(isinstance(anchor,list) and len(anchor)==2)
     self.assertTrue(all(a in written for a in anchor))
 def test_four_unrelated_roles_two_styles_each(self):
  self.assertEqual(len({c["sector"] for c in CASES}),4)
  self.assertEqual([c["sector"] for c in CASES[::2]],[
   "pharmaceutical distribution","renewable power","legal operations","education technology"])
if __name__=="__main__":unittest.main()
