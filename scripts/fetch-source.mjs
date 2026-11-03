import { createHash } from "node:crypto";
import { execFile as execFileCallback } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { SOURCE } from "../dist/src/data.js";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const outputDirectory = resolve(root, "tmp/source");
const metadataPath = resolve(outputDirectory, "legco-2024-01-31-orq05.json");
const pdfPath = resolve(outputDirectory, "cm20240131-translate-e.pdf");

const execFile = promisify(execFileCallback);

async function download(url) {
  const { stdout } = await execFile("curl", ["-fsSL", url], {
    encoding: "buffer",
    maxBuffer: 50 * 1024 * 1024,
  });
  return stdout;
}

await mkdir(dirname(metadataPath), { recursive: true });
const metadata = JSON.parse((await download(SOURCE.odataRecordUrl)).toString("utf8"));
const record = metadata.value?.[0];
if (!record || record.RundownID !== SOURCE.rundownId || record.HansardID !== SOURCE.hansardId) {
  throw new Error("The official metadata no longer matches the stored source identity");
}
await writeFile(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`);

const pdfUrl = SOURCE.officialRecordUrl.split("#")[0];
const pdf = await download(pdfUrl);
const checksum = createHash("sha256").update(pdf).digest("hex");
if (checksum !== SOURCE.sourceSha256) {
  throw new Error(`Source checksum changed: expected ${SOURCE.sourceSha256}, received ${checksum}`);
}
await writeFile(pdfPath, pdf);

console.log(JSON.stringify({
  metadataPath,
  pdfPath,
  rundownId: record.RundownID,
  hansardId: record.HansardID,
  checksum,
}, null, 2));
