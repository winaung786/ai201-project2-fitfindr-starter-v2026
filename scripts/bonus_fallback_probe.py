"""Record a deliberate model failure to measure the fallback caption boundary."""

import argparse
import hashlib
import json
import re
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

import sys
sys.path.insert(0, str(ROOT))

import tools
from generate import ModelUnavailable
from utils.data_loader import load_listings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    item = next(listing for listing in load_listings() if listing["id"] == "lst_002")
    outfit = (
        f"1) Pair the {item['title']} with jeans. Add white sneakers for contrast.\n"
        f"2) Style the {item['title']} with a denim skirt and boots."
    )
    with patch.object(tools, "generate", side_effect=ModelUnavailable("deliberate model outage")):
        caption = tools.create_fit_card(outfit, item)
    sentences = [part for part in re.split(r"(?<=[.!?])\s+", caption) if part.strip()]
    result = {
        "label": args.label,
        "method": "Forced ModelUnavailable in create_fit_card; captured the real local fallback result.",
        "source_sha256": hashlib.sha256((ROOT / "tools.py").read_bytes()).hexdigest(),
        "listing_id": item["id"],
        "outfit_input": outfit,
        "caption": caption,
        "sentence_count": len(sentences),
        "exact_title": item["title"] in caption,
        "price": f"${float(item['price']):.2f}" in caption,
        "platform": item["platform"] in caption,
    }
    path = ROOT / "results" / f"bonus-fallback-{args.label}.json"
    if path.exists():
        raise SystemExit(f"Refusing to overwrite {path}")
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{path.relative_to(ROOT)}: {len(sentences)} sentences")
    print(caption)


if __name__ == "__main__":
    main()
