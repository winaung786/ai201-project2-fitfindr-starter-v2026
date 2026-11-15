#!/usr/bin/env python3
"""Unit 9 three-trial pre/post *provisional* evaluation.

This exercises real Flask handlers, real MCP tool subprocesses, and the local
model fallback. It does not claim student-authored criteria or keyed model
performance. Never revise the checks between the before and after rounds.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["AI201_CACHE"] = "0"
os.environ["GEMINI_API_KEY"] = ""  # intentionally offline/no provider spend
os.environ.pop("FITFINDR_MCP_MODEL_LOG", None)

from serve import app  # noqa: E402

CASES = [
    (1, "Structured successful request", {"query": "vintage graphic tee under $30, size M"}),
    (2, "Recover ordered tool path", {"query": "vintage graphic tee under $30, size M"}),
    (3, "Rejected input logged", {}),
    (4, "Size retry preserved", {"query": "vintage graphic tee under $30, size XL"}),
    (5, "No-match logging and zero provider usage", {"query": "designer ballgown size XXS under $5"}),
]


def _trial(client, number, payload, log_path):
    previous_count = len(log_path.read_text(encoding="utf-8").splitlines()) if log_path.exists() else 0
    response = client.post("/ask", json=payload)
    data = response.get_json()
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    record = rows[-1]
    got_one_log = len(rows) == previous_count + 1
    correlation = bool(response.headers.get("X-FitFindr-Run-ID")) and (
        response.headers["X-FitFindr-Run-ID"] == record.get("run_id")
    )
    output = record.get("output") or {}
    calls = (data or {}).get("tool_calls", [])
    sequence = [item.get("tool") for item in calls]

    if number == 1:
        checks = {
            "http_200": response.status_code == 200,
            "one_log_record": got_one_log,
            "matching_run_id": correlation,
            "listing_and_fit_card": bool(data.get("selected_item") and data.get("fit_card")),
            "timestamp": bool(record.get("timestamp")),
            "input_and_output": bool(record.get("input", {}).get("query")) and bool(output),
            "http_status_logged": record.get("http_status") == 200,
            "duration_ms": isinstance(record.get("duration_ms"), (int, float)) and record["duration_ms"] >= 0,
            "usage_counters": (isinstance(record.get("model_calls"), int)
                               and record["model_calls"] >= 0
                               and all(isinstance(record.get("model_tokens", {}).get(k), int)
                                       and record["model_tokens"][k] >= 0
                                       for k in ("prompt", "output", "total"))),
        }
    elif number == 2:
        target_sequence = ["search_listings", "suggest_outfit", "create_fit_card"]
        checks = {
            "http_200": response.status_code == 200,
            "one_log_record": got_one_log,
            "request_run_id": correlation,
            "actual_tool_calls": sequence == target_sequence,
            "logged_tool_sequence": output.get("tool_sequence") == target_sequence,
            "logged_matches_actual": output.get("tool_sequence") == sequence,
        }
    elif number == 3:
        checks = {
            "http_400": response.status_code == 400,
            "one_log_record": got_one_log,
            "matching_run_id": correlation,
            "http_400_logged": record.get("http_status") == 400,
            "error_logged": bool(output.get("error")),
            "duration_ms": isinstance(record.get("duration_ms"), (int, float))
                           and record["duration_ms"] >= 0,
        }
    elif number == 4:
        checks = {
            "http_200": response.status_code == 200,
            "one_log_record": got_one_log,
            "exactly_one_relaxed_retry": (len(calls) == 4 and
                                          sequence == ["search_listings", "search_listings",
                                                       "suggest_outfit", "create_fit_card"] and
                                          calls[0].get("inputs", {}).get("size") == "XL" and
                                          calls[1].get("inputs", {}).get("size") is None and
                                          calls[1].get("retry") is True),
            "logged_retry_notice": "without the size filter" in str(output.get("retry_notice", "")),
            "listing_returned": bool(data.get("selected_item")),
        }
    elif number == 5:
        checks = {
            "http_200": response.status_code == 200,
            "one_log_record": got_one_log,
            "agent_error": bool(data.get("error")),
            "no_listing_or_card": data.get("selected_item") is None and data.get("fit_card") is None,
            "logged_app_error": bool(output.get("error")),
            "no_logged_card": output.get("fit_card") is None,
            "zero_provider_calls": record.get("model_calls") == 0,
            "zero_provider_tokens": record.get("model_tokens", {}).get("total") == 0,
        }
    else:
        raise ValueError(number)

    evidence = {
        "http_status": response.status_code,
        "response_run_id": response.headers.get("X-FitFindr-Run-ID"),
        "response_excerpt": {
            "error": data.get("error"),
            "selected_item_id": (data.get("selected_item") or {}).get("id"),
            "fit_card": (data.get("fit_card") or "")[:180] or None,
            "notice": data.get("notice"),
            "tool_calls": calls,
        },
        "structured_log": record,
    }
    return {"passed": all(checks.values()), "checks": checks, "evidence": evidence}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("before", "after"), required=True)
    args = parser.parse_args()
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    log = out / f"capstone-{args.phase}-requests.jsonl"
    os.environ["FITFINDR_LOG_PATH"] = str(log)
    log.unlink(missing_ok=True)

    rows = []
    with app.test_client() as client:
        for number, label, payload in CASES:
            trials = [_trial(client, number, payload, log) for _ in range(3)]
            count = sum(trial["passed"] for trial in trials)
            rows.append({
                "criterion": number, "label": label, "target": "3/3",
                "met": count == 3, "pass_count": count,
                "verdict": "MET" if count == 3 else "MISSED",
                "trials": trials,
            })

    record_count = len(log.read_text(encoding="utf-8").splitlines())
    assert record_count == 15, f"Expected 15 independent requests, received {record_count}"
    criteria = ROOT / "capstone-provisional-criteria.md"
    result = {
        "phase": args.phase,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "15 actual Flask POST requests with real MCP subprocess and local model fallbacks",
        "no_live_model": True,
        "cache_disabled": True,
        "criteria_ai_assisted_not_student_authored": True,
        "criteria_sha256": hashlib.sha256(criteria.read_bytes()).hexdigest(),
        "instrumentation_sha256": hashlib.sha256((ROOT / "capstone_logging.py").read_bytes()).hexdigest(),
        "logged_requests": record_count,
        "rows": rows,
    }
    (out / f"capstone-{args.phase}-trials.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    table = [
        "| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        values = ["PASS" if t["passed"] else "FAIL" for t in row["trials"]]
        table.append(f"| {row['criterion']}. {row['label']} | 3/3 | "
                     + " | ".join(values) + f" | {row['verdict']} ({row['pass_count']}/3) |")
    lines = [
        f"# Unit 9 provisional evaluation — {args.phase}",
        "",
        "AI-assisted rehearsal criteria, **not** independently written by the student.",
        "Actual Flask + MCP subprocess requests with no Gemini key, response cache off.",
        f"Criteria SHA256: `{result['criteria_sha256']}`.",
        "",
        *table, "",
        "## Actual output from one trial per criterion",
        "",
        "Source: `scripts/capstone_eval.py::_trial` invokes `serve.py::ask`;",
        "the structured record is created by `capstone_logging.py::_measure_one`.",
        "",
    ]
    for row in rows:
        trial = row["trials"][0]
        lines += [
            f"### Criterion {row['criterion']} — {row['label']}",
            "",
            "Checks: " + json.dumps(trial["checks"], ensure_ascii=False),
            "",
            "Actual JSONL output:", "~~~json",
            json.dumps(trial["evidence"]["structured_log"], ensure_ascii=False, sort_keys=True),
            "~~~", "",
            "Actual HTTP response excerpt:", "~~~json",
            json.dumps(trial["evidence"]["response_excerpt"], ensure_ascii=False, sort_keys=True),
            "~~~", "",
        ]
    (out / f"capstone-{args.phase}-table.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("\n".join(table))
    print(f"Saved {record_count} actual HTTP records and 15 scored trials ({args.phase}).")
    # A MISSED target is valid diagnostic evidence, not a CI failure.


if __name__ == "__main__":
    main()
