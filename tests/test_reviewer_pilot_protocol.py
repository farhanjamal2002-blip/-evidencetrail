"""No measured impact result may be fabricated from pilot assignments."""
from __future__ import annotations
import unittest

from scripts.prepare_recruiter_pilot_packets import assignments,packet,CRITERIA
from scripts.summarize_recruiter_pilot import report


class ReviewerPilotTests(unittest.TestCase):
    def test_counterbalance(self):
        rows=assignments()
        self.assertEqual(len(rows),24)
        self.assertEqual(len({x["candidate_id"] for x in rows}),12)
        self.assertEqual(len(CRITERIA),4)
        reviewers={x["reviewer_code"] for x in rows}
        self.assertEqual(len(reviewers),4)
        for reviewer in reviewers:
            arm=[x["condition"] for x in rows if x["reviewer_code"]==reviewer]
            self.assertEqual(arm.count("manual"),3)
            self.assertEqual(arm.count("assisted"),3)
        for candidate in {x["candidate_id"] for x in rows}:
            arm=[x["condition"] for x in rows if x["candidate_id"]==candidate]
            self.assertEqual(set(arm),{"manual","assisted"})
            self.assertEqual(len(arm),2)

    def test_no_observations_no_savings(self):
        result=report(None)
        self.assertEqual(result["status"],"NOT MEASURED")
        self.assertIsNone(result["median_time_saved_fraction"])
        self.assertEqual(result["human_tasks_completed"],0)

    def test_incomplete_pilot_is_rejected(self):
        rows=assignments()
        one=dict(rows[0],completed=True,active_seconds=90,
                 reviewer_findings=["supported"]*4)
        with self.assertRaisesRegex(ValueError,"Missing predeclared assignments"):
            report([one])

    def test_arm_mismatch_and_duplicate_are_rejected(self):
        rows=assignments()
        observed=[]
        for r in rows:
            observed.append({
                "reviewer_code":r["reviewer_code"],
                "candidate_id":r["candidate_id"],
                "condition":r["condition"],
                "completed":True,
                "active_seconds":115,
                "reviewer_findings":["uncertain"]*4,
            })
        self.assertIsNone(report(observed)["independent_evidence_adjudication"]["manual"]["false_supported_count"])
        observed[0]["condition"]="bogus"
        with self.assertRaisesRegex(ValueError,"Condition does not match"):
            report(observed)
        observed[0]["condition"]=rows[0]["condition"]
        with self.assertRaisesRegex(ValueError,"duplicate"):
            report(observed+[observed[0]])

    def test_hypothetical_observations_cannot_be_confused_with_live_data(self):
        rows=assignments()
        simulated=[{
            "reviewer_code":r["reviewer_code"],"candidate_id":r["candidate_id"],
            "condition":r["condition"],"completed":True,
            "active_seconds":120 if r["condition"]=="manual" else 80,
            "reviewer_findings":["uncertain"]*4,
        } for r in rows]
        result=report(simulated)
        self.assertEqual(result["manual_median_active_seconds"],120)
        self.assertEqual(result["assisted_median_active_seconds"],80)
        self.assertEqual(result["median_time_saved_fraction"],0.333)
        self.assertEqual(result["status"],"EXPLORATORY HUMAN RESULTS — NOT GENERALIZABLE")
        # This example is ONLY a unit test with synthetic timings, never a study result.

    def test_packet_does_not_contain_fake_outcome(self):
        markdown, rows=packet()
        self.assertEqual(len(rows),24)
        self.assertIn("These are assignments, not results",markdown)
        self.assertIn("R04",markdown)


if __name__=="__main__":
    unittest.main()
