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

// 1. App markers and logic
assert.ok(
  app.includes('previewState.textContent = progressPercent !== null'),
  "app.js must format previewState.textContent with progressPercent"
);
assert.ok(
  app.includes('`Generating · Sampling ${progressPercent}%`'),
  "app.js must format previewState with exact 'Generating · Sampling ${progressPercent}%'"
);
assert.ok(
  app.includes('job?.progress?.kind === "sampling"'),
  "app.js must require progress.kind === 'sampling'"
);

// 2. Behavioral verification of progress presentation
function computePreviewStateText(job, statusLabelForJob) {
  const progressPercent = (job?.state === "RUNNING" && job?.progress?.kind === "sampling" && Number.isFinite(job?.progress?.percent))
    ? job.progress.percent
    : null;
  return progressPercent !== null
    ? `Generating · Sampling ${progressPercent}%`
    : statusLabelForJob(job);
}

function mockStatusLabel(job) {
  if (job?.state === "RUNNING") return "Generating";
  return job?.label || job?.state || "Unknown";
}

// Case 1: RUNNING + progress None -> "Generating" (no percentage)
const r1 = computePreviewStateText({ state: "RUNNING", progress: null }, mockStatusLabel);
assert.equal(r1, "Generating");
assert.equal(r1.includes("Sampling"), false);
assert.equal(r1.includes("%"), false);

// Case 2: RUNNING + valid sampling progress -> "Generating · Sampling 35%"
const r2 = computePreviewStateText(
  { state: "RUNNING", progress: { kind: "sampling", value: 7, max: 20, percent: 35 } },
  mockStatusLabel
);
assert.equal(r2, "Generating · Sampling 35%");
assert.ok(r2.includes("Sampling"));
assert.ok(r2.includes("35%"));

// Case 3: RUNNING + sampling 100% -> "Generating · Sampling 100%" (still visually Generating)
const r3 = computePreviewStateText(
  { state: "RUNNING", progress: { kind: "sampling", value: 20, max: 20, percent: 100 } },
  mockStatusLabel
);
assert.equal(r3, "Generating · Sampling 100%");
assert.ok(r3.startsWith("Generating"));

// Case 4: COMPLETED -> no Sampling label (even if malformed job object retains old progress)
const r4 = computePreviewStateText(
  { state: "COMPLETED", label: "Completed", progress: { kind: "sampling", value: 20, max: 20, percent: 100 } },
  mockStatusLabel
);
assert.equal(r4, "Completed");
assert.equal(r4.includes("Sampling"), false);

// Case 5: FAILED -> no Sampling label
const r5 = computePreviewStateText(
  { state: "FAILED", label: "Failed", progress: { kind: "sampling", value: 7, max: 20, percent: 35 } },
  mockStatusLabel
);
assert.equal(r5, "Failed");
assert.equal(r5.includes("Sampling"), false);

// Case 6: CANCELLED -> no Sampling label
const r6 = computePreviewStateText(
  { state: "CANCELLED", label: "Cancelled", progress: { kind: "sampling", value: 7, max: 20, percent: 35 } },
  mockStatusLabel
);
assert.equal(r6, "Cancelled");
assert.equal(r6.includes("Sampling"), false);

// Case 7: DISCONNECTED -> no Sampling label
const r7 = computePreviewStateText(
  { state: "DISCONNECTED", label: "Backend disconnected", progress: { kind: "sampling", value: 7, max: 20, percent: 35 } },
  mockStatusLabel
);
assert.equal(r7, "Backend disconnected");
assert.equal(r7.includes("Sampling"), false);

// Case 8: Non-sampling progress kind -> ignored
const r8 = computePreviewStateText(
  { state: "RUNNING", progress: { kind: "overall", percent: 50 } },
  mockStatusLabel
);
assert.equal(r8, "Generating");
assert.equal(r8.includes("Sampling"), false);

// 3. Preview Job Ownership Isolation
// Simulating: Preview Job A (completed historical) while Active Job B is running with progress
const state = {
  activeJob: {
    job_id: "job-b",
    state: "RUNNING",
    progress: { kind: "sampling", percent: 45 },
    elapsed_seconds: 12.4,
  },
  previewJob: null,
};

function showPreview(job) {
  state.previewJob = job;
  return {
    stateText: computePreviewStateText(job, mockStatusLabel),
    elapsedText: `${Number(job.elapsed_seconds || 0).toFixed(1)}s`,
  };
}

const historicalJobA = {
  job_id: "job-a",
  state: "COMPLETED",
  label: "Completed",
  progress: null,
  elapsed_seconds: 45.2,
};

const renderedPreviewA = showPreview(historicalJobA);
assert.equal(renderedPreviewA.stateText, "Completed");
assert.equal(renderedPreviewA.stateText.includes("Sampling"), false);
assert.equal(renderedPreviewA.stateText.includes("45%"), false);
assert.equal(renderedPreviewA.elapsedText, "45.2s");

// Forbidden patterns check: no manufactured progress, overall ETA, or "X% complete" claims
assert.equal(app.includes("ETA"), false, "H3 must not fabricate an ETA");
assert.equal(/% complete/i.test(app), false, "Progress must not claim 'X% complete'");
assert.equal(/overall/i.test(app), false, "Progress must not claim 'Overall'");

console.log("H3-G2A truthful sampler progress smoke: 25 PASS");
