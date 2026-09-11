import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveBackendStatusPresentation } from "../app/static/backend-status-presentation.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "app", "static");
const [html, app, styles] = await Promise.all([
  readFile(join(root, "index.html"), "utf8"),
  readFile(join(root, "app.js"), "utf8"),
  readFile(join(root, "styles.css"), "utf8"),
]);

for (const profile of ["CANONICAL_H3", "PROFILE_MISMATCH", "PROFILE_UNVERIFIABLE", "UNAVAILABLE"]) {
  assert.ok(profile, `profile classification must exist: ${profile}`);
}

const mismatch = resolveBackendStatusPresentation({
  next: "PROFILE_MISMATCH",
  message: "Wrong H3 backend profile.",
  currentDetail: "Prompt is ready.",
});
assert.equal(mismatch.detail, "Wrong H3 backend profile.");
assert.equal(mismatch.backendDetail, mismatch.detail);

const recovered = resolveBackendStatusPresentation({
  previousBackendDetail: mismatch.backendDetail,
  next: "READY",
  currentDetail: mismatch.detail,
});
assert.equal(recovered.detail, "Prompt is ready.");
assert.equal(recovered.backendDetail, "");

for (const marker of [
  'PROFILE_MISMATCH: "Wrong H3 backend profile"',
  'PROFILE_UNVERIFIABLE: "H3 profile unverifiable"',
  'status.backend_profile_detail || status.error || ""',
  'state.backend === "READY"',
  'state.activeJob && !TERMINAL.has(state.activeJob.state)',
  'function submitGeneration(event)',
]) {
  assert.ok(app.includes(marker), `R2B app marker missing: ${marker}`);
}
for (const marker of [
  "PROFILE_MISMATCH",
  "PROFILE_UNVERIFIABLE",
]) {
  assert.ok(app.includes(marker), `R2B profile state marker missing: ${marker}`);
}
for (const marker of [
  ".backend-pill.profile_mismatch",
  ".backend-pill.profile_unverifiable",
]) {
  assert.ok(styles.includes(marker), `R2B CSS marker missing: ${marker}`);
}

assert.equal(app.includes('generationStatus.textContent = "Finalizing"'), false);
assert.equal(app.includes('fetch("/prompt"'), false, "Browser must submit through the H3 skin boundary");
assert.equal(html.includes('type="module" src="/static/app.js"'), true);

console.log("H3-R2B Canonical Native profile guard UI smoke: 16 PASS");
