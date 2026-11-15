#!/usr/bin/env python3
"""Execute the five user-supplied Unit 9 criteria, not the AI provisional checks.

Real Flask /ask endpoint, MCP subprocess, three trials per criterion. C3 has
three invalid requests per trial. This records genuine data and MISSED criteria
without mutating a target. Fallback/no-key tests do not verify Gemini output.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["AI201_CACHE"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("FITFINDR_MCP_MODEL_LOG", None)

from serve import app  # noqa: E402
import generate  # noqa: E402
from utils.data_loader import get_example_wardrobe  # noqa: E402

Q_HAPPY = "vintage graphic tee under $30, size M"
Q_EMPTY = "designer ballgown size XXS under $5"
Q_RETRY = "vintage graphic tee under $30, size XL"
EXPECTED_TITLE_AS_WRITTEN = "Y2K Baby Tee – Butterfly Print"  # en dash: intentional
VALIDATION_MSG = """Send JSON with a 'query' field, e.g. {"query": "vintage graphic tee under $30"}"""
FAKE_SECRET = "test_secret_key_DO_NOT_LOG_999"

TITLES = [
    "Happy-path HTTP telemetry and correlation header",
    "Bounded size-retry and empty-search failure-path telemetry",
    "Malformed and non-string JSON payload rejection",
    "Secret/wardrobe privacy redaction and temporary cleanup",
    "Explicit empty-wardrobe HTTP styling and zero-item telemetry",
]


def lines(path: Path) -> list:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def call(client, log: Path, payload) -> dict:
    prior = len(lines(log))
    response = client.post("/ask", json=payload)
    current = lines(log)
    data = response.get_json(silent=True)
    return {
        "status": response.status_code,
        "header": response.headers.get("X-FitFindr-Run-ID"),
        "body": data,
        "record": current[-1] if current else None,
        "exactly_one_log": len(current) == prior + 1,
    }


def base_checks(x) -> dict:
    r = x["record"] or {}
    return {
        "one_log": x["exactly_one_log"],
        "header_hex12": bool(re.fullmatch(r"[0-9a-f]{12}", x["header"] or "")),
        "correlation": bool(x["header"]) and x["header"] == r.get("run_id"),
    }


def check_1(client, log: Path) -> dict:
    x = call(client, log, {"query": Q_HAPPY})
    body, record = x["body"] or {}, x["record"] or {}
    output = record.get("output") or {}
    card = output.get("fit_card") or ""
    checks = {
        **base_checks(x),
        "http_200": x["status"] == 200,
        "log_200": record.get("http_status") == 200,
        "elapsed_positive": isinstance(record.get("duration_ms"), (float, int)) and record["duration_ms"] > 0,
        "listing_id": output.get("selected_item_id") == "lst_002",
        "error_null": output.get("error") is None,
        "exact_user_title": EXPECTED_TITLE_AS_WRITTEN in card,
        "exact_price": "$18.00" in card,
        "platform": "depop" in card,
    }
    return result(checks, [x])


def check_2(client, log: Path) -> dict:
    x = call(client, log, {"query": Q_EMPTY})
    body, record = x["body"] or {}, x["record"] or {}
    output = record.get("output") or {}
    calls = body.get("tool_calls") or []
    search_calls = [v for v in calls if v.get("tool") == "search_listings"]
    notice = "No matches in size XXS; retried once without the size filter."
    checks = {
        "one_log": x["exactly_one_log"],
        "http_200": x["status"] == 200,
        "no_content": all(body.get(k) is None for k in ("selected_item", "outfit_suggestion", "fit_card")),
        "only_two_search_calls": len(calls) == len(search_calls) == 2,
        "retry_flag": len(search_calls) == 2 and search_calls[1].get("retry") is True,
        "dropped_constraint": len(search_calls) == 2 and search_calls[1].get("dropped_constraint") == "size XXS",
        "log_selected_null": output.get("selected_item_id") is None,
        "log_card_null": output.get("fit_card") is None,
        "exact_retry_notice": output.get("retry_notice") == notice,
        "error_prefix": str(output.get("error") or "").startswith("No listings match that request, even after dropping the size filter"),
    }
    return result(checks, [x])


def check_3(client, log: Path) -> dict:
    requests = [{}, ["vintage graphic tee under $30"], {"query": 123}]
    actual = [call(client, log, payload) for payload in requests]
    checks = {}
    for n, x in enumerate(actual, start=1):
        rec = x["record"] or {}
        err = ((rec.get("output") or {}).get("error")) or ""
        response_err = ((x["body"] or {}).get("error")) or ""
        checks.update({
            f"request_{n}_one_log": x["exactly_one_log"],
            f"request_{n}_http_400": x["status"] == 400,
            f"request_{n}_error_text": response_err == VALIDATION_MSG,
            f"request_{n}_log_400": rec.get("http_status") == 400,
            f"request_{n}_no_model_calls": rec.get("model_calls") == 0,
            f"request_{n}_under_50ms": isinstance(rec.get("duration_ms"), (int, float)) and rec["duration_ms"] < 50,
            f"request_{n}_logged_validation_error": VALIDATION_MSG in err,
        })
    return result(checks, actual)


def check_4(client, log: Path) -> dict:
    old = os.environ.get("GEMINI_API_KEY")
    prior_client = getattr(generate, "_client", None)
    root = Path(tempfile.gettempdir())
    before = sorted(p.name for p in root.glob("fitfindr-capstone-*"))
    os.environ["GEMINI_API_KEY"] = FAKE_SECRET
    generate._client = None
    try:
        x = call(client, log, {"query": Q_RETRY})
    finally:
        generate._client = prior_client
        if old is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = old
    after = sorted(p.name for p in root.glob("fitfindr-capstone-*"))
    rec = x["record"] or {}
    out = rec.get("output") or {}
    serialized = json.dumps(rec, ensure_ascii=False)
    wardrobe = get_example_wardrobe()
    names = [it.get("name") for it in wardrobe.get("items", []) if it.get("name")]
    leaked = [name for name in names if name in serialized]
    checks = {
        "one_log": x["exactly_one_log"],
        "no_secret": FAKE_SECRET not in serialized,
        "no_raw_wardrobe_names": not leaked and "Baggy straight-leg jeans, dark wash" not in serialized,
        "selected_id": out.get("selected_item_id") == "lst_006",
        "retry_notice": out.get("retry_notice") == "No matches in size XL; retried once without the size filter.",
        "zero_temp_directories_after": len(after) == 0,
    }
    outdata = result(checks, [x])
    outdata["privacy_debug"] = {"raw_wardrobe_names_found": leaked, "temp_before_count": len(before), "temp_after_count": len(after)}
    return outdata


def check_5(client, log: Path) -> dict:
    x = call(client, log, {"query": Q_HAPPY, "wardrobe": {"items": []}})
    body, rec = x["body"] or {}, x["record"] or {}
    output, outfit = rec.get("output") or {}, body.get("outfit_suggestion") or ""
    ownership = bool(re.search(r"\b(?:my|our)\s+(?:jeans|wardrobe|shirt|shoes|top)\b|\byou\s+(?:own|already have)\b", outfit, re.I))
    checks = {
        "one_log": x["exactly_one_log"],
        "http_200": x["status"] == 200,
        "error_null": body.get("error") is None,
        "nonempty_outfit": bool(outfit.strip()),
        "no_wardrobe_statement": bool(re.search(r"no wardrobe is saved", outfit, re.I)),
        "exact_user_title": EXPECTED_TITLE_AS_WRITTEN in outfit,
        "other_general_clothes": bool(re.search(r"\b(?:jeans|sneakers|skirt|boots|sandals|pants|trousers|shorts)\b", outfit, re.I)),
        "no_ownership_claim": not ownership,
        "zero_wardrobe_logged": (rec.get("input") or {}).get("wardrobe_item_count") == 0,
        "selected_id": output.get("selected_item_id") == "lst_002",
        "card_price": "$18.00" in (output.get("fit_card") or ""),
    }
    return result(checks, [x])


def result(checks, calls):
    return {"passed": all(checks.values()), "checks": checks,
            "http_requests": [
                {"status": x["status"], "header": x["header"], "body": x["body"],
                 "record": x["record"], "exactly_one_log": x["exactly_one_log"]}
                for x in calls]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=("before", "after"))
    args = parser.parse_args()

    directory = ROOT / "results"
    directory.mkdir(exist_ok=True)
    log = directory / f"capstone-student-{args.phase}-requests.jsonl"
    os.environ["FITFINDR_LOG_PATH"] = str(log)
    log.unlink(missing_ok=True)

    methods = [check_1, check_2, check_3, check_4, check_5]
    rows = []
    with app.test_client() as client:
        for idx, method in enumerate(methods, start=1):
            trials = [method(client, log) for _ in range(3)]
            n = sum(t["passed"] for t in trials)
            rows.append({
                "criterion": idx, "label": TITLES[idx - 1], "target": "3/3",
                "count": n, "verdict": "MET" if n == 3 else "MISSED",
                "trials": trials,
            })
    log_count = len(lines(log))
    assert log_count == 21, f"3×(1+1+3+1+1)=21 HTTP entries required; got {log_count}"
    target_text = (ROOT / "criteria.md").read_text(encoding="utf-8")
    student_part = target_text[target_text.index("## Unit 9 Capstone — student-supplied"):]
    artifact = {
        "phase": args.phase,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "criteria_sha256": hashlib.sha256(student_part.encode()).hexdigest(),
        "http_calls": log_count,
        "mode": "Real Flask/MCP with local fallback; criterion 4 uses dummy invalid key; no live Gemini accuracy claims",
        "rows": rows,
    }
    (directory / f"capstone-student-{args.phase}-trials.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    table = [
        f"# Unit 9 student-supplied five criteria: {args.phase}",
        "",
        f"Criteria SHA256: `{artifact['criteria_sha256']}`.",
        f"Actual requests: {log_count}; three trials per criterion (criterion 3: three malformed requests per trial).",
        "Mode: real Flask + MCP, local model fallbacks, no provider token billing, dummy invalid key only for criterion 4.",
        "",
        "| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        table.append("| " + str(row["criterion"]) + ". " + row["label"]
                     + " | 3/3 | " + " | ".join("PASS" if t["passed"] else "FAIL" for t in row["trials"])
                     + " | " + row["verdict"] + f" ({row['count']}/3) |")
    table += ["", "## Actual saved results (one trial per criterion)", "",
              "Produced by `scripts/capstone_student_eval.py` through `serve.py::ask` and logged by `capstone_logging.py::_measure_one`.", ""]
    for row in rows:
        t = row["trials"][0]
        table += [
            f"### Criterion {row['criterion']}: {row['label']}", "",
            "Checks:", "~~~json", json.dumps(t["checks"], ensure_ascii=False), "~~~", "",
            "Actual HTTP responses and JSONL records from trial 1:", "~~~json",
            json.dumps(t["http_requests"], ensure_ascii=False), "~~~", "",
        ]
    (directory / f"capstone-student-{args.phase}-table.md").write_text("\n".join(table), encoding="utf-8")
    print("\n".join(table[:13]))
    print(f"Saved 21 requests and 15 independently scored trials ({args.phase}).")
    # MISSED is evidence; this script never changes acceptance standards.


if __name__ == "__main__":
    main()
