"""Bounded outfit path using the existing MCP search and styling tools."""

import re

from budget import BudgetError, CATEGORIES, cents, dollars, select_outfit
from mcp_client import MCPError
import trace


def is_outfit_request(query, budget=None):
    return budget is not None or isinstance(query, str) and bool(re.search(r"\boutfit\b", query, re.I))


def parse_request(query, budget=None, sizes=None):
    if not isinstance(query, str) or not query.strip() or len(query) > 2000:
        raise BudgetError("invalid_input", "Send a clothing request of 1 to 2000 characters.")
    if sizes is None:
        sizes = {}
    if not isinstance(sizes, dict) or any(
        k not in CATEGORIES or not isinstance(v, str) or not v.strip() or len(v) > 32
        for k, v in sizes.items()
    ):
        raise BudgetError("invalid_input", "Sizes must map tops, bottoms, or shoes to short size strings.")
    matches = list(re.finditer(r"\b(?:under|below|max(?:imum)?|budget(?:\s+of)?)\s*\$?\s*([^\s;!?]+)", query, re.I))
    amounts = [cents(m.group(1).rstrip(",")) for m in matches]
    if budget is not None:
        amounts.append(cents(budget))
    if not amounts:
        raise BudgetError("budget_required", "Add a total USD budget, for example 'casual outfit under $100'.")
    if len(set(amounts)) != 1:
        raise BudgetError("conflicting_budget", "The query and budget field disagree. Send one total budget.")
    description = query
    for match in reversed(matches):
        description = description[:match.start()] + " " + description[match.end():]
    if re.search(r"\bsize\b", description, re.I):
        raise BudgetError("ambiguous_size", "Use category sizes (tops, bottoms, shoes) in the sizes field; one size cannot describe a whole outfit.")
    description = re.sub(r"\b(?:find|build|make|recommend|suggest|give|me|an?|the|outfit|please|for|i|want)\b", " ", description, flags=re.I)
    description = re.sub(r"\bcasual\b", "classic basics streetwear", description, flags=re.I)
    description = re.sub(r"\bminimalist\b", "minimal", description, flags=re.I)
    description = " ".join(description.strip(" ,.!?").split()) or "classic vintage basics streetwear"
    return {"description": description, "budget": dollars(amounts[0]), "sizes": sizes}


def run_budget(session, budget, sizes, call_tool, create_fit_card):
    session["mode"] = "budget_outfit"
    try:
        parsed = parse_request(session["query"], budget, sizes)
        session["parsed"] = parsed
        candidates = {}
        for category in CATEGORIES:
            inputs = {"description": parsed["description"], "size": parsed["sizes"].get(category),
                      "max_price": float(parsed["budget"]), "category": category}
            session["tool_calls"].append({"tool": "search_listings", "inputs": inputs})
            found = call_tool("search_listings", inputs)
            if not isinstance(found, list):
                raise BudgetError("invalid_tool_result", "Search returned an unexpected format. Please retry.")
            candidates[category] = found
            trace.step("search_listings (via MCP)", inputs=str(inputs), returned=found,
                       note="Keep the category and size filters; never relax the total budget.")
        session["search_results"] = [i for rows in candidates.values() for i in rows]
        result = select_outfit(candidates, parsed["budget"])
        session["budget_result"] = result
        # Use catalog dictionaries for the existing tool inputs, not invented pieces.
        ids = {i["id"] for i in result["items"]}
        session["selected_items"] = [i for i in session["search_results"] if isinstance(i, dict) and i.get("id") in ids]
        session["selected_item"] = session["selected_items"][0]
        inputs = {"new_item": session["selected_item"], "wardrobe": session["wardrobe"], "budget_result": result}
        session["tool_calls"].append({"tool": "suggest_outfit", "item_ids": sorted(ids)})
        outfit = call_tool("suggest_outfit", inputs)
        if not isinstance(outfit, str) or not outfit.strip():
            raise BudgetError("invalid_tool_result", "Styling returned no outfit. Please retry.")
        session["outfit_suggestion"] = outfit
        session["tool_calls"].append({"tool": "create_fit_card", "item_ids": sorted(ids)})
        session["fit_card"] = create_fit_card(outfit, session["selected_item"], budget_result=result)
        session["notice"] = result["notice"]
        trace.step("validate_budget", inputs=str({"budget": parsed["budget"]}), returned=session["fit_card"], note="Integer-cent validation passed before presentation.")
    except BudgetError as exc:
        session["error"] = str(exc)
        session["error_type"] = exc.code
    except (MCPError, OSError, ValueError, KeyError, TypeError):
        session["error"] = "The outfit tools could not complete this request. Check the local catalog and MCP server, then retry."
        session["error_type"] = "tool_failure"
    if session["error"]:
        # A partial pipeline is never a successful shopping recommendation.
        session.update(budget_result=None, selected_items=[], selected_item=None,
                       outfit_suggestion=None, fit_card=None)
    return session
