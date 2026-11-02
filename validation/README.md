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

## Completed validation

- 48 Python unit tests and 6 isolated RAG integration cases passed.
- 15 frontend tests, ESLint/MVVM RuleTester, TypeScript checking and the Vite/Tailwind production build passed.
- All 9 Playwright scenarios passed, covering both themes, screen sizes and resizing, keyboard access, skeletons, real HTTP streaming, partial failures, safe text rendering and long content. The extractive browser case used the real local index.
- A separate bounded live OpenAI browser check passed: answer text was visible before completion, followed by grounded policy evidence. It is not part of CI.
- All 303 locked npm versions and 138 pinned Python versions passed publication-date checks. npm audit reported zero vulnerabilities.
- A fresh independent review inspected code and desktop/mobile screenshots and reran deterministic checks. Its two initial minor findings were resolved. Targeted follow-up independently passed all 15 frontend tests and 11 Python streaming tests, approved the fixes with no blockers, and scored the work 95/100.

The original untracked design-exploration files remain local. Only the user-selected card-based reference is included with the implementation commits.
