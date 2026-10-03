# FitFindr

Read [RUNNING.md](RUNNING.md) for setup and commands. The Unit 4 sections below are reserved for the next unit.

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

**Branch rule:** If `search_listings` returns `[]`, write a helpful message to the session and stop before `suggest_outfit`. Otherwise store the first result, call `suggest_outfit`, then `create_fit_card` with values read from the session. If the outfit suggestion is blank, stop before the fit card.

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

**Unit 4 so far:** I used Codex to register search over MCP, compare its results with direct search, add per-step traces, and trigger the required failures. The invalid-key run exposed a swallowed error, so Codex added a user message while preserving the existing local fallback. The model, dataset, search behavior, and committed acceptance criteria are unchanged.

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

**On the MCP move:** `search_listings` is registered in `mcp_server.py` with the same typed inputs as Tool Inventory. `agent.py::run_agent` calls it through the starter `mcp_client.call_tool` instead of directly. The other two tools remain direct calls. Three direct-versus-MCP searches returned identical lists, including the empty case, and a fresh full query still completed. Registration, input types, and real outputs are in [MCP verification](results/unit4-mcp-verification.md).



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
