# FitFindr Unit 9 — measured before/after comparison (provisional checks)

**Scope and authorship:** AI-assisted provisional evaluation, not the five independently student-authored criteria required by the professor. These checks were committed as `capstone-provisional-criteria.md` **before** the first test results. The student must replace or affirm via personally authored Unit 9 criteria and rerun a course-eligible evaluation.

**Environment:** Python 3.12 GitHub Actions clean checkout; existing Flask `serve.py::ask` and real MCP subprocess; caching off; **no Gemini API key**. The real requests exercised the local model fallback, so the results do **not** establish live Gemini accuracy, pricing or latency.

**Repeated measures:** 5 checks × 3 independent HTTP requests per phase = **15 actual requests before** and **15 actual requests after**. No target changed. The full 30 JSONL records are saved in `results/capstone-before-requests.jsonl` and `results/capstone-after-requests.jsonl`; the trial-by-trial checks in `results/capstone-before-trials.json` and `results/capstone-after-trials.json`.

**Unchanged provisional criteria SHA256:** `3fc2e0921a4eaa37a44a6b28afc5941956d565ff1d010464c288d7d849967842`.

**Instrumentation source SHA256:** before `e66982a7a256c7e28e8e9671d362780cecb9e4a8ca0a908f62413fe71463fe06`, after `106a1dd82d4a15f7d6b1452ba867d0c66dec077313d193cd78e0c53b3bfed6a9`.

## Five checks, same three-trial format

| Check | Target | Before (3 tries) | After (3 tries) |
|---|---|---|---|
| 1. Structured successful request | 3/3 | MET (3/3) | MET (3/3) |
| 2. Recover ordered tool path | 3/3 | MISSED (0/3) | MET (3/3) |
| 3. Rejected input logged | 3/3 | MET (3/3) | MET (3/3) |
| 4. Size retry preserved | 3/3 | MET (3/3) | MET (3/3) |
| 5. No-match logging and zero provider usage | 3/3 | MET (3/3) | MET (3/3) |

## Diagnosis of every baseline miss

**Check 2 — MISSED, 0/3.** The actual `agent.py::run_agent` response correctly contained `tool_calls` in `search_listings → suggest_outfit → create_fit_card` order. But `capstone_logging.py::_output_summary` constructed a reduced dictionary with listing ID, caption, error and retry notice **without any tool-call sequence field**. `capstone_logging.py::_measure_one` then persisted that reduced summary into JSONL, so each recorded request had no `output.tool_sequence`. This is a concrete omitted-field mechanism, not model variability; the application fulfilled the tools but the operator could not reconstruct the sequence from the structured log.

**Checks 1, 3, 4 and 5 — MET, 3/3 each.** They had no baseline misses requiring a fix. The existing HTTP instrumentation correctly logged successful requests, HTTP 400 rejected input, one size-filter retry, and application-level no-results with zero provider tokens in fallback mode.

## One change and its measured effect

**Only code change:** Add `output.tool_sequence` to `capstone_logging.py::_output_summary` by extracting only the `tool` strings from `data["tool_calls"]`. No wardrobe contents, tool arguments, or model prompts are copied into that new field. The agent loop, MCP tools, dataset, targets and evaluation runner were unchanged.

**Result:** Check 2 rose from **0/3 MISSED** to **3/3 MET**. The other four checks remained **3/3 MET**. That is 12/15 to 15/15 individual passing trials across the five provisional checks. The change improved operational traceability; it does not demonstrate increased model correctness.

**Tradeoff and remaining issue:** More metadata per record and possible tool names in logs, but no raw tool argument or wardrobe inclusion in the new field. Full user query text is still logged up to 180 characters and needs a privacy review before public deployment. The keyed Gemini path and dollar API spend were not exercised. The assignment's independent-criteria requirement also remains for student completion.

## Real recorded output (one before and one after per check)

These are actual JSONL records from `scripts/capstone_eval.py::_trial`, produced by `capstone_logging.py::_measure_one`; not summaries made to resemble output.

### Check 1 — Structured successful request

Before HTTP status: 200; after HTTP status: 200. All raw trials and their checks are in the two saved JSON files.

**Actual before structured log (trial 1)**

```json
{"duration_ms":2801.31,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size M","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":null,"selected_item_id":"lst_002"},"route":"/ask","run_id":"65bd6859f122","timestamp":"2026-11-15T21:15:13.548363+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

**Actual after structured log (trial 1)**

```json
{"duration_ms":2729.34,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size M","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":null,"selected_item_id":"lst_002","tool_sequence":["search_listings","suggest_outfit","create_fit_card"]},"route":"/ask","run_id":"ce7582ddad78","timestamp":"2026-11-15T21:17:42.914916+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

### Check 2 — Recover ordered tool path

Before HTTP status: 200; after HTTP status: 200. All raw trials and their checks are in the two saved JSON files.

**Actual before structured log (trial 1)**

```json
{"duration_ms":1672.63,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size M","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":null,"selected_item_id":"lst_002"},"route":"/ask","run_id":"72092599e16b","timestamp":"2026-11-15T21:15:19.663293+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

**Actual after structured log (trial 1)**

```json
{"duration_ms":1731.16,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size M","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":null,"selected_item_id":"lst_002","tool_sequence":["search_listings","suggest_outfit","create_fit_card"]},"route":"/ask","run_id":"73ded3e28041","timestamp":"2026-11-15T21:17:49.099172+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

### Check 3 — Rejected input logged

Before HTTP status: 400; after HTTP status: 400. All raw trials and their checks are in the two saved JSON files.

**Actual before structured log (trial 1)**

```json
{"duration_ms":0.37,"http_status":400,"input":{"json_object":true,"query":null,"wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}","fit_card":null,"retry_notice":null,"selected_item_id":null},"route":"/ask","run_id":"a13826f66114","timestamp":"2026-11-15T21:15:24.648863+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

**Actual after structured log (trial 1)**

```json
{"duration_ms":0.38,"http_status":400,"input":{"json_object":true,"query":null,"wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}","fit_card":null,"retry_notice":null,"selected_item_id":null,"tool_sequence":[]},"route":"/ask","run_id":"0a476209b335","timestamp":"2026-11-15T21:17:54.318127+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

### Check 4 — Size retry preserved

Before HTTP status: 200; after HTTP status: 200. All raw trials and their checks are in the two saved JSON files.

**Actual before structured log (trial 1)**

```json
{"duration_ms":2156.19,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size XL","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Graphic Tee — 2003 Tour Bootleg Style for $24.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":"No matches in size XL; retried once without the size filter.","selected_item_id":"lst_006"},"route":"/ask","run_id":"554c329dc938","timestamp":"2026-11-15T21:15:24.651775+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

**Actual after structured log (trial 1)**

```json
{"duration_ms":2313.47,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size XL","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Graphic Tee — 2003 Tour Bootleg Style for $24.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":"No matches in size XL; retried once without the size filter.","selected_item_id":"lst_006","tool_sequence":["search_listings","search_listings","suggest_outfit","create_fit_card"]},"route":"/ask","run_id":"805158bbf6fc","timestamp":"2026-11-15T21:17:54.320989+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

### Check 5 — No-match logging and zero provider usage

Before HTTP status: 200; after HTTP status: 200. All raw trials and their checks are in the two saved JSON files.

**Actual before structured log (trial 1)**

```json
{"duration_ms":1011.72,"http_status":200,"input":{"json_object":true,"query":"designer ballgown size XXS under $5","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"No listings match that request, even after dropping the size filter. Try changing a keyword or raising the price limit.","fit_card":null,"retry_notice":"No matches in size XXS; retried once without the size filter.","selected_item_id":null},"route":"/ask","run_id":"433724421b1e","timestamp":"2026-11-15T21:15:31.226488+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

**Actual after structured log (trial 1)**

```json
{"duration_ms":1051.32,"http_status":200,"input":{"json_object":true,"query":"designer ballgown size XXS under $5","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"No listings match that request, even after dropping the size filter. Try changing a keyword or raising the price limit.","fit_card":null,"retry_notice":"No matches in size XXS; retried once without the size filter.","selected_item_id":null,"tool_sequence":["search_listings","search_listings"]},"route":"/ask","run_id":"cbf48a8623a5","timestamp":"2026-11-15T21:18:01.152280+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

## Reproduction and course status

Run with installed requirements and no API key: `python scripts/capstone_eval.py --phase before` or `--phase after`. Re-running now tests the **current** improved version; the historical before records are preserved in git and should not be overwritten. `RUNNING.md` contains clean-checkout setup. Because all five acceptance criteria were drafted by AI, these tests are a **technical completion of the requested evaluation and improvement**, not certification that the professor's personally-authored criterion requirement has been met.
