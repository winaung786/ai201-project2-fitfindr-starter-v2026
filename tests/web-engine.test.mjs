import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { cents, validateOutfit, makeOutfit, styles } from "../web/assets/outfit-engine.mjs";
const catalog = JSON.parse(await readFile(new URL("../data/listings.json", import.meta.url), "utf8"));
const item = (category, price) => ({ id: category, category, price, title: `Test ${category}`, platform: "fixture", size: "M", style_tags: ["classic"] });

test("money is calculated in exact integer cents, with invalid values rejected", () => {
  assert.equal(cents("0.10"), 10);
  for (const value of [0, -1, true, null, {}, "1e2", "100..", "1.001", Infinity, NaN, "1000001"]) assert.throws(() => cents(value));
  const items = [item("tops", "0.10"), item("bottoms", "0.20"), item("shoes", "0.30")];
  assert.equal(validateOutfit(items, "0.60").remaining_cents, 0);
  assert.throws(() => validateOutfit(items, "0.59"), { code: "over_budget" });
});
test("outfits retain original catalog prices and omit absent links", () => {
  const result = makeOutfit({ style: "casual", budget: "100" }, catalog);
  assert.equal(result.total_cents, 7400);
  assert.equal(result.remaining_cents, 2600);
  assert.deepEqual(result.items.map(i => i.id), ["lst_020", "lst_001", "lst_035"]);
  assert.ok(result.items.every(i => !i.url && cents(catalog.find(c => c.id === i.id).price) === i.price_cents));
});
test("every selectable style has a complete result when budget permits", () => {
  for (const style of styles) {
    const result = makeOutfit({ style, budget: "150" }, catalog);
    assert.equal(result.items.length, 3);
    assert.ok(result.within_budget && result.total_cents <= 15000);
  }
});
test("separate sizes stay in place; impossible choices do not relax filters", () => {
  const result = makeOutfit({ style: "casual", budget: 100, sizes: { tops: "M", bottoms: "W30", shoes: "US 9" } }, catalog);
  assert.equal(result.items[0].size, "M");
  assert.ok(["W30", "W30 L30"].includes(result.items[1].size));
  assert.equal(result.items[2].size, "US 9");
  assert.throws(() => makeOutfit({ style: "casual", budget: 100, sizes: { shoes: "US 12" } }, catalog), { code: "no_valid_products" });
  assert.throws(() => makeOutfit({ style: "casual", budget: 1 }, catalog), { code: "no_valid_products" });
});
test("incomplete, missing-price, unavailable and foreign-currency fixtures fail closed", () => {
  const items = [item("tops", 10), item("bottoms", 20), item("shoes", 30)];
  for (const change of [{ price: null }, { available: false }, { currency: "EUR" }]) assert.throws(() => validateOutfit([{ ...items[0], ...change }, ...items.slice(1)], 100));
  assert.throws(() => validateOutfit(items.slice(0, 2), 100));
  assert.throws(() => validateOutfit([{ ...items[0], id: "same" }, { ...items[1], id: "same" }, items[2]], 100));
});
