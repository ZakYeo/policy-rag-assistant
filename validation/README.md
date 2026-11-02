# NorthStar Policy Desk validation

The implementation follows the **card-based** Stitch screen saved at `designs/northstar/01-corporate/v2/draft-preview.png`, not Simplified Editorial View.

## Package release policy

- `frontend/.npmrc` fixes the cutoff at **2026-10-29T20:06:01Z**, four days before dependency selection.
- `frontend/tooling/check-release-dates.mjs` validates every locked npm version against registry metadata, including optional, bundled and transitive packages. `frontend/dependency-publish-audit.json` records the checks.
- `requirements-ci.txt` pins the existing working Python 3.12 environment; `scripts/check_python_release_dates.py` verifies every release's artifact timestamps before CI installation. The adjacent JSON report records those checks.
- Ruff was separately verified before installation; no new Python transitive dependencies were installed.
- ESLint was updated to its supported major and minimatch overridden to **11.0.3** to address its audit advisory. The patched version is older than the cutoff; npm audit reports no vulnerabilities. The later 11.0.4 release was deliberately excluded.

## Reproducible checks

Backend: `.venv/bin/python -m unittest discover -s tests -v`, `./scripts/run_rag_integration_tests.sh`, `.venv/bin/ruff check app tests integration_tests scripts/check_python_release_dates.py`.

Frontend, from `frontend/`: `npm run lint`, `npm test`, `npm run build`, `npm run test:e2e`.

Playwright starts an isolated test app on port 8010. It uses the production routes and static frontend with deterministic streaming service overrides from `tests/browser_app.py`. Test-control endpoints exist only in that fixture, never in the actual app. One browser test uses the real local extractive pipeline. No CI test needs OpenAI credentials.

The optional live check is separate: with the actual app on port 8001 and backend credentials configured, run `npm exec -- playwright test --config playwright.live.config.ts` from `frontend/`. It sends one question and verifies real text arrives before completion. This is a paid provider call and is not run in CI.

Browser screenshots/traces are generated under ignored `frontend/test-results/`; the HTML report is under `frontend/playwright-report/`.
