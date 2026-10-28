"""Deterministic date arithmetic tests; no model or network access."""

from __future__ import annotations

import unittest
from datetime import date

from timeline_audit import audit_employment_timeline, parse_date_bound


def quote_locator(quote, pages, page_hint):
    candidates = pages
    if page_hint is not None:
        candidates = [page for page in pages if page["number"] == page_hint]
    for page in candidates:
        if quote and quote in page["text"]:
            return {"page": page["number"], "boxes": []}
    return None


class EmploymentTimelineTests(unittest.TestCase):
    def test_year_only_dates_use_half_open_boundaries(self):
        today = date(2026, 10, 28)
        self.assertEqual(parse_date_bound("2018", end=False, as_of=today), (2018 * 12, "year"))
        self.assertEqual(parse_date_bound("2024", end=True, as_of=today), (2024 * 12, "year"))
        self.assertEqual(parse_date_bound("May 2021", end=False, as_of=today), (2021 * 12 + 4, "month"))
        self.assertEqual(parse_date_bound("May 2021", end=True, as_of=today), (2021 * 12 + 5, "month"))
        self.assertEqual(parse_date_bound("Present", end=True, as_of=today), (2026 * 12 + 10, "current_month"))

    def test_tenure_unions_adjacent_roles_and_flags_excess_claim(self):
        pages = [{
            "number": 1,
            "text": "Procurement Analyst | 2018–2024\nBuyer | 2024–2026\nProfile: 12 years in procurement and contract work.",
        }]
        episodes = [
            {
                "role": "Procurement Analyst", "company": "", "start_date": "2018",
                "end_date": "2024", "date_quote": "Procurement Analyst | 2018–2024",
                "scope_quote": None, "experience_areas": [], "page_hint": 1,
            },
            {
                "role": "Buyer", "company": "", "start_date": "2024",
                "end_date": "2026", "date_quote": "Buyer | 2024–2026",
                "scope_quote": None, "experience_areas": [], "page_hint": 1,
            },
        ]
        claims = [{
            "topic": "procurement and contract work",
            "claim_quote": "Profile: 12 years in procurement and contract work.",
            "page_hint": 1,
        }]
        result = audit_employment_timeline(episodes, claims, pages, quote_locator, as_of=date(2026, 10, 28))
        self.assertEqual(result["dated_employment_months"], 96)
        self.assertEqual(result["overlaps"], [])
        self.assertEqual(result["experience_claims"][0]["documented_months"], 96)
        self.assertEqual(result["flags"][0]["type"], "claimed_tenure_exceeds_dated_evidence")

    def test_concurrent_roles_are_flagged_and_counted_once(self):
        pages = [{"number": 1, "text": "Analyst | 2020–2022\nConsultant | 2021–2023"}]
        episodes = [
            {
                "role": "Analyst", "company": "", "start_date": "2020", "end_date": "2022",
                "date_quote": "Analyst | 2020–2022", "scope_quote": None,
                "experience_areas": [], "page_hint": 1,
            },
            {
                "role": "Consultant", "company": "", "start_date": "2021", "end_date": "2023",
                "date_quote": "Consultant | 2021–2023", "scope_quote": None,
                "experience_areas": [], "page_hint": 1,
            },
        ]
        result = audit_employment_timeline(episodes, [], pages, quote_locator, as_of=date(2026, 10, 28))
        self.assertEqual(result["dated_employment_months"], 36)
        self.assertEqual(result["overlaps"][0]["overlap_months"], 12)
        self.assertEqual(result["flags"][0]["type"], "employment_date_overlap")
        self.assertIn("part-time", result["flags"][0]["review_note"])

    def test_unanchored_or_mismatched_dates_are_excluded(self):
        pages = [{"number": 1, "text": "Analyst | 2018–2022"}]
        episodes = [{
            "role": "Analyst", "company": "", "start_date": "2018", "end_date": "2024",
            "date_quote": "Analyst | 2018–2022", "scope_quote": None,
            "experience_areas": [], "page_hint": 1,
        }]
        result = audit_employment_timeline(episodes, [], pages, quote_locator, as_of=date(2026, 10, 28))
        self.assertEqual(result["episodes"], [])
        self.assertEqual(result["dated_employment_months"], 0)
        self.assertEqual(result["excluded_proposals"][0]["reason"], "dates_do_not_match_quote")

    def test_area_tenure_requires_a_quote_verified_work_scope_not_a_title(self):
        pages = [{
            "number": 1,
            "text": "Procurement Analyst | 2020–2024\nManaged procurement contracts and vendor bids.",
        }]
        episode = {
            "role": "Procurement Analyst", "company": "", "start_date": "2020",
            "end_date": "2024", "date_quote": "Procurement Analyst | 2020–2024",
            "scope_quote": "Managed procurement contracts and vendor bids.",
            "experience_areas": ["procurement", "contracts"], "page_hint": 1,
        }
        result = audit_employment_timeline([episode], [], pages, quote_locator, as_of=date(2026, 10, 28))
        self.assertEqual(result["tenure_by_area"], [
            {"area": "contracts", "months": 48},
            {"area": "procurement", "months": 48},
        ])

        title_only = dict(episode, scope_quote="Procurement Analyst", experience_areas=["procurement"])
        title_result = audit_employment_timeline([title_only], [], pages, quote_locator, as_of=date(2026, 10, 28))
        self.assertEqual(title_result["tenure_by_area"], [])

    def test_duration_ranges_are_not_collapsed_to_a_single_number(self):
        quote = "Profile: between 5 and 7 years in procurement."
        pages = [{"number": 1, "text": quote}]
        result = audit_employment_timeline([], [{
            "topic": "procurement", "claim_quote": quote, "page_hint": 1,
        }], pages, quote_locator, as_of=date(2026, 10, 28))
        self.assertEqual(result["experience_claims"], [])
        self.assertEqual(result["excluded_proposals"][0]["reason"], "claim_duration_or_topic_missing")

if __name__ == "__main__":
    unittest.main()
