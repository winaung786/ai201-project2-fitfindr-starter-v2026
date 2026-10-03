"""Score saved Unit 4 runs without model calls; ownership judgments require reviewed text."""

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).parent
TARGETS = {1: 4, 2: 5, 3: 5, 4: 4, 5: 4}
NAMES = {1: "Full three-tool run returns a fit card", 2: "Empty search stops before styling",
         3: "Actual item inputs match session state", 4: "Fit card accuracy", 5: "Empty wardrobe behavior"}


def score(data, reviews):
    rows = []
    assert data["complete"] and data["metadata"]["tries_per_criterion"] == 5
    assert data["metadata"]["cache_enabled"] is False
    assert {r["scenario"]["criterion"] for r in data["rows"]} == set(TARGETS)
    for row in data["rows"]:
        number = row["scenario"]["criterion"]
        assert len(row["tries"]) == 5
        scores = []
        for i, record in enumerate(row["tries"], 1):
            session = record.get("session") or {}
            item = session.get("selected_item") or {}
            card, outfit = session.get("fit_card") or "", session.get("outfit_suggestion") or ""
            calls = [x["tool"] for x in session.get("tool_calls", [])]
            checks = {"no_crash": record.get("crashed") is None}
            if number == 1:
                checks.update(tool_order=calls == ["search_listings", "suggest_outfit", "create_fit_card"], fit_card_nonempty=bool(card.strip()))
            elif number == 2:
                checks.update(search_only=calls == ["search_listings"], selected_item_none=session.get("selected_item") is None,
                              outfit_none=session.get("outfit_suggestion") is None, card_none=session.get("fit_card") is None,
                              useful_message=bool(re.search(r"keyword|size|price", session.get("error") or "", re.I)))
            elif number == 3:
                receipts = record.get("tool_inputs", [])
                checks.update(recording_replacements_used=record.get("state_probe") is True,
                              both_calls_received=len(receipts) == 2 and [r["tool"] for r in receipts] == ["suggest_outfit", "create_fit_card"],
                              ids_match=bool(item) and len(receipts) == 2 and all(r["new_item"].get("id") == item.get("id") for r in receipts),
                              selected_matches_first=bool(item) and bool(session.get("search_results")) and item == session["search_results"][0])
            elif number == 4:
                review = reviews[f"4-{i}"]
                assert review["text_sha256"] == hashlib.sha256(card.encode()).hexdigest(), "Ownership review is for different text"
                sentences = [x for x in re.split(r"(?<=[.!?])\s+", card) if x.strip()]
                checks.update(card_nonempty=bool(card.strip()), one_to_four_sentences=1 <= len(sentences) <= 4,
                              exact_title=bool(item) and item["title"] in card,
                              formatted_price=bool(item) and f"${float(item['price']):.2f}" in card,
                              platform=bool(item) and item["platform"].lower() in card.lower(),
                              ownership_review=review["passes"])
            elif number == 5:
                review = reviews[f"5-{i}"]
                assert review["text_sha256"] == hashlib.sha256(outfit.encode()).hexdigest(), "Ownership review is for different text"
                checks.update(no_session_error=session.get("error") is None, selected_item_present=bool(item),
                              outfit_nonempty=bool(outfit.strip()), exact_title=bool(item) and item["title"] in outfit,
                              other_clothing_pair=bool(item) and bool(re.search(r"\b(?:jeans|skirt|sneakers|boots|trousers|pants|shorts|sandals|loafers|shoes|hoodie|jacket|tank|sweatshirt|dress|shirt|heels|flats|cardigan|blazer|tee)\b", re.sub(re.escape(item["title"]), "", outfit, flags=re.I), re.I)),
                              ownership_review=review["passes"])
            scores.append({"try": i, "passed": all(checks.values()), "checks": checks,
                           "ownership_note": reviews.get(f"{number}-{i}", {}).get("note")})
        count = sum(s["passed"] for s in scores)
        rows.append({"criterion": number, "target": TARGETS[number], "passes": count,
                     "verdict": "MET" if count >= TARGETS[number] else "MISSED", "tries": scores})
    return rows


def table(rows):
    lines = ["| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |",
             "|---|---|---|---|---|---|---|---|"]
    for row in rows:
        cells = " | ".join("PASS" if t["passed"] else "FAIL" for t in row["tries"])
        lines.append(f"| {row['criterion']}. {NAMES[row['criterion']]} | {row['target']} of 5 | {cells} | {row['verdict']} ({row['passes']}/5) |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    source = ROOT / "results" / f"unit4-{args.label}.json"
    before_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    data = json.loads(source.read_text())
    reviews = json.loads((ROOT / "results" / f"unit4-{args.label}-ownership-review.json").read_text())["reviews"]
    rows = score(data, reviews)
    output = {"source": source.name, "source_sha256": before_hash,
              "method": "Deterministic checks plus caption/outfit ownership reviews against the saved wording and wardrobe; no model calls.", "rows": rows}
    (ROOT / "results" / f"unit4-{args.label}-scored.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "results" / f"unit4-{args.label}-table.md").write_text(table(rows) + "\n")
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before_hash
    print(table(rows))


if __name__ == "__main__":
    main()
