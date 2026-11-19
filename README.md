# Cookie Security Checker

A small, dependency-free Python CLI that audits a website's cookies
against the standard hardening rules: Secure, HttpOnly and SameSite
flags, `__Secure-` / `__Host-` prefix rules, sensible expiry, and a
narrow Domain/Path scope. It grades the site A-F and explains each
finding in plain language, so students and small teams can see
exactly where a session cookie invites theft or abuse and how to fix
it.

Standard library only (`http.client`, `ssl`, `urllib.parse`). No
third-party packages, no telemetry, nothing is stored. The checker
only sends read-only GET requests, follows redirects itself so it
can collect the Set-Cookie headers sent at every hop, and never logs
in or submits data.

## What it checks

| Check | What a good result looks like |
| --- | --- |
| Secure | Every cookie set over HTTPS carries the Secure flag |
| HttpOnly | Cookies are not readable by JavaScript (unless JS genuinely needs them) |
| SameSite | Every cookie sets SameSite=Lax or Strict; SameSite=None always pairs with Secure |
| Prefixes | `__Secure-` cookies carry Secure; `__Host-` cookies carry Secure, use Path=/ and no Domain |
| Expiry | Max-Age under a year, much shorter for session cookies |
| Domain | No leading-dot Domain sharing a cookie with every subdomain |

Session-like cookies (names containing session, auth, token, sid,
login, csrf, jwt and similar) are held to a stricter bar: a missing
Secure or HttpOnly flag on one of those is High severity, while the
same gap on a plain preference cookie is Medium.

Findings are graded by severity:

| Severity | Examples |
| --- | --- |
| High | Session cookie without Secure or HttpOnly, SameSite=None without Secure, broken `__Secure-`/`__Host-` prefix |
| Medium | Plain cookie without Secure or HttpOnly, missing SameSite |
| Low | Over-long expiry, leading-dot Domain, unrecognised SameSite value |

Score starts at 100 and deducts 25 / 10 / 3 per high / medium / low
finding: 90+ is A, 75+ B, 60+ C, 40+ D, below that F.

## Install

No installation needed. Python 3.8+ only, standard library only:

```bash
git clone https://github.com/sajidhussainraza/cookie-security-checker.git
cd cookie-security-checker
```

## Usage

Audit a website's cookies:

```bash
python3 cookie_security_checker.py https://example.com
```

Machine-readable output:

```bash
python3 cookie_security_checker.py https://example.com --json
```

Use it as a CI gate (fail only on high-severity findings):

```bash
python3 cookie_security_checker.py https://example.com --fail-on high
```

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | No findings at/above `--fail-on` |
| 1 | Findings at/above `--fail-on` were found |
| 2 | Usage error (bad URL, site unreachable) |

Note: the checker only reads the cookies a site sets on an
anonymous visit. It cannot audit cookies set after login, or
cookies set by JavaScript in the browser; those need a logged-in
browser session.

## Example

```
$ python3 cookie_security_checker.py https://github.com
Cookie security report: https://github.com
Score: 84/100  Grade: B

  Final URL: https://github.com
  Status: 200
  Redirects: 0
  Cookies: 3 (_gh_sess, _octo, logged_in)

Findings (3):
  [MEDIUM] _octo (HttpOnly): Cookie is readable by JavaScript, so a
  cross-site scripting (XSS) flaw can steal it.
        Fix: Set the HttpOnly flag unless JavaScript genuinely needs
        to read this cookie.
  [LOW] _octo (Domain): Cookie is shared with every subdomain of
  '.github.com', which widens the blast radius if any subdomain is
  compromised.
        Fix: Drop the leading dot and the Domain attribute unless
        subdomains genuinely need the cookie.
  [LOW] logged_in (Domain): Cookie is shared with every subdomain of
  '.github.com', which widens the blast radius if any subdomain is
  compromised.
        Fix: Drop the leading dot and the Domain attribute unless
        subdomains genuinely need the cookie.
```

All three findings are deliberate choices by GitHub: `_octo` is a
JavaScript-readable analytics cookie, and `.github.com` sharing is
intentional so subdomains can read the login state. For a site that
does not need either behaviour, all three would be real fixes. The
full output of that run is saved in
`examples/sample-output-github.com.txt` (captured 16 November 2026).

## Teaching notes

This tool pairs well with a lesson on session security and XSS: run
it against a deliberately insecure demo site, then fix one flag at a
time and watch the grade move. Good discussion points:

- Why HttpOnly matters: without it, one XSS flaw hands the attacker
  the victim's session cookie, and the login is bypassed entirely.
- Why the Secure flag is not optional on HTTPS sites: without it, a
  single plain-HTTP request (or a downgrade attack) leaks the cookie.
- Why SameSite=Lax is the safe default, and why SameSite=None only
  exists for cookies that genuinely need to travel cross-site.
- Why `__Host-` is the strongest cookie prefix: it locks the cookie
  to one host, one path and HTTPS, so a compromised subdomain cannot
  overwrite it.
- Why expiry is a security control: a stolen cookie stays useful
  until it expires, so a two-year session cookie is a two-year window.

## Tests

```bash
python3 tests/run_tests.py   # 12 tests, including a live audit of github.com
```

The mock-server tests run a local fake site in secure and insecure
modes, so they need no internet. The live test runs a real audit
against github.com and is skipped automatically when the network
is unreachable. (pytest is also supported if it is installed:
`python3 -m pytest tests/ -q`.)

## License

MIT
