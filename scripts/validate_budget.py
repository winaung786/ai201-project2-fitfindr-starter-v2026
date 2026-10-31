"""Three-trial AI-assisted technical evaluation, separate from student criteria."""

import argparse
from contextlib import redirect_stderr
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import agent
from budget import BudgetError, validate_outfit
from budget_agent import parse_request
from mcp_client import MCPError
from serve import app
from tools import suggest_outfit
from utils.data_loader import load_listings

SOURCES = ("agent.py", "budget.py", "budget_agent.py", "tools.py", "telemetry.py",
           "mcp_client.py", "mcp_server.py", "serve.py", "data/listings.json")
MARKER = "SYNTHETIC_PRIVATE_MARKER_93"


def digest(path):
    # Normalize only newlines so Git CRLF conversion cannot masquerade as a code change.
    return hashlib.sha256(path.read_text(encoding="utf-8").replace("\r\n", "\n").encode()).hexdigest()


def fixture(category, price):
    return {"id": "fixture_" + category, "title": "TEST ONLY " + category,
            "category": category, "size": "M", "platform": "test-fixture",
            "price": price, "style_tags": ["classic"], "colors": ["black"]}


def fixture_transport(fault=None):
    def call(name, arguments):
        if fault == "transport":
            raise MCPError(MARKER)
        if name == "suggest_outfit":
            return suggest_outfit(**arguments)
        category = arguments["category"]
        item = fixture(category, 20)
        if category == "shoes":
            if fault == "empty":
                return []
            if fault == "missing_price":
                item.pop("price")
            if fault == "unavailable":
                item["available"] = False
            if fault == "currency":
                item["currency"] = "EUR"
            if fault == "expensive":
                item["price"] = 200
        return [item]
    return call


def case(name, inputs, output, checks, transport):
    return {"name": name, "input": inputs, "output": output,
            "checks": checks, "passed": all(checks.values()), "transport": transport}


def grounded():
    q = "casual outfit under $100"
    s = agent.run_agent(q, {"items": []})
    b = s.get("budget_result") or {}
    items = b.get("items", [])
    catalog = {i["id"]: i for i in load_listings()}
    receipts = {i["id"]: i for i in s["search_results"]}
    original = all(i["id"] in catalog and i["id"] in receipts and
                   Decimal(i["price"]) == Decimal(str(catalog[i["id"]]["price"])) and
                   i["title"] == catalog[i["id"]]["title"] and
                   i.get("url") == catalog[i["id"]].get("url") for i in items)
    total = sum(int(Decimal(i["price"]) * 100) for i in items)
    checks = {"success": not s["error"], "three_categories": len(items) == 3 and {i["category"] for i in items} == {"tops", "bottoms", "shoes"},
              "distinct_ids": len({i["id"] for i in items}) == 3, "catalog_grounding": original,
              "correct_total": b.get("total_cents") == total <= 10000,
              "correct_remainder": b.get("remaining_cents") == 10000 - total,
              "grounded_card": b.get("total", "MISSING") in (s["fit_card"] or "") and
                  "Sample catalog" in (s["fit_card"] or "") and "tax and shipping are excluded" in (s["fit_card"] or "")}
    return [case("catalog outfit", {"query": q}, s, checks, "real stdio MCP")]


def money():
    cases = []
    items = [fixture(c, p) for c, p in zip(("tops", "bottoms", "shoes"), ("0.10", "0.20", "0.30"))]
    r = validate_outfit(items, "0.60")
    cases.append(case("exact cents", {"prices": ["0.10", "0.20", "0.30"], "budget": "0.60"}, r,
                      {"exact_total": r["total_cents"] == 60 and r["remaining_cents"] == 0}, "direct deterministic validator; synthetic fixtures"))
    try:
        r = validate_outfit(items, "0.59")
        accepted = True
    except BudgetError as exc:
        r, accepted = {"error_type": exc.code, "error": str(exc)}, False
    cases.append(case("one cent too low", {"budget": "0.59"}, r, {"rejected": not accepted}, "direct validator"))
    for name, q, budget, expected in (
        ("sentence punctuation", "outfit under $100.", None, True),
        ("zero", "outfit under $0", None, False),
        ("negative", "outfit under $-10", None, False),
        ("excess decimals", "outfit under $100.001", None, False),
        ("conflicting", "outfit under $90", 100, False),
        ("repeated dot", "outfit under $100..", None, False),
        ("repeated comma", "outfit under $100,,", None, False),
        ("mixed punctuation", "outfit under $100.,", None, False),
    ):
        try:
            output = parse_request(q, budget)
            accepted = True
        except BudgetError as exc:
            output, accepted = {"error_type": exc.code, "error": str(exc)}, False
        cases.append(case(name, {"query": q, "budget": budget}, output,
                          {"correct_acceptance": accepted == expected}, "direct request parser"))
    return cases


def failures():
    cases = []
    for fault in ("missing_price", "unavailable", "currency", "empty", "expensive", "transport"):
        with patch.object(agent, "call_tool", side_effect=fixture_transport(fault)):
            s = agent.run_agent("casual outfit under $100", {"items": []})
        expected = "tool_failure" if fault == "transport" else "over_budget" if fault == "expensive" else "no_valid_products"
        checks = {"clear_error": bool(s["error"]) and s.get("error_type") == expected,
                  "no_partial_recommendation": all(not s.get(k) for k in ("budget_result", "selected_item", "outfit_suggestion", "fit_card")),
                  "stopped_before_styling": all(t["tool"] == "search_listings" for t in s["tool_calls"])}
        cases.append(case(fault, {"fault": fault}, s, checks, "injected transport/catalog fixture; real agent"))
    return cases


def sizes():
    payload = {"query": "casual outfit", "budget": 100, "sizes": {"tops": "M", "bottoms": "W30", "shoes": "US 9"}}
    response = app.test_client().post("/ask", json=payload)
    s = response.get_json()
    b = s.get("budget_result") or {}
    items = b.get("items", [])
    allowed_sizes = {"tops": {"M", "S/M", "M/L"}, "bottoms": {"W30", "W30 L30"}, "shoes": {"US 9"}}
    calls = [t for t in s.get("tool_calls", []) if t["tool"] == "search_listings"]
    checks = {"http_200": response.status_code == 200,
              "size_matches": len(items) == 3 and all(i["size"] in allowed_sizes[i["category"]] for i in items),
              "constraints_retained": len(calls) == 3 and all(t["inputs"]["size"] == payload["sizes"][t["inputs"]["category"]] and not t.get("retry") for t in calls),
              "within_budget": b.get("within_budget") is True and b["total_cents"] <= 10000}
    return [case("category sizes", payload, {"http_status": response.status_code, "session": s}, checks, "Flask request handler with real stdio MCP")]


def logs():
    cases = []
    for name in ("success", "failure", "bad_http"):
        capture = io.StringIO()
        with redirect_stderr(capture):
            if name == "bad_http":
                response = app.test_client().post("/ask", json={"query": []})
                s = response.get_json()
            else:
                with patch.object(agent, "call_tool", side_effect=fixture_transport("transport" if name == "failure" else None)):
                    s = agent.run_agent("casual outfit under $100 " + MARKER, {"items": [{"name": MARKER, "category": "tops"}]})
        raw = capture.getvalue()
        entries = [json.loads(line) for line in raw.splitlines() if line.startswith("{")]
        r = entries[0] if entries else {}
        expect = "success" if name == "success" else "failure"
        expected_error = None if name == "success" else "tool_failure" if name == "failure" else "invalid_input"
        checks = {"one_log": len(entries) == 1, "correct_status": r.get("status") == expect and r.get("error_type") == expected_error,
                  "utc_and_timing": r.get("timestamp", "").endswith("+00:00") and r.get("duration_ms", -1) >= 0,
                  "response_run_id": bool(s.get("run_id")) and r.get("run_id") == s.get("run_id"),
                  "private_text_removed": MARKER not in raw,
                  "sanitized_input_output": "query_sha256" in r.get("input", {}) and "has_fit_card" in r.get("output", {}),
                  "matching_total": name != "success" or r.get("output", {}).get("total_cents") == s["budget_result"]["total_cents"]}
        cases.append(case(name, {"scenario": name, "private_marker": "synthetic, not a real credential"}, {"response": s, "logs": entries}, checks, "fixture-backed agent or malformed Flask request"))
    ids = [c["output"]["logs"][0]["run_id"] for c in cases if c["output"]["logs"]]
    for c in cases:
        c["checks"]["distinct_ids"] = len(ids) == len(set(ids)) == 3
        c["passed"] = all(c["checks"].values())
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", choices=("before", "after"), required=True)
    args = parser.parse_args()
    output = ROOT / "results" / f"unit9-validation-{args.label}.json"
    if output.exists():
        raise SystemExit(f"Refusing to overwrite evidence: {output.name}")
    report = {"label": args.label, "authorship": "AI-assisted developer checks; not student-authored criteria",
              "timestamp": datetime.now(timezone.utc).isoformat(),
              "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "plan_sha256": digest(ROOT / "docs/unit9-validation-plan.md"), "runner_sha256": digest(Path(__file__)),
              "criteria_sha256": digest(ROOT / "criteria.md"), "source_sha256": {n: digest(ROOT / n) for n in SOURCES},
              "cache": "no model/cache calls on budget path", "trials": []}
    previous = os.environ.pop("FITFINDR_LOG_PATH", None)
    try:
        with output.with_suffix(".jsonl").open("w", encoding="utf-8") as stream, redirect_stderr(stream):
            for trial in range(1, 4):
                groups = []
                for number, function in enumerate((grounded, money, failures, sizes, logs), 1):
                    cases = function()
                    groups.append({"check": number, "cases": cases, "passed": all(c["passed"] for c in cases)})
                    print(f"{args.label} trial {trial}, check {number}: {sum(c['passed'] for c in cases)}/{len(cases)}", flush=True)
                report["trials"].append({"trial": trial, "groups": groups})
    finally:
        if previous is not None:
            os.environ["FITFINDR_LOG_PATH"] = previous
    report["summary"] = [{"check": n, "trials": [
        {"passed_cases": sum(c["passed"] for c in t["groups"][n-1]["cases"]), "total_cases": len(t["groups"][n-1]["cases"])}
        for t in report["trials"]], "verdict": "MET" if all(t["groups"][n-1]["passed"] for t in report["trials"]) else "MISSED"} for n in range(1, 6)]
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
