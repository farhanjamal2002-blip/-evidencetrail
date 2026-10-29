"""Safe API error classification without network calls."""

from __future__ import annotations

import unittest

import httpx
from openai import APIConnectionError

from app import muse_api_failure_message
from muse_protocol import MuseProtocolError


class MuseApiFailureMessageTests(unittest.TestCase):
    def test_connection_error_points_to_server_network_not_credentials(self):
        error = APIConnectionError(
            message="sensitive provider details",
            request=httpx.Request("POST", "https://api.meta.ai/v1/chat/completions"),
        )

        message = muse_api_failure_message(error)

        self.assertIn("could not reach Meta Model API", message)
        self.assertIn("outbound DNS/HTTPS", message)
        self.assertNotIn("sensitive provider details", message)

    def test_http_statuses_identify_auth_quota_and_service_failures(self):
        class StatusFailure(Exception):
            def __init__(self, status_code):
                super().__init__("private error payload")
                self.status_code = status_code

        expected = {
            401: "credentials",
            403: "permissions",
            429: "quota",
            503: "server error",
        }
        for status_code, phrase in expected.items():
            with self.subTest(status_code=status_code):
                message = muse_api_failure_message(StatusFailure(status_code))
                self.assertIn(phrase, message)
                self.assertNotIn("private error payload", message)

    def test_invalid_model_response_is_distinguished_from_network_failure(self):
        message = muse_api_failure_message(MuseProtocolError("private payload"))
        self.assertIn("failed local schema validation", message)
        self.assertNotIn("private payload", message)


if __name__ == "__main__":
    unittest.main()
