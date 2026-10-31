import asyncio
from contextlib import redirect_stderr
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import agent
from mcp_client import MCPError
import mcp_client
from serve import app
from tools import create_fit_card, search_listings, suggest_outfit
from test_budget import listing


def local_tool(name, arguments):
    # Tests use the real tool implementations; only the subprocess transport is replaced.
    return {"search_listings": search_listings, "suggest_outfit": suggest_outfit}[name](**arguments)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = Path(self.tmp.name) / "runs.jsonl"
        self.env = patch.dict(os.environ, {"FITFINDR_LOG_PATH": str(self.log)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.stderr = redirect_stderr(io.StringIO())
        self.stderr.__enter__()
        self.addCleanup(self.stderr.__exit__, None, None, None)

    def test_complete_path_uses_catalog_and_never_model(self):
        with patch.object(agent, "call_tool", side_effect=local_tool), patch("tools.generate", side_effect=AssertionError("budget path must not call a model")):
            r = agent.run_agent("casual outfit under $100", {"items": []})
        self.assertIsNone(r["error"])
        b = r["budget_result"]
        self.assertEqual(len(b["items"]), 3)
        self.assertEqual(b["total_cents"], sum(i["price_cents"] for i in b["items"]))
        self.assertLessEqual(b["total_cents"], 10000)
        self.assertEqual([t["tool"] for t in r["tool_calls"]], ["search_listings"] * 3 + ["suggest_outfit", "create_fit_card"])
        self.assertIn(b["total"], r["fit_card"])
        self.assertIn("Sample catalog", r["fit_card"])
        self.assertEqual(r["metrics"]["usage"]["model_calls"], 0)

    def test_impossible_budget_stops_before_styling(self):
        with patch.object(agent, "call_tool", side_effect=local_tool):
            r = agent.run_agent("casual outfit under $1", {})
        self.assertTrue(r["error"])
        self.assertIsNone(r["fit_card"])
        self.assertEqual(len(r["tool_calls"]), 3)

    def test_empty_and_malformed_search(self):
        for result in ([], "bad", [{"price": None}], [None]):
            with self.subTest(result=result), patch.object(agent, "call_tool", return_value=result):
                r = agent.run_agent("casual outfit under $100", {})
                self.assertTrue(r["error"])
                self.assertIsNone(r["fit_card"])

    def test_tool_failure_has_no_partial_recommendation(self):
        for side_effect in (MCPError("token=private"), [ [listing("tops", 20)], [listing("bottoms", 30)], [listing("shoes", 20)], MCPError("broken") ]):
            with patch.object(agent, "call_tool", side_effect=side_effect):
                r = agent.run_agent("casual outfit under $100", {})
            self.assertEqual(r["error_type"], "tool_failure")
            self.assertIsNone(r["budget_result"])
            self.assertNotIn("private", r["error"])

    def test_logs_success_failures_and_redacts_text(self):
        secret = "person@example.com API_KEY_123"
        with patch.object(agent, "call_tool", side_effect=local_tool):
            agent.run_agent("casual outfit under $100", {})
            agent.run_agent(secret + " outfit under $-10", {})
        raw = self.log.read_text()
        self.assertNotIn(secret, raw)
        rows = [json.loads(line) for line in raw.splitlines()]
        self.assertEqual([r["status"] for r in rows], ["success", "failure"])
        self.assertNotEqual(rows[0]["run_id"], rows[1]["run_id"])
        self.assertTrue(all(r["duration_ms"] >= 0 for r in rows))
        self.assertTrue(all(r["timestamp"].endswith("+00:00") for r in rows))

    def test_http_rejects_malformed_payloads(self):
        client = app.test_client()
        payloads = [[], {}, {"query": []}, {"query": " "}, {"query": 123}, {"query": "outfit", "budget": None}, {"query": "outfit", "wardrobe": {}}, {"query": "outfit", "wardrobe": {"items": [None]}}]
        for payload in payloads:
            with self.subTest(payload=payload):
                self.assertEqual(client.post("/ask", json=payload).status_code, 400)
        self.assertEqual(client.post("/ask", data="not-json", content_type="application/json").status_code, 400)
        self.assertEqual(len(self.log.read_text().splitlines()), len(payloads) + 1)

    def test_http_budget_and_errors(self):
        client = app.test_client()
        with patch.object(agent, "call_tool", side_effect=local_tool):
            self.assertEqual(client.post("/ask", json={"query": "casual outfit", "budget": 100}).status_code, 200)
            self.assertEqual(client.post("/ask", json={"query": "casual outfit", "budget": 1}).status_code, 422)
            self.assertEqual(client.post("/ask", json={"query": "casual outfit", "budget": -1}).status_code, 400)
        self.assertEqual(client.post("/ask", data="x" * 33000, content_type="application/json").status_code, 413)
        self.assertEqual(client.get("/health").status_code, 200)

    def test_legacy_single_item_route_still_works(self):
        item = listing("tops", 18, "old")
        item.update(colors=["black"])
        with patch.object(agent, "call_tool", side_effect=[[item], "1) Pair tops with jeans.\n2) Pair tops with shorts."]), patch.object(agent, "create_fit_card", return_value="Legacy caption"):
            r = agent.run_agent("tee under $30", {"items": []})
        self.assertIsNone(r["error"])
        self.assertEqual(r["fit_card"], "Legacy caption")

    def test_timeout_becomes_readable_mcp_error(self):
        async def timeout(*args):
            raise TimeoutError("private details")
        with patch.object(mcp_client, "_call", side_effect=timeout), self.assertRaises(MCPError):
            mcp_client.call_tool("search_listings", {})


if __name__ == "__main__":
    unittest.main()
