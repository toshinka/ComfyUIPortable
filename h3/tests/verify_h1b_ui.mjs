import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "app", "static");
const [html, app] = await Promise.all([
  readFile(join(root, "index.html"), "utf8"),
  readFile(join(root, "app.js"), "utf8"),
]);

for (const marker of [
  'id="reference-file"',
  'id="reference-add"',
  'id="reference-thumbnail"',
  'id="reference-replace"',
  'id="reference-remove"',
  'accept="image/png,image/jpeg,image/webp',
]) {
  assert.ok(html.includes(marker), `Reference UI marker missing: ${marker}`);
}

for (const marker of [
  'body.append("reference", file, file.name)',
  'fetch("/api/references"',
  'setReferenceView(result.reference)',
  'referenceRemove.addEventListener',
  'setReferenceView(null)',
  'reference: state.reference ? { id: state.reference.id, role: state.reference.role } : null',
  'const routeLabel = job.route_label || (job.reference_used ? "Start Frame" : "T2V")',
]) {
  assert.ok(app.includes(marker), `H1B browser behavior missing: ${marker}`);
}

assert.equal(app.includes("fallback"), false, "I2V must not silently fall back to T2V.");
console.log("H1B UI smoke: 13 PASS");
