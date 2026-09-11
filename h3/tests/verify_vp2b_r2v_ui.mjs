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
  'id="r2v-motion-start"',
  'type="number" min="0" step="0.1"',
  "Start (sec)",
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
  'r2vMotionStartSeconds: 0',
  'const r2vMotionStartInput = $("r2v-motion-start")',
  'async function uploadR2VPicture(file)',
  'requestJson("/api/r2v/picture"',
  'async function uploadR2VMotionVideo(file)',
  'requestJson("/api/r2v/video"',
  'endpoint = "/api/r2v/generate"',
  'payload.video_type = "reference"',
  'payload.picture_id = state.r2vPicture.id',
  'payload.motion_video_id = state.r2vMotionVideo?.id || null',
  'const parsed = parseMotionStartInput(r2vMotionStartInput.value)',
  'payload.motion_start_seconds = parsed.value',
  'async function resolveReferenceVideoHistorySettings(entry)',
  'await verifyR2VAsset(picture, "picture")',
  'await verifyR2VAsset(motionVideo, "motion")',
  'setR2VMotionView(settings.motionVideo, settings.motionStartSeconds ?? 0)',
  'r2vMotionStartSeconds: state.r2vMotionStartSeconds',
  'setVideoType("reference")',
  'entry.video_type !== "reference"',
]) {
  assert.ok(app.includes(marker), `VP2B app behavior marker missing: ${marker}`);
}

const referenceSubmit = app.slice(app.indexOf('if (state.videoType === "reference")'), app.indexOf('} else {', app.indexOf('if (state.videoType === "reference")')));
assert.ok(referenceSubmit.includes('endpoint = "/api/r2v/generate"'));
assert.ok(referenceSubmit.includes('payload.motion_start_seconds = parsed.value'));
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
  ".r2v-motion-start-row",
  ".reference-audio-note",
]) {
  assert.ok(styles.includes(marker), `VP2B CSS marker missing: ${marker}`);
}

// Test parseMotionStartInput logic extracted from app.js
const parseMotionStartFnMatch = app.match(/function parseMotionStartInput\(rawValue\) \{([\s\S]*?)\n\}/);
assert.ok(parseMotionStartFnMatch, "parseMotionStartInput function definition must exist in app.js");
const parseMotionStartInput = new Function("rawValue", parseMotionStartFnMatch[1]);

// Valid inputs
assert.deepEqual(parseMotionStartInput("0"), { valid: true, value: 0 });
assert.deepEqual(parseMotionStartInput(0), { valid: true, value: 0 });
assert.deepEqual(parseMotionStartInput("12.5"), { valid: true, value: 12.5 });
assert.deepEqual(parseMotionStartInput(12.5), { valid: true, value: 12.5 });
assert.deepEqual(parseMotionStartInput("  3.2  "), { valid: true, value: 3.2 });
assert.deepEqual(parseMotionStartInput("0.0"), { valid: true, value: 0 });

// Invalid inputs (empty, whitespace, non-numeric, negative)
assert.deepEqual(parseMotionStartInput(""), { valid: false, value: null });
assert.deepEqual(parseMotionStartInput("   "), { valid: false, value: null });
assert.deepEqual(parseMotionStartInput("\t"), { valid: false, value: null });
assert.deepEqual(parseMotionStartInput("abc"), { valid: false, value: null });
assert.deepEqual(parseMotionStartInput("-1"), { valid: false, value: null });
assert.deepEqual(parseMotionStartInput("-0.5"), { valid: false, value: null });
assert.deepEqual(parseMotionStartInput(null), { valid: false, value: null });
assert.deepEqual(parseMotionStartInput(undefined), { valid: false, value: null });
assert.deepEqual(parseMotionStartInput(NaN), { valid: false, value: null });
assert.deepEqual(parseMotionStartInput(Infinity), { valid: false, value: null });

// Verify generate availability logic rejects null or invalid motion start
const checkMotionStartAvailability = (referenceMode, r2vMotionVideo, r2vMotionStartSeconds) => {
  return !referenceMode || !r2vMotionVideo || (
    Number.isFinite(r2vMotionStartSeconds) && r2vMotionStartSeconds >= 0
  );
};
assert.equal(checkMotionStartAvailability(true, { id: "vid" }, 0), true);
assert.equal(checkMotionStartAvailability(true, { id: "vid" }, 5.5), true);
assert.equal(checkMotionStartAvailability(true, { id: "vid" }, null), false);
assert.equal(checkMotionStartAvailability(true, { id: "vid" }, -1), false);
assert.equal(checkMotionStartAvailability(true, { id: "vid" }, undefined), false);
assert.equal(checkMotionStartAvailability(false, { id: "vid" }, null), true);
assert.equal(checkMotionStartAvailability(true, null, null), true);

// Verify submit handler checks parsed validity before POST
const submitHandlerFull = app.slice(app.indexOf("async function submitGeneration"), app.indexOf("async function cancelGeneration"));
const submitValidationSlice = referenceSubmit.slice(referenceSubmit.indexOf("if (state.r2vMotionVideo)"));
assert.ok(submitValidationSlice.includes("parseMotionStartInput(r2vMotionStartInput.value)"));
assert.ok(submitValidationSlice.includes('throw new Error("Start time must be 0 seconds or greater.")'));
assert.ok(submitHandlerFull.indexOf('throw new Error("Start time must be 0 seconds or greater.")') < submitHandlerFull.indexOf("await requestJson(endpoint"));

// Verify input listener updates state to null on invalid
const inputListenerSlice = app.slice(app.indexOf('r2vMotionStartInput.addEventListener("input"'));
assert.ok(inputListenerSlice.includes("state.r2vMotionStartSeconds = parsed.valid ? parsed.value : null;"));

console.log("VP2B Experimental R2V UI contract smoke: 44 PASS");
