"""Deterministic USD validation and selection. No model performs arithmetic."""

from decimal import Decimal, InvalidOperation
from itertools import product
import re
from urllib.parse import urlsplit

CATEGORIES = ("tops", "bottoms", "shoes")
LIMIT_CENTS = 100_000_000


class BudgetError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def cents(value) -> int:
    """Accept plain dollars with at most two decimals; never round a price."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise BudgetError("invalid_price", "Use a positive USD amount with at most two decimals.")
    raw = str(value).strip()
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", raw):
        raise BudgetError("invalid_price", "Use a positive USD amount with at most two decimals.")
    try:
        amount = Decimal(raw) * 100
    except InvalidOperation as exc:
        raise BudgetError("invalid_price", "Invalid USD amount.") from exc
    if not 0 < amount <= LIMIT_CENTS:
        raise BudgetError("invalid_price", "USD amount must be greater than zero and at most 1,000,000.")
    return int(amount)


def dollars(value: int) -> str:
    return f"{value // 100}.{value % 100:02d}"


def priced_item(item: dict) -> dict:
    if not isinstance(item, dict) or any(
        not isinstance(item.get(k), str) or not item[k].strip()
        for k in ("id", "title", "category", "size", "platform")
    ):
        raise BudgetError("invalid_listing", "Listing is incomplete.")
    if item.get("currency", "USD") != "USD":
        raise BudgetError("unsupported_currency", "Only USD listings can be compared.")
    if item.get("available") is False or item.get("availability") in ("sold", "unavailable", "out_of_stock"):
        raise BudgetError("unavailable_item", "Listing is unavailable.")
    amount = cents(item.get("price"))
    result = {k: item[k] for k in ("id", "title", "category", "size", "platform")}
    result.update(price_cents=amount, price=dollars(amount), currency="USD")
    # Keep only a URL actually supplied by the catalog. No synthesized shop links.
    url = item.get("url")
    if isinstance(url, str):
        try:
            parsed = urlsplit(url)
            if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password:
                result["url"] = url
        except ValueError:
            pass
    return result


def validate_outfit(items: list[dict], budget) -> dict:
    limit = cents(budget)
    checked = [priced_item(item) for item in items]
    if len(checked) != 3 or {i["category"] for i in checked} != set(CATEGORIES):
        raise BudgetError("incomplete_outfit", "A budget outfit needs one top, one bottom, and shoes.")
    if len({i["id"] for i in checked}) != 3:
        raise BudgetError("duplicate_item", "An outfit cannot count the same listing twice.")
    total = sum(i["price_cents"] for i in checked)
    if total > limit:
        raise BudgetError("over_budget", "No complete outfit fits this budget. Try a higher budget or another style.")
    return {
        "items": checked, "currency": "USD", "budget_cents": limit,
        "total_cents": total, "remaining_cents": limit - total,
        "budget": dollars(limit), "total": dollars(total), "remaining": dollars(limit - total),
        "within_budget": True, "source": "bundled_sample_catalog",
        "notice": "Sample catalog preview; prices and availability are not live. Merchandise subtotal only; tax and shipping are excluded. Check listing sizes before buying.",
    }


def select_outfit(candidates: dict[str, list[dict]], budget) -> dict:
    """Search all returned combinations; prefer search rank and shared styles."""
    limit = cents(budget)
    pools = []
    for category in CATEGORIES:
        pool = []
        seen = set()
        for rank, item in enumerate(candidates.get(category, [])):
            try:
                checked = priced_item(item)
            except BudgetError:
                continue
            if checked["category"] == category and checked["id"] not in seen:
                pool.append((rank, item, checked["price_cents"]))
                seen.add(checked["id"])
        if not pool:
            raise BudgetError("no_valid_products", f"No priced, suitable {category} found. Try another style or size; missing prices cannot be estimated.")
        pools.append(pool)
    feasible = []
    for combination in product(*pools):
        if sum(row[2] for row in combination) > limit:
            continue
        items = [row[1] for row in combination]
        if len({i["id"] for i in items}) != 3:
            continue
        tags = [set(i.get("style_tags", [])) for i in items]
        shared = sum(len(tags[a] & tags[b]) for a, b in ((0, 1), (0, 2), (1, 2)))
        score = (sum(row[0] for row in combination) - shared, sum(row[2] for row in combination), tuple(i["id"] for i in items))
        feasible.append((score, items))
    if not feasible:
        raise BudgetError("over_budget", "No complete outfit fits this budget. Try a higher budget or another style.")
    return validate_outfit(min(feasible, key=lambda row: row[0])[1], budget)


def render_outfit(result: dict) -> str:
    return "\n".join(f"{i['category']}: {i['title']} (${i['price']}; size {i['size']})" for i in result["items"])


def render_card(result: dict) -> str:
    return (f"Outfit subtotal: ${result['total']} / ${result['budget']} USD. "
            f"Budget remaining: ${result['remaining']}. {result['notice']}")
