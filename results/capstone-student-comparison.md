# FitFindr Unit 9 — student-supplied acceptance criteria: actual before/after evaluation

These **five targets were supplied by the student**, not the earlier AI provisional rehearsal. The criteria were committed under `## Unit 9 Capstone — student-supplied acceptance criteria` in `criteria.md` before this run. The original exact strings and 3/3 targets were held fixed before and after.

**Test mode:** Two real GitHub Actions clean-checkout executions on Python 3.12. `scripts/capstone_student_eval.py` issued actual HTTP requests through `serve.py::ask`; the agent used real MCP subprocesses and local styling fallback. `AI201_CACHE=0`; no valid Gemini API key was provided. Criterion 4 deliberately used the documented fake invalid string `test_secret_key_DO_NOT_LOG_999` to verify secret leakage behavior. Therefore this is **not a live Gemini model quality or dollar spend measurement**.

**Volume:** Five criteria × three trials per phase = **15 graded trials before** and **15 graded trials after**. Criterion 3 contains *three distinct HTTP requests per trial*, so each phase sent **21 real HTTP requests**, for **42 actual HTTP requests total**. The full raw records and per-trial checks live in `results/capstone-student-before-trials.json` and `results/capstone-student-after-trials.json`, plus the matching JSONL files.

**Unchanged original criteria SHA256:** `214265cbf1709c7fce9f03e5c1e52483ea61d03f2dbb41fa61224cc4e4e1a854` before and after. The evaluation runner also remained unchanged. One source change only: `serve.py` input type checking, committed between the baseline and the retest.

## Before and after results

| Student criterion | Target | Before (Run 1/2/3) | Before verdict | After (Run 1/2/3) | After verdict |
|---|---|---|---|---|---|
| 1. Happy-path HTTP telemetry and correlation header | 3/3 | FAIL, FAIL, FAIL | MISSED (0/3) | FAIL, FAIL, FAIL | MISSED (0/3) |
| 2. Bounded size-retry and empty-search failure-path telemetry | 3/3 | PASS, PASS, PASS | MET (3/3) | PASS, PASS, PASS | MET (3/3) |
| 3. Malformed and non-string JSON payload rejection | 3/3 | FAIL, FAIL, FAIL | MISSED (0/3) | PASS, PASS, PASS | MET (3/3) |
| 4. Secret/wardrobe privacy redaction and temporary cleanup | 3/3 | FAIL, FAIL, FAIL | MISSED (0/3) | FAIL, FAIL, FAIL | MISSED (0/3) |
| 5. Explicit empty-wardrobe HTTP styling and zero-item telemetry | 3/3 | FAIL, FAIL, FAIL | MISSED (0/3) | FAIL, FAIL, FAIL | MISSED (0/3) |

An honest 3/3 target is MET only if **all three** separate trials satisfy every listed check. Missing a target is a valid capstone outcome when explained, not a reason to relax it after testing.

## Diagnosis — location and mechanism for every miss

**Criterion 1, MISSED 0/3 before and after:** Everything in the HTTP and JSONL request/response/correlation path passed, including `lst_002`, price and platform. The sole failing check was the literal title substring. The criterion requires `Y2K Baby Tee – Butterfly Print` (U+2013 en dash), but `data/listings.json` and `tools.py::create_fit_card` use `Y2K Baby Tee — Butterfly Print` (U+2014 em dash). This check measures a typography mismatch rather than incorrect item selection. Original target was retained unchanged; consider a legitimate recorded revision that compares the selected item's title from the source listing instead of a manually copied punctuation variant.

**Criterion 2, MET 3/3:** The no-results branch in `agent.py::run_agent` issued precisely two `search_listings` calls, second with `retry: true` and `dropped_constraint: "size XXS"`; no styling/card calls followed. The logger kept the expected null values, exact retry notice and useful no-match error. No miss.

**Criterion 3, MISSED 0/3 before, MET 3/3 after:** `serve.py::ask` ran `(payload.get("query") or "").strip()` before type-checking JSON. An array had no `.get()`; an integer had no `.strip()`. Those two exceptions reached the generic `capstone_logging.py::_measure_one` handler, producing HTTP 500 instead of the specified validation message; the empty dictionary alone returned 400. **Exactly one improvement** changed input parsing in `serve.py::ask` to require an object and a nonempty string before trimming. With no criteria changes, all nine individual malformed payloads (three per trial) returned 400 and were logged as such, under 50 ms, with zero model calls.

**Criterion 4, MISSED 0/3 before and after:** The dummy test key was absent from the saved JSONL records, matching the secret-redaction target, and `tempfile.TemporaryDirectory` cleaned up all `fitfindr-capstone-*` temporary directories after each request. However, `capstone_logging.py::_output_summary` saves up to 180 characters of `data["fit_card"]`. The normal local caption included example wardrobe items `Baggy straight-leg jeans, dark wash` and `Chunky white sneakers`; these names therefore leaked into the structured log, violating the stated strict privacy target. Correct next mechanism-level fix is to omit/redact raw caption from persistent telemetry or log only safe metadata. This was not silently applied because this evaluation measured **one** targeted code improvement.

**Criterion 5, MISSED 0/3 before and after:** The HTTP response had a nonempty general styling suggestion saying no wardrobe was saved; the agent did not assert ownership, and logged wardrobe count was zero, selected listing `lst_002` and fit card price `$18.00`. Only the copied literal en-dash title check failed: the real selected item uses an em dash (see criterion 1). The current target was preserved exactly; a documented revision could compare the actual selected listing title rather than manually transcribed punctuation.

## One measured improvement

**Change:** In `serve.py::ask`, replace unguarded `payload.get(...).strip()` with a type check requiring a JSON object and a nonempty string query. Preserve the same JSON error message used for an empty body.

**Observed effect:** Criterion 3 improved from **0/3 to 3/3** with all three distinct malformed payloads returning HTTP 400 in each of three trials; the structured logs likewise recorded HTTP 400, no model calls and sub-50ms elapsed time. Criterion 2 remained MET (3/3). Criteria 1, 4 and 5 remained MISSED for their diagnosed reasons. The number of passing graded trials increased from **3/15 to 6/15**. This does not prove broader model reliability, but it verifies the targeted input-hardening improvement without changing the criteria.

## Exact recorded output excerpts (one trial per criterion, both phases)

The following are real structured JSONL records, not fabricated samples. `capstone_logging.py::_measure_one` produced the log fields; `scripts/capstone_student_eval.py` evaluated the check results. See the JSON files for all other trials and full response bodies.

### Criterion 1: Happy-path HTTP telemetry and correlation header

**Before checks, trial 1:**
```json
{"one_log":true,"header_hex12":true,"correlation":true,"http_200":true,"log_200":true,"elapsed_positive":true,"listing_id":true,"error_null":true,"exact_user_title":false,"exact_price":true,"platform":true}
```
**Actual before JSONL, trial 1:**
```json
{"duration_ms":2772.36,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size M","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":null,"selected_item_id":"lst_002","tool_sequence":["search_listings","suggest_outfit","create_fit_card"]},"route":"/ask","run_id":"4c15a2920b2d","timestamp":"2026-11-15T21:32:57.964934+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```
**After checks, trial 1:**
```json
{"one_log":true,"header_hex12":true,"correlation":true,"http_200":true,"log_200":true,"elapsed_positive":true,"listing_id":true,"error_null":true,"exact_user_title":false,"exact_price":true,"platform":true}
```
**Actual after JSONL, trial 1:**
```json
{"duration_ms":2071.51,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size M","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":null,"selected_item_id":"lst_002","tool_sequence":["search_listings","suggest_outfit","create_fit_card"]},"route":"/ask","run_id":"02e27e641157","timestamp":"2026-11-15T21:34:24.885153+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```


### Criterion 2: Bounded size-retry and empty-search failure-path telemetry

**Before checks, trial 1:**
```json
{"one_log":true,"http_200":true,"no_content":true,"only_two_search_calls":true,"retry_flag":true,"dropped_constraint":true,"log_selected_null":true,"log_card_null":true,"exact_retry_notice":true,"error_prefix":true}
```
**Actual before JSONL, trial 1:**
```json
{"duration_ms":1057.28,"http_status":200,"input":{"json_object":true,"query":"designer ballgown size XXS under $5","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"No listings match that request, even after dropping the size filter. Try changing a keyword or raising the price limit.","fit_card":null,"retry_notice":"No matches in size XXS; retried once without the size filter.","selected_item_id":null,"tool_sequence":["search_listings","search_listings"]},"route":"/ask","run_id":"1a911d7ed052","timestamp":"2026-11-15T21:33:04.236874+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```
**After checks, trial 1:**
```json
{"one_log":true,"http_200":true,"no_content":true,"only_two_search_calls":true,"retry_flag":true,"dropped_constraint":true,"log_selected_null":true,"log_card_null":true,"exact_retry_notice":true,"error_prefix":true}
```
**Actual after JSONL, trial 1:**
```json
{"duration_ms":872.53,"http_status":200,"input":{"json_object":true,"query":"designer ballgown size XXS under $5","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"No listings match that request, even after dropping the size filter. Try changing a keyword or raising the price limit.","fit_card":null,"retry_notice":"No matches in size XXS; retried once without the size filter.","selected_item_id":null,"tool_sequence":["search_listings","search_listings"]},"route":"/ask","run_id":"5eed76a79994","timestamp":"2026-11-15T21:34:29.887827+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```


### Criterion 3: Malformed and non-string JSON payload rejection

**Before checks, trial 1:**
```json
{"request_1_one_log":true,"request_1_http_400":true,"request_1_error_text":true,"request_1_log_400":true,"request_1_no_model_calls":true,"request_1_under_50ms":true,"request_1_logged_validation_error":true,"request_2_one_log":true,"request_2_http_400":false,"request_2_error_text":false,"request_2_log_400":false,"request_2_no_model_calls":true,"request_2_under_50ms":true,"request_2_logged_validation_error":false,"request_3_one_log":true,"request_3_http_400":false,"request_3_error_text":false,"request_3_log_400":false,"request_3_no_model_calls":true,"request_3_under_50ms":true,"request_3_logged_validation_error":false}
```
**Actual before JSONL, trial 1:**
```json
{"duration_ms":0.38,"http_status":400,"input":{"json_object":true,"query":null,"wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}","fit_card":null,"retry_notice":null,"selected_item_id":null,"tool_sequence":[]},"route":"/ask","run_id":"e5b5af2bf637","timestamp":"2026-11-15T21:33:07.444728+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms":0.33,"http_status":500,"input":{"json_object":false,"query":null,"wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"Internal server error; retry or inspect the local log.","fit_card":null,"retry_notice":null,"selected_item_id":null,"tool_sequence":[]},"route":"/ask","run_id":"567a14ae4e9c","timestamp":"2026-11-15T21:33:07.445894+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms":0.32,"http_status":500,"input":{"json_object":true,"query":null,"wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"Internal server error; retry or inspect the local log.","fit_card":null,"retry_notice":null,"selected_item_id":null,"tool_sequence":[]},"route":"/ask","run_id":"bcb0186e952c","timestamp":"2026-11-15T21:33:07.446901+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```
**After checks, trial 1:**
```json
{"request_1_one_log":true,"request_1_http_400":true,"request_1_error_text":true,"request_1_log_400":true,"request_1_no_model_calls":true,"request_1_under_50ms":true,"request_1_logged_validation_error":true,"request_2_one_log":true,"request_2_http_400":true,"request_2_error_text":true,"request_2_log_400":true,"request_2_no_model_calls":true,"request_2_under_50ms":true,"request_2_logged_validation_error":true,"request_3_one_log":true,"request_3_http_400":true,"request_3_error_text":true,"request_3_log_400":true,"request_3_no_model_calls":true,"request_3_under_50ms":true,"request_3_logged_validation_error":true}
```
**Actual after JSONL, trial 1:**
```json
{"duration_ms":0.32,"http_status":400,"input":{"json_object":true,"query":null,"wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}","fit_card":null,"retry_notice":null,"selected_item_id":null,"tool_sequence":[]},"route":"/ask","run_id":"a01327182858","timestamp":"2026-11-15T21:34:32.489183+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms":0.22,"http_status":400,"input":{"json_object":false,"query":null,"wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}","fit_card":null,"retry_notice":null,"selected_item_id":null,"tool_sequence":[]},"route":"/ask","run_id":"ac30d76e338e","timestamp":"2026-11-15T21:34:32.490020+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms":0.22,"http_status":400,"input":{"json_object":true,"query":null,"wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}","fit_card":null,"retry_notice":null,"selected_item_id":null,"tool_sequence":[]},"route":"/ask","run_id":"47e6e42f12af","timestamp":"2026-11-15T21:34:32.490774+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```


### Criterion 4: Secret/wardrobe privacy redaction and temporary cleanup

**Before checks, trial 1:**
```json
{"one_log":true,"no_secret":true,"no_raw_wardrobe_names":false,"selected_id":true,"retry_notice":true,"zero_temp_directories_after":true}
```
**Actual before JSONL, trial 1:**
```json
{"duration_ms":2552.42,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size XL","wardrobe_item_count":null},"model_calls":2,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Graphic Tee — 2003 Tour Bootleg Style for $24.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":"No matches in size XL; retried once without the size filter.","selected_item_id":"lst_006","tool_sequence":["search_listings","search_listings","suggest_outfit","create_fit_card"]},"route":"/ask","run_id":"fc29bbd7f048","timestamp":"2026-11-15T21:33:07.454350+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```
**After checks, trial 1:**
```json
{"one_log":true,"no_secret":true,"no_raw_wardrobe_names":false,"selected_id":true,"retry_notice":true,"zero_temp_directories_after":true}
```
**Actual after JSONL, trial 1:**
```json
{"duration_ms":2063.44,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size XL","wardrobe_item_count":null},"model_calls":2,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Graphic Tee — 2003 Tour Bootleg Style for $24.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":"No matches in size XL; retried once without the size filter.","selected_item_id":"lst_006","tool_sequence":["search_listings","search_listings","suggest_outfit","create_fit_card"]},"route":"/ask","run_id":"bda02884dfa1","timestamp":"2026-11-15T21:34:32.496383+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```


### Criterion 5: Explicit empty-wardrobe HTTP styling and zero-item telemetry

**Before checks, trial 1:**
```json
{"one_log":true,"http_200":true,"error_null":true,"nonempty_outfit":true,"no_wardrobe_statement":true,"exact_user_title":false,"other_general_clothes":true,"no_ownership_claim":true,"zero_wardrobe_logged":true,"selected_id":true,"card_price":true}
```
**Actual before JSONL, trial 1:**
```json
{"duration_ms":1712.17,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size M","wardrobe_item_count":0},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Pair it with relaxed jeans and clean sneakers.","retry_notice":null,"selected_item_id":"lst_002","tool_sequence":["search_listings","suggest_outfit","create_fit_card"]},"route":"/ask","run_id":"71ca3df6009a","timestamp":"2026-11-15T21:33:15.003393+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```
**After checks, trial 1:**
```json
{"one_log":true,"http_200":true,"error_null":true,"nonempty_outfit":true,"no_wardrobe_statement":true,"exact_user_title":false,"other_general_clothes":true,"no_ownership_claim":true,"zero_wardrobe_logged":true,"selected_id":true,"card_price":true}
```
**Actual after JSONL, trial 1:**
```json
{"duration_ms":1377.79,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size M","wardrobe_item_count":0},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Pair it with relaxed jeans and clean sneakers.","retry_notice":null,"selected_item_id":"lst_002","tool_sequence":["search_listings","suggest_outfit","create_fit_card"]},"route":"/ask","run_id":"5cd150a8bfbe","timestamp":"2026-11-15T21:34:38.665825+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```


## What's still broken and why I stopped

1. **Text equality target mismatches:** The manually copied criterion title uses U+2013 while the actual listing uses U+2014. This is not an incorrect listing result. A future criterion revision should keep the original and explicitly note that the original target measured typography instead of the item's identity; only revise according to the professor's permitted reasons.
2. **Privacy leak in stored caption snippet:** Raw example wardrobe item names survive into the first 180 characters of `output.fit_card`. Redacting/omitting such text from persistent logs is the first engineering security improvement I would do next because live user wardrobes would be private.
3. **Live Gemini usage unverified:** The student capstone repeated tests used local model fallback; keyed model quality, token consumption, and dollar-cost would need separate real keyed trials. The earlier no-key measured running-time figure remains available in the README.

The requirement was **one change, diagnosed, with the same full five-criterion test rerun**. Stopping here keeps the causal comparison attributable to `serve.py` only; further fixes should be separately scoped and measured.
