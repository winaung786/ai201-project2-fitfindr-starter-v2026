# FitFindr acceptance criteria

These targets were set before implementation testing. A try means one fresh call to `run_agent` with the named input; record the returned session and tool call log each time. For model behavior, disable any response cache during the five tries.

1. Given `vintage graphic tee under $30, size M` with the example wardrobe, the agent completes `search_listings`, `suggest_outfit`, and `create_fit_card` in that order and returns a nonempty fit card in at least **4 of 5** tries.
   **Why this target:** The three-step flow is the main experience. One transient model failure is tolerable if the remaining tries work, but a lower target would hide a recurring failure.

2. Given `designer ballgown size XXS under $5` with the example wardrobe, the agent stops after `search_listings`, leaves `selected_item`, `outfit_suggestion`, and `fit_card` as `None`, and says to change a keyword, size, or price in **5 of 5** tries.
   **Why this target:** An empty result is deterministic for the supplied data, so every run should stop and offer a useful next action.

3. Run the query in criterion 1 with the example wardrobe five times. For this state check, replace `agent.suggest_outfit` and `agent.create_fit_card` with recording functions that capture the `new_item["id"]` each actually receives and return nonempty text. In **5 of 5** runs, both captured IDs must equal `session["selected_item"]["id"]`, and `session["selected_item"]` must equal `session["search_results"][0]`. A missing call or item counts as a failure.
   **Why this target:** Passing the same item between tools is deterministic, so every transfer should work. Recording the actual arguments catches a mismatch that an agent-written call log alone might miss, while the recording functions isolate state from model failures.

4. Across **5** runs of the query in criterion 1 with the example wardrobe and the response cache off, at least **4** fit cards must be 1–4 sentences, contain the selected item's exact `title`, its price formatted to two decimal places (for example, `$18.00`), and its `platform` name. A card must not claim the user owns a specific clothing item unless that item's name appears in `wardrobe["items"]`. A missing fit card fails that try.
   **Why this target:** Exact listing facts and ownership claims can be checked even when the caption's wording varies. One miss allows occasional model variation, but more would make the card unreliable.

5. Across **5** runs of `vintage graphic tee under $30, size M` with `get_empty_wardrobe()` and the response cache off, at least **4** sessions must have no error and a nonempty `outfit_suggestion` that names the selected item's exact `title` and suggests at least one other clothing or shoe type (for example, jeans or sneakers). The suggestion must not say the user owns a specific piece. A missing item or suggestion fails that try.
   **Why this target:** A person with no saved wardrobe still needs a concrete pairing idea. One imperfect model response in five is tolerable; repeated failures would make the empty-wardrobe route unusable.
