"""Zero-network tests for the local Muse-shaped response boundary."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from muse_protocol import (
    MuseProtocolError,
    decode_chat_json_response,
    validate_mapping_result,
    validate_verification_result,
)


def fake_response(
    content: object,
    *,
    finish_reason: str | None = "stop",
    refusal: str | None = None,
    choices: int = 1,
    usage: object | None = None,
) -> SimpleNamespace:
    message = SimpleNamespace(content=content, refusal=refusal)
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    return SimpleNamespace(
        choices=[choice for _ in range(choices)],
        usage=usage or SimpleNamespace(prompt_tokens=23, completion_tokens=11),
    )


def valid_mapping() -> dict[str, object]:
    return {
        "requirements": [
            {
                "requirement": "At least five years of Python experience",
                "evidence": [
                    {
                        "quote": "Python experience: 8 years",
                        "role": "supports",
                        "page_hint": 1,
                    }
                ],
            }
        ],
        "application_claims": [],
        "employment_episodes": [],
        "experience_claims": [],
    }


def valid_verification() -> tuple[dict[str, object], dict[str, object]]:
    payload: dict[str, object] = {
        "requirements": [{"id": "R1", "text": "Python", "source_span_ids": ["S1"]}],
        "application_claims": [],
        "source_spans": [{"id": "S1", "text": "Python experience: 8 years"}],
    }
    result: dict[str, object] = {
        "reviews": [
            {
                "requirement_id": "R1",
                "status": "supported",
                "evidence_type": "direct",
                "evidence_strength": "stated",
                "transfer_explanation": None,
                "unproven_aspects": [],
                "follow_up_question": None,
                "certainty": "clear",
                "reason": "The source span states Python experience.",
                "evidence": [
                    {"source_id": "S1", "quote": "Python experience: 8 years", "role": "supports"}
                ],
            }
        ],
        "application_reviews": [],
    }
    return result, payload


class MuseProtocolTests(unittest.TestCase):
    def test_accepts_one_completed_json_response_and_normalizes_usage(self) -> None:
        response = fake_response(
            json.dumps(valid_mapping()),
            usage=SimpleNamespace(prompt_tokens=23, completion_tokens=11),
        )
        decoded, usage = decode_chat_json_response(response, response_name="map")
        validate_mapping_result(decoded, max_application_claims=12)
        self.assertEqual(decoded, valid_mapping())
        self.assertEqual(usage, {
            "input_tokens": 23,
            "output_tokens": 11,
            "cached_input_tokens": 0,
            "reasoning_tokens": 0,
        })

    def test_optional_cached_and_reasoning_usage_is_reported(self) -> None:
        response = fake_response(
            json.dumps(valid_mapping()),
            usage=SimpleNamespace(
                prompt_tokens=230,
                completion_tokens=110,
                prompt_tokens_details=SimpleNamespace(cached_tokens=160),
                completion_tokens_details=SimpleNamespace(reasoning_tokens=87),
            ),
        )
        _decoded, usage = decode_chat_json_response(response, response_name="map")
        self.assertEqual(usage, {
            "input_tokens": 230,
            "output_tokens": 110,
            "cached_input_tokens": 160,
            "reasoning_tokens": 87,
        })

    def test_rejects_refusal_truncation_ambiguous_choices_and_non_text_content(self) -> None:
        cases = [
            (fake_response(json.dumps(valid_mapping()), refusal="refused"), "refusal"),
            (fake_response('{"requirements":', finish_reason="length"), "truncation"),
            (fake_response("{}", choices=2), "multiple choices"),
            (fake_response(None), "missing content"),
            (fake_response("[]"), "wrong root type"),
            (fake_response("x" * 128_001), "oversized content"),
        ]
        for response, label in cases:
            with self.subTest(label=label), self.assertRaises(MuseProtocolError):
                decode_chat_json_response(response, response_name="map")

    def test_rejects_malformed_json_duplicate_keys_and_non_json_numbers(self) -> None:
        for content in (
            "{not json}",
            '{"requirements": [], "requirements": [], "application_claims": [], "employment_episodes": [], "experience_claims": []}',
            '{"requirements": NaN, "application_claims": [], "employment_episodes": [], "experience_claims": []}',
        ):
            with self.subTest(content=content), self.assertRaises(MuseProtocolError):
                decode_chat_json_response(fake_response(content), response_name="map")

    def test_extreme_json_nesting_is_rejected_without_leaking_recursion_errors(self) -> None:
        content = "[" * 2_000 + "]" * 2_000
        with self.assertRaises(MuseProtocolError):
            decode_chat_json_response(fake_response(content), response_name="map")

    def test_mapping_validator_rejects_bad_types_unknown_fields_and_resource_bombs(self) -> None:
        malformed = []
        item = valid_mapping()
        item["unexpected"] = "ignore this extra field"
        malformed.append(item)
        item = valid_mapping()
        item["requirements"] = [{"requirement": ["Python"], "evidence": []}]
        malformed.append(item)
        item = valid_mapping()
        item["requirements"] = [
            {
                "requirement": "Python",
                "evidence": [{"quote": "Python", "role": "supports", "page_hint": True}],
            }
        ]
        malformed.append(item)
        item = valid_mapping()
        item["requirements"] = [
            {"requirement": "Python", "evidence": [{"quote": "Python", "role": [], "page_hint": 1}]}
        ]
        malformed.append(item)
        item = valid_mapping()
        item["requirements"] = [
            {"requirement": "Python", "evidence": [
                {"quote": "Python", "role": "supports", "page_hint": 1}
                for _ in range(13)
            ]}
        ]
        malformed.append(item)
        item = valid_mapping()
        item["requirements"] = [
            {"requirement": f"Requirement {index}", "evidence": []}
            for index in range(81)
        ]
        malformed.append(item)
        for candidate in malformed:
            with self.subTest(candidate=candidate), self.assertRaises(MuseProtocolError):
                validate_mapping_result(candidate, max_application_claims=12)

    def test_mapping_validator_accepts_bounded_timeline_proposals(self) -> None:
        candidate = valid_mapping()
        candidate["employment_episodes"] = [{
            "role": "Procurement Analyst",
            "company": "Example Corp",
            "start_date": "2018",
            "end_date": "2024",
            "date_quote": "Procurement Analyst | 2018–2024",
            "scope_quote": "Managed procurement contracts and vendor bids.",
            "experience_areas": ["procurement", "contracts"],
            "page_hint": 1,
        }]
        candidate["experience_claims"] = [{
            "topic": "procurement",
            "claim_quote": "Profile: 12 years in procurement.",
            "page_hint": 1,
        }]
        validate_mapping_result(candidate, max_application_claims=12)

    def test_verification_validator_requires_exact_unique_ids_and_valid_citations(self) -> None:
        result, payload = valid_verification()
        validate_verification_result(result, payload, max_application_claims=12)

        wrong_id = json.loads(json.dumps(result))
        wrong_id["reviews"][0]["requirement_id"] = "R999"
        duplicate = json.loads(json.dumps(result))
        duplicate["reviews"].append(duplicate["reviews"][0])
        invalid_enum = json.loads(json.dumps(result))
        invalid_enum["reviews"][0]["status"] = "probably"
        invalid_source = json.loads(json.dumps(result))
        invalid_source["reviews"][0]["evidence"][0]["source_id"] = ""
        invalid_evidence = json.loads(json.dumps(result))
        invalid_evidence["reviews"][0]["evidence"] = {"source_id": "S1"}

        for candidate in (wrong_id, duplicate, invalid_enum, invalid_source, invalid_evidence):
            with self.subTest(candidate=candidate), self.assertRaises(MuseProtocolError):
                validate_verification_result(candidate, payload, max_application_claims=12)

    def test_absent_or_malformed_usage_never_crashes_protocol_parsing(self) -> None:
        response = fake_response(
            json.dumps(valid_mapping()),
            usage=SimpleNamespace(prompt_tokens=-4, completion_tokens="unknown"),
        )
        _decoded, usage = decode_chat_json_response(response, response_name="map")
        self.assertEqual(usage, {
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_input_tokens": 0,
            "reasoning_tokens": 0,
        })


if __name__ == "__main__":
    unittest.main()
