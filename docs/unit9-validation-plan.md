# Unit 9 technical validation plan - AI-assisted

These five checks were prepared by Codex at the user's request to complete
testing and the write-up. They are **not claimed to be student-authored
acceptance criteria**. The original Unit 3/4 `criteria.md` remains unchanged.
Commit this plan and its runner before recording this validation baseline.
The remaining course authorship requirement must be reviewed by the student.

Run each check three separate times without changing code, cases, targets,
or catalog between trials. A check is MET only if every case passes in all
three trials. Preserve actual results, log records, source hashes, the plan
hash and runner hash. After diagnosing the baseline, change one mechanism
and repeat the identical full set. No model variation is expected: this
budget path is deterministic and makes no model or response-cache calls.

1. **Catalog-grounded complete outfit.** On each fresh real-MCP request for
   `casual outfit under $100`, 1/1 response must contain exactly one top,
   one bottom and shoes with distinct IDs from the returned catalog, their
   original prices, an exact integer-cent sum at or below 10000, and the
   matching remainder. The displayed card must use that sum and disclose
   sample data and excluded shipping/tax; absent source links stay absent.
   **Reason:** A single invented product or incorrect subtotal defeats the
   budget guarantee; no allowance for such failures is justified.

2. **Exact money and input rejection.** In each trial, 10/10 fixed cases
   must pass: an exact $0.60 outfit from $0.10/$0.20/$0.30 fixtures; rejection
   at $0.59; valid sentence punctuation after $100; and rejection of zero,
   negative, excess-decimal, conflicting, repeated-dot, repeated-comma and
   mixed-punctuation budget amounts. Invalid inputs must not be silently
   converted to another valid amount. The runner records parser/validator
   outputs directly, without a model or shopping claims about fixture data.
   **Reason:** Money boundaries and invalid input are deterministic. A 9/10
   target would accept an avoidable interpretation error involving money.

3. **Fail closed when products/tools are unusable.** In each trial, 6/6
   deliberately injected cases (missing price, unavailable listing, EUR
   listing, empty shoes result, over-budget combination, and MCP failure)
   must return an actionable error and leave budget_result, selected_item,
   outfit_suggestion and fit_card empty. No styling/card tool may be reached
   after a search/selection failure. Fixtures replace transport only; the
   actual agent and selection code run unchanged.
   **Reason:** A plausible partial recommendation would conceal the failure.
   These six known failures should all be handled; live marketplace behavior
   is outside this sample-catalog check.

4. **Retain separate size constraints.** On each fresh real-MCP HTTP request
   with tops M, bottoms W30, shoes US 9, and budget $100, 1/1 response must be
   HTTP 200 with all three items matching their requested category sizes.
   Search receipts must retain the original size in every category and
   contain no relaxed-size retry. The response must stay within budget.
   **Reason:** A cheap outfit in the wrong size is not a useful success.
   One size cannot apply to a top, waist and shoe interchangeably.

5. **Observable successful and failed calls without raw secrets.** In each
   trial, 3/3 fresh calls (fixture-backed success, fixture-backed transport
   failure, malformed HTTP request) must each create exactly one distinct
   JSON record with UTC timestamp, nonnegative elapsed time, correct
   success/failure and error type, sanitized input/output, and the response's
   run ID. Raw synthetic query/wardrobe/exception markers must not appear in
   the log. Successful totals must match the response. No model cost is
   inferred for unmeasured paths.
   **Reason:** A failure that is missing or leaks private text makes the
   run record unsuitable for diagnosing or sharing this local application.
