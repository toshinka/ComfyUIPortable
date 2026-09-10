import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveHistoryScalars, resolveHistorySettings } from "../app/static/history-settings.js";
import { resolveStillHistorySettings } from "../app/static/still-history-settings.js";
import { validateContinuationSource } from "../app/static/continuation-source.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "app", "static");
const [html, app] = await Promise.all([
  readFile(join(root, "index.html"), "utf8"),
  readFile(join(root, "app.js"), "utf8"),
]);

for (const marker of [
  'id="resolution"',
  'id="duration"',
  'id="duration-field"',
  'id="mode-still"',
]) {
  assert.ok(html.includes(marker), `VP1 HTML marker missing: ${marker}`);
}

for (const marker of [
  "config: null",
  "function configuredResolutionOptions(still = false)",
  "function populateResolutionOptions()",
  "function populateDurationOptions()",
  "state.config = config",
  "configuredResolutionOptions(false).map(resolutionValue)",
  "configuredResolutionOptions(true).map(resolutionValue)",
  "state.videoResolution = settings.resolution",
  "state.videoDuration = settings.duration",
  'const seed = seedText === "" ? "random" : seedText',
  "durationInput.disabled = still",
]) {
  assert.ok(app.includes(marker), `VP1 app behavior marker missing: ${marker}`);
}

const videoOptions = {
  resolutionValues: ["608x352", "736x416"],
  durationValues: ["5", "15"],
  stepsValue: "20",
  maxPromptLength: 4000,
};
const candidateRequest = {
  prompt: "A retained candidate prompt",
  width: 736,
  height: 416,
  duration: 5,
  seed: "4121755688520062686",
  steps: 20,
};

const restoredCandidate = await resolveHistorySettings(
  { request: candidateRequest, references: { start_frame: null, end_frame: null } },
  { ...videoOptions, verifyReference: async () => {} },
);
assert.equal(restoredCandidate.resolution, "736x416");
assert.equal(restoredCandidate.duration, "5");
assert.equal(restoredCandidate.seed, "4121755688520062686");

const durationCandidate = resolveHistoryScalars(
  { request: { ...candidateRequest, width: 608, height: 352, duration: 15 } },
  videoOptions,
);
assert.equal(durationCandidate.resolution, "608x352");
assert.equal(durationCandidate.duration, "15");
assert.equal(durationCandidate.seed, "4121755688520062686");

await assert.rejects(
  resolveHistorySettings(
    { request: { ...candidateRequest, width: 864, height: 480 }, references: { start_frame: null, end_frame: null } },
    { ...videoOptions, verifyReference: async () => {} },
  ),
  /Resolution cannot be restored with the current UI/,
);
assert.throws(
  () => resolveHistoryScalars(
    { request: { ...candidateRequest, duration: 10 } },
    videoOptions,
  ),
  /Duration cannot be restored with the current UI/,
);

const continuationSource = validateContinuationSource({
  state: "COMPLETED",
  job_id: "vp1-candidate-1",
  video_url: "/api/jobs/vp1-candidate-1/video",
});
assert.equal(continuationSource, "/api/jobs/vp1-candidate-1/video");

const stillRequest = {
  media_kind: "still",
  request: {
    prompt: "Still stays isolated",
    width: 608,
    height: 352,
    seed: 20260910,
    steps: 20,
  },
  source: null,
};
const stillSettings = await resolveStillHistorySettings(stillRequest, {
  resolutionValues: ["608x352"],
  stepsValue: "20",
});
assert.equal(stillSettings.resolution, "608x352");
await assert.rejects(
  resolveStillHistorySettings(
    { ...stillRequest, request: { ...stillRequest.request, width: 736, height: 416 } },
    { resolutionValues: ["608x352"], stepsValue: "20" },
  ),
  /Resolution cannot be restored with the current UI/,
);

const useHandler = app.slice(app.indexOf("async function useHistorySettings"), app.indexOf("function createHistoryCard"));
assert.ok(useHandler.indexOf("await resolveHistorySettings") >= 0);
assert.ok(useHandler.indexOf("applyHistorySettings(settings)") > useHandler.indexOf("await resolveHistorySettings"));
assert.ok(useHandler.indexOf("await resolveStillHistorySettings") >= 0);
assert.equal(useHandler.includes("/api/generate"), false);
assert.equal(useHandler.includes("state.activeJob ="), false);

console.log("VP1 Video config/history/Continue/Still isolation smoke: PASS");
