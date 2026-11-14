"""Structured per-request telemetry for the Unit 9 FitFindr local run.

Records are appended to a JSONL file; API keys and full wardrobes are never
written. Set FITFINDR_LOG_PATH to choose the file. The MCP child writes *only*
call counts and token totals to a temporary file, removed after the request.
"""
from __future__ import annotations

from datetime import datetime, timezone
from functools import wraps
import json
import os
from pathlib import Path
import tempfile
import threading
import time
from uuid import uuid4

from flask import jsonify, make_response, request

import config
import generate


def _tokens_delta(after: dict, before: dict) -> dict:
    return {key: max(0, int(after.get(key, 0)) - int(before.get(key, 0)))
            for key in ("prompt", "output", "total")}


def _mcp_usage(path: Path) -> tuple[int, dict]:
    calls = 0
    tokens = {"prompt": 0, "output": 0, "total": 0}
    if not path.is_file():
        return calls, tokens
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        calls += int(entry.get("model_calls", 0))
        for key in tokens:
            tokens[key] += int(entry.get("tokens", {}).get(key, 0))
    return calls, tokens


def _input_summary(payload) -> dict:
    if not isinstance(payload, dict):
        return {"json_object": False, "query": None, "wardrobe_item_count": None}
    query = payload.get("query")
    wardrobe = payload.get("wardrobe")
    items = wardrobe.get("items") if isinstance(wardrobe, dict) else None
    return {
        "json_object": True,
        "query": query[:180] if isinstance(query, str) else None,
        "wardrobe_item_count": len(items) if isinstance(items, list) else None,
    }


def _output_summary(data) -> dict:
    if not isinstance(data, dict):
        return {"selected_item_id": None, "fit_card": None, "error": "Nonobject response"}
    selected = data.get("selected_item")
    return {
        "selected_item_id": selected.get("id") if isinstance(selected, dict) else None,
        "fit_card": str(data.get("fit_card"))[:180] if data.get("fit_card") else None,
        "error": str(data.get("error"))[:180] if data.get("error") else None,
        "retry_notice": str(data.get("notice"))[:180] if data.get("notice") else None,
    }


def append_log(record: dict) -> Path:
    target = Path(os.getenv("FITFINDR_LOG_PATH", str(config.RESULTS_DIR / "capstone-requests.jsonl")))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return target


_telemetry_lock = threading.Lock()


def instrument_http(handler):
    """Serialize telemetry environment changes across overlapping HTTP requests."""
    @wraps(handler)
    def wrapped(*args, **kwargs):
        with _telemetry_lock:
            return _measure_one(handler, *args, **kwargs)
    return wrapped


def _measure_one(handler, *args, **kwargs):
    request_id = uuid4().hex[:12]
    started = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()
    payload = request.get_json(silent=True)
    local_calls_before = generate.call_count()
    local_tokens_before = generate.token_counts()

    # The agent is serialised by serve.py's lock. This temporary environment
    # variable is scoped to the request, not persisted as a server setting.
    with tempfile.TemporaryDirectory(prefix="fitfindr-capstone-") as tempdir:
        metrics_path = Path(tempdir) / "mcp-usage.jsonl"
        previous = os.environ.get("FITFINDR_MCP_METRICS_LOG")
        os.environ["FITFINDR_MCP_METRICS_LOG"] = str(metrics_path)
        try:
            try:
                response = make_response(handler(*args, **kwargs))
            except Exception:
                # Avoid leaking provider details or secrets to the user/log.
                response = make_response(jsonify({"error": "Internal server error; retry or inspect the local log."}), 500)
        finally:
            if previous is None:
                os.environ.pop("FITFINDR_MCP_METRICS_LOG", None)
            else:
                os.environ["FITFINDR_MCP_METRICS_LOG"] = previous
        try:
            remote_calls, remote_tokens = _mcp_usage(metrics_path)
        except (OSError, ValueError, TypeError):
            remote_calls, remote_tokens = 0, {"prompt": 0, "output": 0, "total": 0}

    local_tokens = _tokens_delta(generate.token_counts(), local_tokens_before)
    total_tokens = {key: local_tokens[key] + remote_tokens[key] for key in local_tokens}
    body = response.get_json(silent=True) if response.is_json else None
    record = {
        "timestamp": timestamp,
        "run_id": request_id,
        "route": "/ask",
        "input": _input_summary(payload),
        "output": _output_summary(body),
        "http_status": response.status_code,
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        "model_calls": max(0, generate.call_count() - local_calls_before) + remote_calls,
        "model_tokens": total_tokens,
        "token_measurement": "Observed provider usage; zero means no billed model calls were recorded.",
    }
    append_log(record)
    response.headers["X-FitFindr-Run-ID"] = request_id
    return response
