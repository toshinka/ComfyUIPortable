import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { resolvePrepHistorySettings } from "../app/static/prep-history-settings.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "app", "static");
const [html, app, styles] = await Promise.all([
  readFile(join(root, "index.html"), "utf8"),
  readFile(join(root, "app.js"), "utf8"),
  readFile(join(root, "styles.css"), "utf8"),
]);

for (const marker of [
  'id="mode-prep"',
  'id="prep-card"',
  'id="prep-source-file"',
  'id="prep-donor-file"',
  'data-prep-dropzone="source"',
  'data-prep-dropzone="donor"',
  'Donor Image <span class="optional-mark">Experimental</span>',
  "Fixed Native baseline: 608 x 352 · 20 steps",
]) {
  assert.ok(html.includes(marker), `IP2 HTML marker missing: ${marker}`);
}
const prepMarkup = html.slice(html.indexOf('id="prep-card"'), html.indexOf('id="resolution-field"'));
for (const forbidden of ["pixel lock", "identity lock", "exact preservation", "Photoshop", "strength", "fidelity"]) {
  assert.equal(prepMarkup.toLowerCase().includes(forbidden), false, `Prep UI must not advertise ${forbidden}.`);
}

for (const marker of [
  'import { resolvePrepHistorySettings } from "./prep-history-settings.js";',
  'prepSource: null',
  'prepDonor: null',
  'function captureModeSettings()',
  'function restoreModeSettings(mode)',
  'modePrep.addEventListener("click", () => setMode("prep"))',
  'prepCard.hidden = !prep',
  'durationField.hidden = still || prep',
  'async function uploadPrepAsset(kind, file)',
  'requestJson(`/api/prep/${kind}`',
  'function installSingleFileDropzone(dropzone, label, upload, status)',
  'installSingleFileDropzone(prepSourceDropzone',
  'installSingleFileDropzone(prepDonorDropzone',
  'endpoint = "/api/prep/generate"',
  'source_id: state.prepSource.id',
  'donor_id: state.prepDonor?.id || null',
  'async function usePrepSourceHandoff(entry)',
  'requestJson("/api/prep/from-still"',
  'prepButton.textContent = "Edit in Prep"',
  'route === "native_image_prep"',
]) {
  assert.ok(app.includes(marker), `IP2 app behavior marker missing: ${marker}`);
}

const modeHandler = app.slice(app.indexOf("function setMode"), app.indexOf("function updateGenerateAvailability"));
assert.equal(modeHandler.includes("fetch("), false, "Mode switching must remain UI-only.");
assert.equal(modeHandler.includes("/api/prep/generate"), false, "Mode switching must not submit generation.");

const submitHandler = app.slice(app.indexOf("async function submitGeneration"), app.indexOf("async function cancelGeneration"));
const prepStart = submitHandler.indexOf('if (state.mode === "prep")');
const prepEnd = submitHandler.indexOf("} else {", prepStart);
const prepSubmit = submitHandler.slice(prepStart, prepEnd);
assert.ok(prepSubmit.includes('endpoint = "/api/prep/generate"'));
assert.ok(prepSubmit.includes("source_id: state.prepSource.id"));
assert.ok(prepSubmit.includes("donor_id: state.prepDonor?.id || null"));
assert.equal(prepSubmit.includes("width"), false, "Prep Browser payload must not expose resolution controls.");
assert.equal(prepSubmit.includes("steps"), false, "Prep Browser payload must not expose steps controls.");

for (const marker of [
  ".prep-card",
  ".prep-source-slot",
  ".prep-donor-slot",
  ".prep-donor-helper",
  ".prep-source-slot.drag-active",
  ".history-kind-badge.prep",
]) {
  assert.ok(styles.includes(marker), `IP2 CSS marker missing: ${marker}`);
}

const sourceId = "a".repeat(32);
const donorId = "b".repeat(32);
const source = { id: sourceId, width: 608, height: 352 };
const donor = { id: donorId, width: 608, height: 352 };
const request = {
  prompt: "change the coat color",
  width: 608,
  height: 352,
  seed: "4121755688520062686",
  steps: 20,
  source_id: sourceId,
  donor_id: donorId,
};
const verified = [];
const settings = await resolvePrepHistorySettings(
  {
    media_kind: "still",
    route: "native_image_prep",
    request,
    prep_source: source,
    prep_donor: donor,
  },
  {
    stepsValue: "20",
    verifyAsset: async (asset, kind) => verified.push(`${kind}:${asset.id}`),
  },
);
assert.equal(settings.prompt, request.prompt);
assert.equal(settings.resolution, "608x352");
assert.equal(settings.seed, request.seed);
assert.equal(settings.steps, "20");
assert.equal(settings.source.id, sourceId);
assert.equal(settings.donor.id, donorId);
assert.deepEqual(verified, [`source:${sourceId}`, `donor:${donorId}`]);

const sourceOnly = await resolvePrepHistorySettings(
  {
    media_kind: "still",
    route: "native_image_prep",
    request: { ...request, donor_id: null },
    prep_source: source,
    prep_donor: null,
  },
  { stepsValue: "20", verifyAsset: async () => {} },
);
assert.equal(sourceOnly.donor, null);

await assert.rejects(
  resolvePrepHistorySettings(
    { media_kind: "still", route: "native_image_prep", request, prep_source: source, prep_donor: donor },
    { stepsValue: "20", verifyAsset: async () => { throw new Error("missing asset"); } },
  ),
  /missing asset/,
);
await assert.rejects(
  resolvePrepHistorySettings(
    { media_kind: "still", route: "native_image_prep", request: { ...request, donor_id: "c".repeat(32) }, prep_source: source, prep_donor: donor },
    { stepsValue: "20", verifyAsset: async () => {} },
  ),
  /metadata is inconsistent/,
);
await assert.rejects(
  resolvePrepHistorySettings(
    { media_kind: "still", route: "native_image_prep", request: { ...request, width: 736 }, prep_source: source, prep_donor: donor },
    { stepsValue: "20", verifyAsset: async () => {} },
  ),
  /fixed Native baseline/,
);

console.log("IP2 experimental Browser Prep/Edit UI source+logic smoke: 45 PASS");
