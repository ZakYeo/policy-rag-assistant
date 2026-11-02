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

## Initial question-page validation

- 48 Python unit tests and 8 isolated RAG integration cases passed. The added sample-question checks verify the catalog covers the three current PDFs and all four cross-policy prompts retrieve their declared documents with the local pipeline.
- 16 frontend tests, ESLint/MVVM RuleTester, TypeScript checking and the Vite/Tailwind production build passed.
- All 10 Playwright scenarios passed, covering both themes, screen sizes and resizing, keyboard access, skeletons, real HTTP streaming, partial failures, safe text rendering and long content. The extractive browser case used the real local index. Sample-panel checks cover the floating left margin, inline fallback, focus, unchanged answer mode and no automatic requests.
- A separate bounded live OpenAI browser check passed: answer text was visible before completion, followed by grounded policy evidence. It is not part of CI.
- All 303 locked npm versions and 138 pinned Python versions passed publication-date checks. npm audit reported zero vulnerabilities.
- The initial implementation received a fresh independent review of code and desktop/mobile screenshots. Its two minor findings were resolved. Targeted follow-up independently passed the then-current 15 frontend tests and 11 Python streaming tests, approved the fixes with no blockers, and scored that implementation 95/100.

The original untracked design-exploration files remain local. Only the user-selected card-based reference is included with the implementation commits.

## Policy management validation — 2026-11-02

- **77 backend tests**, **20 frontend tests**, **8 RAG integration cases**, and
  **13 Playwright scenarios** passed. Ruff, ESLint/MVVM, TypeScript and the
  production build passed. No new packages were installed.
- Browser coverage includes upload, rename, delete/cancel, content, chunks,
  preview invalidation, applying changes, HTML controls, invalid/duplicate files,
  direct navigation, question-draft preservation, both themes and resizing from
  320px through 1920px. Tests use a temporary policy library, never live policies.
- A held indexing operation proves the previous revision remains searchable.
  A browser test reloads during held indexing, simulates a status-request failure,
  and verifies automatic reconnection and eventual completion.
- Regression coverage includes 6,001-chunk indexing, atomic publication/operation
  completion, interrupted-job recovery, canonical HTML source spans, preserved PDF
  paragraphs and byte-bounded OpenAI embedding inputs with vector pooling.
- A fresh independent reviewer applied the **thermo-nuclear-code-quality-review**
  skill and initially requested changes. All findings were implemented in further
  tested commits: indexing concurrency, bounded vector writes, atomic operation
  publication, browser recovery, source provenance and embedding request limits.
  Re-review approved the work at **91/100**, with no blockers; the final PDF
  paragraph correction was independently checked and approved too.
- OpenAI adapter limits were tested with a fake client, not paid API calls.
  Existing streamed-answer behavior passed deterministic HTTP/browser regression
  checks. Earlier live-provider evidence above belongs to the original question
  page implementation.
- Desktop light and mobile dark screenshots were inspected under
  `frontend/test-results/`; a read-only Playwright check also loaded the real
  review app at `http://localhost:8001/policies` and verified its seeded policy
  settings and 320px layout.

Deployment remains a single local/internal app process. Back up `data/policies/`
as one unit. The registry imports the seed PDFs once; deleting a managed seed
policy does not cause it to reappear after a restart.

## Page alignment follow-up

The question and management pages now share their page-intro component, typography,
responsive text space and panel padding. A stable root scrollbar gutter prevents
horizontal movement when navigating between pages with different scroll heights.
The browser regression first reproduced a 7.2px subtitle displacement, then passed
comparisons of header, navigation, title, subtitle and first-card geometry across
16 window shapes (including breakpoint boundaries, 320px mobile and tall desktop).
The existing 20 frontend tests, MVVM lint, type checking and production build passed.
All 14 Playwright scenarios passed after the alignment fix; desktop light and
mobile dark screenshots were inspected for both pages.
