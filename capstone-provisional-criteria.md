# Unit 9 FitFindr — provisional evaluation checks (AI-assisted draft)

**Academic integrity note:** These five checks were drafted with AI assistance so the
user can rehearse the technical build–test–diagnose–fix cycle. They are **not**
claimed to be the student's independently written five Unit 9 acceptance
criteria. The professor expressly requires the student to write their own.
Before submission, the student must review/write and commit their own five
criteria under the Unit 9 section of `criteria.md`, then rerun the capstone
evaluation against them. Older Unit 3/4 criteria remain unchanged.

**System and path:** FitFindr Unit 9, Shape A (deploy and instrument),
local Flask server through the real MCP subprocess; offline local model
fallback mode with `AI201_CACHE=0`, no Gemini API key. Each "trial" is a
fresh independent POST handled by Flask's actual `serve.py::ask` route.
All five checks have a **target of 3 of 3 separate trials**.
The first three and the fifth evaluate new observability behavior.
These targets were fixed **before the baseline run**, not adjusted to match results.

1. **Valid request gets a structured log (+ instrumentation).** For each
   `POST /ask` with `vintage graphic tee under $30, size M`, expect HTTP 200,
   a usable selected listing and fit card, and exactly one fresh JSONL record
   whose `run_id` equals the `X-FitFindr-Run-ID` response header. That record
   must contain a UTC timestamp, nonempty input query, output, HTTP status,
   numeric nonnegative `duration_ms`, and nonnegative numeric usage counters.
   **Target: 3/3. Reason:** A missing or mismatched record makes a real
   request impossible to correlate after the fact.

2. **Tool path can be reconstructed from the log (+ instrumentation).** For
   each `POST /ask` with `vintage graphic tee under $30, size M`, the
   new JSONL record's `output.tool_sequence` must be exactly
   `["search_listings", "suggest_outfit", "create_fit_card"]` and match the
   actual `tool_calls` returned by the session. **Target: 3/3. Reason:**
   A log that merely says which item was chosen cannot reveal which tool
   step failed or whether a retry occurred.

3. **Invalid request gets an observable failure (+ instrumentation).** For
   each `POST /ask` with empty JSON `{}`, expect HTTP 400 and one JSONL
   record with matching run ID, HTTP 400, nonempty `output.error`, and
   numeric nonnegative `duration_ms`. **Target: 3/3. Reason:** Rejected
   user requests must not disappear from operational records.

4. **Size-filter retry remains functional (+ regression of existing agent).**
   For `vintage graphic tee under $30, size XL`, the response must include
   exactly two initial `search_listings` calls (first `size="XL"`, second
   `size=None`) before the outfit and card calls; the log must record a
   nonempty `retry_notice` and a chosen listing. **Target: 3/3. Reason:**
   Observability must not break the earlier Unit 4 bounded retry behavior.

5. **No-match branch is recorded without bogus spend (+ instrumentation).**
   For `designer ballgown size XXS under $5`, expect HTTP 200 with an
   agent-level nonempty error, no selected listing or fit card; the JSONL
   record must preserve the error, have `output.fit_card=None`, and record
   zero model calls and zero provider tokens. **Target: 3/3. Reason:**
   A normal HTTP 200 can still represent an application-level failed
   search, and it should not be mistaken for a successful outfit or a billed
   generation.

**Interpretation:** A criterion is MET only if all three individual trials
pass all its named checks. An observed MISSED result is preserved, diagnosed,
and not relabeled or the target softened. A single source-code change
addressing a baseline miss will be compared using the exact same tests.
