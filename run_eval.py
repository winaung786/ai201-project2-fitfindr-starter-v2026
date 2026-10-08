#!/usr/bin/env python3
"""
Run your scenarios repeatedly and write the results down. ← UNIT 4

    python run_eval.py --label before      five tries, the default
    python run_eval.py --label after       after your improvement
    python run_eval.py --tries 10          more tries

This does the mechanical half of unit 4 for you. It runs every scenario in
`scenarios.py` five separate times, **with caching off** so you get five real
answers, captures the trace and the session for each, and writes it all into
`results/` in the table format the submission asks for.

Five, because your criteria are written out of five — "4 of 5 tries", "5 of 5
tries". One column per try means you count the passes and read the verdict
straight off the row, with no arithmetic in between.

⚠️ What it does NOT do is decide whether a try passed.

That judgment is yours, and it has to be, because it depends on criteria you
wrote. The Verdict column comes out blank and you fill it in from the output
underneath. Deciding what counts as a pass is the lesson — a scorer handed to
you would teach you nothing.

**Two of your three tools call a model, so tries will legitimately differ.**
That is expected here, unlike pair 1. If all five tries come back identical
on a criterion that involves the fit card, check that you're really in test
mode — caching is what usually explains it.
"""

import argparse
import datetime as dt
import hashlib
import json
import sys
import traceback

import config
import scenarios as scenario_module


def run_once(scenario, use_trace=True):
    """Record real model responses and received tool inputs, preserving agent behavior."""
    import contextlib
    import copy
    import io
    import os
    import time
    import tempfile
    from unittest.mock import patch
    # Import before redirection: the SDK binds its default child stderr at import time.
    import mcp.client.stdio  # noqa: F401
    import agent
    import generate
    import tools
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe
    import trace as trace_module

    wardrobe = get_empty_wardrobe() if scenario["wardrobe"] == "empty" else get_example_wardrobe()
    if use_trace:
        trace_module.start_trace()
    record = {"session": None, "trace": "", "crashed": None, "tool_inputs": [],
              "model_responses": [], "state_probe": scenario.get("mode") == "state_probe"}
    original_outfit, original_card, original_generate = agent.suggest_outfit, agent.create_fit_card, tools.generate
    # MCP passes stderr to a child process, so it needs a real file descriptor.
    stdout, stderr = io.StringIO(), tempfile.TemporaryFile(mode="w+", encoding="utf-8")
    child_log = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".jsonl", delete=False)
    child_log_path = child_log.name
    child_log.close()
    child_responses = []
    started, calls_before, tokens_before = time.monotonic(), generate.call_count(), generate.token_counts()

    def recorded_generate(prompt, *args, **kwargs):
        response = {"prompt": prompt, "temperature": kwargs.get("temperature", config.TEMPERATURE)}
        record["model_responses"].append(response)
        try:
            response["raw_text"] = original_generate(prompt, *args, **kwargs)
            return response["raw_text"]
        except Exception as exc:
            response["error"] = f"{type(exc).__name__}: {exc}"
            raise

    def recorded_outfit(new_item, wardrobe):
        record["tool_inputs"].append({"tool": "suggest_outfit", "new_item": copy.deepcopy(new_item), "wardrobe": copy.deepcopy(wardrobe)})
        return "State probe outfit." if record["state_probe"] else original_outfit(new_item, wardrobe)

    def recorded_card(outfit, new_item):
        record["tool_inputs"].append({"tool": "create_fit_card", "new_item": copy.deepcopy(new_item), "outfit": outfit})
        return "State probe fit card." if record["state_probe"] else original_card(outfit, new_item)

    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), patch.dict(os.environ, {"FITFINDR_MCP_MODEL_LOG": child_log_path}), patch.object(tools, "generate", recorded_generate), patch.object(agent, "suggest_outfit", recorded_outfit), patch.object(agent, "create_fit_card", recorded_card):
            try:
                record["session"] = agent.run_agent(scenario["query"], wardrobe)
            except Exception as exc:
                record["crashed"] = f"{type(exc).__name__}: {exc}"
                record["traceback"] = traceback.format_exc()
        with open(child_log_path, encoding="utf-8") as log:
            child_responses = [json.loads(line) for line in log if line.strip()]
    finally:
        os.unlink(child_log_path)
    record["model_responses"] = child_responses + record["model_responses"]
    record["trace"] = trace_module.get_trace() if use_trace else ""
    stderr.seek(0)
    record["stdout"], record["stderr"] = stdout.getvalue(), stderr.read()
    stderr.close()
    record["elapsed_seconds"] = round(time.monotonic() - started, 3)
    record["model_calls"] = generate.call_count() - calls_before + sum(
        response.get("model_calls", 0) for response in child_responses
    )
    tokens_after = generate.token_counts()
    record["tokens"] = {name: tokens_after[name] - value + sum(
        response.get("tokens", {}).get(name, 0) for response in child_responses
    ) for name, value in tokens_before.items()}
    if not record["state_probe"] and record["session"]:
        session = record["session"]
        record["model_text_used"] = {
            name: index < len(record["model_responses"]) and record["model_responses"][index].get("raw_text") == session.get(name)
            for index, name in enumerate(("outfit_suggestion", "fit_card"))
        } if record["model_responses"] else {}
    # Secrets never enter a saved report, including an unexpected provider exception.
    key = os.getenv("GEMINI_API_KEY", "")
    if key:
        record = json.loads(json.dumps(record, ensure_ascii=False).replace(key, "[REDACTED]"))
    return record


def write_checkpoint(rows, args, metadata, complete=False):
    """Persist every finished try; interruption cannot discard earlier model answers."""
    config.RESULTS_DIR.mkdir(exist_ok=True)
    path = config.RESULTS_DIR / f"unit4-{args.label or 'run'}.json"
    payload = {"metadata": metadata, "complete": complete, "rows": rows}
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def main():
    parser = argparse.ArgumentParser(description="Run the scenarios and log the results.")
    parser.add_argument("--tries", "--trials", type=int, default=5, dest="tries",
                        help="tries per scenario (default 5, matching your criteria)")
    parser.add_argument("--label", default="", help="a name for this run, e.g. 'before'")
    args = parser.parse_args()

    problems = scenario_module.validate()
    if problems:
        print("scenarios.py has problems:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    if not scenario_module.SCENARIOS:
        print("scenarios.py is empty. Milestone 3 starts by filling it in.", file=sys.stderr)
        sys.exit(1)

    if args.tries < 5:
        print(f"⚠️  {args.tries} tries. Your criteria are written out of five.\n")

    # Caching off. Five tries have to be five real answers.
    config.CACHE_ENABLED = False
    print("Cache is OFF for this run — that's deliberate.\n")

    report_path = config.RESULTS_DIR / f"unit4-{args.label or 'run'}.json"
    if report_path.exists():
        raise SystemExit(f"Refusing to overwrite {report_path}. Choose a new --label to preserve the evidence.")
    metadata = {
        "label": args.label, "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "tries_per_criterion": args.tries, "cache_enabled": config.CACHE_ENABLED,
        "model": config.MODEL, "temperature": config.TEMPERATURE,
        "file_sha256": {name: hashlib.sha256((config.ROOT / name).read_bytes()).hexdigest()
                        for name in ("criteria.md", "scenarios.py", "tools.py", "agent.py", "config.py", "generate.py", "mcp_server.py", "mcp_client.py", "run_eval.py", "data/listings.json", "data/wardrobe_schema.json")},
        "state_test": "Criterion 3 replaces only the two text tools with recording functions as specified in criteria.md; MCP search is real.",
    }
    rows = []
    write_checkpoint(rows, args, metadata)
    for scenario in scenario_module.SCENARIOS:
        print(f"{scenario['name']}  ({scenario['wardrobe']} wardrobe)")
        print(f"  query: {scenario['query']}")

        tries = []
        rows.append({"scenario": scenario, "tries": tries})
        for attempt in range(1, args.tries + 1):
            record = run_once(scenario)
            tries.append(record)
            write_checkpoint(rows, args, metadata)

            if record["crashed"]:
                print(f"  try {attempt}: CRASHED — {record['crashed']}")
            else:
                session = record["session"] or {}
                if session.get("error"):
                    print(f"  try {attempt}: stopped early — {str(session['error'])[:60]}")
                else:
                    card = (session.get("fit_card") or "")
                    print(f"  try {attempt}: completed — fit card {len(card)} chars")

        print()

    metadata["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    total_calls = sum(record["model_calls"] for row in rows for record in row["tries"])
    metadata["usage"] = f"{total_calls} model calls across agent and MCP server"
    metadata["tokens"] = {name: sum(record["tokens"][name] for row in rows for record in row["tries"])
                          for name in ("prompt", "output", "total")}
    path = write_checkpoint(rows, args, metadata, complete=True)
    print(f"Wrote {path.relative_to(config.ROOT)}", flush=True)
    write_report(rows, args)


def write_report(rows, args):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"

    n = args.tries
    headers = " | ".join(f"Try {i}" for i in range(1, n + 1))
    divider = "|".join(["---"] * n)

    lines = [
        f"# Run log{f' — {args.label}' if args.label else ''}",
        "",
        "- Produced by: `run_eval.py::main`",
        "- Loop: `agent.py::run_agent` · tools: `tools.py`",
        f"- Tries per scenario: {n}, caching off",
        f"- Temperature: {config.TEMPERATURE}",
        f"- When: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Paste the table below into your README. Fill in the Criterion and",
        "Target columns from `criteria.md`, then mark each try PASS or FAIL",
        "from the output underneath and count them for the Verdict.",
        "",
        f"| Criterion | Target | {headers} | Verdict |",
        f"|---|---|{divider}|---|",
    ]

    for row in rows:
        scenario = row["scenario"]
        number = scenario.get("criterion")
        # A scenario with "criterion": None is a diagnostic run, not one of
        # your five. It's marked so you don't paste an unnumbered row into a
        # table the README asks you to number 1-5.
        label_text = (
            f"{number}. {scenario['name']}"
            if number
            else f"{scenario['name']} _(diagnostic — not one of your five)_"
        )
        lines.append(f"| {label_text} |  | {' | '.join([' '] * n)} |  |")

    lines += [
        "",
        "> The Try and Verdict columns are blank on purpose. Whether a try",
        "> passed depends on the criterion you wrote, so it's yours to decide.",
        "> Count the passes, then read that count against your target: a row",
        "> targeting 4 of 5 with three PASS cells is MISSED (3/5).",
        "",
        "---",
        "",
        "## What actually happened",
        "",
        "Real output, as text. Paste the relevant parts into your README —",
        "the rubric asks for output, not a description of it.",
        "",
    ]

    for row in rows:
        scenario = row["scenario"]
        lines += [f"### {scenario['name']}", "",
                  f"- Query: `{scenario['query']}`",
                  f"- Wardrobe: {scenario['wardrobe']}", ""]

        for i, record in enumerate(row["tries"], 1):
            lines.append(f"**Try {i}**")
            lines.append("")

            if record["crashed"]:
                lines += ["Crashed:", "", "```", record["crashed"], "```", ""]
                continue

            session = record["session"] or {}
            item = session.get("selected_item") or {}
            lines += [
                f"- stopped early: {'yes — ' + str(session.get('error')) if session.get('error') else 'no'}",
                f"- selected_item: {item.get('title', '(none)')}"
                + (f" (${item.get('price')}, {item.get('platform')})" if item else ""),
                f"- search_results: {len(session.get('search_results') or [])}",
                "",
            ]
            if session.get("outfit_suggestion"):
                lines += ["Outfit suggestion:", "", "```",
                          str(session["outfit_suggestion"]), "```", ""]
            if session.get("fit_card"):
                lines += ["Fit card:", "", "```", str(session["fit_card"]), "```", ""]
            if record["trace"]:
                lines += ["Trace:", "", "```", record["trace"], "```", ""]

    path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {path.relative_to(config.ROOT)}")
    total_calls = sum(record["model_calls"] for row in rows for record in row["tries"])
    print(f"{total_calls} model calls across agent and MCP server")
    print("\nCommit this file. It's the evidence the test actually happened.")

    if not any(r["tries"][0]["trace"] for r in rows):
        print(
            "\nNote: no trace was captured. You haven't added trace.step() calls\n"
            "to run_agent() yet — that's Milestone 2, and the trace is required\n"
            "evidence worth a point."
        )


if __name__ == "__main__":
    main()
