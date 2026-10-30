"""Sanity checks for strict human-pilot accounting; never invent reviewers."""
import unittest
from scripts.evaluate_reviewer_pilot import evaluate,median,p90

FIELDS=("reviewer_code","reviewer_type","experience_band","condition","order",
 "cv_id","job_family","difficulty","active_seconds","source_clicks",
 "criterion_unsupported_as_supported","criterion_supported_missed",
 "unresolved_items","completed","model_calls","notes")

def row(reviewer,cv,condition,seconds,missed=0):
    values=(reviewer,"hiring manager","2-5 years",condition,"1",cv,
        "procurement","standard",str(seconds),"2","0",str(missed),"1",
        "yes","0","")
    return dict(zip(FIELDS,values))

class PilotAnalysisTests(unittest.TestCase):
    def test_no_reviewer_data_generates_no_impact_claim(self):
        result=evaluate([])
        self.assertFalse(result["claims_authorized"])
        self.assertEqual(result["participants"],0)
        self.assertIn("NO HUMAN",result["status"])

    def test_descriptive_real_rows_and_errors_are_not_laundered(self):
        rows=[
            row("R-A","ET-001","manual",120),
            row("R-A","ET-002","manual",180),
            row("R-A","ET-003","assisted",60),
            row("R-A","ET-004","assisted",90,missed=1),
            row("R-B","ET-005","assisted",70),
            row("R-B","ET-006","assisted",110),
            row("R-B","ET-007","manual",200),
            row("R-B","ET-008","manual",160),
        ]
        result=evaluate(rows)
        self.assertTrue(result["claims_authorized"])
        self.assertFalse(result["causal_effect_claim_authorized"])
        self.assertEqual(result["completed_tasks"],8)
        self.assertEqual(result["conditions"]["manual"]["median_seconds"],170)
        self.assertEqual(result["conditions"]["assisted"]["median_seconds"],80)
        self.assertEqual(result["conditions"]["assisted"]["supported_claims_missed"],1)
        self.assertEqual(result["both_arm_reviewers"],2)

    def test_invalid_data_never_produces_a_win_claim(self):
        rows=[row("R-A","ET-001","manual",120)]*8
        with self.assertRaisesRegex(ValueError,"Repeated identical CV"):
            evaluate(rows)
        rows=[row("R-A","ET-001","assisted",120)]
        rows[0]["model_calls"]="1"
        self.assertFalse(evaluate(rows)["claims_authorized"])
        rows[0]["condition"]="auto_reject"
        with self.assertRaisesRegex(ValueError,"Invalid reviewer"):
            evaluate(rows)

    def test_p90_is_observed_not_interpolated(self):
        self.assertEqual(p90([10,20,30,40,50]),50)
        self.assertEqual(median([60,30]),45)

if __name__=="__main__":
    unittest.main()
