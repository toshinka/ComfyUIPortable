import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  ACTIVE_STATUS_COPY,
  PREVIEW_STATUS_COPY,
  activeStatusDetail,
  previewStatusDetail,
} from "../app/static/job-status-copy.js";
import { resolveHistorySettings } from "../app/static/history-settings.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "app", "static");
const [html, app, styles] = await Promise.all([
  readFile(join(root, "index.html"), "utf8"),
  readFile(join(root, "app.js"), "utf8"),
  readFile(join(root, "styles.css"), "utf8"),
]);

const options = {
  resolutionValues: ["608x352"],
  durationValues: ["5"],
  stepsValue: "20",
  maxPromptLength: 4000,
};
const start = { id: "start-id", role: "start_frame", width: 608, height: 352 };
const end = { id: "end-id", role: "end_frame", width: 608, height: 352 };
const request = {
  prompt: "A retained prompt",
  width: 608,
  height: 352,
  duration: 5,
  seed: 20260909,
  steps: 20,
};

for (const [state, expected] of Object.entries(ACTIVE_STATUS_COPY)) {
  assert.equal(activeStatusDetail({ state }), expected, `Active status copy missing for ${state}`);
}
for (const [state, expected] of Object.entries(PREVIEW_STATUS_COPY)) {
  assert.equal(previewStatusDetail({ state }), expected, `Preview status copy missing for ${state}`);
}
assert.match(activeStatusDetail({ state: "CANCELLED" }), /cancelled/i);
assert.doesNotMatch(activeStatusDetail({ state: "CANCELLED" }), /processing/i);
assert.match(activeStatusDetail({ state: "DISCONNECTED" }), /unknown/i);
assert.match(activeStatusDetail({ state: "DISCONNECTED" }), /reconnect/i);
assert.doesNotMatch(activeStatusDetail({ state: "DISCONNECTED" }), /Generate again/i);
assert.doesNotMatch(previewStatusDetail({ state: "DISCONNECTED" }), /Generate again/i);

const verifyCalls = [];
const verifyReference = async (reference, slot) => verifyCalls.push(`${slot}:${reference.id}`);
const textOnly = await resolveHistorySettings({ request, references: { start_frame: null, end_frame: null } }, {
  ...options,
  verifyReference,
});
assert.deepEqual(textOnly.references, { start_frame: null, end_frame: null });
assert.equal(textOnly.prompt, request.prompt);
assert.equal(textOnly.seed, "20260909");
assert.equal(textOnly.steps, "20");

const startOnly = await resolveHistorySettings({ request, references: { start_frame: start, end_frame: null } }, {
  ...options,
  verifyReference,
});
assert.equal(startOnly.references.start_frame.id, "start-id");
assert.equal(startOnly.references.end_frame, null);

const legacyStart = await resolveHistorySettings({ request, reference: start }, {
  ...options,
  verifyReference,
});
assert.equal(legacyStart.references.start_frame.id, "start-id");
assert.equal(legacyStart.references.start_frame.preview_url, "/api/references/start-id");
assert.equal(legacyStart.references.end_frame, null);

const endOnly = await resolveHistorySettings({ request, references: { start_frame: null, end_frame: end } }, {
  ...options,
  verifyReference,
});
assert.equal(endOnly.references.start_frame, null);
assert.equal(endOnly.references.end_frame.id, "end-id");

const both = await resolveHistorySettings({ request, references: { start_frame: start, end_frame: end } }, {
  ...options,
  verifyReference,
});
assert.equal(both.references.start_frame.id, "start-id");
assert.equal(both.references.end_frame.id, "end-id");
assert.deepEqual(verifyCalls, ["start_frame:start-id", "start_frame:start-id", "end_frame:end-id", "start_frame:start-id", "end_frame:end-id"]);

await assert.rejects(
  resolveHistorySettings({ request, references: { start_frame: start, end_frame: end } }, {
    ...options,
    verifyReference: async (_reference, slot) => {
      if (slot === "end_frame") throw new Error("End Frame reference is no longer available.");
    },
  }),
  /End Frame reference is no longer available/,
);
await assert.rejects(
  resolveHistorySettings({ request: { ...request, width: 1024 }, references: { start_frame: null, end_frame: null } }, {
    ...options,
    verifyReference,
  }),
  /Resolution cannot be restored with the current UI/,
);
await assert.rejects(
  resolveHistorySettings({ request: { ...request, seed: "random" }, references: { start_frame: null, end_frame: null } }, {
    ...options,
    verifyReference,
  }),
  /safe numeric value/,
);

for (const marker of [
  'id="history-action-status"',
  'type="module" src="/static/app.js"',
]) {
  assert.ok(html.includes(marker), `P2 HTML marker missing: ${marker}`);
}
for (const marker of [
  'import { activeStatusDetail, previewStatusDetail } from "./job-status-copy.js";',
  'import { resolveHistorySettings } from "./history-settings.js";',
  'const TERMINAL = new Set(["COMPLETED", "FAILED", "CANCELLED"]);',
  'state.activeJob && !TERMINAL.has(state.activeJob.state)',
  'async function verifyHistoryReference(reference, slot)',
  'setReferenceSlotView("start_frame", settings.references.start_frame)',
  'setReferenceSlotView("end_frame", settings.references.end_frame)',
  'useSettings.textContent = "Use settings"',
  'showPreviewJob(entry)',
]) {
  assert.ok(app.includes(marker), `P2 app behavior marker missing: ${marker}`);
}
assert.equal(app.includes("selectedHistoryJob"), false);
assert.equal(app.includes("reuseJob"), false);
assert.equal(app.includes("draftJob"), false);
const useHandler = app.slice(app.indexOf("async function useHistorySettings"), app.indexOf("function createHistoryCard"));
assert.ok(useHandler.indexOf("await resolveHistorySettings") >= 0);
assert.ok(useHandler.indexOf("applyHistorySettings(settings)") > useHandler.indexOf("await resolveHistorySettings"));
assert.equal(useHandler.includes("/api/generate"), false);
assert.equal(useHandler.includes("state.activeJob ="), false);
assert.equal(useHandler.includes("state.previewJob ="), false);
assert.equal(useHandler.includes("showPreviewJob"), false);
assert.ok(app.includes("entry.references"));
assert.ok(app.includes("entry.reference"));
for (const marker of [
  ".history-content .history-use-settings",
  ".history-action-status",
  ".history-action-status.error",
]) {
  assert.ok(styles.includes(marker), `P2 CSS marker missing: ${marker}`);
}

console.log("H1B.1 UX P2 status/history source+logic smoke: 44 PASS");
