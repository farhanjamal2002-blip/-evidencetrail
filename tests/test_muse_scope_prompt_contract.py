"""The prompt upgrade retains the explicit distinction between an unmet JD
requirement and mutually contradictory claims in the CV itself."""
import unittest
import app

class MuseScopePromptContract(unittest.TestCase):
    def test_incompatible_cv_claims_not_candidate_job_gap(self):
        prompt=app.SYSTEM_PROMPT
        self.assertIn("two explicit incompatible statements WITHIN",prompt)
        self.assertIn("same CV",prompt)
        self.assertIn("Missing\nproof and negative experience disclosures use not_found",prompt)
        self.assertIn("The job requirement\ndisagreeing with a CV limitation is NOT",prompt)

    def test_adjacent_work_not_claimed_as_conflict(self):
        prompt=app.SYSTEM_PROMPT
        self.assertIn("I prepared notes; the director led negotiations",prompt)
        self.assertIn("choose status=not_found",prompt)
        self.assertIn("another team authored rules",prompt)
        self.assertIn("A course listing keywords without job duties",prompt)

    def test_true_cv_contradictions_are_preserved(self):
        prompt=app.SYSTEM_PROMPT
        self.assertIn('I personally led negotiations" AND elsewhere',prompt)
        self.assertIn("roles\nsupports and contradicts respectively",prompt)

    def test_no_ranking_and_source_grounding_retained(self):
        prompt=app.SYSTEM_PROMPT
        self.assertIn("Never infer negotiation, ownership",prompt)
        self.assertIn("Local code will reject a citation",prompt)
        self.assertIn("Do not score, rank, recommend",prompt)
if __name__=="__main__":unittest.main()
