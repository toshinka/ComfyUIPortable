import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  ACTIVE_STATUS_COPY,
  activeStatusDetail,
} from "../app/static/job-status-copy.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "app", "static");
const [html, app, styles] = await Promise.all([
  readFile(join(root, "index.html"), "utf8"),
  readFile(join(root, "app.js"), "utf8"),
  readFile(join(root, "styles.css"), "utf8"),
]);

const count = (value, marker) => value.split(marker).length - 1;

for (const marker of [
  'id="narrow-view-switch"',
  'id="narrow-create-button"',
  'id="narrow-result-button"',
  'id="stage-action-bar"',
  'id="stage-status-slot"',
  'id="stage-action-slot"',
  'id="generate-action-slot"',
  'id="generation-status-block"',
  'aria-pressed="true"',
  'aria-pressed="false"',
  'id="generate-action-dock"',
  'id="generate-label"',
  'id="submit-status"',
  'aria-live="polite"',
]) {
  assert.ok(html.includes(marker), `R1 HTML marker missing: ${marker}`);
}
assert.equal(count(html, 'id="generate-button"'), 1, "R1 must keep one Generate action.");
assert.ok(html.includes('form="generate-form"'), "Wide Generate must remain associated with the native form.");
assert.ok(html.indexOf('id="stage-action-bar"') < html.indexOf('class="section-kicker">Preview'));
assert.ok(html.indexOf('id="generate-action-dock"') < html.indexOf('class="advanced-panel"'));

for (const marker of [
  "submitting: false",
  'narrowView: "create"',
  "function isNarrowViewport()",
  "function setNarrowView(nextView)",
  "function syncResponsiveMounts()",
  "const actionSlot = wide ? stageActionSlot : generateActionSlot;",
  "const statusSlot = wide ? stageStatusSlot : statusStrip;",
  "window.addEventListener(\"resize\", syncResponsiveMounts);",
  "function statusLabelForJob(job)",
  'if (job?.state === "RUNNING") return "Generating";',
  "function renderSubmittingState()",
  "state.submitting",
  'narrowCreateButton.addEventListener("click", () => setNarrowView("create"))',
  'narrowResultButton.addEventListener("click", () => setNarrowView("result"))',
]) {
  assert.ok(app.includes(marker), `R1 app behavior marker missing: ${marker}`);
}

assert.equal(ACTIVE_STATUS_COPY.SUBMITTING, "Submitting the generation request to Native H3.");
assert.match(activeStatusDetail({ state: "SUBMITTING" }), /Submitting/);
assert.equal(activeStatusDetail({ state: "RUNNING" }), ACTIVE_STATUS_COPY.RUNNING);

const submitStart = app.indexOf("async function submitGeneration");
const submitEnd = app.indexOf("async function cancelGeneration", submitStart);
assert.ok(submitStart >= 0 && submitEnd > submitStart, "R1 submit handler must remain present.");
const submitHandler = app.slice(submitStart, submitEnd);
const guardIndex = submitHandler.indexOf("if (!promptInput.value.trim()");
const submittingGuardIndex = submitHandler.indexOf("state.submitting", guardIndex);
const requestIndex = submitHandler.indexOf("await requestJson(endpoint");
const submittingSetIndex = submitHandler.indexOf("state.submitting = true;");
const acceptedIndex = submitHandler.indexOf("accepted = true;");
const acceptedClearIndex = submitHandler.indexOf("state.submitting = false;", acceptedIndex);
const acceptedJobIndex = submitHandler.indexOf("setActiveJob(body.job", acceptedClearIndex);
const acceptedResultIndex = submitHandler.indexOf('setNarrowView("result")', acceptedJobIndex);
const catchIndex = submitHandler.indexOf("} catch (error)");
const catchClearIndex = submitHandler.indexOf("state.submitting = false;", catchIndex);
assert.ok(guardIndex >= 0 && submittingGuardIndex > guardIndex, "Repeated submit must be ignored while submitting.");
assert.ok(submittingSetIndex > submittingGuardIndex, "Submitting must be set after the guard.");
assert.ok(requestIndex > submittingSetIndex, "Submitting must be set before the generation POST.");
assert.ok(acceptedIndex > requestIndex, "Accepted state must follow the POST response.");
assert.ok(acceptedClearIndex > acceptedIndex, "Submitting must clear after an accepted Job.");
assert.ok(acceptedJobIndex > acceptedClearIndex, "Accepted Job must become the active Job.");
assert.ok(acceptedResultIndex > acceptedJobIndex, "Narrow Result may switch only after Job acceptance.");
assert.ok(catchIndex > requestIndex && catchClearIndex > catchIndex, "Pre-accept failure must clear submitting.");
assert.ok(submitHandler.includes('statusDetail.textContent = "Generation was not submitted.";'));
assert.equal(submitHandler.includes('promptInput.value = ""'), false, "Submission failure must retain inputs.");
assert.equal(submitHandler.includes('seedInput.value = ""'), false, "Submission failure must retain seed input.");

const narrowHandlerStart = app.indexOf("function setNarrowView(nextView)");
const narrowHandlerEnd = app.indexOf("function statusLabelForJob", narrowHandlerStart);
const narrowHandler = app.slice(narrowHandlerStart, narrowHandlerEnd);
assert.equal(narrowHandler.includes("fetch("), false, "Viewport view switching must not submit or fetch.");
assert.equal(narrowHandler.includes("modeSettings"), false, "Viewport view switching must not alter domain settings.");
assert.equal(narrowHandler.includes("promptInput"), false, "Viewport view switching must not alter the prompt.");
assert.equal(narrowHandler.includes("seedInput"), false, "Viewport view switching must not alter the seed.");

const updateActiveStart = app.indexOf("function updateActiveJob");
const updateActiveEnd = app.indexOf("async function pollJob", updateActiveStart);
const updateActive = app.slice(updateActiveStart, updateActiveEnd);
assert.equal(updateActive.includes("setNarrowView"), false, "Polling completion must not override narrow user intent.");
assert.equal(updateActive.includes(".focus("), false, "Polling completion must not steal focus.");
assert.equal(app.includes('generationStatus.textContent = "Finalizing"'), false);
assert.equal(/\b\d+%/.test(`${html}\n${app}`), false, "R1 must not fabricate percentage progress.");

const historyStart = app.indexOf("function createHistoryCard");
const historyEnd = app.indexOf("async function loadHistory", historyStart);
const history = app.slice(historyStart, historyEnd);
assert.ok(history.includes("showPreviewJob(entry)"), "Explicit History selection must show the Stage result.");
assert.ok(history.includes('setNarrowView("result")'), "History selection must expose Result on narrow view.");

for (const marker of [
  ".stage-action-bar {",
  ".stage-action-slot .generate-action-dock {",
  ".stage-action-slot .primary-button {",
  ".preview-column {\n    position: sticky;",
  ".generate-action-dock {\n  position: sticky;",
  ".narrow-view-switch {\n    width:",
  'body[data-narrow-view="create"] .preview-column { display: none; }',
  'body[data-narrow-view="result"] .control-column { display: none; }',
  ".narrow-view-button:focus-visible",
]) {
  assert.ok(styles.includes(marker), `R1 CSS marker missing: ${marker}`);
}
assert.ok(styles.includes(".stage-action-bar { display: none; }"), "Narrow must hide the wide Stage action bar.");
assert.equal(styles.includes("position: fixed"), false, "R1 Stage must not become a page-wide fixed overlay.");
assert.equal(styles.includes("overflow: auto"), false, "R1 must not add a nested scrolling workspace.");

console.log("H3-R1A Stage / Generate visibility source+logic smoke: 61 PASS");
