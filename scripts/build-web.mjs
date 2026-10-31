import { mkdir, readFile, writeFile, cp } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.join(root, "dist");
await mkdir(dist, { recursive: true });
await cp(path.join(root, "web"), dist, { recursive: true });
const catalog = JSON.parse(await readFile(path.join(root, "data/listings.json"), "utf8"));
if (!Array.isArray(catalog) || !catalog.length) throw new Error("The catalog is missing.");
await writeFile(path.join(dist, "catalog.json"), JSON.stringify(catalog));
console.log(`Built FitFindr website with ${catalog.length} original sample listings.`);
