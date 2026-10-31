import { makeOutfit, validateOutfit, money, styles } from "./outfit-engine.mjs";
import { garmentArt } from "./illustrations.mjs";

const $ = id => document.getElementById(id);
const icon = name => `<svg class="icon" aria-hidden="true"><use href="#i-${name}"/></svg>`;
const styleNames = { casual: "Casual & everyday", minimal: "Clean & minimal", vintage: "Vintage inspired", streetwear: "Streetwear", y2k: "A little Y2K", "earth tones": "Warm & earthy" };
const titles = { casual: "An everyday kind of good.", minimal: "Less fuss. More you.", vintage: "A little timeless. A little you.", streetwear: "An easy step into your style.", y2k: "A little throwback. All you.", "earth tones": "A warmer kind of everyday." };
const storageKey = "fitfindr.saved.v1";
let catalog = [], current = null, currentInput = null, saved = [], busy = false, toastTimer;

function announce(message) { $("live-status").textContent = message; }
function toast(message) {
  $("toast").textContent = message;
  $("toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $("toast").hidden = true; }, 5000);
}
function formInput() {
  const sizes = Object.fromEntries(["tops", "bottoms", "shoes"].map(c => [c, $("size-" + c).value]).filter(([, value]) => value));
  return { budget: $("budget").value, style: $("style").value, sizes };
}
function fillForm(input) {
  $("budget").value = input.budget;
  $("style").value = input.style;
  for (const c of ["tops", "bottoms", "shoes"]) $("size-" + c).value = input.sizes?.[c] ?? "";
  $("size-options").open = !!Object.keys(input.sizes ?? {}).length;
}
const fingerprint = (result, input) => `${input.style}|${result.budget_cents}|${result.items.map(i => i.id).sort().join(",")}`;

function loadSaved() {
  try {
    const value = JSON.parse(localStorage.getItem(storageKey) ?? "[]");
    if (!Array.isArray(value)) return [];
    return value.slice(0, 24).filter(entry => {
      try {
        if (!entry || typeof entry.id !== "string" || !styles.includes(entry.input?.style) || !Array.isArray(entry.itemIds)) return false;
        const items = entry.itemIds.map(id => catalog.find(i => i.id === id));
        validateOutfit(items, entry.input.budget);
        return true;
      } catch { return false; }
    });
  } catch { return []; }
}
function persistSaved(next) {
  try { localStorage.setItem(storageKey, JSON.stringify(next)); saved = next; return true; }
  catch { toast("Your browser couldn’t save this look. Allow local storage, then try again."); return false; }
}
function entryResult(entry) { return validateOutfit(entry.itemIds.map(id => catalog.find(i => i.id === id)), entry.input.budget); }
function currentSaved() {
  if (!current) return null;
  return saved.find(entry => fingerprint(entryResult(entry), entry.input) === fingerprint(current, currentInput));
}
function updateSaveButton() {
  const isSaved = !!currentSaved();
  $("save-button").classList.toggle("is-saved", isSaved);
  $("save-button").setAttribute("aria-pressed", String(isSaved));
  $("save-button").querySelector("span").textContent = isSaved ? "Saved" : "Save outfit";
}
function updateSavedCount() {
  $("saved-count").hidden = !saved.length;
  $("saved-count").textContent = saved.length;
  $("nav-saved").setAttribute("aria-label", `Saved outfits${saved.length ? `, ${saved.length} saved` : ""}`);
}

function productCard(item, number) {
  const original = catalog.find(i => i.id === item.id) ?? item;
  const card = document.createElement("article");
  card.className = "product-card";
  card.innerHTML = `<div class="product-art"><span class="piece-index">0${number}</span>${garmentArt(original)}</div><div class="product-meta"><span class="product-category"></span><span class="product-price"></span></div><h3></h3><div class="product-details"><span class="item-size"></span><span class="separator" aria-hidden="true">·</span><span class="platform"></span></div>`;
  card.querySelector(".product-category").textContent = { tops: "The top", bottoms: "The bottoms", shoes: "The shoes" }[item.category];
  card.querySelector(".product-price").textContent = money(item.price_cents);
  card.querySelector("h3").textContent = item.title.replace(/ — /g, " · ");
  card.querySelector(".item-size").textContent = `Size ${item.size}`;
  card.querySelector(".platform").textContent = item.platform;
  if (item.url) {
    const link = document.createElement("a");
    link.className = "listing-link"; link.href = item.url; link.target = "_blank"; link.rel = "noopener noreferrer";
    link.textContent = "View original listing ↗"; card.append(link);
  }
  return card;
}

function renderResult(result, input) {
  current = result; currentInput = structuredClone(input);
  $("result-title").textContent = titles[input.style] ?? "Your next look is here.";
  $("outfit-grid").replaceChildren(...result.items.map((item, i) => productCard(item, i + 1)));
  $("outfit-total").textContent = money(result.total_cents);
  $("of-budget").textContent = `of ${money(result.budget_cents)}`;
  $("budget-remaining").textContent = result.remaining_cents === 0 ? "Right on budget" : `${money(result.remaining_cents)} left to spare`;
  $("budget-fill").style.width = `${result.total_cents / result.budget_cents * 100}%`;
  $("budget-meter").setAttribute("aria-label", `${money(result.total_cents)} of your ${money(result.budget_cents)} budget used; ${money(result.remaining_cents)} remaining.`);
  $("loading-state").hidden = true; $("empty-result").hidden = true; $("outfit-content").hidden = false;
  $("result-panel").setAttribute("aria-busy", "false");
  updateSaveButton();
}

async function buildOutfit({ focus = false } = {}) {
  if (busy || !$("outfit-form").reportValidity()) return;
  busy = true;
  $("form-error").hidden = true;
  $("build-button").disabled = true;
  $("build-button").querySelector(".button-label").textContent = "Finding your fit…";
  $("build-button").querySelector(".icon").hidden = true;
  $("build-button").querySelector(".spinner").hidden = false;
  $("result-panel").setAttribute("aria-busy", "true");
  $("outfit-content").hidden = true; $("empty-result").hidden = true; $("loading-state").hidden = false;
  announce("Finding an outfit within your budget.");
  const input = formInput();
  try {
    let result;
    if (document.body.dataset.transport === "api") {
      const response = await fetch("/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: `${input.style} outfit`, budget: input.budget, sizes: input.sizes }), signal: AbortSignal.timeout(125000) });
      const session = await response.json();
      if (!response.ok || session.error) throw new Error(session.error || "We couldn’t finish that look. Please try again.");
      // Verify the response before presenting it, even when it came from the agent.
      result = validateOutfit(session.budget_result.items, input.budget);
    } else result = makeOutfit(input, catalog);
    renderResult(result, input);
    announce(`Your outfit is ready. Total ${money(result.total_cents)}. ${money(result.remaining_cents)} left in your budget.`);
    if (focus) {
      $("result-title").focus({ preventScroll: true });
      if (matchMedia("(max-width: 800px)").matches) $("result-panel").scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth" });
    }
  } catch (error) {
    current = null; currentInput = null;
    const message = error.name === "TimeoutError" || error.name === "TypeError" ? "We couldn’t reach the outfit builder. Check your connection, then try again." : error.message;
    $("form-error").textContent = message; $("form-error").hidden = false;
    $("outfit-content").hidden = true; $("loading-state").hidden = true; $("empty-result").hidden = false;
    $("result-title").textContent = "Let’s try a different combination.";
    $("result-panel").setAttribute("aria-busy", "false");
    announce(message);
  } finally {
    busy = false;
    $("build-button").disabled = false;
    $("build-button").querySelector(".button-label").textContent = "Build my outfit";
    $("build-button").querySelector(".icon").hidden = false;
    $("build-button").querySelector(".spinner").hidden = true;
  }
}

function renderSaved() {
  updateSavedCount();
  $("saved-empty").hidden = !!saved.length;
  $("saved-privacy").hidden = !saved.length;
  $("saved-grid").replaceChildren(...saved.map(entry => {
    const result = entryResult(entry);
    const card = document.createElement("article"); card.className = "saved-card";
    card.innerHTML = `<div class="saved-card-art"></div><div class="saved-card-top"><h2></h2><span class="saved-card-total"></span></div><p class="saved-card-subtitle"></p><div class="saved-card-bottom"><button class="open-look">View outfit ${icon("arrow")}</button><button class="quiet-button delete-look">${icon("trash")}</button></div>`;
    card.querySelector(".saved-card-art").innerHTML = result.items.map(item => `<div>${garmentArt(catalog.find(i => i.id === item.id), true)}</div>`).join("");
    card.querySelector("h2").textContent = styleNames[entry.input.style];
    card.querySelector(".saved-card-total").textContent = money(result.total_cents);
    card.querySelector(".saved-card-subtitle").textContent = `${money(result.remaining_cents)} left from a ${money(result.budget_cents)} budget`;
    card.querySelector(".open-look").addEventListener("click", () => {
      fillForm(entry.input); renderResult(result, entry.input); $("form-error").hidden = true;
      location.hash = "builder";
      requestAnimationFrame(() => { $("result-title").focus({ preventScroll: true }); $("result-panel").scrollIntoView({ block: "nearest" }); });
    });
    const remove = card.querySelector(".delete-look");
    remove.setAttribute("aria-label", `Remove saved ${styleNames[entry.input.style]} outfit`);
    remove.addEventListener("click", () => {
      const index = saved.findIndex(e => e.id === entry.id);
      if (!persistSaved(saved.filter(e => e.id !== entry.id))) return;
      renderSaved(); updateSaveButton(); toast("Outfit removed from your saved looks.");
      const next = $("saved-grid").children[Math.min(index, saved.length - 1)];
      (next?.querySelector(".open-look") ?? $("saved-empty").querySelector("a")).focus();
    });
    return card;
  }));
}

function navigate() {
  const isSaved = location.hash === "#saved";
  $("builder-view").hidden = isSaved; $("saved-view").hidden = !isSaved;
  for (const name of ["builder", "saved"]) {
    const active = (name === "saved") === isSaved;
    $("nav-" + name).classList.toggle("active", active);
    if (active) $("nav-" + name).setAttribute("aria-current", "page"); else $("nav-" + name).removeAttribute("aria-current");
  }
  if (isSaved) renderSaved();
  document.title = `${isSaved ? "Saved outfits" : "Your style, within reach"} — FitFindr`;
}

$("outfit-form").addEventListener("submit", event => { event.preventDefault(); buildOutfit({ focus: true }); });
$("save-button").addEventListener("click", () => {
  if (!current) return;
  const existing = currentSaved();
  if (existing) {
    if (!persistSaved(saved.filter(e => e.id !== existing.id))) return;
    toast("Outfit removed from your saved looks.");
  } else {
    if (saved.length >= 24) { toast("You’ve saved 24 looks. Remove one to make room for a new favorite."); return; }
    const entry = { id: crypto.randomUUID(), createdAt: new Date().toISOString(), input: structuredClone(currentInput), itemIds: current.items.map(i => i.id) };
    if (!persistSaved([entry, ...saved])) return;
    toast("A good look, kept close. Outfit saved.");
  }
  updateSaveButton(); updateSavedCount();
});
$("copy-button").addEventListener("click", async () => {
  if (!current) return;
  const summary = `My FitFindr look · ${styleNames[currentInput.style]}\n${current.items.map(i => `${i.title} — ${money(i.price_cents)} (size ${i.size})`).join("\n")}\nTotal: ${money(current.total_cents)} · Budget: ${money(current.budget_cents)} · Remaining: ${money(current.remaining_cents)}\nSample catalog preview; tax and shipping excluded. Prices and availability are not live.`;
  try { await navigator.clipboard.writeText(summary); toast("Outfit summary copied. Ready to keep or share."); }
  catch { toast("Copy is unavailable in this browser. Your outfit is still here to view."); }
});
$("about-button").addEventListener("click", () => $("about-dialog").showModal());
$("close-dialog").addEventListener("click", () => $("about-dialog").close());
$("got-it").addEventListener("click", () => $("about-dialog").close());
$("about-dialog").addEventListener("click", event => { if (event.target === $("about-dialog")) { const r = event.target.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) event.target.close(); } });
window.addEventListener("hashchange", navigate);
window.addEventListener("storage", event => { if (event.key === storageKey) { saved = loadSaved(); renderSaved(); updateSaveButton(); } });

try {
  const response = await fetch("/catalog.json", { signal: AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error("Catalog unavailable");
  catalog = await response.json();
  if (!Array.isArray(catalog) || !catalog.length) throw new Error("Catalog unavailable");
  saved = loadSaved(); updateSavedCount(); navigate();
  await buildOutfit();
} catch {
  $("loading-state").hidden = true; $("empty-result").hidden = false;
  $("form-error").textContent = "The sample catalog couldn’t load. Check your connection and refresh the page to try again.";
  $("form-error").hidden = false;
  $("build-button").disabled = true;
  $("result-panel").setAttribute("aria-busy", "false");
}
