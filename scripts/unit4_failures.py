"""Trigger the three required failures and record actual CLI output, without saving keys."""

import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    key_path = ROOT / ".env"
    original = key_path.read_text(encoding="utf-8")
    from dotenv import dotenv_values
    key = dotenv_values(key_path).get("GEMINI_API_KEY", "")
    if not key:
        raise SystemExit("Set GEMINI_API_KEY in your local .env before running this check.")
    changed_key = key[:-1] + ("X" if key[-1] != "X" else "Y")
    cases = [
        ("happy_trace", "vintage graphic tee under $30, size M", False, False),
        ("empty_search", "designer ballgown size XXS under $5", False, False),
        ("empty_wardrobe", "vintage graphic tee under $30, size M", True, False),
        ("model_unavailable", "90s track jacket under $45, size M", False, True),
    ]
    records = []
    try:
        for name, query, empty, invalid in cases:
            key_path.write_text("GEMINI_API_KEY=" + (changed_key if invalid else key) + "\n", encoding="utf-8")
            env = os.environ.copy()
            env.pop("GEMINI_API_KEY", None)
            env["AI201_CACHE"] = "0"
            args = [sys.executable, "app.py", "ask", query, "--trace"]
            if empty:
                args.append("--empty-wardrobe")
            result = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
            stdout = result.stdout.replace(key, "[REDACTED]").replace(changed_key, "[REDACTED]")
            stderr = result.stderr.replace(key, "[REDACTED]").replace(changed_key, "[REDACTED]")
            record = {"name": name, "query": query, "empty_wardrobe": empty,
                      "one_key_character_changed": invalid, "cache_enabled": False,
                      "returncode": result.returncode, "stdout": stdout, "stderr": stderr}
            records.append(record)
            print(f"{name}\n{stdout}{stderr}", flush=True)
    finally:
        key_path.write_text(original, encoding="utf-8")

    output = {"when_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "records": records,
              "key_restored": key_path.read_text(encoding="utf-8") == original}
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results/unit4-failures.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    by_name = {r["name"]: r for r in records}
    assert all(r["returncode"] == 0 for r in records), "A diagnostic run crashed"
    assert "[3] create_fit_card" in by_name["happy_trace"]["stdout"]
    assert "[2]" not in by_name["empty_search"]["stdout"]
    assert "keyword" in by_name["empty_search"]["stdout"]
    assert "No wardrobe items are saved" in by_name["empty_wardrobe"]["stdout"]
    assert "general" in by_name["empty_wardrobe"]["stdout"].lower()
    assert "model couldn't be reached" in by_name["model_unavailable"]["stdout"]
    assert "GEMINI_API_KEY" in by_name["model_unavailable"]["stdout"]
    assert "served from cache" not in by_name["model_unavailable"]["stdout"]
    print("All required failures produced actionable output; the key was restored.")


if __name__ == "__main__":
    main()
