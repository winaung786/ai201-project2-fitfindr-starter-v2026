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

