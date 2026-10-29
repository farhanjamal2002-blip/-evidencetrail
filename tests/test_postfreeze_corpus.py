"""Post-prompt-freeze CV challenge is source-locked before any inference."""
import unittest
import fitz
from scripts.postfreeze_cv_corpus import cases,manifest,render_pdf,DOMAINS

class PostfreezeCVChallengeTests(unittest.TestCase):
    def test_fixed_source_criteria_and_diverse_sectors(self):
        m=manifest()
        self.assertEqual(m["cases"],16)
        self.assertEqual(m["requirements"],48)
        self.assertEqual(m["reference_distribution"],{
            "supported":16,"not_found":28,"conflicting":4,
        })
        self.assertEqual(len(m["sectors"]),4)
        self.assertEqual(len(set(m["sha256"].values())),16)

    def test_pdf_scenario_truths_are_author_set_and_source_present(self):
        arr=cases()
        for case in arr:
            with fitz.open(stream=render_pdf(case),filetype="pdf") as doc:
                self.assertEqual(len(doc),2)
            domain=next(d for d in DOMAINS if d["name"]==case["domain"])
            texts=" ".join(" ".join(page) for page in case["pages"])
            if case["style"]=="buried_direct":
                for statement in domain["direct"]:
                    self.assertIn(statement,texts)
            if case["style"]=="explicit_role_boundaries":
                for statement in domain["related"]:
                    self.assertIn(statement,texts)
            if case["style"]=="contradictory_attestation":
                self.assertIn(domain["direct"][0],texts)
                self.assertIn(domain["denial"],texts)
                self.assertNotEqual(domain["direct"][0],domain["denial"])
            self.assertEqual(len(case["criteria"]),3)
            self.assertEqual(len(case["expected"]),3)

if __name__=="__main__":unittest.main()
