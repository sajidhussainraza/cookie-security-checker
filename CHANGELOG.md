# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Professional README: banner, badges, quick start, scoring table, CLI reference, architecture diagram, FAQ, and roadmap.
- Original brand assets: `assets/banner.svg`, `assets/logo.svg`, and a static terminal demo preview (`assets/demo.svg`).
- Repository files: `.gitignore`, `.editorconfig`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`.
- GitHub templates: bug report and feature request issue forms, issue config, pull request template.
- Continuous integration: `.github/workflows/ci.yml` runs the test suite on Linux, Windows, and macOS across Python 3.8–3.13.

## [1.0.0] - 2026-11-19

### Added

- Dependency-free Python CLI (`cookie_security_checker.py`) that audits a website's cookies for Secure, HttpOnly, SameSite, `__Secure-` / `__Host-` prefix rules, expiry, and Domain/Path scope.
- A–F grading with a 0–100 score (start at 100; deduct 25 / 10 / 3 per high / medium / low finding).
- Session-aware severity: session-like cookies are held to a stricter bar than plain preference cookies.
- Plain-language message and fix for every finding.
- `--json` machine-readable output and `--fail-on {high,medium,low}` exit codes for CI gating.
- Redirect-aware fetching (up to 5 hops), collecting `Set-Cookie` headers at every hop.
- Read-only design: anonymous GET requests only, no login, no telemetry, nothing stored.
- Test suite: 12 tests, including mock-server secure/insecure fixtures and a live audit of github.com (auto-skipped when offline).
- Example output from a real audit of github.com (84/100, grade B) in `examples/sample-output-github.com.txt`.
- MIT license.

[Unreleased]: https://github.com/sajidhussainraza/cookie-security-checker/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/sajidhussainraza/cookie-security-checker/releases/tag/v1.0.0
