# Unit 9: budget-aware outfit extension

Shape C extends the existing FitFindr repository and three-tool pipeline.
The new path selects one top, one bottom, and one pair of shoes from search
results, validates their USD merchandise subtotal using integer cents, and
reports the budget and remaining amount. Exact-budget outfits are allowed.
The existing single-item/wardrobe path remains available.

The bundled catalog is sample data: no live availability or shopping URLs
are supplied. The app must label previews accordingly, never invent links,
and exclude missing/invalid prices, foreign currencies, and unavailable items.
Tax and shipping are unknown and excluded, with that limit displayed.

Out of scope: a new repository, accounts, wardrobe management, weather,
live marketplace integrations, and a redesign of the existing application.
Use the local-with-logs run path. No cloud signup is required.

## Student-owned work still pending

The student chose to write their five Unit 9 acceptance criteria later.
`criteria.md` currently contains the original Unit 3/4 criteria; do not treat
them as Unit 9 criteria or overwrite them with AI-written ones.
Archive the old criteria, then commit the student's five numbered criteria
with targets and reasons before running/committing the formal acceptance
baseline. Review them for measurable targets, at least three about the
extension, and at least one failure case. Do not change targets to fit results.

Developer regression tests and the ten-run cost/instrumentation measurement
are build checks, not the student's acceptance results. After the criteria
commit: run each criterion three times, preserve raw outputs, diagnose all
misses, commit one improvement, and repeat the full set three times.
No formal before/after verdicts or capstone completion claims exist yet.
