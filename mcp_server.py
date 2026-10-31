"""Expose FitFindr search and styling over MCP stdio."""

import contextlib
import json
import os
import sys

from mcp.server.fastmcp import FastMCP
import generate as model_usage
import tools
from tools import search_listings as _search_listings_impl
from tools import suggest_outfit as _suggest_outfit_impl

mcp = FastMCP("fitfindr", log_level="WARNING")


@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
    category: str | None = None,
) -> list[dict]:
    """Search the bundled sample catalog by description, optional size, inclusive max_price in USD, and optional category. Returns ranked listing dictionaries or []; does not verify live availability or supply absent product URLs."""
    return _search_listings_impl(description, size, max_price, category)


@mcp.tool()
def suggest_outfit(new_item: dict, wardrobe: dict, budget_result: dict | None = None) -> str:
    """Suggest two wardrobe pairings, or render one validated catalog outfit when budget_result is provided (no model arithmetic)."""
    # A stdio MCP server reserves stdout for protocol messages. The styling
    # tool's helpful diagnostic prints therefore go to stderr.
    log_path = os.environ.get("FITFINDR_MCP_MODEL_LOG")
    original_generate = tools.generate

    def recorded_generate(prompt, *args, **kwargs):
        before_calls = model_usage.call_count()
        before_tokens = model_usage.token_counts()
        entry = {"prompt": prompt, "temperature": kwargs.get("temperature")}
        try:
            entry["raw_text"] = original_generate(prompt, *args, **kwargs)
            return entry["raw_text"]
        except Exception as exc:
            entry["error_type"] = type(exc).__name__
            raise
        finally:
            entry["model_calls"] = model_usage.call_count() - before_calls
            after_tokens = model_usage.token_counts()
            entry["tokens"] = {
                key: after_tokens[key] - value for key, value in before_tokens.items()
            }
            with open(log_path, "a", encoding="utf-8") as log:
                log.write(json.dumps(entry, ensure_ascii=False) + "\n")

    if log_path:
        tools.generate = recorded_generate
    try:
        with contextlib.redirect_stdout(sys.stderr):
            return _suggest_outfit_impl(new_item, wardrobe, budget_result)
    finally:
        tools.generate = original_generate


if __name__ == "__main__":
    mcp.run(transport="stdio")
