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
  'data-r2v-dropzone="picture"',
  'data-r2v-dropzone="motion"',
  'id="r2v-picture-file"',
  'id="r2v-motion-file"',
  "Drop one local image here",
  "Drop one local MP4 here",
]) {
  assert.ok(html.includes(marker), `VP2C HTML marker missing: ${marker}`);
}

for (const marker of [
  "handoffInFlight: false",
  "function isFileDrag(event)",
  "function singleDroppedFile(event, label)",
  "file instanceof File",
  "function installR2VDropzone(dropzone, label, upload)",
  "event.preventDefault()",
  "dropzone.classList.add(\"drag-active\")",
  "dropzone.classList.remove(\"drag-active\")",
  "await upload(singleDroppedFile(event, label))",
  'installR2VDropzone(r2vPictureDropzone, "Character Image", uploadR2VPicture)',
  'installR2VDropzone(r2vMotionDropzone, "Motion Video", uploadR2VMotionVideo)',
  "function generationIsActive()",
  "function snapshotR2VHandoffState()",
  "function restoreR2VHandoffState(snapshot)",
  "async function useHistoryHandoff(entry, kind)",
  '"/api/r2v/from-still"',
  '"/api/r2v/from-video"',
  "JSON.stringify({ job_id: entry.job_id })",
  "asset.source_kind",
  "asset.source_job_id",
  'setMode("video")',
  'setVideoType("reference")',
  'characterButton.textContent = "Use as Character"',
  'motionButton.textContent = "Use as Motion"',
  'entry.video_type !== "reference"',
]) {
  assert.ok(app.includes(marker), `VP2C app behavior marker missing: ${marker}`);
}

const dropHandler = app.slice(
  app.indexOf("function installR2VDropzone"),
  app.indexOf("function setReferenceSlotView"),
);
assert.ok(dropHandler.includes("dataTransfer?.files"));
assert.ok(app.includes("files.length !== 1"));
assert.ok(app.includes("local file"));
assert.ok(dropHandler.includes("upload(singleDroppedFile(event, label))"));

const handoff = app.slice(
  app.indexOf("async function useHistoryHandoff"),
  app.indexOf("function captureContinuationFrame"),
);
assert.ok(handoff.includes('body: JSON.stringify({ job_id: entry.job_id })'));
assert.equal(handoff.includes("entry.request?.prompt"), false, "Handoff must not copy source prompt.");
assert.equal(handoff.includes("/api/r2v/generate"), false, "Handoff must not auto-generate.");
assert.ok(handoff.indexOf("snapshotR2VHandoffState()") < handoff.indexOf("requestJson(endpoint"));
assert.ok(handoff.indexOf("restoreR2VHandoffState(snapshot)") > handoff.indexOf("catch"));

const history = app.slice(app.indexOf("function createHistoryCard"), app.indexOf("async function loadHistory"));
assert.ok(history.includes('isStill && entry.state === "COMPLETED"'));
assert.ok(history.includes('!isStill && entry.state === "COMPLETED"'));
assert.ok(history.includes('characterButton.textContent = "Use as Character"'));
assert.ok(history.includes('motionButton.textContent = "Use as Motion"'));
assert.ok(history.includes('entry.video_type !== "reference"'));

for (const marker of [
  ".r2v-dropzone",
  ".r2v-dropzone.drag-active",
  "border-color: var(--maroon)",
  "background: var(--surface-rose)",
]) {
  assert.ok(styles.includes(marker), `VP2C CSS marker missing: ${marker}`);
}

console.log("VP2C Reference Handoff and D&D UI contract smoke: 36 PASS");
