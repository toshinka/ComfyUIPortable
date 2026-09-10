import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "app", "static");
const [html, app, styles] = await Promise.all([
  readFile(join(root, "index.html"), "utf8"),
  readFile(join(root, "app.js"), "utf8"),
  readFile(join(root, "styles.css"), "utf8"),
]);

for (const marker of [
  'id="mode-video"',
  'id="mode-still"',
  'id="video-type-card"',
  'id="video-type-standard"',
  'id="video-type-reference"',
  'id="r2v-card"',
  'id="r2v-picture-file"',
  'id="r2v-motion-file"',
  "Appearance reference only — not an identity lock.",
  "Audio reference is disabled; uploaded audio is ignored.",
]) {
  assert.ok(html.includes(marker), `VP2B HTML marker missing: ${marker}`);
}

for (const marker of [
  'videoType: "standard"',
  'function setVideoType(nextType)',
  'videoTypeCard.hidden = state.mode !== "video"',
  'r2vCard.hidden = !showingReference',
  'videoReferenceCard.hidden = state.mode !== "video" || showingReference',
  'async function uploadR2VPicture(file)',
  'requestJson("/api/r2v/picture"',
  'async function uploadR2VMotionVideo(file)',
  'requestJson("/api/r2v/video"',
  'endpoint = "/api/r2v/generate"',
  'payload.video_type = "reference"',
  'payload.picture_id = state.r2vPicture.id',
  'payload.motion_video_id = state.r2vMotionVideo?.id || null',
  'async function resolveReferenceVideoHistorySettings(entry)',
  'await verifyR2VAsset(picture, "picture")',
  'await verifyR2VAsset(motionVideo, "motion")',
  'setVideoType("reference")',
  'entry.video_type !== "reference"',
]) {
  assert.ok(app.includes(marker), `VP2B app behavior marker missing: ${marker}`);
}

const referenceSubmit = app.slice(app.indexOf('if (state.videoType === "reference")'), app.indexOf('} else {', app.indexOf('if (state.videoType === "reference")')));
assert.ok(referenceSubmit.includes('endpoint = "/api/r2v/generate"'));
assert.equal(referenceSubmit.includes('payload.references'), false);

const useHandler = app.slice(app.indexOf("async function useHistorySettings"), app.indexOf("function createHistoryCard"));
assert.ok(useHandler.indexOf("await resolveReferenceVideoHistorySettings(entry)") >= 0);
assert.ok(useHandler.indexOf("setVideoType(\"reference\")") > useHandler.indexOf("await resolveReferenceVideoHistorySettings(entry)"));
assert.equal(useHandler.includes("/api/r2v/generate"), false);
assert.equal(useHandler.includes("state.activeJob ="), false);
assert.equal(useHandler.includes("state.previewJob ="), false);

for (const marker of [
  ".video-type-card",
  ".video-type-button.active",
  ".r2v-card",
  ".reference-audio-note",
]) {
  assert.ok(styles.includes(marker), `VP2B CSS marker missing: ${marker}`);
}

console.log("VP2B Experimental R2V UI contract smoke: 28 PASS");
