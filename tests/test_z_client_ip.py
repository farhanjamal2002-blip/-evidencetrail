from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import app


class ClientIpRateLimitTests(unittest.TestCase):
    def make_request(self, forwarded: str = "", peer: str = "10.0.0.8"):
        return SimpleNamespace(
            headers={"cf-connecting-ip": forwarded},
            client=SimpleNamespace(host=peer),
        )

    def test_uses_valid_cloudflare_ip_when_explicitly_enabled(self) -> None:
        request = self.make_request("2001:0db8:0:0::1")
        with patch.object(app, "TRUST_CF_CONNECTING_IP", True):
            self.assertEqual(app.client_ip_for_rate_limit(request), "2001:db8::1")

    def test_ignores_forwarded_header_by_default(self) -> None:
        request = self.make_request("198.51.100.24")
        with patch.object(app, "TRUST_CF_CONNECTING_IP", False):
            self.assertEqual(app.client_ip_for_rate_limit(request), "10.0.0.8")

    def test_malformed_forwarded_header_falls_back_to_socket_peer(self) -> None:
        request = self.make_request("198.51.100.24, 203.0.113.5")
        with patch.object(app, "TRUST_CF_CONNECTING_IP", True):
            self.assertEqual(app.client_ip_for_rate_limit(request), "10.0.0.8")

    def test_missing_socket_peer_uses_stable_unknown_bucket(self) -> None:
        request = SimpleNamespace(headers={}, client=None)
        with patch.object(app, "TRUST_CF_CONNECTING_IP", False):
            self.assertEqual(app.client_ip_for_rate_limit(request), "unknown")


if __name__ == "__main__":
    unittest.main()
