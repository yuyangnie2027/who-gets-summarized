import { readFile, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { CORPUS_STATS, SOURCE, TURNS } from "../dist/src/data.js";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const required = [
  "dist/index.html",
  "dist/styles.css",
  "dist/src/app.js",
  "dist/src/data.js",
  "dist/src/engine.js",
  "docs/METHODOLOGY.md",
  "docs/PORTFOLIO_STATEMENT.md",
  "docs/DEMO_SCRIPT.md",
  "docs/RESEARCH_NOTES.md",
  "scripts/fetch-source.mjs",
  "test/engine.test.mjs",
];

for (const path of required) {
  const info = await stat(resolve(root, path));
  if (!info.isFile() || info.size === 0) throw new Error(`Missing or empty: ${path}`);
}

const html = await readFile(resolve(root, "dist/index.html"), "utf8");
const css = await readFile(resolve(root, "dist/styles.css"), "utf8");
const app = await readFile(resolve(root, "dist/src/app.js"), "utf8");
const engine = await readFile(resolve(root, "dist/src/engine.js"), "utf8");

const externalAssets = [...html.matchAll(/(?:src|href)=["'](https?:\/\/[^"']+)/g)]
  .map((match) => match[1]);
const unexpectedDomains = externalAssets.filter((url) => !url.includes("legco.gov.hk"));
if (unexpectedDomains.length) {
  throw new Error(`Unexpected external link or asset: ${unexpectedDomains.join(", ")}`);
}

if (!app.includes("AUTHOR-REVIEWED PARAPHRASE") || !app.includes("PAGE-LINKED")) {
  throw new Error("Paraphrase disclosure is missing from the interface");
}
if (!(html.includes("What is this?") || html.includes("What is this for?")) || !html.includes("Official Record of Proceedings")) {
  throw new Error("Purpose or primary-source statement is missing");
}
if (!html.includes("“") || !html.includes("”")) {
  throw new Error("Visible English quotations must use curly quotation marks");
}
if (!html.includes("aria-live") || !css.includes("prefers-reduced-motion")) {
  throw new Error("Expected accessibility affordances are missing");
}
if (/fetch\s*\(|XMLHttpRequest|WebSocket/.test(app)) {
  throw new Error("Runtime interface must not make remote requests");
}
for (const term of ["tfidfVectors", "jensenShannonDivergence", "stabilityAnalysis", "paretoAlternatives"]) {
  if (!engine.includes(term)) throw new Error(`Advanced method missing: ${term}`);
}

const words = TURNS.reduce((sum, turn) => sum + turn.words, 0);
if (TURNS.length !== 14 || words !== 3463 || CORPUS_STATS.speakers !== 7) {
  throw new Error("Derived corpus totals do not match the documented source record");
}
if (!/^https:\/\/www\.legco\.gov\.hk\//.test(SOURCE.officialRecordUrl)) {
  throw new Error("Official source URL is invalid");
}
if (!/^[a-f0-9]{64}$/.test(SOURCE.sourceSha256)) {
  throw new Error("Source checksum is invalid");
}

console.log(`Validated ${required.length} authored files.`);
console.log("Verified transparent browser runtime and official source links.");
console.log("Verified purpose, provenance, paraphrase disclosure, advanced methods and accessibility.");
