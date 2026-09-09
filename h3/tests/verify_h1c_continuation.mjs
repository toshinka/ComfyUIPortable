import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveHistoryScalars } from "../app/static/history-settings.js";
import { validateContinuationSource } from "../app/static/continuation-source.js";

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
const request = {
  prompt: "A retained source prompt",
  width: 608,
  height: 352,
  duration: 5,
  seed: 24680,
  steps: 20,
};
const completed = {
  state: "COMPLETED",
  job_id: "source-job-1",
  video_url: "/api/jobs/source-job-1/video",
  request,
  references: { start_frame: { id: "old-start" }, end_frame: { id: "old-end" } },
};

assert.equal(validateContinuationSource(completed), "/api/jobs/source-job-1/video");
assert.throws(
  () => validateContinuationSource({ ...completed, video_url: "https://example.invalid/video.mp4" }),
  /same-origin/,
);
assert.throws(
  () => validateContinuationSource({ ...completed, video_url: "file:///D:/video.mp4" }),
  /same-origin/,
);
assert.throws(
  () => validateContinuationSource({ ...completed, video_url: "/api/jobs/other-job/video" }),
  /same-origin/,
);
assert.throws(
  () => validateContinuationSource({ ...completed, video_url: "/api/jobs/source-job-1/video?raw=1" }),
  /same-origin/,
);
assert.throws(
  () => validateContinuationSource({ ...completed, video_url: null }),
  /unavailable/,
);
assert.throws(
  () => validateContinuationSource({ ...completed, state: "FAILED" }),
  /completed/,
);
assert.throws(
  () => validateContinuationSource({ ...completed, job_id: "../source-job-1" }),
  /source History job is invalid/,
);

const scalarSettings = resolveHistoryScalars(completed, options);
assert.deepEqual(scalarSettings, {
  prompt: request.prompt,
  resolution: "608x352",
  duration: "5",
  seed: "24680",
  steps: "20",
});
assert.equal(scalarSettings.seed, "24680");
assert.throws(
  () => resolveHistoryScalars({ ...completed, request: { ...request, seed: "random" } }, options),
  /safe numeric value/,
);
assert.throws(
  () => resolveHistoryScalars({ ...completed, request: { ...request, width: 1024 } }, options),
  /Resolution cannot be restored/,
);
assert.throws(
  () => resolveHistoryScalars({ ...completed, request: { ...request, steps: 24 } }, options),
  /Steps cannot be restored/,
);

for (const marker of [
  'import { resolveHistorySettings } from "./history-settings.js";',
  'import { resolveHistoryScalars } from "./history-settings.js";',
  'import { validateContinuationSource } from "./continuation-source.js";',
  'continueButton.textContent = "Continue"',
  'entry.state === "COMPLETED" && typeof entry.video_url === "string" && entry.video_url.trim()',
  'continueButton.title = "Use this result\'s end frame as the next Start Frame."',
  'video.currentTime = Math.max(0, video.duration - 0.05)',
  'canvas.width = video.videoWidth',
  'canvas.height = video.videoHeight',
  'canvas.toBlob',
  '"image/png"',
  'body.append("slot", "start_frame")',
  'requestJson("/api/references", { method: "POST", body })',
  'setReferenceSlotView("start_frame", settings.reference)',
  'setReferenceSlotView("end_frame", null)',
  'Continuation prepared. Edit the prompt if needed, then Generate.',
  'Continuation was not prepared.',
]) {
  assert.ok(app.includes(marker), `H1C app marker missing: ${marker}`);
}
for (const marker of [
  'id="history-action-status"',
  'type="module" src="/static/app.js"',
]) {
  assert.ok(html.includes(marker), `H1C HTML marker missing: ${marker}`);
}
for (const marker of [
  ".history-actions",
  ".history-content .history-use-settings",
  ".history-content .history-continue",
  ".history-action-status",
]) {
  assert.ok(styles.includes(marker), `H1C CSS marker missing: ${marker}`);
}

const card = app.slice(app.indexOf("function createHistoryCard"), app.indexOf("async function loadHistory"));
assert.ok(card.indexOf('entry.state === "COMPLETED"') >= 0);
assert.ok(card.indexOf('continueButton.className = "quiet-button history-continue"') >= 0);
assert.ok(card.indexOf("actions.append(useSettings)") < card.indexOf("actions.append(continueButton)"));

const preparation = app.slice(app.indexOf("async function prepareContinuation"), app.indexOf("function createHistoryCard"));
const preparationOrder = [
  "resolveHistoryScalars(entry, historyScalarOptions())",
  "validateContinuationSource(entry)",
  "captureContinuationFrame(sourceUrl)",
  "uploadContinuationReference(frame, entry.job_id)",
  "applyContinuationSettings({ ...scalarSettings, reference })",
];
for (let index = 1; index < preparationOrder.length; index += 1) {
  assert.ok(
    preparation.indexOf(preparationOrder[index - 1]) < preparation.indexOf(preparationOrder[index]),
    `H1C preparation order broken before ${preparationOrder[index]}`,
  );
}
assert.equal(preparation.includes("/api/generate"), false);
assert.equal(preparation.includes("state.activeJob ="), false);
assert.equal(preparation.includes("state.previewJob ="), false);
assert.equal(preparation.includes("showPreviewJob"), false);
assert.equal(app.includes("continuationJob"), false);
assert.equal(app.includes("segmentJob"), false);
assert.equal(app.includes("selectedContinuationJob"), false);

const apply = app.slice(app.indexOf("function applyContinuationSettings"), app.indexOf("async function prepareContinuation"));
assert.ok(apply.includes("const before = snapshotFormSettings()"));
assert.ok(apply.includes("restoreFormSettings(before)"));
assert.ok(apply.includes('setReferenceSlotView("end_frame", null)'));

console.log("H1C frame-bridged continuation source+logic smoke: 38 PASS");
