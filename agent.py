"""FitFindr's stateful planning loop."""

import re

import trace
from mcp_client import MCPError, call_tool
from tools import create_fit_card


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """Keep a named call seam for the criterion 3 recording probe."""
    return call_tool("suggest_outfit", {"new_item": new_item, "wardrobe": wardrobe})


def new_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "tool_calls": [],
        "notice": None,
        "error": None,
    }


def _parse_query(query: str) -> dict:
    price_match = re.search(r"\b(?:under|below|max(?:imum)?)\s*\$?\s*(\d+(?:\.\d+)?)\b", query, re.I)
    size_match = re.search(r"\bsize\s+([A-Za-z0-9./-]+)", query, re.I)
    description = query
    for match in (price_match, size_match):
        if match:
            description = description.replace(match.group(0), " ")
    description = re.sub(r"\s+", " ", description.strip(" ,.!? ")).strip(" ,.!? ")
    return {
        "description": description,
        "size": size_match.group(1).rstrip(".,!?;:") if size_match else None,
        "max_price": float(price_match.group(1)) if price_match else None,
    }


def run_agent(query: str, wardrobe: dict) -> dict:
    """Choose each next tool from the current session and stop after three stages."""
    session = new_session(query, wardrobe)
    if not query or not query.strip():
        session["error"] = "Describe an item to search for, such as 'vintage graphic tee under $30'."
        return session
    session["parsed"] = _parse_query(query)
    stage = "search"
    iteration = 0
    while stage:
        iteration += 1
        trace.check_iterations(iteration)
        if stage == "search":
            session["tool_calls"].append({"tool": "search_listings", "inputs": session["parsed"].copy()})
            try:
                session["search_results"] = call_tool("search_listings", session["parsed"])
            except (MCPError, OSError, ValueError, KeyError, TypeError) as exc:
                session["error"] = (
                    f"Search failed over MCP ({type(exc).__name__}). "
                    "Check mcp_server.py and data/listings.json, then retry."
                )
                trace.step("search_listings (via MCP)", inputs=str(session["parsed"]),
                           returned=session["error"], note="Search failed; stop before styling.")
                break
            results = session["search_results"]
            if not isinstance(results, list) or any(
                not isinstance(item, dict) or not all(
                    key in item for key in ("id", "title", "category", "colors", "price", "platform")
                ) for item in results
            ):
                session["error"] = (
                    "Search returned an unexpected format. Check that the MCP tool "
                    "returns a list of complete listing dictionaries, then retry."
                )
                trace.step("search_listings (via MCP)", inputs=str(session["parsed"]),
                           returned=str(results), note=session["error"])
                break
            retry_size = session["parsed"].get("size") if not results else None
            trace.step("search_listings (via MCP)", inputs=str(session["parsed"]),
                       returned=results, note=(
                           f"No matches; retry once without the size filter ({retry_size})."
                           if retry_size else
                           "No matches; stop before suggest_outfit. Change keyword, size, or price."
                           if not results else "Matches found; store the first result in the session and style it."
                       ))
            if retry_size:
                retry_inputs = {**session["parsed"], "size": None}
                session["notice"] = f"No matches in size {retry_size}; retried once without the size filter."
                session["tool_calls"].append({
                    "tool": "search_listings", "inputs": retry_inputs.copy(),
                    "retry": True, "dropped_constraint": f"size {retry_size}",
                })
                try:
                    results = call_tool("search_listings", retry_inputs)
                except (MCPError, OSError, ValueError, KeyError, TypeError) as exc:
                    session["error"] = (
                        f"Retry without size failed over MCP ({type(exc).__name__}). "
                        "Check mcp_server.py and data/listings.json, then retry."
                    )
                    trace.step("search_listings (via MCP) retry without size",
                               inputs=str(retry_inputs), returned=session["error"],
                               note="The one permitted retry failed; stop before styling.")
                    break
                if not isinstance(results, list) or any(
                    not isinstance(item, dict) or not all(
                        key in item for key in ("id", "title", "category", "colors", "price", "platform")
                    ) for item in results
                ):
                    session["error"] = "Retry returned an unexpected listing format; check the MCP tool and retry."
                    trace.step("search_listings (via MCP) retry without size",
                               inputs=str(retry_inputs), returned=str(results), note=session["error"])
                    break
                session["search_results"] = results
                trace.step("search_listings (via MCP) retry without size",
                           inputs=str(retry_inputs), returned=results,
                           note=("Size filter dropped; matches found, so continue to styling."
                                 if results else "Size filter dropped; still no matches, so stop before styling."))
            if not session["search_results"]:
                session["error"] = (
                    "No listings match that request, even after dropping the size filter. "
                    "Try changing a keyword or raising the price limit."
                    if retry_size else
                    "No listings match that request. Try changing a keyword, "
                    "choosing another size, or raising the price limit."
                )
                break
            session["selected_item"] = session["search_results"][0]
            stage = "outfit"
        elif stage == "outfit":
            item = session["selected_item"]
            session["tool_calls"].append({"tool": "suggest_outfit", "new_item_id": item["id"]})
            try:
                session["outfit_suggestion"] = suggest_outfit(item, session["wardrobe"])
            except (MCPError, OSError, ValueError, KeyError, TypeError) as exc:
                session["error"] = (
                    f"Styling failed over MCP ({type(exc).__name__}). "
                    "Check the styling tool and model connection, then retry."
                )
                trace.step("suggest_outfit (via MCP)", inputs=str({"new_item_id": item["id"]}),
                           returned=session["error"], note="Styling failed; stop before the caption.")
                break
            trace.step("suggest_outfit (via MCP)", inputs=str({"new_item_id": item["id"],
                       "wardrobe_items": len(session["wardrobe"].get("items", []))}),
                       returned=session["outfit_suggestion"],
                       note="Read the selected item from the session; a nonempty outfit permits the caption step.")
            if not session["outfit_suggestion"] or not session["outfit_suggestion"].strip():
                session["error"] = "No outfit suggestion was produced. Try another listing or check the styling tool, then retry."
                break
            stage = "card"
        elif stage == "card":
            item = session["selected_item"]
            session["tool_calls"].append({"tool": "create_fit_card", "new_item_id": item["id"]})
            session["fit_card"] = create_fit_card(session["outfit_suggestion"], item)
            trace.step("create_fit_card", inputs=str({"new_item_id": item["id"],
                       "outfit": session["outfit_suggestion"]}), returned=session["fit_card"],
                       note="Read the outfit and item from the session; the caption completes this run.")
            stage = None
        else:
            session["error"] = "The agent reached an unknown step."
            break
    return session
