import unittest

from budget import BudgetError, cents, select_outfit, validate_outfit
from budget_agent import parse_request


def listing(category, price, item_id=None, **extra):
    return {"id": item_id or category, "title": category, "category": category,
            "size": "M", "platform": "test", "price": price,
            "style_tags": ["classic"], **extra}


def pools(prices=(28, 42, 25)):
    return {c: [listing(c, p)] for c, p in zip(("tops", "bottoms", "shoes"), prices)}


class BudgetTests(unittest.TestCase):
    def test_subtotal_and_remainder(self):
        r = select_outfit(pools(), 100)
        self.assertEqual((r["total_cents"], r["remaining_cents"]), (9500, 500))

    def test_decimal_boundary(self):
        r = select_outfit(pools(("0.10", "0.20", "0.30")), "0.60")
        self.assertEqual((r["total"], r["remaining"]), ("0.60", "0.00"))
        with self.assertRaises(BudgetError):
            select_outfit(pools(("0.10", "0.20", "0.30")), "0.59")

    def test_invalid_money(self):
        for value in (None, True, False, 0, -1, "-10", float("nan"), float("inf"), "1.001", "$10", "1e2", {}, "1,000", "1000001"):
            with self.subTest(value=value), self.assertRaises(BudgetError):
                cents(value)

    def test_no_greedy_false_failure(self):
        p = pools((80, 30, 20))
        p["tops"].append(listing("tops", 15, "cheaper-top"))
        r = select_outfit(p, 65)
        self.assertEqual(r["total"], "65.00")
        self.assertEqual(r["items"][0]["id"], "cheaper-top")

    def test_bad_listings_excluded(self):
        for extra in ({"price": None}, {"price": "unknown"}, {"price": -10}, {"currency": "EUR"}, {"available": False}, {"availability": "sold"}, {"id": None}):
            p = pools()
            p["tops"][0].update(extra)
            with self.subTest(extra=extra), self.assertRaises(BudgetError):
                select_outfit(p, 100)

    def test_missing_category_and_duplicate(self):
        with self.assertRaises(BudgetError):
            select_outfit({}, 100)
        items = [listing(c, 10, "same") for c in ("tops", "bottoms", "shoes")]
        with self.assertRaises(BudgetError):
            validate_outfit(items, 100)

    def test_no_fabricated_links(self):
        r = select_outfit(pools(), 100)
        self.assertTrue(all("url" not in i for i in r["items"]))
        for url in ("javascript:alert(1)", "http://shop.test/item", "https://secret@shop.test/item", "https://[bad"):
            p = pools()
            p["tops"][0]["url"] = url
            self.assertNotIn("url", select_outfit(p, 100)["items"][0])
        p["tops"][0]["url"] = "https://shop.test/item"
        self.assertEqual(select_outfit(p, 100)["items"][0]["url"], "https://shop.test/item")

    def test_budget_parser(self):
        self.assertEqual(parse_request("find a casual outfit under $100")["budget"], "100.00")
        self.assertEqual(parse_request("classic outfit", "95.50")["budget"], "95.50")
        self.assertEqual(parse_request("casual outfit under $100.")["budget"], "100.00")
        self.assertEqual(parse_request("outfit under $100", 100, {"shoes": "US 9"})["sizes"], {"shoes": "US 9"})

    def test_bad_budget_queries(self):
        for q in ("outfit", "outfit under $-10", "outfit under $0", "outfit under $100.999", "outfit under $1e2", "outfit under $100 size M", "outfit under $100 below $90"):
            with self.subTest(query=q), self.assertRaises(BudgetError):
                parse_request(q)
        with self.assertRaises(BudgetError):
            parse_request("outfit under $90", 100)
        with self.assertRaises(BudgetError):
            parse_request("outfit", 100, {"head": "XL"})


if __name__ == "__main__":
    unittest.main()
