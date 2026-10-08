"""The three FitFindr tools. Each can be called independently."""

import re

import config
from generate import ModelUnavailable, generate
from utils.data_loader import load_listings


_STOP_WORDS = {"a", "an", "and", "for", "i", "in", "looking", "me", "of", "the", "want", "with"}
_ITEM_WORDS = {"tee", "jacket", "skirt", "boot", "jean", "pant", "top", "shirt", "dress", "hoodie", "sneaker", "bag", "belt", "cardigan", "blazer", "vest", "trouser", "sweatshirt", "hat", "flannel", "polo", "short"}


def _words(text: str) -> set[str]:
    words = set(re.findall(r"[a-z0-9]+", text.lower().replace("t-shirt", "tee"))) - _STOP_WORDS
    aliases = {"tees": "tee", "tshirt": "tee", "tshirts": "tee", "jeans": "jean", "pants": "pant", "boots": "boot", "sneakers": "sneaker", "trousers": "trouser", "shorts": "short"}
    return {aliases.get(word, word) for word in words}


def _size_matches(wanted: str, actual: str) -> bool:
    wanted = wanted.strip().upper()
    actual = actual.upper()
    if wanted in {"XXS", "XS", "S", "M", "L", "XL", "XXL"}:
        return bool(re.search(rf"(?<![A-Z]){re.escape(wanted)}(?![A-Z])", actual))
    return bool(re.search(rf"(?<![A-Z0-9.]){re.escape(wanted)}(?![A-Z0-9.])", actual))


def search_listings(
    description: str, size: str | None = None, max_price: float | None = None
) -> list[dict]:
    """Return relevant listing dictionaries satisfying optional size and price limits."""
    query_words = _words(description)
    if not query_words:
        return []
    scored = []
    for listing in load_listings():
        if max_price is not None and float(listing["price"]) > max_price:
            continue
        if size and not _size_matches(size, listing["size"]):
            continue
        title_words = _words(listing["title"])
        tag_words = _words(" ".join(listing["style_tags"]))
        other_words = _words(" ".join([
            listing["description"], listing["category"],
            " ".join(listing["colors"]), listing.get("brand") or "",
        ]))
        item_words = query_words & _ITEM_WORDS
        # A description may mention another garment (for example, a mesh top
        # advertised as layering under a graphic tee). It is not that item.
        if item_words and not item_words & (title_words | tag_words):
            continue
        score = 3 * len(query_words & title_words) + 2 * len(query_words & tag_words) + len(query_words & other_words)
        if score:
            scored.append((score, listing))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"], pair[1]["id"]))
    return [listing for _, listing in scored[:config.SEARCH_RESULT_LIMIT]]


def _fallback_outfit(new_item: dict, wardrobe_items: list[dict]) -> str:
    title = new_item["title"]
    category = new_item["category"]
    wanted_categories = ["bottoms", "shoes"] if category == "tops" else ["tops", "shoes"]
    if category == "shoes":
        wanted_categories = ["tops", "bottoms"]
    choices = []
    for wanted in wanted_categories:
        names = [item["name"] for item in wardrobe_items if item["category"] == wanted]
        if names:
            choices.append(names)
    if choices:
        first = " and ".join(names[0] for names in choices)
        second = " and ".join(names[1] if len(names) > 1 else names[0] for names in choices)
        return (
            f"1) Wear the {title} with {first} for a relaxed look.\n"
            f"2) Style the {title} with {second} for a different look."
        )
    if wardrobe_items:
        owned = wardrobe_items[0]["name"]
        return (
            f"1) Pair the {title} with {owned} and relaxed jeans.\n"
            f"2) Try the {title} with {owned} and clean sneakers."
        )
    return (
        "No wardrobe is saved, so these are general outfit ideas:\n"
        f"1) Pair the {title} with relaxed jeans and clean sneakers.\n"
        f"2) Try the {title} with a neutral skirt and ankle boots."
    )


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """Suggest two outfits, labeling general ideas when no wardrobe is saved."""
    items = wardrobe.get("items", [])
    names = [item["name"] for item in items]
    if names:
        context = "Available owned pieces: " + "; ".join(names)
        rule = "Use only these named owned pieces, spelled exactly as shown."
    else:
        print("No wardrobe items are saved. Using general pairing ideas; add wardrobe items for personal suggestions.")
        context = "The user's wardrobe is empty."
        rule = "These are general ideas because no wardrobe is saved. Never claim the user owns any clothing."
    prompt = (
        f"You are a concise thrift stylist. New item: {new_item['title']} "
        f"({new_item['category']}; colors: {', '.join(new_item['colors'])}). "
        f"{context} {rule} Give exactly two distinct outfit suggestions, one per line "
        "labeled 1) and 2). Name the new item by its exact title and pair it "
        "with at least one other clothing or shoe type in each idea. "
        "If the wardrobe is empty, first say that these are general ideas "
        "because no wardrobe is saved."
    )
    try:
        result = generate(prompt, temperature=0.6).strip()
        ideas = re.findall(r"(?m)^\s*[12][).]\s*(.+)$", result)
        has_owned_pieces = not names or all(
            any(name in idea for name in names) for idea in ideas
        )
        general_label = bool(re.search(r"no wardrobe|wardrobe is empty", result, re.I))
        ownership_claim = bool(re.search(
            r"\b(?:my|our|your)\b|\b(?:you|the user|i|we)\s+(?:already\s+)?(?:have|own)\b",
            result, re.I,
        ))
        if (
            len(ideas) == 2
            and new_item["title"].lower() in result.lower()
            and has_owned_pieces
            and (names or (general_label and not ownership_claim))
        ):
            return result
        return _fallback_outfit(new_item, items)
    except ModelUnavailable as exc:
        print(f"The outfit model couldn't be reached. {exc} Using local styling advice; check GEMINI_API_KEY in .env and your connection, then retry.")
        return _fallback_outfit(new_item, items)


def create_fit_card(outfit: str, new_item: dict) -> str:
    """Write a short caption for the selected listing and outfit."""
    if not outfit or not outfit.strip():
        return "Cannot create a fit card without an outfit suggestion."
    title = new_item["title"]
    price = f"${float(new_item['price']):.2f}"
    platform = new_item["platform"]
    prompt = (
        "Write a casual social-media outfit caption in 2-4 sentences about discovering an available secondhand listing. "
        f"Mention this exact item title once: {title}. Mention its exact price {price} "
        f"and platform {platform} once each. Outfit ideas: {outfit}. "
        "Describe possible pairings with 'could pair' or 'would style'. Only say the listing "
        "was found or spotted. Do not claim the user bought, scored, acquired, picked up, "
        "owns, or has worn any item. Do not call clothing 'my' or 'our'. Do not claim "
        "the user listed or is selling anything. The price and platform belong only to "
        "the new item; do not price the entire outfit. Keep wardrobe pieces grounded in "
        "the supplied ideas and keep empty-wardrobe pairings hypothetical. No hashtags."
    )
    try:
        result = generate(prompt, temperature=0.9).strip()
        seller_claim = re.search(r"\b(?:i|we)\s+(?:just\s+)?(?:listed|sell|selling)\b", result, re.I)
        sentences = [part for part in re.split(r"(?<=[.!?])\s+", result) if part.strip()]
        if (
            not seller_claim
            and 2 <= len(sentences) <= 4
            and title.lower() in result.lower()
            and price in result
            and platform.lower() in result.lower()
        ):
            return result
    except ModelUnavailable as exc:
        print(f"The caption model couldn't be reached. {exc} Using a local caption; check GEMINI_API_KEY in .env and your connection, then retry.")
        pass
    ideas = re.findall(r"(?m)^\s*[12][).]\s*(.+)$", outfit)
    outfit_text = ideas[0] if ideas else outfit.strip().splitlines()[0]
    outfit_text = re.sub(rf"\bthe\s+{re.escape(title)}", "it", outfit_text, count=1, flags=re.I)
    # A numbered idea can itself contain several sentences. Use its first
    # complete thought so the local caption keeps a stable two-sentence shape.
    first_thought = re.split(r"[.!?]+(?=\s|$)", outfit_text, maxsplit=1)[0].strip()
    if not first_thought:
        first_thought = "Try one of the suggested outfit pairings"
    return f"Found {title} for {price} on {platform}. {first_thought.rstrip('.!?')}."
