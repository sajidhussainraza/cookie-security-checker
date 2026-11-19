"""Tests for cookie_security_checker.py.

Run with:  python3 tests/run_tests.py
Or with pytest:  python3 -m pytest tests/ -q

The mock-server tests run a local fake site in secure and insecure
modes, so they need no internet. The live test audits github.com
and is skipped automatically when the network is unreachable.
"""

import http.server
import socket
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cookie_security_checker import (  # noqa: E402
    audit, check_cookie, grade,
)
from http.cookies import SimpleCookie  # noqa: E402

SECURE_COOKIES = [
    "session_id=abc123; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600",
    "prefs=dark; Secure; HttpOnly; SameSite=Lax; Path=/; Max-Age=86400",
]
INSECURE_COOKIES = [
    "session_id=abc123; Path=/",
    "auth_token=xyz; SameSite=None; Path=/",
    "tracking=1; Max-Age=63072000; Domain=.example.test; Path=/",
    "__Host-bad=1; Path=/account",
]


class CookieHandler(http.server.BaseHTTPRequestHandler):
    mode = "secure"

    def do_GET(self):
        cookies = SECURE_COOKIES if self.mode == "secure" else INSECURE_COOKIES
        self.send_response(200)
        for cookie in cookies:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body>ok</body></html>")

    def log_message(self, *args):
        pass


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class TestCheckCookie(unittest.TestCase):
    def _morsel(self, header):
        jar = SimpleCookie()
        jar.load(header)
        return next(iter(jar.values()))

    def test_fully_hardened_cookie_has_no_findings(self):
        cookie = self._morsel(
            "session_id=abc; Secure; HttpOnly; SameSite=Strict; Path=/")
        self.assertEqual(check_cookie(cookie, "example.com", True), [])

    def test_missing_secure_and_httponly_are_high_for_session_cookie(self):
        cookie = self._morsel("session_id=abc; Path=/")
        findings = check_cookie(cookie, "example.com", True)
        by_check = {f.check: f.severity for f in findings}
        self.assertEqual(by_check["Secure"], "high")
        self.assertEqual(by_check["HttpOnly"], "high")

    def test_missing_flags_are_medium_for_plain_cookie(self):
        cookie = self._morsel("theme=dark; Path=/")
        findings = check_cookie(cookie, "example.com", True)
        by_check = {f.check: f.severity for f in findings}
        self.assertEqual(by_check["Secure"], "medium")
        self.assertEqual(by_check["HttpOnly"], "medium")

    def test_samesite_none_without_secure_is_high(self):
        cookie = self._morsel(
            "auth_token=xyz; HttpOnly; SameSite=None; Path=/")
        findings = check_cookie(cookie, "example.com", True)
        self.assertTrue(any(f.check == "SameSite" and f.severity == "high"
                            for f in findings))

    def test_host_prefix_without_secure_path_and_domain_rules(self):
        cookie = self._morsel("__Host-bad=1; Domain=example.com; Path=/account")
        findings = check_cookie(cookie, "example.com", True)
        prefix = [f for f in findings if f.check == "Prefix"]
        self.assertEqual(len(prefix), 3)

    def test_secure_prefix_without_secure_flag_is_high(self):
        cookie = self._morsel("__Secure-x=1; HttpOnly; SameSite=Lax; Path=/")
        findings = check_cookie(cookie, "example.com", True)
        self.assertTrue(any(f.check == "Prefix" and f.severity == "high"
                            for f in findings))

    def test_two_year_expiry_is_flagged(self):
        cookie = self._morsel(
            "tracking=1; Secure; HttpOnly; SameSite=Lax; Max-Age=63072000")
        findings = check_cookie(cookie, "example.com", True)
        self.assertTrue(any(f.check == "Expiry" for f in findings))

    def test_leading_dot_domain_is_flagged(self):
        cookie = self._morsel(
            "x=1; Secure; HttpOnly; SameSite=Lax; Domain=.example.com")
        findings = check_cookie(cookie, "example.com", True)
        self.assertTrue(any(f.check == "Domain" for f in findings))


class TestGrade(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(grade(100), "A")
        self.assertEqual(grade(90), "A")
        self.assertEqual(grade(89), "B")
        self.assertEqual(grade(75), "B")
        self.assertEqual(grade(60), "C")
        self.assertEqual(grade(40), "D")
        self.assertEqual(grade(39), "F")


class TestLiveAudit(unittest.TestCase):
    def _run_server(self, mode):
        CookieHandler.mode = mode
        port = free_port()
        server = http.server.HTTPServer(("127.0.0.1", port), CookieHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, port

    def test_secure_site_scores_100(self):
        server, port = self._run_server("secure")
        try:
            report = audit("http://127.0.0.1:%d/" % port)
        finally:
            server.shutdown()
        # Plain HTTP, so Secure is not expected; only HttpOnly/SameSite
        # matter here, and both are set on the secure fixture.
        self.assertEqual(report["cookies"], 2)
        self.assertEqual(report["score"], 100)
        self.assertEqual(report["grade"], "A")

    def test_insecure_site_scores_low_with_high_findings(self):
        server, port = self._run_server("insecure")
        try:
            report = audit("http://127.0.0.1:%d/" % port)
        finally:
            server.shutdown()
        self.assertEqual(report["cookies"], 4)
        self.assertLess(report["score"], 40)
        self.assertEqual(report["grade"], "F")
        severities = {f.severity for f in report["findings"]}
        self.assertIn("high", severities)

    def test_live_github_audit(self):
        try:
            report = audit("https://github.com")
        except OSError:
            self.skipTest("network unreachable")
        self.assertGreaterEqual(report["cookies"], 1)
        self.assertIn("score", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
