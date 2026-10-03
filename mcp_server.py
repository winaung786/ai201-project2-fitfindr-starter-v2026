"""Expose FitFindr search over MCP stdio; the search implementation stays in tools.py."""

from mcp.server.fastmcp import FastMCP
from tools import search_listings as _search_listings_impl

mcp = FastMCP("fitfindr", log_level="WARNING")


@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """Search secondhand listings by description (string), optional size (string), and optional inclusive max_price (number in US dollars); return ranked listing dictionaries, or [] when nothing matches."""
    return _search_listings_impl(description, size, max_price)


if __name__ == "__main__":
    mcp.run(transport="stdio")
