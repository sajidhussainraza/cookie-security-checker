# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you find a security vulnerability in Cookie Security Checker, please report it privately so it can be fixed before it is publicly disclosed.

- **Preferred:** use GitHub's private vulnerability reporting on this repository (Security tab → Report a vulnerability).
- **Alternative:** email info@cyberlegends.org with the subject "Cookie Security Checker vulnerability".

Please include a description of the issue, steps to reproduce it, and the version you tested against. Reports are reviewed as soon as possible; please allow time for triage and a fix before disclosing the issue publicly.

## Scope notes

Cookie Security Checker is a read-only auditing tool: it sends only anonymous GET requests, never logs in, never submits data, and stores nothing. It is not a penetration-testing tool and cannot audit cookies set after login or by JavaScript in the browser.
