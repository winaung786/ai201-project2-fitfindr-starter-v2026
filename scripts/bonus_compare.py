"""Audit the bonus baseline and after records without making model calls."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / "results" / name).read_text(encoding="utf-8"))


def main():
    before = read("unit4-bonus-baseline.json")
    after = read("unit4-bonus-after.json")
    before_score = read("unit4-bonus-baseline-scored.json")
    after_score = read("unit4-bonus-after-scored.json")
    fallback_before = read("bonus-fallback-before.json")
    fallback_after = read("bonus-fallback-after.json")

    before_hashes = before["metadata"]["file_sha256"]
    after_hashes = after["metadata"]["file_sha256"]
    changed = sorted(name for name in before_hashes if before_hashes[name] != after_hashes[name])
    assert changed == ["tools.py"], changed
    assert before["metadata"]["model"] == after["metadata"]["model"]
    assert before["metadata"]["temperature"] == after["metadata"]["temperature"]
    assert before["metadata"]["cache_enabled"] is after["metadata"]["cache_enabled"] is False
    assert before["complete"] and after["complete"]
    assert all(len(row["tries"]) == 5 for run in (before, after) for row in run["rows"])
    assert fallback_before["outfit_input"] == fallback_after["outfit_input"]
    assert fallback_before["listing_id"] == fallback_after["listing_id"]
    assert fallback_before["sentence_count"] == 3 and fallback_after["sentence_count"] == 2

    def details(run, scored):
        records = [record for row in run["rows"] for record in row["tries"]]
        return {
            "tries": len(records),
            "model_calls": sum(record["model_calls"] for record in records),
            "all_model_text_used": all(
                all(record["model_text_used"].values()) for record in records
                if record.get("model_text_used")
            ),
            "scores": {str(row["criterion"]): row["passes"] for row in scored["rows"]},
            "tokens": run["metadata"]["tokens"],
        }

    audit = {
        "changed_hashed_source_files": changed,
        "unchanged_criteria_sha256": before_hashes["criteria.md"],
        "unchanged_scenarios_sha256": before_hashes["scenarios.py"],
        "same_model": before["metadata"]["model"],
        "same_temperature": before["metadata"]["temperature"],
        "cache_disabled_in_both": True,
        "baseline": details(before, before_score),
        "after": details(after, after_score),
        "fallback_probe": {
            "same_input": True,
            "before_sentences": fallback_before["sentence_count"],
            "after_sentences": fallback_after["sentence_count"],
            "listing_facts_present_both": all(
                probe[key] for probe in (fallback_before, fallback_after)
                for key in ("exact_title", "price", "platform")
            ),
        },
    }
    path = ROOT / "results" / "bonus-comparison-audit.json"
    path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
