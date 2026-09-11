import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveBackendStatusPresentation } from "../app/static/backend-status-presentation.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "app", "static");
const [html, app] = await Promise.all([
  readFile(join(root, "index.html"), "utf8"),
  readFile(join(root, "app.js"), "utf8"),
]);

const unavailable = "Native backend unavailable.";
const healthy = resolveBackendStatusPresentation({
  next: "READY",
  currentDetail: "Prompt is ready.",
});
assert.equal(healthy.detail.includes(unavailable), false, "A: healthy Ready must not show unavailable detail");

const disconnected = resolveBackendStatusPresentation({
  next: "DISCONNECTED",
  message: unavailable,
  currentDetail: "Prompt is ready.",
});
assert.equal(disconnected.detail, unavailable, "B: disconnected detail must remain visible");
assert.equal(disconnected.backendDetail, unavailable, "Disconnected detail must be owned by backend presentation");

const recovered = resolveBackendStatusPresentation({
  previousBackendDetail: disconnected.backendDetail,
  next: "READY",
  currentDetail: disconnected.detail,
});
assert.equal(recovered.detail, "Prompt is ready.", "A/C: Ready must clear stale unavailable detail");
assert.equal(recovered.backendDetail, "", "Ready must release backend detail ownership");

const legitimateError = "History request failed.";
const preserved = resolveBackendStatusPresentation({
  previousBackendDetail: disconnected.backendDetail,
  next: "READY",
  currentDetail: legitimateError,
});
assert.equal(preserved.detail, legitimateError, "D: current non-backend error must remain visible");

const activeJobDetail = "Backend connection lost. Current job status is unknown.";
const activeJobPreserved = resolveBackendStatusPresentation({
  previousBackendDetail: disconnected.backendDetail,
  next: "READY",
  hasActiveJob: true,
  currentDetail: activeJobDetail,
});
assert.equal(activeJobPreserved.detail, activeJobDetail, "Active job detail must not be erased");

assert.equal(app.includes('import { resolveBackendStatusPresentation } from "./backend-status-presentation.js";'), true);
assert.equal(app.includes("backendStatusDetail: \"\""), true);
assert.equal(app.includes("function setStatusDetail(message)"), true);
assert.equal(app.includes("window.setTimeout(pollBackend, 2200)"), true, "Existing backend poll cadence must remain");
assert.equal(app.includes('statusDetail.textContent = "Finalizing"'), false, "Generation vocabulary must remain unchanged");
assert.equal(html.includes('type="module" src="/static/app.js"'), true, "H3 app module must remain mounted");

for (const marker of [
  'state.backend === "READY"',
  'state.activeJob && !TERMINAL.has(state.activeJob.state)',
  'statusDetail.textContent = presentation.detail',
  'state.backendStatusDetail = presentation.backendDetail',
]) {
  assert.ok(app.includes(marker), `R2A1 app behavior marker missing: ${marker}`);
}

console.log("H3-R2A1 Backend reconnect presentation source+logic smoke: 10 PASS");
