import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveStillHistorySettings } from "../app/static/still-history-settings.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "app", "static");
const [html, app, styles] = await Promise.all([
  readFile(join(root, "index.html"), "utf8"),
  readFile(join(root, "app.js"), "utf8"),
  readFile(join(root, "styles.css"), "utf8"),
]);

for (const marker of [
  'id="mode-video"',
  'id="mode-still"',
  'id="brand-mode"',
  'id="preview-image"',
  'id="still-source-card"',
  'id="still-source-file"',
  'accept="image/png,image/jpeg,.png,.jpg,.jpeg"',
  'id="duration-field"',
]) {
  assert.ok(html.includes(marker), `H2C HTML marker missing: ${marker}`);
}
assert.ok(html.indexOf('id="generate-button"') < html.indexOf('class="advanced-panel"'));
assert.equal(html.includes("image/webp,.webp"), false, "Still source must not advertise WebP.");

for (const marker of [
  'mode: "video"',
  'stillSource: null',
  'function setMode(nextMode)',
  'videoReferenceCard.hidden = still',
  'stillSourceCard.hidden = !still',
  'durationField.hidden = still',
  'async function uploadStillSource(file)',
  'requestJson("/api/still/source"',
  'endpoint = "/api/still/generate"',
  'payload.source_id = state.stillSource.id',
  'job.media_kind === "still"',
  'job.image_url',
  'function verifyStillSource(source)',
  'resolveStillHistorySettings(entry',
  'entry.media_kind === "still"',
  'kindBadge.textContent = isStill ? "Still" : "Video"',
  '!isStill && entry.state === "COMPLETED"',
  'activeJob: null',
  'previewJob: null',
  'state.activeJob?.job_id',
]) {
  assert.ok(app.includes(marker), `H2C app behavior missing: ${marker}`);
}
const modeHandler = app.slice(app.indexOf("function setMode"), app.indexOf("function updateGenerateAvailability"));
assert.equal(modeHandler.includes("fetch("), false, "Mode switch must remain UI-only.");
assert.equal(modeHandler.includes("/api/generate"), false, "Mode switch must not submit generation.");
assert.equal(app.includes('setReferenceSlotView("start_frame", state.stillSource'), false);

for (const marker of [
  "--surface-rose",
  "--surface-cream",
  "--surface-paper",
  ".mode-switch",
  ".mode-button.active",
  ".preview-image",
  "object-fit: contain",
  ".history-image",
  ".history-kind-badge",
]) {
  assert.ok(styles.includes(marker), `H2C CSS marker missing: ${marker}`);
}

const sourceId = "a".repeat(32);
const source = { id: sourceId, width: 608, height: 352 };
const request = {
  prompt: "A small paper robot in warm light",
  width: 608,
  height: 352,
  seed: 20260910,
  steps: 20,
  source_id: sourceId,
};
const verified = [];
const anchored = await resolveStillHistorySettings(
  { media_kind: "still", request, source },
  {
    resolutionValues: ["608x352"],
    stepsValue: "20",
    verifySource: async (value) => verified.push(value.id),
  },
);
assert.equal(anchored.prompt, request.prompt);
assert.equal(anchored.resolution, "608x352");
assert.equal(anchored.seed, "20260910");
assert.equal(anchored.steps, "20");
assert.equal(anchored.source.id, sourceId);
assert.deepEqual(verified, [sourceId]);

const promptOnly = await resolveStillHistorySettings(
  {
    media_kind: "still",
    request: { ...request, source_id: null },
    source: null,
  },
  { resolutionValues: ["608x352"], stepsValue: "20" },
);
assert.equal(promptOnly.source, null);

const losslessSeed = "4121755688520062686";
const lossless = await resolveStillHistorySettings(
  {
    media_kind: "still",
    request: { ...request, seed: losslessSeed },
    source,
  },
  { resolutionValues: ["608x352"], stepsValue: "20", verifySource: async () => {} },
);
assert.equal(lossless.seed, losslessSeed);

await assert.rejects(
  resolveStillHistorySettings(
    { media_kind: "still", request, source },
    { resolutionValues: ["608x352"], stepsValue: "20", verifySource: async () => { throw new Error("missing"); } },
  ),
  /missing/,
);
await assert.rejects(
  resolveStillHistorySettings(
    { media_kind: "still", request: { ...request, duration: 1 }, source },
    { resolutionValues: ["608x352"], stepsValue: "20", verifySource: async () => {} },
  ),
  /Duration/,
);
await assert.rejects(
  resolveStillHistorySettings(
    { media_kind: "still", request: { ...request, source_id: "../escape" }, source: { id: "../escape" } },
    { resolutionValues: ["608x352"], stepsValue: "20", verifySource: async () => {} },
  ),
  /metadata is invalid/,
);

console.log("H2C Still UI source+logic smoke: 52 PASS");
