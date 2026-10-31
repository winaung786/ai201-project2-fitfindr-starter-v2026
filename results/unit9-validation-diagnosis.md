# Technical validation baseline and chosen improvement

Authorship: AI-assisted developer validation, not student-authored criteria.
The plan and runner were committed as `c501263` before these results.

Command: `python scripts/validate_budget.py --label before`

| Check | Target in every trial | Trial 1 | Trial 2 | Trial 3 | Verdict |
|---|---|---|---|---|---|
| 1. Catalog-grounded complete outfit | 1/1 | 1/1 | 1/1 | 1/1 | MET |
| 2. Exact money and input rejection | 10/10 | 7/10 | 7/10 | 7/10 | MISSED |
| 3. Product/tool failures stop cleanly | 6/6 | 6/6 | 6/6 | 6/6 | MET |
| 4. Category-specific sizes retained | 1/1 | 1/1 | 1/1 | 1/1 | MET |
| 5. Logs are complete and sanitized | 3/3 | 3/3 | 3/3 | 3/3 | MET |

Every trial is a new execution. Real-MCP catalog/size calls and injected
failure/price/log fixtures are labeled individually in the raw JSON.
Identical deterministic results are expected; no model is being cached.

## Every miss: stage and mechanism

All nine failed cases trace to **request parsing**, specifically
`budget_agent.py::parse_request`. `m.group(1).rstrip(".,")` removes an entire
sequence of trailing periods or commas before passing the token to `cents`.
The numeric validator sees `100` instead of the original malformed token and
accepts it. The exact failed inputs in each trial are:

```text
outfit under $100..
outfit under $100,,
outfit under $100.,
```

Actual baseline parser output for each of these inputs:

```json
{"description": "classic vintage basics streetwear", "budget": "100.00", "sizes": {}}
```

These are three symptoms of one normalization mechanism. Search, catalog
selection and arithmetic did not produce this failure: the isolated parser
had already accepted the input before any search or model call.

## One chosen change, recorded before applying it

Remove at most one final sentence punctuation mark before strict monetary
validation, instead of stripping every trailing mark. Leave all other parsing,
selection, prices, model/tool configuration, scenarios and targets unchanged.
Add a regression test for these three inputs and preserve normal `$100.` and
`$100,` sentence punctuation. Then run the exact same five-check runner three
times again, and compare plan, runner, original-criteria and source hashes.

The intended gain is zero silent acceptance of these malformed tokens.
The tradeoff is that a conversational amount followed by an ellipsis now
requires the caller to enter a plain amount or one sentence-ending mark.
This is a deliberately narrow fix, not a claim to parse every currency or
natural-language budget expression.
