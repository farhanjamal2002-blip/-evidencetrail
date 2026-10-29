"""Preflight: new synthetic holdout is valid before any Meta model calls."""
import unittest
import fitz

from scripts import conflict_holdout_corpus as holdout
from scripts.hard_cv_corpus import SECTORS as PREVIOUS_SECTORS


class NewHoldoutCorpusTests(unittest.TestCase):
    def test_locked_80_labels_and_genuine_discrepancies(self):
        manifest=holdout.corpus_manifest()
        self.assertEqual(manifest["cases"],20)
        self.assertEqual(manifest["criterion_instances"],80)
        self.assertEqual(manifest["status_distribution"],
                         {"supported":20,"not_found":55,"conflicting":5})
        self.assertFalse(any(manifest["invalid_references"].values()),
                         manifest["invalid_references"])

    def test_new_sectors_and_unique_pdf_inputs(self):
        cases=holdout.build_all_cases()
        self.assertTrue(set(role["code"] for role in holdout.ROLES).isdisjoint(
            set(role["code"] for role in PREVIOUS_SECTORS)))
        manifest=holdout.corpus_manifest()
        self.assertEqual(len(set(manifest["pdf_sha256_by_case"].values())),20)
        for case in cases:
            with self.subTest(case=case["id"]):
                with fitz.open(stream=holdout.render_pdf(case),filetype="pdf") as doc:
                    self.assertEqual(len(doc),2)
                self.assertEqual(len(case["oracle_evidence"]),4)
                if case["archetype"]=="opposing_cv_claims":
                    item=case["oracle_evidence"][0]
                    self.assertEqual(item["status"],"conflicting")
                    self.assertNotEqual(item["anchor"],item["opposing_anchor"])

if __name__=="__main__":
    unittest.main()
