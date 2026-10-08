"""Save one full trace proving the one-time size-filter retry."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config
from run_eval import run_once


def main():
    config.CACHE_ENABLED = False
    scenario = {
        "name": "size-only miss retries without size",
        "query": "vintage graphic tee under $30, size XL",
        "wardrobe": "example",
        "criterion": None,
    }
    record = run_once(scenario)
    session = record["session"] or {}
    calls = session.get("tool_calls", [])
    assert record["crashed"] is None
    assert [call["tool"] for call in calls] == [
        "search_listings", "search_listings", "suggest_outfit", "create_fit_card"
    ]
    assert calls[0]["inputs"]["size"] == "XL"
    assert calls[1]["inputs"]["size"] is None
    assert calls[1]["dropped_constraint"] == "size XL"
    assert "size filter" in session["notice"]
    assert all(record["model_text_used"].values())
    path = ROOT / "results" / "bonus-retry-run.json"
    if path.exists():
        raise SystemExit(f"Refusing to overwrite {path}")
    path.write_text(json.dumps({"scenario": scenario, "record": record}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)}")
    print(session["notice"])
    print(record["trace"])


if __name__ == "__main__":
    main()
