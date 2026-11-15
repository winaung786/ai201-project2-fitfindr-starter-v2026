# Unit 9 provisional evaluation — before

AI-assisted rehearsal criteria, **not** independently written by the student.
Actual Flask + MCP subprocess requests with no Gemini key, response cache off.
Criteria SHA256: `3fc2e0921a4eaa37a44a6b28afc5941956d565ff1d010464c288d7d849967842`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Structured successful request | 3/3 | PASS | PASS | PASS | MET (3/3) |
| 2. Recover ordered tool path | 3/3 | FAIL | FAIL | FAIL | MISSED (0/3) |
| 3. Rejected input logged | 3/3 | PASS | PASS | PASS | MET (3/3) |
| 4. Size retry preserved | 3/3 | PASS | PASS | PASS | MET (3/3) |
| 5. No-match logging and zero provider usage | 3/3 | PASS | PASS | PASS | MET (3/3) |

## Actual output from one trial per criterion

Source: `scripts/capstone_eval.py::_trial` invokes `serve.py::ask`;
the structured record is created by `capstone_logging.py::_measure_one`.

### Criterion 1 — Structured successful request

Checks: {"http_200": true, "one_log_record": true, "matching_run_id": true, "listing_and_fit_card": true, "timestamp": true, "input_and_output": true, "http_status_logged": true, "duration_ms": true, "usage_counters": true}

Actual JSONL output:
~~~json
{"duration_ms": 2801.31, "http_status": 200, "input": {"json_object": true, "query": "vintage graphic tee under $30, size M", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": null, "fit_card": "Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.", "retry_notice": null, "selected_item_id": "lst_002"}, "route": "/ask", "run_id": "65bd6859f122", "timestamp": "2026-11-15T21:15:13.548363+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
~~~

Actual HTTP response excerpt:
~~~json
{"error": null, "fit_card": "Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.", "notice": null, "selected_item_id": "lst_002", "tool_calls": [{"inputs": {"description": "vintage graphic tee", "max_price": 30.0, "size": "M"}, "tool": "search_listings"}, {"new_item_id": "lst_002", "tool": "suggest_outfit"}, {"new_item_id": "lst_002", "tool": "create_fit_card"}]}
~~~

### Criterion 2 — Recover ordered tool path

Checks: {"http_200": true, "one_log_record": true, "request_run_id": true, "actual_tool_calls": true, "logged_tool_sequence": false, "logged_matches_actual": false}

Actual JSONL output:
~~~json
{"duration_ms": 1672.63, "http_status": 200, "input": {"json_object": true, "query": "vintage graphic tee under $30, size M", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": null, "fit_card": "Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.", "retry_notice": null, "selected_item_id": "lst_002"}, "route": "/ask", "run_id": "72092599e16b", "timestamp": "2026-11-15T21:15:19.663293+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
~~~

Actual HTTP response excerpt:
~~~json
{"error": null, "fit_card": "Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.", "notice": null, "selected_item_id": "lst_002", "tool_calls": [{"inputs": {"description": "vintage graphic tee", "max_price": 30.0, "size": "M"}, "tool": "search_listings"}, {"new_item_id": "lst_002", "tool": "suggest_outfit"}, {"new_item_id": "lst_002", "tool": "create_fit_card"}]}
~~~

### Criterion 3 — Rejected input logged

Checks: {"http_400": true, "one_log_record": true, "matching_run_id": true, "http_400_logged": true, "error_logged": true, "duration_ms": true}

Actual JSONL output:
~~~json
{"duration_ms": 0.37, "http_status": 400, "input": {"json_object": true, "query": null, "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": "Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}", "fit_card": null, "retry_notice": null, "selected_item_id": null}, "route": "/ask", "run_id": "a13826f66114", "timestamp": "2026-11-15T21:15:24.648863+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
~~~

Actual HTTP response excerpt:
~~~json
{"error": "Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}", "fit_card": null, "notice": null, "selected_item_id": null, "tool_calls": []}
~~~

### Criterion 4 — Size retry preserved

Checks: {"http_200": true, "one_log_record": true, "exactly_one_relaxed_retry": true, "logged_retry_notice": true, "listing_returned": true}

Actual JSONL output:
~~~json
{"duration_ms": 2156.19, "http_status": 200, "input": {"json_object": true, "query": "vintage graphic tee under $30, size XL", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": null, "fit_card": "Found Graphic Tee — 2003 Tour Bootleg Style for $24.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.", "retry_notice": "No matches in size XL; retried once without the size filter.", "selected_item_id": "lst_006"}, "route": "/ask", "run_id": "554c329dc938", "timestamp": "2026-11-15T21:15:24.651775+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
~~~

Actual HTTP response excerpt:
~~~json
{"error": null, "fit_card": "Found Graphic Tee — 2003 Tour Bootleg Style for $24.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.", "notice": "No matches in size XL; retried once without the size filter.", "selected_item_id": "lst_006", "tool_calls": [{"inputs": {"description": "vintage graphic tee", "max_price": 30.0, "size": "XL"}, "tool": "search_listings"}, {"dropped_constraint": "size XL", "inputs": {"description": "vintage graphic tee", "max_price": 30.0, "size": null}, "retry": true, "tool": "search_listings"}, {"new_item_id": "lst_006", "tool": "suggest_outfit"}, {"new_item_id": "lst_006", "tool": "create_fit_card"}]}
~~~

### Criterion 5 — No-match logging and zero provider usage

Checks: {"http_200": true, "one_log_record": true, "agent_error": true, "no_listing_or_card": true, "logged_app_error": true, "no_logged_card": true, "zero_provider_calls": true, "zero_provider_tokens": true}

Actual JSONL output:
~~~json
{"duration_ms": 1011.72, "http_status": 200, "input": {"json_object": true, "query": "designer ballgown size XXS under $5", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": "No listings match that request, even after dropping the size filter. Try changing a keyword or raising the price limit.", "fit_card": null, "retry_notice": "No matches in size XXS; retried once without the size filter.", "selected_item_id": null}, "route": "/ask", "run_id": "433724421b1e", "timestamp": "2026-11-15T21:15:31.226488+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
~~~

Actual HTTP response excerpt:
~~~json
{"error": "No listings match that request, even after dropping the size filter. Try changing a keyword or raising the price limit.", "fit_card": null, "notice": "No matches in size XXS; retried once without the size filter.", "selected_item_id": null, "tool_calls": [{"inputs": {"description": "designer ballgown", "max_price": 5.0, "size": "XXS"}, "tool": "search_listings"}, {"dropped_constraint": "size XXS", "inputs": {"description": "designer ballgown", "max_price": 5.0, "size": null}, "retry": true, "tool": "search_listings"}]}
~~~
