#!/usr/bin/env python3
"""Cookie Security Checker.

A small, dependency-free Python CLI that audits a website's cookies
against the standard hardening rules: Secure, HttpOnly and SameSite
flags, __Secure- / __Host- prefix rules, sensible expiry, and a
narrow Domain/Path scope. It grades the site A-F and explains each
finding in plain language, so students and small teams can see
exactly where a session cookie invites theft or abuse and how to fix
it.

Standard library only (``http.client``, ``ssl``, ``urllib.parse``).
No third-party packages, no telemetry, nothing is stored. The checker
only sends read-only GET requests, follows redirects itself so it can
collect the Set-Cookie headers sent at every hop, and never logs in
or submits data.
"""

import argparse
import http.client
import json
import ssl
import sys
from http.cookies import SimpleCookie
from urllib.parse import urlparse

VERSION = "1.0.0"
MAX_REDIRECTS = 5
MAX_COOKIE_AGE_DAYS = 365

SEVERITY_WEIGHTS = {"high": 25, "medium": 10, "low": 3}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# Cookie names that usually carry a session or an auth token. A
# missing HttpOnly or Secure flag hurts more on these than on a
# harmless preference cookie.
SESSION_NAME_HINTS = (
    "session", "sess", "auth", "token", "sid", "login", "csrf",
    "xsrf", "remember", "jwt", "access", "refresh", "account",
)


class Finding:
    """One cookie problem, with a severity and a suggested fix."""

    def __init__(self, severity, cookie, check, message, fix):
        self.severity = severity
        self.cookie = cookie
        self.check = check
        self.message = message
        self.fix = fix

    def to_dict(self):
        return {
            "severity": self.severity,
            "cookie": self.cookie,
            "check": self.check,
            "message": self.message,
            "fix": self.fix,
        }


def grade(score):
    """Map a 0-100 score to a letter grade."""
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def is_session_cookie(name):
    """True when the name looks like it carries a session or token."""
    lowered = name.lower()
    return any(hint in lowered for hint in SESSION_NAME_HINTS)


def parse_max_age(attrs):
    """Return Max-Age in seconds as an int, or None if absent/invalid."""
    raw = attrs.get("max-age")
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def check_cookie(cookie, host, is_https):
    """Audit one parsed cookie and return a list of Findings."""
    findings = []
    name = cookie.key
    attrs = {k.lower(): v for k, v in cookie.items()}
    session_like = is_session_cookie(name)

    # --- Secure flag -------------------------------------------------
    if is_https and not attrs.get("secure"):
        severity = "high" if session_like else "medium"
        findings.append(Finding(
            severity, name, "Secure",
            "Cookie is set without the Secure flag, so a browser may "
            "send it over plain HTTP where it can be intercepted.",
            "Set the Secure flag on every cookie served over HTTPS.",
        ))

    # --- HttpOnly flag -----------------------------------------------
    if not attrs.get("httponly"):
        severity = "high" if session_like else "medium"
        findings.append(Finding(
            severity, name, "HttpOnly",
            "Cookie is readable by JavaScript, so a cross-site "
            "scripting (XSS) flaw can steal it.",
            "Set the HttpOnly flag unless JavaScript genuinely needs "
            "to read this cookie.",
        ))

    # --- SameSite attribute ------------------------------------------
    samesite = (attrs.get("samesite") or "").lower()
    if not samesite:
        findings.append(Finding(
            "medium", name, "SameSite",
            "Cookie has no SameSite attribute, so browsers fall back "
            "to Lax and the cookie may still ride along on some "
            "cross-site requests.",
            "Set SameSite=Lax for most cookies, or SameSite=Strict "
            "for cookies that only the site itself needs.",
        ))
    elif samesite == "none" and not attrs.get("secure"):
        findings.append(Finding(
            "high", name, "SameSite",
            "SameSite=None requires the Secure flag; without it "
            "browsers reject the cookie entirely.",
            "Add the Secure flag, or change SameSite to Lax.",
        ))
    elif samesite not in ("lax", "strict", "none"):
        findings.append(Finding(
            "low", name, "SameSite",
            "SameSite has an unrecognised value %r." % samesite,
            "Use SameSite=Lax, Strict or None.",
        ))

    # --- __Secure- / __Host- prefixes --------------------------------
    lowered_name = name.lower()
    if lowered_name.startswith("__secure-") and not attrs.get("secure"):
        findings.append(Finding(
            "high", name, "Prefix",
            "__Secure- cookies must carry the Secure flag; browsers "
            "reject them otherwise.",
            "Add the Secure flag, or drop the __Secure- prefix.",
        ))
    if lowered_name.startswith("__host-"):
        if not attrs.get("secure"):
            findings.append(Finding(
                "high", name, "Prefix",
                "__Host- cookies must carry the Secure flag; browsers "
                "reject them otherwise.",
                "Add the Secure flag, or drop the __Host- prefix.",
            ))
        if attrs.get("domain"):
            findings.append(Finding(
                "high", name, "Prefix",
                "__Host- cookies must not carry a Domain attribute; "
                "browsers reject them otherwise.",
                "Remove the Domain attribute, or drop the __Host- "
                "prefix.",
            ))
        if (attrs.get("path") or "") != "/":
            findings.append(Finding(
                "high", name, "Prefix",
                "__Host- cookies must use Path=/; browsers reject "
                "them otherwise.",
                "Set Path=/, or drop the __Host- prefix.",
            ))

    # --- Expiry --------------------------------------------------------
    max_age = parse_max_age(attrs)
    if max_age is not None and max_age > MAX_COOKIE_AGE_DAYS * 86400:
        findings.append(Finding(
            "low", name, "Expiry",
            "Cookie lives for %d days; a stolen cookie stays useful "
            "for that whole time." % (max_age // 86400),
            "Keep Max-Age under a year, and much shorter for "
            "session cookies.",
        ))
    if max_age is not None and max_age < 0:
        findings.append(Finding(
            "low", name, "Expiry",
            "Cookie has a negative Max-Age, so it is deleted at once.",
            "Remove the cookie or set a positive Max-Age.",
        ))

    # --- Domain scope --------------------------------------------------
    domain = attrs.get("domain") or ""
    if domain:
        stripped = domain.lstrip(".")
        if stripped != host and not host.endswith("." + stripped):
            findings.append(Finding(
                "low", name, "Domain",
                "Cookie Domain %r does not match this host %r."
                % (domain, host),
                "Set Domain to the site's own host, or drop it.",
            ))
        elif domain.startswith("."):
            findings.append(Finding(
                "low", name, "Domain",
                "Cookie is shared with every subdomain of %r, which "
                "widens the blast radius if any subdomain is "
                "compromised." % domain,
                "Drop the leading dot and the Domain attribute unless "
                "subdomains genuinely need the cookie.",
            ))

    return findings


def fetch_cookies(url):
    """GET a URL, follow redirects, and collect Set-Cookie headers.

    Returns (final_url, is_https, cookies, status, hops) where cookies
    is a list of http.cookies.Morsel objects. Raises ValueError for a
    bad URL and OSError for network failures.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("URL must start with http:// or https://")

    current = parsed
    cookies = []
    status = None
    hops = 0
    for _ in range(MAX_REDIRECTS + 1):
        is_https = current.scheme == "https"
        port = current.port or (443 if is_https else 80)
        if is_https:
            conn = http.client.HTTPSConnection(
                current.hostname, port, timeout=15,
                context=ssl.create_default_context())
        else:
            conn = http.client.HTTPConnection(current.hostname, port, timeout=15)
        try:
            path = current.path or "/"
            if current.query:
                path += "?" + current.query
            conn.request("GET", path, headers={"User-Agent": "cookie-security-checker/%s" % VERSION})
            response = conn.getresponse()
            response.read()
            status = response.status
            for header, value in response.getheaders():
                if header.lower() == "set-cookie":
                    jar = SimpleCookie()
                    try:
                        jar.load(value)
                    except Exception:
                        continue
                    cookies.extend(jar.values())
            location = response.getheader("Location")
        finally:
            conn.close()
        if status in (301, 302, 303, 307, 308) and location:
            hops += 1
            current = urlparse(location if urlparse(location).netloc
                               else "%s://%s%s" % (current.scheme, current.netloc, location))
            continue
        break
    else:
        raise ValueError("Too many redirects (over %d)" % MAX_REDIRECTS)

    return current.geturl(), current.scheme == "https", cookies, status, hops


def audit(url):
    """Audit a URL's cookies and return a report dict."""
    final_url, is_https, cookies, status, hops = fetch_cookies(url)
    host = urlparse(final_url).hostname or ""
    findings = []
    for cookie in cookies:
        findings.extend(check_cookie(cookie, host, is_https))
    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.cookie, f.check))
    score = max(0, 100 - sum(SEVERITY_WEIGHTS[f.severity] for f in findings))
    return {
        "url": url,
        "final_url": final_url,
        "https": is_https,
        "status": status,
        "redirects": hops,
        "cookies": len(cookies),
        "cookie_names": sorted({c.key for c in cookies}),
        "score": score,
        "grade": grade(score),
        "findings": findings,
    }


def format_report(report):
    """Render the human-readable text report."""
    lines = [
        "Cookie security report: %s" % report["url"],
        "Score: %d/100  Grade: %s" % (report["score"], report["grade"]),
        "",
        "  Final URL: %s" % report["final_url"],
        "  Status: %s" % report["status"],
        "  Redirects: %s" % report["redirects"],
        "  Cookies: %s (%s)" % (
            report["cookies"],
            ", ".join(report["cookie_names"]) or "none",
        ),
        "",
    ]
    if not report["findings"]:
        lines.append("No cookie issues found. Every cookie carries the "
                     "flags it should.")
    else:
        lines.append("Findings (%d):" % len(report["findings"]))
        for finding in report["findings"]:
            lines.append("  [%s] %s (%s): %s" % (
                finding.severity.upper(), finding.cookie,
                finding.check, finding.message))
            lines.append("        Fix: %s" % finding.fix)
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit a website's cookies for Secure, HttpOnly, "
                    "SameSite, prefix, expiry and scope problems.")
    parser.add_argument("url", help="Website URL, e.g. https://example.com")
    parser.add_argument("--json", action="store_true",
                        help="Print the report as JSON")
    parser.add_argument("--fail-on", choices=["high", "medium", "low"],
                        default="high",
                        help="Exit 1 when a finding at or above this "
                             "severity is found (default: high)")
    args = parser.parse_args(argv)

    try:
        report = audit(args.url)
    except ValueError as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("Error: could not reach %s (%s)" % (args.url, exc),
              file=sys.stderr)
        return 2

    if args.json:
        out = dict(report)
        out["findings"] = [f.to_dict() for f in report["findings"]]
        print(json.dumps(out, indent=2))
    else:
        print(format_report(report))

    threshold = SEVERITY_ORDER[args.fail_on]
    worst = min((SEVERITY_ORDER[f.severity] for f in report["findings"]),
                default=99)
    return 1 if worst <= threshold else 0


if __name__ == "__main__":
    sys.exit(main())
