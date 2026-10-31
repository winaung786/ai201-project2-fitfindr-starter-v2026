# FitFindr website

The user requested a professional, easy-to-use website with few navigation controls.
This follow-up adds the interface to the existing repository. The earlier capstone
scope and measured results remain a historical record; the new website was requested
after that test cycle.

## Experience

- Two top navigation links: Outfit builder and Saved outfits. No sidebar.
- One main form with budget, a six-option style selector, optional sizes, and
  one Build my outfit action. Input labels remain visible.
- Three item cards with original catalog titles/prices/sizes and decorative
  garment illustrations. Actual product links appear only if provided by the catalog.
- Exact merchandise subtotal, remaining budget, a labeled budget meter, a sample
  catalog badge, and a short tax/shipping/live-stock note.
- Save/unsave and view/remove looks on this browser, with no server account.
  Storage errors are reported instead of showing a false success. Up to 24 looks
  are retained; clearing browser data removes them. Saved item IDs are revalidated
  against the catalog before they are displayed.
- Copy a grounded summary to the clipboard, with success/failure feedback.
- A short explanation dialog, meaningful error/empty/loading states, keyboard focus
  indicators, a skip link, live status messages, native form controls, and reduced-motion
  support. The small-screen form stacks above results; sizes remain optional.

No checkout, live marketplace feed, user account, or AI-generated fashion-quality
claim has been added. The illustrations are decorative and not photographs of the
sample listings.

## Two run paths

The source lives under `web/`. `node scripts/build-web.mjs` copies the static files
to ignored `dist/` and supplies `dist/catalog.json` from `data/listings.json`.
No frontend dependencies or CDN libraries are required. The hosted edition is
buildless HTML/CSS/ES modules with a deterministic JavaScript budget companion.
It performs its selection in the browser; it does not run Python/MCP or record
per-visitor agent logs. Saved choices stay on the device.

The existing Flask server serves the same interface at `/`, with
`data-transport="api"`. The UI then uses the real `/ask` agent endpoint and its
existing structured logs and bounded MCP tools. `/catalog.json` supplies the
original sample data and `/assets/` supplies the website files. Static file serving
is directory-bound; a route test verifies that a traversal attempt cannot read `.env`.

Hosting identity is tracked in `.openai/hosting.json`. New hosting starts owner-private;
no sharing-policy change was requested. This is separate from the existing public
GitHub source repository. Hosting synchronization preserves the original GitHub
remote and branch history.

## Validation performed

- `python -m unittest discover -s tests -v`: all 21 tests passed, including the
  existing 19 regressions, website routes, and Python/JavaScript selection parity.
  The parity test checks 33 combinations of six styles, five budgets, and additional
  category sizes, including unsuccessful cases. The browser result IDs, totals,
  remainders and error types agree with the existing Python rules on those cases.
- `node --test tests/web-engine.test.mjs`: all 5 groups passed, covering exact cents,
  original catalog grounding, every selectable style, retained size filters and
  invalid/missing/unavailable/foreign-currency fixtures.
- Browser: default outfit $74 with $26 remaining from $100; low budget returns
  an explanation with no partial recommendation; M/W30/US 9 produces a fitting
  $65 outfit with $35 remaining; save survives refresh; saved look can be opened;
  copying shows success feedback; explanation dialog opens and closes.
- Responsive review: phone viewport 390 x 844, no horizontal document overflow,
  stacked form/results and readable controls; normal panel-width layout checked.
- Local API review: the website returned the actual catalog-backed $74 outfit
  through the existing Python/MCP agent, with no browser console error.

These are website development checks, not replacement student-authored acceptance
criteria. The historic capstone reports remain unchanged. A fixed sample catalog
and these checks do not establish live shopping reliability, exhaustive accessibility
conformance or fashion quality.
