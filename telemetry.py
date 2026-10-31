"""Allowlisted JSONL records; never log raw queries, wardrobes, or model text."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from uuid import uuid4


def clocks():
    return time.perf_counter(), time.process_time()


def record_run(query, session, start, *, surface="agent", error_type=None):
    budget = session.get("budget_result") or {}
    raw = query if isinstance(query, str) else ""
    error = error_type or session.get("error_type") or ("agent_error" if session.get("error") else None)
    is_budget = session.get("mode") == "budget_outfit"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(), "run_id": uuid4().hex,
        "surface": surface, "mode": session.get("mode", "single_item"),
        "input": {"query_sha256": hashlib.sha256(raw.encode()).hexdigest(), "query_length": len(raw)},
        "output": {"item_count": len(budget.get("items", [])),
                   "budget_cents": budget.get("budget_cents"), "total_cents": budget.get("total_cents"),
                   "remaining_cents": budget.get("remaining_cents"), "has_fit_card": bool(session.get("fit_card"))},
        "duration_ms": round((time.perf_counter() - start[0]) * 1000, 3),
        "parent_cpu_ms": round((time.process_time() - start[1]) * 1000, 3),
        "cpu_scope": "parent process only; excludes MCP subprocesses",
        "status": "failure" if error else "success", "error_type": error,
        "tool_count": len(session.get("tool_calls", [])),
        "usage": {"model_calls": 0 if is_budget else None, "prompt_tokens": 0 if is_budget else None,
                  "output_tokens": 0 if is_budget else None,
                  "scope": "complete deterministic budget path" if is_budget else "not collected for legacy MCP model path"},
    }
    line = json.dumps(record, ensure_ascii=True, allow_nan=False)
    # stderr works for local sessions and host log capture. Optional file is local-only.
    print(line, file=sys.stderr, flush=True)
    path = os.getenv("FITFINDR_LOG_PATH")
    if path:
        try:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as stream:
                stream.write(line + "\n")
        except OSError:
            print('{"event":"log_file_unavailable","fallback":"stderr"}', file=sys.stderr, flush=True)
    session["run_id"] = record["run_id"]
    session["metrics"] = {k: record[k] for k in ("duration_ms", "parent_cpu_ms", "usage")}
    return record
