# Contributing to Cookie Security Checker

Thanks for helping improve the checker! Contributions of all sizes are welcome: bug reports, new checks, documentation fixes, and test improvements.

## Quick steps

1. Fork the repository and clone your fork.
2. Create a branch: `git checkout -b fix/my-fix` (or `feature/my-feature`).
3. Make your change. New checks should come with a test in `tests/`.
4. Run the suite: `python3 tests/run_tests.py` — all tests must pass.
5. Open a pull request with a clear description of the change.

## Ground rules

- **Dependency-free:** the tool uses only the Python standard library. Do not add third-party packages.
- **Every finding needs a fix:** each finding must carry a plain-language message and a concrete fix, matching the existing style.
- **Match the existing style:** 4-space indentation, descriptive names, short functions.
- **Test what you add:** the mock-server fixtures in `tests/test_cookie_security_checker.py` cover secure and insecure sites — extend them rather than adding network-dependent tests.
- **No secrets:** never commit credentials, tokens, or personal data. The tool itself sends only anonymous read-only GET requests and stores nothing.

## Reporting bugs

Use the bug report template on the Issues tab. Include the exact command you ran, the Python version (`python3 --version`), your OS, and the full output.

## Questions

Open an issue with the `question` label, or start a discussion on the repository.
