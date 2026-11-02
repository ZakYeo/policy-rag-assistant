# Implementation reference

Use the original card-based **NorthStar Policy Desk – Version 2** selected by the user, not Simplified Editorial View.

Reference: `../designs/northstar/01-corporate/v2/draft-design.html` and `draft-preview.png`.
Stitch screen: `projects/15528260949309752882/screens/a36547e533ec4737959a099f714d9743`.

Intent: employees resolve policy questions and check evidence. Preserve the small NorthStar star, cream canvas, navy action, white cards, two-column answer/evidence hierarchy and direct policy quotations.

Palette: paper, ink, navy signage and quiet stationery borders. Subtle shadows match the selected reference. Source Sans 3 carries reading text, Source Code Pro technical identifiers. Use a consistent quarter-rem spacing scale and fluid responsive composition.

Frontend architecture: Models contain I/O, ViewModels contain state/actions, Views receive props, composition connects them, contracts contain shared types. `npm run lint` enforces import and side-effect boundaries and tests intentional violations.

Dependencies are pinned. `.npmrc` fixes the requested four-day release cutoff; `node tooling/check-release-dates.mjs --write` checks every lockfile version against registry publication metadata before installation and records the evidence in `dependency-publish-audit.json`.
