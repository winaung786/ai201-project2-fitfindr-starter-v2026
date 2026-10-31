// Browser-local companion to the existing Python agent, using the same catalog,
// integer-cent validation, ranking and complete-outfit rules. No model calls.
export class OutfitError extends Error {
  constructor(code, message) { super(message); this.code = code; }
}
export const categories = ["tops", "bottoms", "shoes"];
export const styles = ["casual", "minimal", "vintage", "streetwear", "y2k", "earth tones"];
export function cents(value) {
  if (!["string", "number"].includes(typeof value) || !/^\d+(?:\.\d{1,2})?$/.test(String(value).trim())) {
    throw new OutfitError("invalid_price", "Enter a budget in US dollars, with no more than two decimal places.");
  }
  const [whole, fraction = ""] = String(value).trim().split(".");
  const amount = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
  if (!Number.isSafeInteger(amount) || amount <= 0 || amount > 100000000) {
    throw new OutfitError("invalid_price", "Choose a budget between $0.01 and $1,000,000.");
  }
  return amount;
}
export const dollars = value => `${Math.floor(value / 100)}.${String(value % 100).padStart(2, "0")}`;
export const money = value => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: value % 100 ? 2 : 0 }).format(value / 100);

function pricedItem(item) {
  if (!item || ["id", "title", "category", "size", "platform"].some(k => typeof item[k] !== "string" || !item[k].trim())) {
    throw new OutfitError("invalid_listing", "This item is missing listing information.");
  }
  if ((item.currency ?? "USD") !== "USD") throw new OutfitError("unsupported_currency", "Only US dollar prices can be compared.");
  if (item.available === false || ["sold", "unavailable", "out_of_stock"].includes(item.availability)) {
    throw new OutfitError("unavailable_item", "This item is unavailable.");
  }
  const amount = cents(item.price);
  const result = Object.fromEntries(["id", "title", "category", "size", "platform"].map(k => [k, item[k]]));
  Object.assign(result, { price: dollars(amount), price_cents: amount, currency: "USD" });
  try {
    if (typeof item.url === "string") {
      const url = new URL(item.url);
      if (url.protocol === "https:" && url.hostname && !url.username && !url.password) result.url = item.url;
    }
  } catch { /* A missing or malformed product URL stays absent. */ }
  return result;
}

export function validateOutfit(items, budget) {
  const limit = cents(budget);
  const checked = items.map(pricedItem);
  if (checked.length !== 3 || categories.some(c => checked.filter(i => i.category === c).length !== 1)) {
    throw new OutfitError("incomplete_outfit", "A complete look needs a top, bottoms, and shoes.");
  }
  if (new Set(checked.map(i => i.id)).size !== 3) throw new OutfitError("duplicate_item", "An item cannot be counted twice.");
  const total = checked.reduce((sum, item) => sum + item.price_cents, 0);
  if (total > limit) throw new OutfitError("over_budget", "We couldn’t find a complete look within this budget. Try a higher budget or a different style.");
  return { items: checked, currency: "USD", budget_cents: limit, total_cents: total, remaining_cents: limit - total,
    budget: dollars(limit), total: dollars(total), remaining: dollars(limit - total), within_budget: true,
    source: "bundled_sample_catalog", notice: "Sample catalog preview; prices and availability are not live. Merchandise subtotal only; tax and shipping are excluded. Check listing sizes before buying." };
}

const stopWords = new Set(["a", "an", "and", "for", "i", "in", "looking", "me", "of", "the", "want", "with"]);
const itemWords = new Set(["tee", "jacket", "skirt", "boot", "jean", "pant", "top", "shirt", "dress", "hoodie", "sneaker", "bag", "belt", "cardigan", "blazer", "vest", "trouser", "sweatshirt", "hat", "flannel", "polo", "short"]);
const aliases = { tees: "tee", tshirt: "tee", tshirts: "tee", jeans: "jean", pants: "pant", boots: "boot", sneakers: "sneaker", trousers: "trouser", shorts: "short" };
function words(text) { return new Set((text.toLowerCase().replaceAll("t-shirt", "tee").match(/[a-z0-9]+/g) ?? []).filter(w => !stopWords.has(w)).map(w => aliases[w] ?? w)); }
const overlap = (a, b) => [...a].filter(w => b.has(w)).length;
const union = (...sets) => new Set(sets.flatMap(s => [...s]));
const escapeRegex = text => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
function sizeMatches(wanted, actual) {
  const alphabetic = ["XXS", "XS", "S", "M", "L", "XL", "XXL"].includes(wanted.trim().toUpperCase());
  const edge = alphabetic ? "A-Z" : "A-Z0-9.";
  return new RegExp(`(?<![${edge}])${escapeRegex(wanted.trim().toUpperCase())}(?![${edge}])`).test(actual.toUpperCase());
}
const lexical = (a, b) => a < b ? -1 : a > b ? 1 : 0;

function search(description, size, limit, category, catalog) {
  const query = words(description);
  const scored = [];
  for (const item of catalog) {
    let valid;
    try { valid = pricedItem(item); } catch { continue; }
    if (valid.category !== category || valid.price_cents > limit || size && !sizeMatches(size, item.size)) continue;
    const title = words(item.title), tags = words((item.style_tags ?? []).join(" "));
    const other = words([item.description, item.category, (item.colors ?? []).join(" "), item.brand ?? ""].join(" "));
    const garmentWords = new Set([...query].filter(w => itemWords.has(w)));
    if (garmentWords.size && !overlap(garmentWords, union(title, tags))) continue;
    const score = 3 * overlap(query, title) + 2 * overlap(query, tags) + overlap(query, other);
    if (score) scored.push({ score, item, amount: valid.price_cents });
  }
  scored.sort((a, b) => b.score - a.score || a.amount - b.amount || lexical(a.item.id, b.item.id));
  return scored.slice(0, 10).map(row => row.item);
}

export function makeOutfit(input, catalog) {
  const limit = cents(input.budget);
  if (!styles.includes(input.style)) throw new OutfitError("invalid_input", "Choose one of the available styles.");
  const sizes = input.sizes ?? {};
  if (!sizes || Array.isArray(sizes) || typeof sizes !== "object" || Object.entries(sizes).some(([k, v]) => !categories.includes(k) || typeof v !== "string" || !v.trim() || v.length > 32)) {
    throw new OutfitError("invalid_input", "Choose a separate size for each clothing category.");
  }
  const description = input.style === "casual" ? "classic basics streetwear" : input.style;
  const pools = categories.map(category => search(description, sizes[category], limit, category, catalog));
  const missing = pools.findIndex(p => !p.length);
  if (missing !== -1) throw new OutfitError("no_valid_products", `We couldn’t find matching ${{tops: "tops", bottoms: "bottoms", shoes: "shoes"}[categories[missing]]}. Try another style, budget, or size.`);
  let winner;
  for (const [a, top] of pools[0].entries()) for (const [b, bottom] of pools[1].entries()) for (const [c, shoe] of pools[2].entries()) {
    const items = [top, bottom, shoe];
    if (new Set(items.map(i => i.id)).size !== 3) continue;
    const total = items.reduce((sum, i) => sum + cents(i.price), 0);
    if (total > limit) continue;
    const tags = items.map(i => new Set(i.style_tags ?? []));
    const shared = overlap(tags[0], tags[1]) + overlap(tags[0], tags[2]) + overlap(tags[1], tags[2]);
    const rank = a + b + c - shared, ids = items.map(i => i.id).join("\0");
    if (!winner || rank < winner.rank || rank === winner.rank && (total < winner.total || total === winner.total && lexical(ids, winner.ids) < 0)) winner = { items, rank, total, ids };
  }
  if (!winner) throw new OutfitError("over_budget", "We couldn’t find a complete look within this budget. Try a higher budget or a different style.");
  return validateOutfit(winner.items, input.budget);
}
