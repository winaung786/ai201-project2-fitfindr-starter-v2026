# FitFindr

Read [RUNNING.md](RUNNING.md) for setup and commands. Unit 3 build notes and Unit 4 test evidence are recorded below.


## Unit 4 Stretch Features — Declared Before Implementation

**Declaration checkpoint (bonus work, after the completed required Unit 4 submission):** The features below are planned in this commit **before** changing the agent or tools for the bonus. The existing Unit 3 criteria, original Unit 4 before/after evidence, and the required one-improvement comparison will remain intact.

1. **Second MCP tool (+1):** Publish `suggest_outfit(new_item: dict, wardrobe: dict) -> str` alongside `search_listings`, use it from the agent through `mcp_client.call_tool`, and capture a full trace showing both MCP calls. `create_fit_card` stays direct. The model's work will occur in the MCP server subprocess, which is a measurement limitation to disclose.
2. **Retry with looser constraints (+1):** Only when search returns no matches **and the user specified a size**, retry **once** with `size=None` while preserving the description and maximum price; show clearly that the **size filter was dropped**. If the retry also returns nothing, stop without outfit or card and explain the empty result. No unbounded retries.
3. **Second measured improvement (+2):** Fix the already-diagnosed **fallback caption sentence-boundary problem** in `tools.py::create_fit_card`, leaving the normal model prompt unchanged. Evaluate against the existing after baseline, then generate a third **five-criteria × five-tries** uncached run log, judge the unchanged criteria, and report whether it helped, failed, or produced no observable difference. A third live run requires a valid private Gemini key; deterministic/offline tests must not be presented as equivalent live evidence.

**Commit-order rule:** This README declaration must appear in Git history *before* the corresponding implementation commits. Do not count any stretch points until the code, documented runtime evidence, and measurement conditions exist.

## Stretch Features — Implemented and Measured

The declaration above was committed as `3e4486b` before any bonus implementation. The second MCP tool, bounded retry, and their live baseline were committed as `5b73b1a`. The fallback improvement and its full comparison run were committed as `375cc9e`. The original Unit 4 before/after logs and `criteria.md` remain in place.

### Second MCP tool (+1)

`mcp_server.py` now registers `suggest_outfit(new_item: dict, wardrobe: dict) -> str` alongside `search_listings`. `agent.py::run_agent` calls styling through `mcp_client.call_tool`, while `create_fit_card` remains a direct tool call. The MCP wrapper returns the same string shape as the direct styling tool. The client passes the model settings to the server subprocess; `run_eval.py` records that subprocess's model response and token use so evaluation counts both model tools. The CLI's final `generate.usage()` line is local to the caption process and does not include styling calls made inside MCP; use the saved evaluation totals for the complete count.

One actual uncached run in [the bonus retry record](results/bonus-retry-run.json) includes both MCP tools in order. The tool outputs below are clipped by `trace.py`; the saved JSON has the full strings:

```text
[1] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': 'XL', 'max_price': 30.0}
      out: [] (empty)
      →    No matches; retry once without the size filter (XL).
[2] search_listings (via MCP) retry without size
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 3 items: Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey, Y2K Baby Tee — Butterfly Print
      →    Size filter dropped; matches found, so continue to styling.
[3] suggest_outfit (via MCP)
      in:  {'new_item_id': 'lst_006', 'wardrobe_items': 10}
      out: 1) Graphic Tee — 2003 Tour Bootleg Style layered under a Black cropped zip hoodie with Baggy straight-leg jean…
      →    Read the selected item from the session; a nonempty outfit permits the caption step.
[4] create_fit_card
      in:  {'new_item_id': 'lst_006', 'outfit': '1) Graphic Tee — 2003 Tour Bootleg Style layered under a Black cropped z…
      out: Spotted this incredible Graphic Tee — 2003 Tour Bootleg Style listed on depop for $24.00. One could pair it un…
      →    Read the outfit and item from the session; the caption completes this run.
```

### One retry with a looser size constraint (+1)

If the first search is empty **and a size was specified**, the agent makes exactly one more `search_listings` MCP call with `size=None`. It keeps the description and price ceiling. The session records `dropped_constraint: size XL` and displays `No matches in size XL; retried once without the size filter.` The trace above shows the first empty result and the successful retry. If the retry also finds nothing, the agent stops before styling; the five `designer ballgown size XXS under $5` runs in each bonus log show that shorter path. A query without a size does not retry.

Criterion 2 in the unchanged `criteria.md` requires the agent to stop **after search** without styling or a card; it does not require exactly one search call. The bonus scorer therefore accepts one or two `search_listings` calls and still requires no selected item, outfit, or card on that empty scenario. This interpretation is visible in `score_saved.py`, and the raw `tool_calls` are preserved in both bonus logs.

### Second measured improvement (+2)

The earlier [What's Still Broken](#whats-still-broken) diagnosis named unstable sentence boundaries in the **local fallback** from `tools.py::create_fit_card`. When the first outfit idea contains two sentences, the old fallback copied both after its listing-facts sentence. I changed only the fallback assembly to use the first complete outfit thought; the model prompt and normal model path stayed the same.

A deliberate model failure used the same listing and outfit text on both versions. Actual output from `tools.py::create_fit_card`, recorded by `scripts/bonus_fallback_probe.py`:

```text
Before (3 sentences): Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Pair it with jeans. Add white sneakers for contrast.
After  (2 sentences): Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Pair it with jeans.
```

The [before](results/bonus-fallback-before.json) and [after](results/bonus-fallback-after.json) probe records contain the identical input, the actual captions, sentence counts, and code hashes. Title, `$18.00`, and `depop` remain present. The shorter fallback loses the second styling detail; that is the tradeoff for a stable caption length.

I also ran the unchanged five criteria five times each with caching off before and after this fallback change. The **bonus baseline** was recorded after the two other stretch features and before the fallback edit. It is an additional comparison point; the original Unit 4 before/after evaluation is untouched. The saved [bonus baseline](results/unit4-bonus-baseline.json) has 25 tries and 30 model calls, and the saved [bonus after](results/unit4-bonus-after.json) has 25 tries and 31 calls, including one rate-limit retry. In every model-based try, the saved raw response equals the returned text; the fallback was not exercised in these live runs. The [comparison audit](results/bonus-comparison-audit.json) confirms `tools.py` was the only hashed source file changed between these two batches, with the same scenarios, criteria, model, temperature, and cache setting.

The bonus runs were made from a Windows checkout, so their raw working-tree SHA256 for `criteria.md` includes CRLF line endings. Normalizing only those line endings produces the original Unit 4 criteria SHA256, `e0c23c191dffa83722910db3a82c663db8ca7c784dbb69c00f6bddea8a11dbba`. The GitHub file content and committed targets were not revised; the audit records both hashes.

**Bonus baseline — five tries per criterion:**

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full three-tool run returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stops before styling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Actual item inputs match session state | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card accuracy | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Empty wardrobe behavior | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Bonus after — the same format and unchanged targets:**

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full three-tool run returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stops before styling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Actual item inputs match session state | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card accuracy | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Empty wardrobe behavior | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Did it help?** Yes on the diagnosed fallback input: three sentences became two with the listing facts preserved. The five live criterion scores stayed at 5/5 because their valid model responses did not reach the fallback. That is a measured *no observable effect on those five live scenarios*, not evidence that the fallback changed model behavior. Full output for every try appears in [the baseline run log](results/run_2026-10-07_2216_bonus-baseline.md) and [the after run log](results/run_2026-10-07_2232_bonus-after.md); the saved [ownership reviews](results/unit4-bonus-after-ownership-review.json) explain the semantic judgments.

One actual bonus-after try per criterion, captured by `run_eval.py::run_once` from `agent.py::run_agent`:

```text
Criterion 1, try 1 — tools: search_listings → suggest_outfit → create_fit_card
fit_card: Spotted this cute Y2K Baby Tee — Butterfly Print listed on depop for $18.00. It could pair with a black cropped zip hoodie, baggy straight-leg dark wash jeans, and chunky white sneakers for an effortless throwback vibe. Alternatively, one would style it with wide-leg khaki trousers, black combat boots, a brown leather belt, and a black crossbody bag.

Criterion 2, try 1 — tools: search_listings → search_listings; size XXS was dropped
selected_item: None; outfit_suggestion: None; fit_card: None
error: No listings match that request, even after dropping the size filter. Try changing a keyword or raising the price limit.

Criterion 3, try 1 — recorded by run_eval.py::run_once
selected_item id: lst_002; suggest_outfit received: lst_002; create_fit_card received: lst_002

Criterion 4, try 1 — produced by tools.py::create_fit_card
Spotted a Y2K Baby Tee — Butterfly Print listed on depop for $18.00. This top could pair nicely under a black cropped zip hoodie with baggy straight-leg jeans in a dark wash and chunky white sneakers. Alternatively, it would style well with wide-leg khaki trousers, a brown leather belt, and black combat boots.

Criterion 5, try 1 — produced by tools.py::suggest_outfit through MCP
These are general ideas because no wardrobe is saved.
1) Y2K Baby Tee — Butterfly Print with low-rise bootcut denim jeans and chunky platform sandals.
2) Y2K Baby Tee — Butterfly Print with a pleated pink tennis skirt and retro white skate sneakers.
```

## What This Does

FitFindr takes a request such as `vintage graphic tee under $30, size M`, searches the supplied secondhand listings, selects the highest-ranked match, suggests two outfits from a wardrobe, and writes a caption. If nothing matches, it stops after search and names filters the user can change. An empty wardrobe gets two general pairing ideas labeled as general because no wardrobe is saved.

Use Python 3.11–3.13, create a virtual environment, install `requirements.txt`, copy `.env.example` to `.env`, put your own `GEMINI_API_KEY` there, and run `python test.py`. The starter's `generate.py` handles model pacing and caching. Without a key, the text tools use a local fallback, but `test.py` still requires a valid key.

## Tool Inventory

### `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`

- **What it does:** Loads the sample listings, filters by size and inclusive price cap, and ranks item and style word matches.
- **Inputs:** `description` (`str`) is the requested item text; `size` (`str | None`) is an optional clothing or shoe size; `max_price` (`float | None`) is an optional dollar ceiling. `M` matches `M` and `S/M`, but not `XL`.
- **Returns:** At most `config.SEARCH_RESULT_LIMIT` listing dictionaries, best first, each with `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.
- **When it has nothing:** Returns `[]` when no item matches all filters.

### `suggest_outfit(new_item: dict, wardrobe: dict) -> str`

- **What it does:** Calls the model for two outfits using the selected listing and wardrobe pieces.
- **Inputs:** `new_item` (`dict`) is one complete listing; `wardrobe` (`dict`) contains an `items` list of wardrobe item dictionaries.
- **Returns:** A nonempty string with two numbered outfit suggestions naming the selected item and, when available, wardrobe pieces by their exact names.
- **When it has nothing:** With an empty wardrobe it gives two general pairings and says they are general because no wardrobe is saved. If the model is unavailable or fails the output checks, it returns two local suggestions using the supplied item and wardrobe.

### `create_fit_card(outfit: str, new_item: dict) -> str`

- **What it does:** Calls the model for a short social caption about the chosen item and outfit.
- **Inputs:** `outfit` (`str`) is the outfit suggestion; `new_item` (`dict`) is the same selected listing.
- **Returns:** A caption string. The model is asked for 2–4 sentences containing the selected item's title, exact formatted price, and platform. A response outside that sentence range, missing those facts, or matching the seller-claim check is replaced with a local fallback caption built from the listing facts and the first outfit idea. Title and platform matching is case-insensitive. The fallback is designed to produce two sentences using the listing facts and the first outfit idea. Both fresh live-model checks passed the 2–4 sentence rule.
- **When it has nothing:** A blank outfit returns `Cannot create a fit card without an outfit suggestion.` If the model is unavailable, the caption uses the real listing facts.

## Planning Loop

**Branch rule:** If `search_listings` returns `[]` and a size was specified, retry once without the size filter. If that retry is also empty, or if the original query had no size, write a helpful message to the session and stop before `suggest_outfit`. Otherwise store the first result, call `suggest_outfit` through MCP, then call `create_fit_card` with values read from the session. If the outfit suggestion is blank, stop before the fit card.

**Where it lives:** `agent.py::run_agent`.

**How the query is parsed:** Regular expressions extract `under $N` and `size N`; the remaining words are the description.

**What moves through the session:** `parsed` → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. `tool_calls` records the order and the selected listing ID. `trace.check_iterations` bounds the loop.

## Sample Run

These outputs used the local fallback because no model key was present in this workspace. A valid key produces model-written wording, and `python test.py` checks the actual service.

```text
$ python app.py ask 'vintage graphic tee under $30, size M'
Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop
Outfit:   1) Wear the Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.
2) Style the Y2K Baby Tee — Butterfly Print with Wide-leg khaki trousers and Black combat boots for a different look.
Fit card: Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.
0 model calls this session

$ python app.py ask 'designer ballgown size XXS under $5'
No listings match that request. Try changing a keyword, choosing another size, or raising the price limit.
0 model calls this session
```

The three tools were also called independently:

```text
$ python -c "from tools import search_listings; print([(x['id'], x['title'], x['price']) for x in search_listings('vintage graphic tee', 'M', 30)])"
[('lst_002', 'Y2K Baby Tee — Butterfly Print', 18.0)]

$ python -c "from tools import suggest_outfit; from utils.data_loader import load_listings,get_example_wardrobe; print(suggest_outfit(load_listings()[1],get_example_wardrobe()))"
1) Wear the Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.
2) Style the Y2K Baby Tee — Butterfly Print with Wide-leg khaki trousers and Black combat boots for a different look.

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('Baggy jeans and white sneakers.',load_listings()[1]))"
Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Baggy jeans and white sneakers.
```

### Fresh live-model check — October 1, 2026

After the slide-contract changes in commit `c6aec62`, Codex ran `python test.py` and a temporary recording wrapper around `agent.py::run_agent` with `AI201_CACHE=0`. The wrapper captured the actual `generate.py::generate` responses alongside the final sessions, so a local fallback could not be mistaken for a successful model answer.

- **Environment:** 10 checks passed, 0 failed; Gemini replied `Ready.` See [environment output](results/environment-check-2026-10-01.txt).
- **Example wardrobe:** All three tools completed. Gemini returned two outfits using exact wardrobe names and a three-sentence caption with the exact item title, `$18.00`, and `depop`.
- **Empty wardrobe:** All three tools completed. Gemini labeled the two suggestions as general because no wardrobe was saved, made no ownership claim, and returned a two-sentence caption with the listing facts.
- **Empty search:** Only search ran. No model request was made, the fit card stayed `None`, and the message named keywords, size, and price as things to change.

All four outfit/caption model responses were accepted directly; no local fallback was used. These agent checks used 4 live model calls and 790 reported tokens (569 prompt, 221 output), plus the separate environment-check request. Full raw responses, sessions, and check outcomes are in [the live-check log](results/live-smoke-2026-10-01.json). This is one run per path, not the Unit 4 five-tries evaluation or proof that every acceptance target has been met.

Actual example-wardrobe output from `agent.py::run_agent`:

```text
Selected: lst_002 — Y2K Baby Tee — Butterfly Print — $18.00 on depop
Outfit:
1) Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash and Chunky white sneakers
2) Y2K Baby Tee — Butterfly Print with Wide-leg khaki trousers and Black combat boots
Fit card:
Scored the cutest Y2K Baby Tee — Butterfly Print secondhand for just $18.00 on depop! It looks so good paired with baggy straight-leg jeans in a dark wash and chunky white sneakers. For another vibe, I styled it with wide-leg khaki trousers and black combat boots.
```

The temporary API-key file was deleted after the checks; it is not part of these logs or commits.

## How I Used AI

**Moment 1:** I used Codex to implement the tool contracts. The initial search included a mesh top for a graphic tee request because its description mentioned layering under a tee. I narrowed the garment check to the title and style tags, and the query now returns only the tee.

**Moment 2:** I used Codex to examine a model caption that claimed the wearer was selling the listing. I tightened the prompt and added a check that falls back to a caption grounded in the actual listing. I then ported the loop to this v2026 starter's `generate.py`, keeping its pacing, cache, and future MCP files.

**Slide contract review:** After reading the full Unit 3 slide deck, I updated `suggest_outfit` to return two numbered ideas and to label general ideas when no wardrobe is saved. I also required two to four sentences in `create_fit_card`. Local checks covered both fallback and model-output validation. On October 1, 2026, Codex ran fresh checks with caching disabled: the example-wardrobe and empty-wardrobe runs received valid Gemini responses without fallback, and the empty-search path stopped early. The outputs are recorded under Sample Run; the full Unit 4 evaluation remains separate.

**Unit 4:** I used Codex to register search over MCP, compare its results with direct search, add per-step traces, and trigger the required failures. The invalid-key run exposed a swallowed error, so Codex added a user message while preserving the existing local fallback. Codex then ran 25 before trials, reviewed ownership claims in the actual saved wording, scored the unchanged criteria, and traced the caption misses to an incomplete prompt. I used its diagnosis to make one caption-prompt change and run the same 25 trials again. Both batches use the actual Gemini model with caching off; recording replacements are confined to the state criterion, as that criterion specifies. Codex wrote the score/review records and this explanation, so the ownership interpretation is explicit for me to review and explain. The model, dataset, search behavior, and committed acceptance criteria are unchanged.

**Unit 4 stretch:** I used Codex to add a second MCP tool, implement and trace one retry without the size filter, capture model calls made inside the MCP subprocess, and run a fresh 25-try bonus baseline. Codex then tested the already-diagnosed fallback caption problem with a forced model outage, changed the fallback assembly, reran the same 25 live trials, and recorded both the targeted improvement and the unchanged live criterion scores. The bonus declaration precedes these implementation commits.

The three additional criteria in `criteria.md` were AI assisted in the earlier fork. Codex later reviewed and clarified their test methods without changing the targets. I then reviewed criteria 3–5 and wrote the reasons for their targets in my own words.

---

## Run Log — Before

Command: `python run_eval.py --label before`. `scenarios.py` maps one scenario to each unchanged criterion using the exact Unit 3 query and wardrobe. Each criterion has five distinct agent runs; caching is off. Criterion 3 replaces only the two text tools with recording functions, as its original wording requires; its search still uses MCP. Criteria 1, 4, and 5 make real model calls. The runner checkpoints every completed try.

The raw [before JSON](results/unit4-before.json) records full sessions, actual tool inputs, raw prompts/responses, traces, exceptions, tokens, and code/data hashes. It completed 25 tries with 30 Gemini calls (4,370 prompt + 1,881 output tokens). All 30 received model responses were used directly; no local fallback was used in this evaluation.

The original `criteria.md` SHA256 remains `e0c23c191dffa83722910db3a82c663db8ca7c784dbb69c00f6bddea8a11dbba`. Targets are 4/5, 5/5, 5/5, 4/5, and 4/5. Criterion 4 is scored at its original **1–4 sentences**, while the tool's separate slide contract requests 2–4 sentences. No criterion or target was revised.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full three-tool run returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stops before styling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Actual item inputs match session state | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card accuracy | 4 of 5 | FAIL | FAIL | PASS | FAIL | PASS | MISSED (2/5) |
| 5. Empty wardrobe behavior | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Scores come from `score_saved.py`, which reads saved JSON and makes no model calls. Ownership is a semantic judgment, so Codex inspected each relevant caption/suggestion and recorded the exact text, its hash, a verdict, and a reason in [ownership review](results/unit4-before-ownership-review.json). The selected tee is not in the saved wardrobe. We read the original rule literally: saying it was “scored” asserts an unsupported acquisition; finding or spotting a listing and describing styling alone do not assert possession. This interpretation is explicit so the verdict can be challenged. The scorer preserves the raw JSON and records its hash in [scored results](results/unit4-before-scored.json).

### Actual output from one try for each criterion

These are actual values captured by `run_eval.py::run_once` from `agent.py::run_agent`, not invented examples.

**Criterion 1, try 1**

Produced by `agent.py::run_agent` and `tools.py::create_fit_card`:

```text
tool order: search_listings -> suggest_outfit -> create_fit_card
fit_card: I spotted the cutest Y2K Baby Tee — Butterfly Print while out thrifting and had to style it two ways. It looks so good paired with baggy straight-leg jeans and chunky white sneakers, or dressed down with wide-leg khaki trousers and black combat boots. I can't believe I found this secondhand gem scrolling on depop for just $18.00!
```

**Criterion 2, try 1**

Produced by `agent.py::run_agent` empty-search branch:

```text
tool order: search_listings
selected_item: None
outfit_suggestion: None
fit_card: None
message: No listings match that request. Try changing a keyword, choosing another size, or raising the price limit.
```

**Criterion 3, try 1**

Produced by `run_eval.py::run_once` recording functions and `agent.py::run_agent`:

```text
selected_item id: lst_002
search_results[0] id: lst_002
suggest_outfit actually received new_item id: lst_002
create_fit_card actually received new_item id: lst_002
selected_item equals search_results[0]: True
model calls: 0 (recording replacements required by criterion 3)
```

**Criterion 4, try 1**

Produced by `tools.py::create_fit_card`, called by `agent.py::run_agent`; this try fails the ownership rule:

```text
Scored the ultimate vintage find while thrifting: the Y2K Baby Tee — Butterfly Print. It’s listed on depop for just $18.00, and I’m obsessed with how versatile it is. You can easily style it with baggy dark-wash jeans and chunky white sneakers, or switch it up with wide-leg khaki trousers and black combat boots.
```

**Criterion 5, try 1**

Produced by `tools.py::suggest_outfit` with `get_empty_wardrobe()`:

```text
error: None
These are general ideas because no wardrobe is saved.
1) Y2K Baby Tee — Butterfly Print with baggy low-rise cargo pants and chunky platform sneakers.
2) Y2K Baby Tee — Butterfly Print with a denim pleated mini skirt and strappy kitten heels.
```

All five actual outputs per criterion are preserved in [the generated run log](results/run_2026-10-03_1945_before.md) and the full JSON above.

---

## Verdicts and Diagnoses

The before scores are judged against the original Unit 3 targets. “MET” means the observed pass count reached the target; it does not mean the agent is reliable for every item or wording.

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Three-tool run and nonempty card | 4 of 5 | MET (5/5) | All five actual tool logs show search → outfit → card, with a nonempty final card. |
| 2 | Empty search stops early | 5 of 5 | MET (5/5) | All five sessions contain only search, three `None` fields, and a message naming filters to change. |
| 3 | State consistency | 5 of 5 | MET (5/5) | Both recording replacements actually received `lst_002` in every try; selected item equals the first MCP result. |
| 4 | Caption facts and ownership | 4 of 5 | MISSED (2/5) | Tries 1, 2, and 4 assert acquisition of the tee even though it is absent from the saved wardrobe. All five meet the title, formatted-price, platform, and original sentence-count checks. |
| 5 | Empty wardrobe advice | 4 of 5 | MET (5/5) | Every session has no error and an outfit naming the exact title, another clothing/shoe pairing, and no ownership claim. |

**Diagnosis for criterion 4:** The failing step is `tools.py::create_fit_card`, step 3 in the loop. The raw model output says “Scored the ultimate vintage find…” (try 1), “Scored the cutest Y2K Baby Tee…” (try 2), or “I just scored secondhand…” (try 4). The selected tee is only an available listing, not a recorded wardrobe item or a completed purchase. Each raw response equals the returned caption, so a fallback did not introduce the claim. Search returned the right item and both actual tool receipts match it: the branch and session are working. The prompt discourages seller claims and invented wardrobe pieces but does not clearly distinguish discovering a listing from acquiring it. The validator checks seller wording, length, title, price, and platform, so these acquisition claims pass its existing checks. This is one repeated model-output problem at the caption tool.

**Challenging the verdict:** The strongest argument for MET is that “scored” could be creative caption shorthand for finding a deal, and all numeric facts are present. I kept MISSED because ordinary first-person “I just scored” asserts an acquisition that the session cannot support. The ownership interpretation and exact excerpts are recorded in the review JSON rather than silently treating that wording as acceptable. No criterion or target was loosened.

**What the passing rows do not cover:** Criterion 1 only checks completion and a nonempty card; its successful cards can still contain inaccurate phrasing. Criteria 2 and 3 cover deterministic behavior on fixed inputs. Criterion 5 checks empty-wardrobe outfit advice, not the caption generated afterward. I would tighten a future criterion 4 to explicitly name acquisition claims and cover empty-wardrobe captions. That is a future recommendation; the current criteria remain byte-for-byte unchanged.

**Chosen improvement, before changing code:** Rewrite only the caption prompt so it describes an available listing and possible pairings, explicitly avoiding claims of purchase, possession, or having worn the outfit. Keep the fallback, validation, search, loop, model, temperature, scenarios, scoring, and targets unchanged. The full after run will use the same five scenarios and five tries each.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path** — actual `python app.py ask 'vintage graphic tee under $30, size M' --trace` output from `agent.py::run_agent` and `tools.py`:

```text
[1] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': 'M', 'max_price': 30.0}
      out: 1 items: Y2K Baby Tee — Butterfly Print
      →    Matches found; store the first result in the session and style it.
[2] suggest_outfit
      in:  {'new_item_id': 'lst_002', 'wardrobe_items': 10}
      out: 1) Y2K Baby Tee — Butterfly Print + Baggy straight-leg jeans, dark wash + Chunky white sneakers 2) Y2K Baby Te…
      →    Read the selected item from the session; a nonempty outfit permits the caption step.
[3] create_fit_card
      in:  {'new_item_id': 'lst_002', 'outfit': '1) Y2K Baby Tee — Butterfly Print + Baggy straight-leg jeans, dark wash …
      out: Found the cutest secondhand Y2K Baby Tee — Butterfly Print while out thrifting and I am obsessed with both way…
      →    Read the outfit and item from the session; the caption completes this run.

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   1) Y2K Baby Tee — Butterfly Print + Baggy straight-leg jeans, dark wash + Chunky white sneakers
2) Y2K Baby Tee — Butterfly Print + Wide-leg khaki trousers + Black combat boots

  Fit card: Found the cutest secondhand Y2K Baby Tee — Butterfly Print while out thrifting and I am obsessed with both ways to style it. You can pair it with baggy straight-leg dark wash jeans and chunky white sneakers, or dress it up with wide-leg khaki trousers and black combat boots. I spotted this exact piece on depop for just $18.00 and it's such a versatile retro find.

2 model calls this session, 302 prompt + 131 output tokens
```

**Empty search** — actual CLI output; only one step ran:

```text
[1] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    No matches; stop before suggest_outfit. Change keyword, size, or price.

  No listings match that request. Try changing a keyword, choosing another size, or raising the price limit.

0 model calls this session
```

### Required failures triggered deliberately

All diagnostic CLI runs used caching off. The invalid-key run changed exactly one character in the temporary `.env`, used an unasked query, and restored the valid key in a `finally` block. The temporary credential file was then deleted. Before adding handlers, a separate invalid-key run silently used fallbacks; [that original output](results/unit4-mcp-and-prehandler.json) records why a message was needed.

- **Empty search:** No matches. The agent tells the user to change a keyword, choose another size, or raise the price limit and stops before styling.
- **Empty wardrobe:** `No wardrobe items are saved. Using general pairing ideas; add wardrobe items for personal suggestions.` Two general ideas followed, rather than an error or blank string.
- **Model unavailable:** The messages below identify the failure and say to check the key/connection and retry. Local advice and a listing-grounded caption follow, explicitly identified as local. There was no cache hit, traceback, or endless loop.

```text
The outfit model couldn't be reached. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. Using local styling advice; check GEMINI_API_KEY in .env and your connection, then retry.
The caption model couldn't be reached. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. Using a local caption; check GEMINI_API_KEY in .env and your connection, then retry.
```

A user can act on these messages by relaxing filters, saving wardrobe items, or fixing the model key/connection. Actual output and exit codes are in [the failure log](results/unit4-failures.json); rerun with `python scripts/unit4_failures.py` using your own local `.env`.

**On the required Unit 4 MCP move, before stretch work:** `search_listings` was registered in `mcp_server.py` with the same typed inputs as Tool Inventory. `agent.py::run_agent` called it through the starter `mcp_client.call_tool` instead of directly. The other two tools were direct calls at that checkpoint. Three direct-versus-MCP searches returned identical lists, including the empty case, and a fresh full query still completed. Registration, input types, and real outputs are in [MCP verification](results/unit4-mcp-verification.md). The stretch work later moved `suggest_outfit` to MCP as recorded above.



---

## The Improvement

**What I changed:** Only the text assigned to `prompt` inside `tools.py::create_fit_card`. The caption now describes discovering an available listing, asks for possible pairings, explicitly forbids purchase/possession/wearing claims such as “scored,” and assigns the price only to the selected item. The exact [prompt diff](results/unit4-improvement.diff) is committed. The code comparison confirms every statement outside that one prompt assignment is identical between the before and after agents.

**Which failure it was meant to fix:** Criterion 4 missed because three raw captions implied acquisition of a tee that search had only found. The prompt now makes that distinction explicit. The existing validator and fallback were not changed.

Command: `python run_eval.py --label after`. This reran all five scenarios five times with caching off: 25 fresh tries and 30 real Gemini calls (5,414 prompt + 1,769 output tokens). No response was replaced by a fallback. The model, temperatures, queries, wardrobes, dataset, MCP client/server, agent loop, evaluation runner, criteria, and targets are identical to before. File hashes and the one-prompt code comparison are recorded in [comparison audit](results/unit4-comparison-audit.json).

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full three-tool run returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stops before styling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Actual item inputs match session state | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card accuracy | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Empty wardrobe behavior | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Full actual outputs are in [after JSON](results/unit4-after.json) and [the generated after run log](results/run_2026-10-03_1954_after.md). The [ownership review](results/unit4-after-ownership-review.json) uses the same interpretation as before; [scored results](results/unit4-after-scored.json) retain each check and the raw report hash.

### Before and after together

| Criterion | Target | Before | After |
|---|---|---|---|
| 1. Three-tool completion | 4 of 5 | MET (5/5) | MET (5/5) |
| 2. Empty-search stop | 5 of 5 | MET (5/5) | MET (5/5) |
| 3. State consistency | 5 of 5 | MET (5/5) | MET (5/5) |
| 4. Fit card accuracy | 4 of 5 | MISSED (2/5) | MET (5/5) |
| 5. Empty wardrobe advice | 4 of 5 | MET (5/5) | MET (5/5) |

**Did it help, and how do I know:** In these five caption-accuracy trials, unsupported acquisition claims fell from three to zero and criterion 4 improved from 2/5 to 5/5, meeting its unchanged 4/5 target. The other four criteria stayed at 5/5. Raw responses equal returned text in both batches, so a new fallback did not hide the change. This small fixed-query sample shows an observed improvement; it does not prove future reliability. The after batch used 932 more total reported tokens (7,183 versus 6,251), and some captions became less natural in wording.

### Actual after output from one try per criterion

The following values are captured by `run_eval.py::run_once` from `agent.py::run_agent`.

**Criterion 1, try 1**

Produced by `agent.py::run_agent` and `tools.py::create_fit_card`:

```text
tool order: search_listings -> suggest_outfit -> create_fit_card
fit_card: Spotted this Y2K Baby Tee — Butterfly Print listed on depop for $18.00. It would style great with baggy straight-leg jeans in a dark wash, a brown leather belt, and chunky white sneakers. Alternatively, one could pair the top with wide-leg khaki trousers, a vintage black denim jacket, and chunky white sneakers for a different look.
```

**Criterion 2, try 1**

Produced by `agent.py::run_agent` empty-search branch:

```text
tool order: search_listings
selected_item: None
outfit_suggestion: None
fit_card: None
message: No listings match that request. Try changing a keyword, choosing another size, or raising the price limit.
```

**Criterion 3, try 1**

Produced by `run_eval.py::run_once` recording functions and `agent.py::run_agent`:

```text
selected_item id: lst_002
search_results[0] id: lst_002
suggest_outfit actually received new_item id: lst_002
create_fit_card actually received new_item id: lst_002
selected_item equals search_results[0]: True
model calls: 0 (recording replacements)
```

**Criterion 4, try 1**

Produced by `tools.py::create_fit_card`:

```text
Spotted this adorable Y2K Baby Tee — Butterfly Print listed on depop for just $18.00! You could pair the top with baggy straight-leg jeans in a dark wash and chunky white sneakers for a classic casual look. Alternatively, the tee would style effortlessly with wide-leg khaki trousers and black combat boots.
```

**Criterion 5, try 1**

Produced by `tools.py::suggest_outfit`:

```text
error: None
These are general ideas because no wardrobe is saved.
1) Y2K Baby Tee — Butterfly Print with low-rise bootcut denim jeans and platform sandals
2) Y2K Baby Tee — Butterfly Print with a pleated pink tennis skirt and chunky white sneakers
```

---

## What's Still Broken

No committed criterion remains MISSED in the after batch. That is the result of five fixed-scenario tries per criterion, not a guarantee of general reliability.

- **Caption grammar:** After criterion 4 tries 4 and 5 include “Alternatively, would style…” without a clear subject. The captions meet the committed facts/length/ownership checks, but some wording would need editing before posting. I would next revise the prompt for natural complete sentences and add a measurable grammar/usability criterion. I stopped after the one permitted improvement so its effect could be measured separately.
- **Ownership validation:** The caption validator still checks facts, length, and seller phrases; it does not deterministically validate every purchase or possession claim. The revised prompt reduced the observed claims to zero, but future responses could regress. A future change would add a grounded ownership check or a constrained response format and test more listings.
- **Fallback sentence boundaries:** The bonus improvement now uses the first complete thought from the first outfit idea; the measured multi-sentence example produces two sentences. Unusual punctuation inside an item title or a first thought could still need a stronger sentence parser. The required invalid-key example stayed readable.
- **Coverage:** The committed model criteria use one tee listing and two fixed wardrobes. Broader descriptions, item categories, and empty-wardrobe captions still need repeated tests. I would tighten future criteria and add those scenarios without altering the original results.

### Submission record

Same repository as Unit 3: [winaung786/ai201-project2-fitfindr-starter-v2026](https://github.com/winaung786/ai201-project2-fitfindr-starter-v2026).

Unit 4 commits follow the milestone order: MCP registration/equality evidence; failure handlers and trace evidence; exact scenarios and logging; before results; diagnoses; one prompt improvement; after results; final write-up. This provides more than the required four new commits. `criteria.md`, `RUNNING.md`, the model/configuration, and both data files retain the Unit 3 contents.

- [x] Required search tool registered and called through MCP, with typed inputs, dollar units, and an empty-case contract; styling later moved through MCP for stretch credit.
- [x] Empty search, empty wardrobe, and model-unavailable cases deliberately triggered and documented.
- [x] Full happy-path and shorter empty-path traces show inputs, results, choices, and the MCP call.
- [x] Five criteria, five tries each, before and after, with actual output for each criterion.
- [x] A verdict for every criterion and a step/mechanism diagnosis for every before miss.
- [x] One prompt change measured with the same agent, data, model, scenarios, and targets.
- [x] Remaining limits and AI use disclosed; no API key included in the repository or evidence.
- [ ] Submit the same repository URL in the course submission page.

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

## Capstone

**What This Extends**

This is the same FitFindr agent built in Units 3 and 4, including MCP-based listing search and outfit suggestions and the fit-card tool. The Unit 9 extension adds an observable, repeatable run path around the existing Flask `POST /ask` endpoint. The agent's shopping and styling logic is retained, rather than rebuilt.

**The Shape**

**A — Deploy and instrument.** Chosen run path: **Path B, local with logs** (equivalent credit to a hosted deployment). Scope is structured JSONL records for each HTTP `/ask` request, including invalid or failed requests; elapsed time; output summary; and actual per-request model-call/token counters. The local server already exists in `serve.py`, so the extension is the operational layer.

**Out of scope:** No new shopping platforms or Amazon integration; no image/face swap; no redesign of the AI prompts or search ranking; no second agent or hosted signup. No extra model or private API key will be committed.

**Running It**

**Path B, local with logs.** Start the existing server using `python serve.py`, as documented with clean-checkout setup in [RUNNING.md](RUNNING.md). A GitHub Actions clean Python 3.12 checkout also executed the actual Flask/MCP path, with real saved `results/capstone-smoke.jsonl` evidence. The provider key was omitted for testing, so successful styling text came from fallback mode. Do not mistake this for hosted URL or keyed-model verification.

**Assessment order and student-owned criteria**

The five Unit 9 acceptance criteria must be **written by the student alone**. They will be added as a clearly labeled Capstone section in `criteria.md`, with measurable targets and reasons, and committed **before** the first Unit 9 evaluation results. AI assistance may *review* them for testability, not author the five standards. The Unit 3/4 criteria remain intact. No pre/post scores will be claimed before those criteria and actual trials exist.

**Instrumentation**

`capstone_logging.py::instrument_http` appends one JSON record per HTTP `POST /ask`. Fields are named: UTC `timestamp`, `run_id`, `route`, clipped `input` query/wardrobe count, summarized `output`, `http_status`, full `duration_ms`, observed `model_calls`, and `model_tokens` (including subprocess usage if a model responds). The API key and full wardrobe are not logged. A temporary metrics file used by the MCP child is deleted after each request. The log is written to `results/capstone-requests.jsonl` by default, or `FITFINDR_LOG_PATH` when set.

**Real run evidence — 10 valid requests plus 1 deliberately rejected request.** This is the actual output produced by `scripts/capstone_smoke.py::main` using `serve.py::ask`, recorded by `capstone_logging.py::instrument_http` in a clean Python 3.12 GitHub Actions checkout. The real MCP subprocess ran; no Gemini key was provided, so text used local fallback. The rejected input returned HTTP 400. This is an *operational smoke session*, not the five acceptance-criteria evaluation.

```json
{"duration_ms": 2657.34, "http_status": 200, "input": {"json_object": true, "query": "vintage graphic tee under $30, size M", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": null, "fit_card": "Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.", "retry_notice": null, "selected_item_id": "lst_002"}, "route": "/ask", "run_id": "7c955013b21a", "timestamp": "2026-11-14T03:13:41.620718+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms": 2065.0, "http_status": 200, "input": {"json_object": true, "query": "vintage graphic tee under $30, size XL", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": null, "fit_card": "Found Graphic Tee — 2003 Tour Bootleg Style for $24.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.", "retry_notice": "No matches in size XL; retried once without the size filter.", "selected_item_id": "lst_006"}, "route": "/ask", "run_id": "30573c4cb656", "timestamp": "2026-11-14T03:13:44.279016+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms": 982.25, "http_status": 200, "input": {"json_object": true, "query": "designer ballgown size XXS under $5", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": "No listings match that request, even after dropping the size filter. Try changing a keyword or raising the price limit.", "fit_card": null, "retry_notice": "No matches in size XXS; retried once without the size filter.", "selected_item_id": null}, "route": "/ask", "run_id": "b759b1d3e65b", "timestamp": "2026-11-14T03:13:46.344667+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms": 1542.42, "http_status": 200, "input": {"json_object": true, "query": "denim jacket under $50", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": null, "fit_card": "Found Denim Jacket — Light Wash, Cropped for $42.00 on poshmark. Wear it with White ribbed tank top and Chunky white sneakers for a relaxed look.", "retry_notice": null, "selected_item_id": "lst_007"}, "route": "/ask", "run_id": "1de5e81b231d", "timestamp": "2026-11-14T03:13:47.327775+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms": 1550.19, "http_status": 200, "input": {"json_object": true, "query": "90s track jacket under $45, size M", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": null, "fit_card": "Found 90s Track Jacket — Navy/White Stripe for $45.00 on poshmark. Wear it with White ribbed tank top and Chunky white sneakers for a relaxed look.", "retry_notice": null, "selected_item_id": "lst_004"}, "route": "/ask", "run_id": "bfe9d384562b", "timestamp": "2026-11-14T03:13:48.870882+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms": 1531.85, "http_status": 200, "input": {"json_object": true, "query": "platform sneakers size 8", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": null, "fit_card": "Found Platform Sneakers — White Chunky Sole for $48.00 on poshmark. Wear it with White ribbed tank top and Baggy straight-leg jeans, dark wash for a relaxed look.", "retry_notice": null, "selected_item_id": "lst_019"}, "route": "/ask", "run_id": "932b272f5152", "timestamp": "2026-11-14T03:13:50.421693+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms": 1536.22, "http_status": 200, "input": {"json_object": true, "query": "silk slip dress under $40", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": null, "fit_card": "Found 90s Silk Slip Dress — Floral, Midi Length for $30.00 on depop. Wear it with White ribbed tank top and Chunky white sneakers for a relaxed look.", "retry_notice": null, "selected_item_id": "lst_013"}, "route": "/ask", "run_id": "bc47fdb54c95", "timestamp": "2026-11-14T03:13:51.954216+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms": 1527.46, "http_status": 200, "input": {"json_object": true, "query": "vintage graphic tee under $30", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": null, "fit_card": "Found Graphic Tee — 2003 Tour Bootleg Style for $24.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.", "retry_notice": null, "selected_item_id": "lst_006"}, "route": "/ask", "run_id": "e35fbf3cbde7", "timestamp": "2026-11-14T03:13:53.491057+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms": 958.87, "http_status": 200, "input": {"json_object": true, "query": "designer ballgown size XXS under $5", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": "No listings match that request, even after dropping the size filter. Try changing a keyword or raising the price limit.", "fit_card": null, "retry_notice": "No matches in size XXS; retried once without the size filter.", "selected_item_id": null}, "route": "/ask", "run_id": "7354f7b97027", "timestamp": "2026-11-14T03:13:55.019173+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms": 1522.76, "http_status": 200, "input": {"json_object": true, "query": "vintage graphic tee under $30, size M", "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": null, "fit_card": "Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.", "retry_notice": null, "selected_item_id": "lst_002"}, "route": "/ask", "run_id": "d0182dec5a2d", "timestamp": "2026-11-14T03:13:55.978659+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
{"duration_ms": 0.32, "http_status": 400, "input": {"json_object": true, "query": null, "wardrobe_item_count": null}, "model_calls": 0, "model_tokens": {"output": 0, "prompt": 0, "total": 0}, "output": {"error": "Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}", "fit_card": null, "retry_notice": null, "selected_item_id": null}, "route": "/ask", "run_id": "44977cbd9d06", "timestamp": "2026-11-14T03:13:57.502024+00:00", "token_measurement": "Observed provider usage; zero means no billed model calls were recorded."}
```

Source evidence: [saved JSONL log](results/capstone-smoke.jsonl), [extract](results/capstone-smoke-extract.md), [summary](results/capstone-smoke-summary.json), [clean-checkout workflow](.github/workflows/capstone-smoke.yml).

**What It Costs**

Measured from ten valid end-to-end HTTP requests with `time.perf_counter` around the Flask request handler. The observed average was **1.5874 seconds per run**, including the two MCP subprocess launches on matching results; actual requests differ with query and branch. At this measured average, **100 sequential runs/day × 1.5874 seconds ≈ 158.74 seconds of processing/wall time per day** (about 2.65 minutes). This is an observed time-resource figure, *not* a hosting charge or total CPU-seconds estimate.

**Provider tokens in this run:** 0 across 10 valid requests, with 0 billed model calls, because the test deliberately ran without a Gemini key and returned local text fallbacks. **The real keyed Gemini API cost remains unmeasured in this capstone run.** A keyed test would be needed before making any dollar-cost or model-token claims.

**Run Log and Verdicts**

**Five AI-assisted provisional checks, three separate trials each, before one code improvement.** These are an instrumented technical rehearsal, **not** the professor-required five independently student-authored criteria. The provisional standards were saved in [capstone-provisional-criteria.md](capstone-provisional-criteria.md) and committed before results; they were not relaxed afterward. Test environment: clean Python 3.12 GitHub Actions checkout, actual Flask + MCP subprocess, no Gemini API key, caching off. `results/capstone-before-requests.jsonl` contains all 15 real log entries.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Structured successful request | 3/3 | PASS | PASS | PASS | MET (3/3) |
| 2. Recover ordered tool path | 3/3 | FAIL | FAIL | FAIL | MISSED (0/3) |
| 3. Rejected input logged | 3/3 | PASS | PASS | PASS | MET (3/3) |
| 4. Size retry preserved | 3/3 | PASS | PASS | PASS | MET (3/3) |
| 5. No-match logging and zero provider usage | 3/3 | PASS | PASS | PASS | MET (3/3) |

**Diagnoses and verdicts:** Checks 1, 3, 4 and 5 were MET on 3/3 each; there was no miss for those checks to diagnose. Check 2 was MISSED on **all three trials**. The agent returned `tool_calls` in the correct three-step order, but `capstone_logging.py::_output_summary` discarded the tool names when making the reduced JSONL `output` summary. Thus `output.tool_sequence` was missing from every baseline log, so an operator could not reconstruct the agent sequence even though the agent itself completed. The stage is the **structured logger**, not the search or model.

**Raw actual output from the first trial of each criterion** (one JSONL record per request, not invented output):

**Criterion 1, trial 1 — actual recorded JSONL** (`scripts/capstone_eval.py::_trial` → `serve.py::ask` → `capstone_logging.py::_measure_one`):

```json
{"duration_ms":2801.31,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size M","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":null,"selected_item_id":"lst_002"},"route":"/ask","run_id":"65bd6859f122","timestamp":"2026-11-15T21:15:13.548363+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

**Criterion 2, trial 1 — actual recorded JSONL** (`scripts/capstone_eval.py::_trial` → `serve.py::ask` → `capstone_logging.py::_measure_one`):

```json
{"duration_ms":1672.63,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size M","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":null,"selected_item_id":"lst_002"},"route":"/ask","run_id":"72092599e16b","timestamp":"2026-11-15T21:15:19.663293+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

**Criterion 3, trial 1 — actual recorded JSONL** (`scripts/capstone_eval.py::_trial` → `serve.py::ask` → `capstone_logging.py::_measure_one`):

```json
{"duration_ms":0.37,"http_status":400,"input":{"json_object":true,"query":null,"wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}","fit_card":null,"retry_notice":null,"selected_item_id":null},"route":"/ask","run_id":"a13826f66114","timestamp":"2026-11-15T21:15:24.648863+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

**Criterion 4, trial 1 — actual recorded JSONL** (`scripts/capstone_eval.py::_trial` → `serve.py::ask` → `capstone_logging.py::_measure_one`):

```json
{"duration_ms":2156.19,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size XL","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Graphic Tee — 2003 Tour Bootleg Style for $24.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":"No matches in size XL; retried once without the size filter.","selected_item_id":"lst_006"},"route":"/ask","run_id":"554c329dc938","timestamp":"2026-11-15T21:15:24.651775+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

**Criterion 5, trial 1 — actual recorded JSONL** (`scripts/capstone_eval.py::_trial` → `serve.py::ask` → `capstone_logging.py::_measure_one`):

```json
{"duration_ms":1011.72,"http_status":200,"input":{"json_object":true,"query":"designer ballgown size XXS under $5","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":"No listings match that request, even after dropping the size filter. Try changing a keyword or raising the price limit.","fit_card":null,"retry_notice":"No matches in size XXS; retried once without the size filter.","selected_item_id":null},"route":"/ask","run_id":"433724421b1e","timestamp":"2026-11-15T21:15:31.226488+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```


See [the complete before log and checks](results/capstone-before-table.md) and [machine-readable trial details](results/capstone-before-trials.json).

**The Improvement**

**Exactly one targeted change:** In `capstone_logging.py::_output_summary`, add `tool_sequence`, extracting only the tool names from the existing agent `tool_calls` list. This follows the measured check-2 logger omission; no agent logic, search ranking, model prompt, MCP behavior, or target criteria were changed. It does not add raw tool arguments or wardrobe data to the new log field.

**Rerun:** Three fresh independent real Flask requests per check, with the **same five AI-assisted provisional criteria**, same targets, Python version, no-key fallback mode and no response caching. All 15 after records are in `results/capstone-after-requests.jsonl`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Structured successful request | 3/3 | PASS | PASS | PASS | MET (3/3) |
| 2. Recover ordered tool path | 3/3 | PASS | PASS | PASS | MET (3/3) |
| 3. Rejected input logged | 3/3 | PASS | PASS | PASS | MET (3/3) |
| 4. Size retry preserved | 3/3 | PASS | PASS | PASS | MET (3/3) |
| 5. No-match logging and zero provider usage | 3/3 | PASS | PASS | PASS | MET (3/3) |

**Did it help?** Yes. The tool-path observation rose from **0/3 MISSED → 3/3 MET**, while the other four stayed MET (3/3 each). Total individual passing trials rose from **12/15 → 15/15**. Both stages used 15 real HTTP requests, not simulations of log lines. The unchanged provisional criteria have identical SHA256 in both test artifacts; the instrumentation source hash differs.

**Actual after-fix log output, check 2 trial 1** (created by `capstone_logging.py::_measure_one`):

```json
{"duration_ms":1731.16,"http_status":200,"input":{"json_object":true,"query":"vintage graphic tee under $30, size M","wardrobe_item_count":null},"model_calls":0,"model_tokens":{"output":0,"prompt":0,"total":0},"output":{"error":null,"fit_card":"Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for a relaxed look.","retry_notice":null,"selected_item_id":"lst_002","tool_sequence":["search_listings","suggest_outfit","create_fit_card"]},"route":"/ask","run_id":"73ded3e28041","timestamp":"2026-11-15T21:17:49.099172+00:00","token_measurement":"Observed provider usage; zero means no billed model calls were recorded."}
```

Evidence: [after table with five real outputs](results/capstone-after-table.md), [full comparison and mechanism-level diagnosis](results/capstone-comparison.md), [before JSON](results/capstone-before-trials.json), and [after JSON](results/capstone-after-trials.json). The after result records **actual local fallback**, not paid Gemini inference.

**What's Still Broken**

All five **provisional** checks now meet their 3/3 targets, but the measured sample remains small and non-keyed. The first target I'd tighten is check 2: verify the new tool sequence on a failed/retried path, including both `search_listings` calls, in 3/3 runs. A model-keyed evaluation would be required to measure actual live Gemini latency and token usage; no claim about those is made here.

**Course requirement still open:** The professor requires the student to write five fresh Unit 9 acceptance criteria independently. The AI-assisted check set in this repository **cannot honestly be presented as independently authored**. The original Unit 3/4 criteria in `criteria.md` do not fill this requirement. The student should write/commit their own five Unit 9 criteria (at least three about this instrumentation layer, one bad path) and rerun the evaluation against those standards before submitting the graded capstone.

**Engineering next step if there were another unit:** Redact sensitive query content from structured logs before exposing the service publicly, then verify the redaction never deletes request correlation. I stopped after the single measured tool-path improvement so the before/after comparison isolates one code change. The system remains Path B local-with-logs, with no public hosted URL.

**How I Used AI**

1. **Scope and observability:** I asked AI for implementation help extending the existing FitFindr server rather than writing a new agent. It reviewed the Flask/MCP run path, drafted a request-logging wrapper, and produced a clean-checkout GitHub Actions smoke test. I kept Shape A (local-with-logs), retained the original agent behavior, and fixed the smoke script import path after an initial failed checkout.
2. **Test execution and diagnosis:** I asked AI to automate three repeated trials for each of five observable behaviors and compare a single targeted fix. AI-assisted provisional checks were committed before the baseline, which revealed `output.tool_sequence` was absent in 0/3 runs. The logger was changed to record only tool names; 15 fresh requests then measured that check at 3/3. These checks are **AI-assisted drafts**, so the professor's independent student-authorship requirement is not claimed as fulfilled.

See [full measured before/after evidence](results/capstone-comparison.md).
