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
  'id="end-reference-file"',
  'id="end-reference-add"',
  'id="end-reference-thumbnail"',
  'id="end-reference-replace"',
  'id="end-reference-remove"',
  'id="reference-empty">No keyframes selected',
  'accept="image/png,image/jpeg,image/webp',
]) {
  assert.ok(html.includes(marker), `Reference UI marker missing: ${marker}`);
}

for (const marker of [
  'body.append("slot", slot)',
  'body.append("reference", file, file.name)',
  'fetch("/api/references"',
  'setReferenceSlotView(slot, result.reference)',
  'setReferenceView(null)',
  'endReferenceRemove.addEventListener',
  'references: {',
  'start_frame: state.references.start_frame',
  'end_frame: state.references.end_frame',
  'job.references?.start_frame && job.references?.end_frame',
  'const routeLabel = job.route_label',
]) {
  assert.ok(app.includes(marker), `H1B browser behavior missing: ${marker}`);
}

assert.equal(app.includes('value="T2V"'), false, "No explicit route selector is allowed.");
assert.equal(app.includes('value="I2V"'), false, "No explicit route selector is allowed.");
assert.equal(app.includes("fallback"), false, "I2V must not silently fall back to T2V.");
console.log("H1B.1 UI smoke: 23 PASS");
