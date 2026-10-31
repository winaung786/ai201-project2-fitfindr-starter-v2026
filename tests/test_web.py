"""Keep the hosted browser companion and existing Python budget rules in agreement."""
import json
from pathlib import Path
import subprocess
import unittest

from budget import BudgetError, select_outfit
from budget_agent import parse_request
from serve import app
from tools import search_listings
from utils.data_loader import load_listings

ROOT = Path(__file__).resolve().parents[1]


class WebsiteTests(unittest.TestCase):
    def test_website_and_catalog_routes(self):
        client = app.test_client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-transport="api"', response.data)
        self.assertIn(b'Build my outfit', response.data)
        self.assertEqual(client.get("/catalog.json").get_json(), load_listings())
        with client.get("/assets/app.mjs") as asset:
            self.assertEqual(asset.status_code, 200)
        self.assertEqual(client.get("/assets/../.env").status_code, 404)

    def test_browser_selection_matches_python_for_styles_budgets_and_sizes(self):
        cases = [{"style": style, "budget": budget, "sizes": {}} for style in
                 ("casual", "minimal", "vintage", "streetwear", "y2k", "earth tones")
                 for budget in (1, 50, 74, 100, 150)]
        cases.extend([
            {"style": "casual", "budget": 100, "sizes": {"tops": "M", "bottoms": "W30", "shoes": "US 9"}},
            {"style": "casual", "budget": 100, "sizes": {"tops": "S", "shoes": "US 7"}},
            {"style": "vintage", "budget": 150, "sizes": {"tops": "XL", "bottoms": "W32"}},
        ])
        result = subprocess.run(["node", str(ROOT / "tests/web-parity-runner.mjs")],
                                input=json.dumps({"cases": cases, "catalog": load_listings()}),
                                capture_output=True, text=True, check=True, timeout=20)
        actual = json.loads(result.stdout)
        for case, browser in zip(cases, actual, strict=True):
            with self.subTest(case=case):
                parsed = parse_request(case["style"] + " outfit", case["budget"], case["sizes"])
                try:
                    pools = {c: search_listings(parsed["description"], case["sizes"].get(c), case["budget"], c)
                             for c in ("tops", "bottoms", "shoes")}
                    chosen = select_outfit(pools, case["budget"])
                    expected = {"ids": [i["id"] for i in chosen["items"]], "total": chosen["total_cents"], "remaining": chosen["remaining_cents"]}
                except BudgetError as exc:
                    expected = {"error": exc.code}
                self.assertEqual(browser, expected)


if __name__ == "__main__":
    unittest.main()
