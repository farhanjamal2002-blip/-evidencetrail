"""Meta Model API request-shape tests; the fake client makes no network calls."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import app


def fake_response(payload: dict) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason="stop",
                message=SimpleNamespace(content=json.dumps(payload), refusal=None),
            )
        ],
        usage=SimpleNamespace(prompt_tokens=17, completion_tokens=9),
    )


class MuseRequestContractTests(unittest.TestCase):
    def test_minimal_reasoning_tier_is_supported_for_controlled_latency_trials(self):
        self.assertEqual(app.parse_muse_reasoning_effort(" minimal "), "minimal")
        self.assertEqual(app.parse_muse_reasoning_effort("LOW"), "low")
        self.assertEqual(app.parse_muse_reasoning_effort(None), "minimal")
        with self.assertRaisesRegex(RuntimeError, "minimal, low, medium, high, xhigh"):
            app.parse_muse_reasoning_effort("none")

    @staticmethod
    def sample_pages():
        words = []
        text = "Used Python for six years."
        x = 10.0
        for token in text.split():
            width = max(12.0, len(token) * 5.0)
            words.append(
                app.word_record(
                    token,
                    x,
                    10,
                    x + width,
                    20,
                    block_id="b1",
                    line_id="b1:l1",
                )
            )
            x += width + 2
        return [{"number": 1, "text": text, "words": words, "blocks": [text], "ocr_used": False}]

    def run_fake_request(self, function, response_payload, *args):
        client = Mock()
        client.chat.completions.create.return_value = fake_response(response_payload)
        with (
            patch.object(app, "_muse_client", None),
            patch.object(app, "_muse_client_api_key", None),
            patch.object(app, "OpenAI", return_value=client),
            patch.object(app, "MOCK_PROVIDER_ENABLED", False),
            patch.dict("os.environ", {"MODEL_API_KEY": "unit-test-key"}),
        ):
            result, usage = function(*args)
        return result, usage, client.chat.completions.create.call_args.kwargs

    def test_muse_client_is_reused_and_initialized_once_across_threads(self):
        from concurrent.futures import ThreadPoolExecutor

        client = object()
        with (
            patch.object(app, "_muse_client", None),
            patch.object(app, "_muse_client_api_key", None),
            patch.object(app, "OpenAI", return_value=client) as openai,
        ):
            with ThreadPoolExecutor(max_workers=5) as pool:
                clients = list(pool.map(
                    lambda _index: app.get_muse_client("unit-test-key"),
                    range(10),
                ))

        self.assertTrue(all(item is client for item in clients))
        openai.assert_called_once_with(
            base_url=app.API_BASE_URL,
            api_key="unit-test-key",
            max_retries=0,
            timeout=90.0,
        )

    def test_mapping_pass_uses_developer_prompt_and_json_schema(self):
        payload = {
            "requirements": [],
            "application_claims": [],
            "employment_episodes": [],
            "experience_claims": [],
        }
        result, usage, request = self.run_fake_request(
            app.call_muse, payload, self.sample_pages(), "A procurement role"
        )

        self.assertEqual(result, payload)
        self.assertEqual(
            {key: usage[key] for key in ("input_tokens", "output_tokens")},
            {"input_tokens": 17, "output_tokens": 9},
        )
        self.assertGreaterEqual(usage["api_latency_ms"], 0)
        for timing_key in (
            "client_setup_ms",
            "prompt_build_ms",
            "response_decode_ms",
            "response_validation_ms",
        ):
            self.assertGreaterEqual(usage[timing_key], 0)
        self.assertEqual(usage["cv_page_count"], 1)
        self.assertEqual(usage["cv_ocr_page_count"], 0)
        self.assertGreater(usage["cv_text_characters"], 0)
        self.assertEqual(request["messages"][0], {
            "role": "developer", "content": app.SYSTEM_PROMPT
        })
        self.assertEqual(request["response_format"], app.OUTPUT_SCHEMA)
        self.assertEqual(request["model"], app.MODEL_ID)
        self.assertEqual(request["reasoning_effort"], app.MUSE_REASONING_EFFORT)
        self.assertEqual(request["prompt_cache_key"], app.MUSE_ANALYSIS_CACHE_KEY)
        self.assertFalse(request["store"])
        self.assertIsInstance(request["messages"][1]["content"], str)
        self.assertIn("[Page 1]", request["messages"][1]["content"])
        self.assertIn("Used Python for six years.", request["messages"][1]["content"])
        self.assertNotIn("file_data", str(request["messages"][1]))

    def test_local_cv_text_packet_keeps_visual_columns_separate(self):
        words = []
        for line_id, y, x, tokens in (
            ("left-1", 10, 10, ("Left", "column", "work")),
            ("right-1", 10, 300, ("Right", "column", "dates")),
            ("left-2", 30, 10, ("Vendor", "contracts")),
            ("right-2", 30, 300, ("Education", "history")),
        ):
            for token in tokens:
                width = max(12.0, len(token) * 5.0)
                words.append(
                    app.word_record(
                        token,
                        x,
                        y,
                        x + width,
                        y + 10,
                        block_id=line_id,
                        line_id=line_id,
                    )
                )
                x += width + 2

        packet = app.format_cv_text_for_model(
            [{"number": 1, "words": words, "text": "", "ocr_used": False}]
        )
        self.assertIn("[Text region 1]\nLeft column work\nVendor contracts", packet)
        self.assertIn("[Text region 2]\nRight column dates\nEducation history", packet)
        self.assertNotIn("Left column work Right column dates", packet)

    def test_mapping_pass_aligns_every_cv_to_the_shared_batch_rubric(self):
        rubric = [
            "At least five years of Python experience",
            "Current AWS Solutions Architect certification",
        ]
        payload = {
            "requirements": [
                {
                    "requirement": rubric[0],
                    "status": "supported",
                    "evidence_type": "direct",
                    "evidence_strength": "specific",
                    "transfer_explanation": None,
                    "unproven_aspects": [],
                    "follow_up_question": None,
                    "certainty": "clear",
                    "reason": "The CV states the duration and names the tool.",
                    "evidence": [{"quote": "Used Python for six years.", "role": "supports", "page_hint": 1}],
                },
                {
                    "requirement": "A model-invented extra requirement",
                    "status": "not_found",
                    "evidence_type": "unsupported",
                    "evidence_strength": "none",
                    "transfer_explanation": None,
                    "unproven_aspects": [],
                    "follow_up_question": "Can you describe relevant experience?",
                    "certainty": "clear",
                    "reason": "No relevant passage was found.",
                    "evidence": [{"quote": "Invented quote.", "role": "supports", "page_hint": 1}],
                },
            ],
            "application_claims": [],
            "employment_episodes": [],
            "experience_claims": [],
        }
        result, _usage, request = self.run_fake_request(
            app.call_muse,
            payload,
            self.sample_pages(),
            "Requirements:\n1. At least five years of Python experience\n2. Current AWS Solutions Architect certification",
            "",
            rubric,
        )

        self.assertEqual([item["requirement"] for item in result["requirements"]], rubric)
        self.assertEqual(result["requirements"][0]["evidence"][0]["quote"], "Used Python for six years.")
        self.assertEqual(result["requirements"][1]["evidence"], [])
        self.assertEqual(result["batch_rubric_alignment"]["missing_model_entries"], 1)
        self.assertEqual(result["batch_rubric_alignment"]["extra_model_entries_dropped"], 1)
        self.assertIn("criteria are shared and fixed", request["messages"][0]["content"])
        self.assertIn("SHARED BATCH REQUIREMENTS", request["messages"][1]["content"])

    def test_prompts_separate_named_system_use_from_concrete_analogous_work(self):
        prompt = " ".join(app.SYSTEM_PROMPT.split())
        self.assertIn("concrete analogous work passage", prompt)
        self.assertIn(
            "purchase-order changes and supplier-record maintenance may relate",
            prompt,
        )
        self.assertIn("do not prove supplier selection", prompt)
        self.assertIn("treat the list disjunctively", prompt)
        self.assertIn("dated role and a concrete same-role duty", prompt)
        self.assertIn("use keyword_only when only a matching skills-list item", prompt)
        self.assertIn("Use none only when the CV contains no matching mention", prompt)
        self.assertIn("use Related when it describes concrete work", app.VERIFIER_SYSTEM_PROMPT)
        self.assertIn("name the exact system as unproven", app.VERIFIER_SYSTEM_PROMPT)

    def test_verification_pass_uses_developer_prompt_and_json_schema(self):
        payload = {"reviews": [], "application_reviews": []}
        verification_input = {
            "requirements": [], "application_claims": [], "source_spans": []
        }
        result, usage, request = self.run_fake_request(
            app.call_muse_verification, payload, verification_input
        )

        self.assertEqual(result, payload)
        self.assertEqual(usage, {
            "input_tokens": 17,
            "output_tokens": 9,
            "cached_input_tokens": 0,
            "reasoning_tokens": 0,
        })
        self.assertEqual(request["messages"][0], {
            "role": "developer", "content": app.VERIFIER_SYSTEM_PROMPT
        })
        self.assertEqual(request["response_format"], app.VERIFIER_SCHEMA)
        self.assertEqual(request["model"], app.MODEL_ID)
        self.assertEqual(request["reasoning_effort"], app.MUSE_REASONING_EFFORT)
        self.assertEqual(request["prompt_cache_key"], app.MUSE_VERIFICATION_CACHE_KEY)
        self.assertFalse(request["store"])


if __name__ == "__main__":
    unittest.main()
