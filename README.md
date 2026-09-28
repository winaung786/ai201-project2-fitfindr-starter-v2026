# FitFindr

Read [RUNNING.md](RUNNING.md) for setup and commands. The Unit 4 sections below are reserved for the next unit.

## What This Does

FitFindr takes a request such as `vintage graphic tee under $30, size M`, searches the supplied secondhand listings, selects the highest-ranked match, suggests an outfit from a wardrobe, and writes a caption. If nothing matches, it stops after search and names filters the user can change. An empty wardrobe gets general pairing advice.

Use Python 3.11–3.13, create a virtual environment, install `requirements.txt`, copy `.env.example` to `.env`, put your own `GEMINI_API_KEY` there, and run `python test.py`. The starter's `generate.py` handles model pacing and caching. Without a key, the text tools use a local fallback, but `test.py` still requires a valid key.

## Tool Inventory

### `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`

- **What it does:** Loads the sample listings, filters by size and inclusive price cap, and ranks item and style word matches.
- **Inputs:** `description` (`str`) is the requested item text; `size` (`str | None`) is an optional clothing or shoe size; `max_price` (`float | None`) is an optional dollar ceiling. `M` matches `M` and `S/M`, but not `XL`.
- **Returns:** At most `config.SEARCH_RESULT_LIMIT` listing dictionaries, best first, each with `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.
- **When it has nothing:** Returns `[]` when no item matches all filters.

### `suggest_outfit(new_item: dict, wardrobe: dict) -> str`

- **What it does:** Calls the model for an outfit using the selected listing and wardrobe pieces.
- **Inputs:** `new_item` (`dict`) is one complete listing; `wardrobe` (`dict`) contains an `items` list of wardrobe item dictionaries.
- **Returns:** A nonempty suggestion string naming the selected item and, when available, owned pieces.
- **When it has nothing:** With an empty wardrobe it gives general pairings. If the model is unavailable it returns a local suggestion using the supplied item and wardrobe.

### `create_fit_card(outfit: str, new_item: dict) -> str`

- **What it does:** Calls the model for a short social caption about the chosen item and outfit.
- **Inputs:** `outfit` (`str`) is the outfit suggestion; `new_item` (`dict`) is the same selected listing.
- **Returns:** A caption string naming the item, exact dollar price, and platform. A model response missing those facts or claiming the user is the seller falls back to a local caption.
- **When it has nothing:** A blank outfit returns `Cannot create a fit card without an outfit suggestion.` If the model is unavailable, the caption uses the real listing facts.

## Planning Loop

**Branch rule:** If `search_listings` returns `[]`, write a helpful message to the session and stop before `suggest_outfit`. Otherwise store the first result, call `suggest_outfit`, then `create_fit_card` with values read from the session.

**Where it lives:** `agent.py::run_agent`.

**How the query is parsed:** Regular expressions extract `under $N` and `size N`; the remaining words are the description.

**What moves through the session:** `parsed` → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. `tool_calls` records the order and the selected listing ID. `trace.check_iterations` bounds the loop.

## Sample Run

These outputs used the local fallback because no model key was present in this workspace. A valid key produces model-written wording, and `python test.py` checks the actual service.

```text
$ python app.py ask 'vintage graphic tee under $30, size M'
Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop
Outfit:   Wear the Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash and Chunky white sneakers for an easy secondhand look.
Fit card: Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Wear it with Baggy straight-leg jeans, dark wash and Chunky white sneakers for an easy secondhand look.
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
Wear the Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash and Chunky white sneakers for an easy secondhand look.

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('Baggy jeans and white sneakers.',load_listings()[1]))"
Found Y2K Baby Tee — Butterfly Print for $18.00 on depop. Baggy jeans and white sneakers.
```

## How I Used AI

**Moment 1:** I used Codex to implement the tool contracts. The initial search included a mesh top for a graphic tee request because its description mentioned layering under a tee. I narrowed the garment check to the title and style tags, and the query now returns only the tee.

**Moment 2:** I used Codex to examine a model caption that claimed the wearer was selling the listing. I tightened the prompt and added a check that falls back to a caption grounded in the actual listing. I then ported the loop to this v2026 starter's `generate.py`, keeping its pacing, cache, and future MCP files.

The three additional criteria in `criteria.md` were AI assisted in the earlier fork. I need to personally review and defend them as the assignment requires.

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



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
