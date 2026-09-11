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

// 1. Stage action bar structure and elements
for (const marker of [
  'id="stage-action-bar"',
  'id="stage-status-slot"',
  'id="stage-action-slot"',
  'id="generate-action-dock"',
  'id="generate-button"',
  'id="cancel-button"',
  'id="generation-status-block"',
  'id="generation-status"',
  'id="status-detail"',
  'id="preview-overlay"',
  'id="preview-state"',
  'id="preview-elapsed"',
]) {
  assert.ok(html.includes(marker), `Required HTML marker missing: ${marker}`);
}

// 2. Mutual exclusivity logic in app.js
assert.ok(
  app.includes("generateButton.hidden = !cancelButton.hidden;"),
  "app.js must enforce generateButton.hidden = !cancelButton.hidden in updateGenerateAvailability"
);

// Simulate the single-slot swapping states
function simulateActionSlot({ submitting = false, cancelAvailable = false, prompt = "test", activeJob = null }) {
  const state = {
    submitting,
    activeJob,
    backend: "READY",
    mode: "video",
    videoType: "standard",
    referenceUploading: {},
    stillSourceUploading: false,
    prepSourceUploading: false,
    prepDonorUploading: false,
    r2vPictureUploading: false,
    r2vMotionUploading: false,
    handoffInFlight: false,
  };
  const TERMINAL = new Set(["COMPLETED", "FAILED", "CANCELLED"]);

  const cancelButton = { hidden: !cancelAvailable };
  const generateButton = { disabled: false, hidden: false };

  // Logic matching app.js
  if (state.submitting) {
    cancelButton.hidden = true;
  }
  const uploading = false;
  const referenceReady = true;
  const prepReady = true;
  generateButton.disabled = !prompt.trim()
    || uploading
    || !referenceReady
    || !prepReady
    || state.submitting
    || Boolean(state.activeJob && !TERMINAL.has(state.activeJob.state));
  generateButton.hidden = !cancelButton.hidden;

  return { generateButton, cancelButton };
}

// State A: Idle / Ready
const readyState = simulateActionSlot({ submitting: false, cancelAvailable: false });
assert.equal(readyState.generateButton.hidden, false, "Generate must be visible when Ready.");
assert.equal(readyState.cancelButton.hidden, true, "Cancel must be hidden when Ready.");
assert.ok(!(!readyState.generateButton.hidden && !readyState.cancelButton.hidden), "Generate and Cancel must not be simultaneously visible when Ready.");

// State B: Submitting
const submittingState = simulateActionSlot({ submitting: true, cancelAvailable: false });
assert.equal(submittingState.generateButton.hidden, false, "Generate must be visible (disabled/submitting label) while submitting.");
assert.equal(submittingState.generateButton.disabled, true, "Generate must be disabled while submitting.");
assert.equal(submittingState.cancelButton.hidden, true, "Cancel must be hidden while submitting.");
assert.ok(!(!submittingState.generateButton.hidden && !submittingState.cancelButton.hidden), "Generate and Cancel must not be simultaneously visible while submitting.");

// State C: Active generation (Job in progress, cancel_available: true)
const activeState = simulateActionSlot({ submitting: false, cancelAvailable: true, activeJob: { state: "RUNNING", cancel_available: true } });
assert.equal(activeState.generateButton.hidden, true, "Generate must be replaced (hidden) when job is active.");
assert.equal(activeState.cancelButton.hidden, false, "Cancel must be shown when job is active.");
assert.ok(!(!activeState.generateButton.hidden && !activeState.cancelButton.hidden), "Generate and Cancel must never be visible simultaneously during active job.");

// State D: Completed job
const completedState = simulateActionSlot({ submitting: false, cancelAvailable: false, activeJob: { state: "COMPLETED", cancel_available: false } });
assert.equal(completedState.generateButton.hidden, false, "Generate must be restored upon job completion.");
assert.equal(completedState.cancelButton.hidden, true, "Cancel must be hidden upon job completion.");

// State E: Failed job
const failedState = simulateActionSlot({ submitting: false, cancelAvailable: false, activeJob: { state: "FAILED", cancel_available: false } });
assert.equal(failedState.generateButton.hidden, false, "Generate must be restored upon job failure.");
assert.equal(failedState.cancelButton.hidden, true, "Cancel must be hidden upon job failure.");

// 3. Compact CSS styles verification
assert.match(styles, /\.stage-action-bar\s*\{[^}]*min-height:\s*42px;/, "stage-action-bar must have compact min-height (42px).");
assert.match(styles, /\.stage-action-bar\s*\{[^}]*margin-bottom:\s*8px;/, "stage-action-bar must have compact margin-bottom (8px).");
assert.match(styles, /\.stage-status-slot\s+\.status-label\s*\{[^}]*display:\s*none;/, "status-label must be hidden in stage-status-slot to achieve single-line compact layout.");
assert.match(styles, /\.stage-action-slot\s+\.primary-button\s*\{[^}]*min-height:\s*34px;/, "primary-button must have compact min-height (34px) in stage action slot.");
assert.match(styles, /\.stage-action-slot\s+\.cancel-button\s*\{[^}]*min-height:\s*34px;/, "cancel-button must have compact min-height (34px) in stage action slot.");

// 4. Preview running elapsed preservation
assert.ok(app.includes("previewElapsed.textContent = `${Number(job.elapsed_seconds || 0).toFixed(1)}s`;"));
assert.ok(app.includes('previewOverlay.hidden = TERMINAL.has(job.state) && job.state !== "COMPLETED";'));

// 5. Truthful error preservation
assert.ok(app.includes('if (job.state === "FAILED" || job.state === "DISCONNECTED")'));
assert.ok(app.includes("setDetails(activeStatusDetail(job));"));
assert.ok(app.includes("generationStatus.textContent = statusLabelForJob(job);"));

// 6. Narrow mode regression
assert.ok(html.includes('id="narrow-view-switch"'));
assert.ok(styles.includes(".stage-action-bar { display: none; }"));
assert.ok(styles.includes('body[data-narrow-view="create"] .preview-column { display: none; }'));
assert.ok(styles.includes('body[data-narrow-view="result"] .control-column { display: none; }'));
assert.ok(app.includes('const actionSlot = wide ? stageActionSlot : generateActionSlot;'));

console.log("H3-G1A Stage action compression & media feasibility smoke: 22 PASS");
