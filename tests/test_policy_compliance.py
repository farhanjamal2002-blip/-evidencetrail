import unittest

import app


class ModelPolicyPromptTests(unittest.TestCase):
    def test_both_muse_passes_ignore_protected_traits_and_leave_decisions_human(self):
        self.assertIn("Do not infer or use protected or", app.SYSTEM_PROMPT)
        self.assertIn("Do not score, rank,", app.SYSTEM_PROMPT)
        self.assertIn("Ignore protected or personal", app.VERIFIER_SYSTEM_PROMPT)
        self.assertIn("Do not score, rank, or make a hiring decision", app.VERIFIER_SYSTEM_PROMPT)

    def test_work_authorization_is_never_inferred_from_personal_traits(self):
        for prompt in (app.SYSTEM_PROMPT, app.VERIFIER_SYSTEM_PROMPT):
            self.assertIn("Never infer work authorization", prompt)


if __name__ == "__main__":
    unittest.main()
