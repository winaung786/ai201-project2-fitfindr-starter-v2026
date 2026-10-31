import { makeOutfit } from "../web/assets/outfit-engine.mjs";
let data = "";
for await (const chunk of process.stdin) data += chunk;
const { cases, catalog } = JSON.parse(data);
console.log(JSON.stringify(cases.map(input => {
  try { const r = makeOutfit(input, catalog); return { ids: r.items.map(i => i.id), total: r.total_cents, remaining: r.remaining_cents }; }
  catch (error) { return { error: error.code }; }
})));
