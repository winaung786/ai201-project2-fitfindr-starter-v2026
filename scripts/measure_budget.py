"""Ten real, uncached MCP budget runs for build instrumentation/cost evidence.

This is not the student's Unit 9 acceptance evaluation.
"""

import argparse
from contextlib import redirect_stderr
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import run_agent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "unit9-build-cost.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    log = args.output.with_suffix(".jsonl")
    previous = os.environ.pop("FITFINDR_LOG_PATH", None)
    runs = []
    try:
        with log.open("w", encoding="utf-8") as stream, redirect_stderr(stream):
            for i in range(10):
                session = run_agent("casual outfit under $100", {"items": []})
                if session["error"]:
                    raise RuntimeError(f"Run {i + 1} failed: {session['error_type']}")
                runs.append({"trial": i + 1, "run_id": session["run_id"],
                             "metrics": session["metrics"], "budget_result": session["budget_result"]})
                print(f"Measured budget run {i + 1}/10: {session['metrics']['duration_ms']} ms", flush=True)
            # Deliberately exercise and preserve a failure, outside the cost average.
            failure = run_agent("outfit under $-1", {"items": []})
            assert failure["error_type"] == "invalid_price"
    finally:
        if previous is not None:
            os.environ["FITFINDR_LOG_PATH"] = previous
    mean_ms = statistics.mean(r["metrics"]["duration_ms"] for r in runs)
    report = {
        "purpose": "build cost and instrumentation measurement, not student acceptance results",
        "timestamp": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                          [ROOT / n for n in ("agent.py", "budget.py", "budget_agent.py", "tools.py", "mcp_client.py", "mcp_server.py", "data/listings.json")]},
        "transport": "real stdio MCP, new subprocess per tool call, no model/cache calls",
        "runs": runs, "summary": {
            "count": len(runs), "mean_wall_ms": round(mean_ms, 3),
            "mean_parent_cpu_ms": round(statistics.mean(r["metrics"]["parent_cpu_ms"] for r in runs), 3),
            "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0, "metered_model_cost_usd": 0,
            "wall_seconds_per_100_runs": round(mean_ms / 1000 * 100, 3),
            "compute_cost_usd": None,
            "limitations": "Wall time includes MCP startup/waiting; parent CPU excludes subprocess CPU. No hosting tariff or energy measurement supplied, so compute dollars are unknown. This does not measure legacy Gemini cost.",
        }, "failure_probe": {k: failure[k] for k in ("run_id", "error", "error_type", "metrics")},
    }
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
