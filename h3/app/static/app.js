import { activeStatusDetail, previewStatusDetail } from "./job-status-copy.js";
import { resolveHistorySettings } from "./history-settings.js";
import { resolveHistoryScalars } from "./history-settings.js";
import { resolveStillHistorySettings } from "./still-history-settings.js";
import { resolvePrepHistorySettings } from "./prep-history-settings.js";
import { validateContinuationSource } from "./continuation-source.js";
import { resolveBackendStatusPresentation } from "./backend-status-presentation.js";

const state = {
  mode: "video",
  videoType: "standard",
  backend: "CONNECTING",
  backendStatusDetail: "",
  config: null,
  videoResolution: "608x352",
  stillResolution: "608x352",
  videoDuration: "5",
  activeJob: null,
  previewJob: null,
  submitting: false,
  narrowView: "create",
  references: { start_frame: null, end_frame: null },
  reference: null,
  referenceUploading: { start_frame: false, end_frame: false },
  stillSource: null,
  stillSourceUploading: false,
  prepSource: null,
  prepDonor: null,
  prepSourceUploading: false,
  prepDonorUploading: false,
  r2vPicture: null,
  r2vMotionVideo: null,
  r2vPictureUploading: false,
  r2vMotionUploading: false,
  handoffInFlight: false,
  pollTimer: null,
  backendTimer: null,
  modeSettings: {
    video: { prompt: "", seed: "", resolution: "608x352", duration: "5" },
    still: { prompt: "", seed: "", resolution: "608x352" },
    prep: { prompt: "", seed: "" },
  },
};

const $ = (id) => document.getElementById(id);
const form = $("generate-form");
const promptInput = $("prompt");
const brandMode = $("brand-mode");
const modeVideo = $("mode-video");
const modeStill = $("mode-still");
const modePrep = $("mode-prep");
const controlColumn = $("control-column");
const stageActionBar = $("stage-action-bar");
const stageActionSlot = $("stage-action-slot");
const generateActionSlot = $("generate-action-slot");
const generateActionDock = $("generate-action-dock");
const stageStatusSlot = $("stage-status-slot");
const statusStrip = document.querySelector(".status-strip");
const generationStatusBlock = $("generation-status-block");
const videoTypeCard = $("video-type-card");
const videoTypeStandard = $("video-type-standard");
const videoTypeReference = $("video-type-reference");
const r2vCard = $("r2v-card");
const r2vPictureFile = $("r2v-picture-file");
const r2vPictureAdd = $("r2v-picture-add");
const r2vPictureReplace = $("r2v-picture-replace");
const r2vPictureRemove = $("r2v-picture-remove");
const r2vPictureEmpty = $("r2v-picture-empty");
const r2vPictureSelected = $("r2v-picture-selected");
const r2vPictureThumbnail = $("r2v-picture-thumbnail");
const r2vPictureName = $("r2v-picture-name");
const r2vPictureStatus = $("r2v-picture-status");
const r2vPictureDropzone = document.querySelector('[data-r2v-dropzone="picture"]');
const r2vMotionFile = $("r2v-motion-file");
const r2vMotionAdd = $("r2v-motion-add");
const r2vMotionReplace = $("r2v-motion-replace");
const r2vMotionRemove = $("r2v-motion-remove");
const r2vMotionEmpty = $("r2v-motion-empty");
const r2vMotionSelected = $("r2v-motion-selected");
const r2vMotionName = $("r2v-motion-name");
const r2vMotionStatus = $("r2v-motion-status");
const r2vMotionDropzone = document.querySelector('[data-r2v-dropzone="motion"]');
const videoReferenceCard = $("video-reference-card");
const stillSourceCard = $("still-source-card");
const durationField = $("duration-field");
const stillSourceFile = $("still-source-file");
const stillSourceAdd = $("still-source-add");
const stillSourceReplace = $("still-source-replace");
const stillSourceRemove = $("still-source-remove");
const stillSourceEmpty = $("still-source-empty");
const stillSourceSelected = $("still-source-selected");
const stillSourceThumbnail = $("still-source-thumbnail");
const stillSourceName = $("still-source-name");
const stillSourceStatus = $("still-source-status");
const prepCard = $("prep-card");
const prepSourceFile = $("prep-source-file");
const prepSourceAdd = $("prep-source-add");
const prepSourceReplace = $("prep-source-replace");
const prepSourceRemove = $("prep-source-remove");
const prepSourceEmpty = $("prep-source-empty");
const prepSourceSelected = $("prep-source-selected");
const prepSourceThumbnail = $("prep-source-thumbnail");
const prepSourceName = $("prep-source-name");
const prepSourceStatus = $("prep-source-status");
const prepSourceDropzone = document.querySelector('[data-prep-dropzone="source"]');
const prepDonorFile = $("prep-donor-file");
const prepDonorAdd = $("prep-donor-add");
const prepDonorReplace = $("prep-donor-replace");
const prepDonorRemove = $("prep-donor-remove");
const prepDonorEmpty = $("prep-donor-empty");
const prepDonorSelected = $("prep-donor-selected");
const prepDonorThumbnail = $("prep-donor-thumbnail");
const prepDonorName = $("prep-donor-name");
const prepDonorStatus = $("prep-donor-status");
const prepDonorDropzone = document.querySelector('[data-prep-dropzone="donor"]');
const referenceFile = $("reference-file");
const referenceAdd = $("reference-add");
const referenceReplace = $("reference-replace");
const referenceRemove = $("reference-remove");
const referenceSelected = $("reference-selected");
const referenceThumbnail = $("reference-thumbnail");
const referenceName = $("reference-name");
const referenceStatus = $("reference-status");
const endReferenceFile = $("end-reference-file");
const endReferenceAdd = $("end-reference-add");
const endReferenceReplace = $("end-reference-replace");
const endReferenceRemove = $("end-reference-remove");
const endReferenceEmpty = $("end-reference-empty");
const endReferenceSelected = $("end-reference-selected");
const endReferenceThumbnail = $("end-reference-thumbnail");
const endReferenceName = $("end-reference-name");
const endReferenceStatus = $("end-reference-status");
const resolutionInput = $("resolution");
const resolutionField = $("resolution-field");
const durationInput = $("duration");
const seedInput = $("seed");
const stepsInput = $("steps");
const generateButton = $("generate-button");
const generateLabel = $("generate-label");
const cancelButton = $("cancel-button");
const submitStatus = $("submit-status");
const narrowCreateButton = $("narrow-create-button");
const narrowResultButton = $("narrow-result-button");
const backendPill = $("backend-pill");
const backendLabel = $("backend-label");
const generationStatus = $("generation-status");
const statusDetail = $("status-detail");
const queueCount = $("queue-count");
const historyCount = $("history-count");
const previewEmpty = $("preview-empty");
const previewVideo = $("preview-video");
const previewImage = $("preview-image");
const previewOverlay = $("preview-overlay");
const previewState = $("preview-state");
const previewElapsed = $("preview-elapsed");
const previewMeta = $("preview-meta");
const detailsPanel = $("details-panel");
const detailsText = $("details-text");
const historyList = $("history-list");
const historyActionStatus = $("history-action-status");
const footerMode = $("footer-mode");

const TERMINAL = new Set(["COMPLETED", "FAILED", "CANCELLED"]);
const BACKEND_STATUS_LABELS = Object.freeze({
  READY: "Ready",
  DISCONNECTED: "Backend disconnected",
  PROFILE_MISMATCH: "Wrong H3 backend profile",
  PROFILE_UNVERIFIABLE: "H3 profile unverifiable",
});

async function requestJson(url, options = {}) {
  const response = await fetch(url, { cache: "no-store", ...options });
  let body = {};
  try { body = await response.json(); } catch { body = {}; }
  if (!response.ok) {
    const error = new Error(body.error || `Request failed (${response.status})`);
    error.body = body;
    throw error;
  }
  return body;
}

function setBackendStatus(next, message = "") {
  state.backend = next;
  backendPill.className = `backend-pill ${next.toLowerCase()}`;
  backendLabel.textContent = BACKEND_STATUS_LABELS[next] || "Connecting";
  const presentation = resolveBackendStatusPresentation({
    previousBackendDetail: state.backendStatusDetail,
    next,
    message,
    hasActiveJob: Boolean(state.activeJob),
    submitting: state.submitting,
    currentDetail: statusDetail.textContent,
  });
  statusDetail.textContent = presentation.detail;
  state.backendStatusDetail = presentation.backendDetail;
  updateGenerateAvailability();
}

function setStatusDetail(message) {
  statusDetail.textContent = message;
  state.backendStatusDetail = "";
}

function resolutionValue(option) {
  return `${Number(option.width)}x${Number(option.height)}`;
}

function configuredResolutionOptions(still = false) {
  const videoType = arguments.length > 1 ? arguments[1] : "standard";
  const configured = state.mode === "prep"
    ? state.config?.prep?.resolution_options
    : still
    ? state.config?.still?.resolution_options
    : videoType === "reference"
      ? state.config?.reference_video?.resolution_options
      : state.config?.resolution_options;
  if (Array.isArray(configured) && configured.length) return configured;
  return [{ label: "608 x 352", width: 608, height: 352 }];
}

function configuredDurationOptions() {
  const configured = state.mode === "video" && state.videoType === "reference"
    ? state.config?.reference_video?.duration_options
    : state.config?.duration_options;
  if (Array.isArray(configured) && configured.length) return configured;
  return [{ label: "5 seconds", value: 5 }];
}

function rememberCurrentResolution() {
  if (state.mode === "video" && state.videoType === "reference") return;
  const key = state.mode === "still" ? "stillResolution" : "videoResolution";
  if (resolutionInput.value) state[key] = resolutionInput.value;
}

function captureModeSettings() {
  const settings = state.modeSettings[state.mode];
  if (!settings) return;
  settings.prompt = promptInput.value;
  settings.seed = seedInput.value;
  if (state.mode === "video") {
    settings.resolution = state.videoResolution;
    settings.duration = state.videoDuration;
  } else if (state.mode === "still") {
    settings.resolution = state.stillResolution;
  }
}

function restoreModeSettings(mode) {
  const settings = state.modeSettings[mode] || {};
  promptInput.value = settings.prompt || "";
  seedInput.value = settings.seed || "";
  if (mode === "video") {
    state.videoResolution = settings.resolution || state.videoResolution;
    state.videoDuration = settings.duration || state.videoDuration;
  } else if (mode === "still") {
    state.stillResolution = settings.resolution || state.stillResolution;
  }
}

function populateResolutionOptions() {
  const still = state.mode === "still";
  const prep = state.mode === "prep";
  const reference = !still && state.videoType === "reference";
  const key = still ? "stillResolution" : "videoResolution";
  const options = configuredResolutionOptions(still, state.videoType).filter((item) =>
    Number.isInteger(Number(item.width)) && Number.isInteger(Number(item.height)),
  );
  const values = options.map(resolutionValue);
  if (!values.length) return;
  resolutionInput.replaceChildren();
  options.forEach((item, index) => {
    const option = document.createElement("option");
    option.value = values[index];
    option.textContent = item.label || `${item.width} x ${item.height}`;
    resolutionInput.append(option);
  });
  if (prep) state.prepResolution = values[0];
  if (!reference && !prep) state[key] = values.includes(state[key]) ? state[key] : values[0];
  resolutionInput.value = reference || prep ? values[0] : state[key];
}

function populateDurationOptions() {
  const reference = state.mode === "video" && state.videoType === "reference";
  const options = configuredDurationOptions().filter((item) => Number.isFinite(Number(item.value)));
  const values = options.map((item) => String(item.value));
  if (!values.length) return;
  durationInput.replaceChildren();
  options.forEach((item, index) => {
    const option = document.createElement("option");
    option.value = values[index];
    option.textContent = item.label || `${item.value} seconds`;
    durationInput.append(option);
  });
  if (!reference) state.videoDuration = values.includes(state.videoDuration) ? state.videoDuration : values[0];
  durationInput.value = reference ? values[0] : state.videoDuration;
}

function referenceVideoEnabled() {
  return state.config?.reference_video?.enabled === true;
}

function updateVideoTypeView() {
  const showingReference = state.mode === "video" && state.videoType === "reference";
  const still = state.mode === "still";
  const prep = state.mode === "prep";
  videoTypeCard.hidden = state.mode !== "video";
  r2vCard.hidden = !showingReference;
  videoReferenceCard.hidden = state.mode !== "video" || showingReference;
  if (still) videoReferenceCard.hidden = still;
  if (prep) videoReferenceCard.hidden = true;
  videoTypeStandard.classList.toggle("active", !showingReference);
  videoTypeReference.classList.toggle("active", showingReference);
  videoTypeStandard.setAttribute("aria-pressed", String(!showingReference));
  videoTypeReference.setAttribute("aria-pressed", String(showingReference));
  resolutionInput.disabled = showingReference || prep;
  durationInput.disabled = still || prep || showingReference;
  if (showingReference || prep) {
    resolutionInput.value = "608x352";
    if (showingReference) durationInput.value = "5";
  }
}

function setVideoType(nextType) {
  if (state.mode !== "video" || !["standard", "reference"].includes(nextType)) return;
  if (nextType === "reference" && !referenceVideoEnabled()) {
    setDetails("Reference · Experimental is unavailable because the Native Ref2VA capability is not ready.");
    return;
  }
  if (state.videoType === "standard" && nextType === "reference") {
    rememberCurrentResolution();
    state.videoDuration = durationInput.value;
  }
  state.videoType = nextType;
  populateResolutionOptions();
  populateDurationOptions();
  updateVideoTypeView();
  updateGenerateAvailability();
}

function setMode(nextMode) {
  if (!["video", "still", "prep"].includes(nextMode)) return;
  captureModeSettings();
  state.mode = nextMode;
  const still = nextMode === "still";
  const prep = nextMode === "prep";
  restoreModeSettings(nextMode);
  modeVideo.classList.toggle("active", nextMode === "video");
  modeStill.classList.toggle("active", still);
  modePrep.classList.toggle("active", prep);
  modeVideo.setAttribute("aria-pressed", String(nextMode === "video"));
  modeStill.setAttribute("aria-pressed", String(still));
  modePrep.setAttribute("aria-pressed", String(prep));
  brandMode.textContent = prep ? "Prep/Edit" : still ? "Still" : "Video";
  document.title = `TEGAKI / ${prep ? "Prep/Edit" : still ? "Still" : "Video"}`;
  document.body.dataset.mode = nextMode;
  stillSourceCard.hidden = !still;
  prepCard.hidden = !prep;
  durationField.hidden = still || prep;
  populateResolutionOptions();
  populateDurationOptions();
  updateVideoTypeView();
  controlColumn.setAttribute("aria-label", `${prep ? "Prep/Edit" : still ? "Still" : "Video"} controls`);
  previewEmpty.querySelector("#preview-heading").textContent = prep
    ? "Your prepared still will appear here"
    : still
      ? "Your still will appear here"
      : "Your video will appear here";
  $("preview-empty-copy").textContent = prep
    ? "Add a source image and describe the preparation."
    : still
      ? "Enter a prompt and generate a Native H3 still."
      : "Enter a prompt and generate a short Native H3 video.";
  promptInput.placeholder = prep ? "Describe the requested image preparation…" : "Describe the video...";
  footerMode.textContent = `H3 / Native ${prep ? "Prep/Edit" : still ? "Still" : "Video"}`;
  updateGenerateAvailability();
}

function isNarrowViewport() {
  return typeof window.matchMedia === "function"
    && window.matchMedia("(max-width: 820px)").matches;
}

function setNarrowView(nextView) {
  if (!["create", "result"].includes(nextView)) return;
  state.narrowView = nextView;
  document.body.dataset.narrowView = nextView;
  narrowCreateButton.classList.toggle("active", nextView === "create");
  narrowResultButton.classList.toggle("active", nextView === "result");
  narrowCreateButton.setAttribute("aria-pressed", String(nextView === "create"));
  narrowResultButton.setAttribute("aria-pressed", String(nextView === "result"));
}

function syncResponsiveMounts() {
  const wide = !isNarrowViewport();
  const actionSlot = wide ? stageActionSlot : generateActionSlot;
  const statusSlot = wide ? stageStatusSlot : statusStrip;
  if (generateActionDock.parentElement !== actionSlot) actionSlot.append(generateActionDock);
  if (generationStatusBlock.parentElement !== statusSlot) {
    if (wide) statusSlot.append(generationStatusBlock);
    else statusSlot.prepend(generationStatusBlock);
  }
  stageActionBar.setAttribute("aria-hidden", String(!wide));
}

function statusLabelForJob(job) {
  if (job?.state === "RUNNING") return "Generating";
  return job?.label || job?.state || "Unknown";
}

function renderSubmittingState() {
  generateLabel.textContent = state.submitting ? "Submitting…" : "Generate";
  submitStatus.hidden = !state.submitting;
  submitStatus.textContent = state.submitting ? "Submitting request…" : "";
  if (state.submitting) {
    generationStatus.textContent = "Submitting";
    setStatusDetail(activeStatusDetail({ state: "SUBMITTING" }));
    cancelButton.hidden = true;
  }
  updateGenerateAvailability();
}

function updateGenerateAvailability() {
  const uploading = Object.values(state.referenceUploading).some(Boolean)
    || state.stillSourceUploading
    || state.prepSourceUploading
    || state.prepDonorUploading
    || state.r2vPictureUploading
    || state.r2vMotionUploading
    || state.handoffInFlight;
  const referenceMode = state.mode === "video" && state.videoType === "reference";
  const referenceReady = !referenceMode
    || (referenceVideoEnabled() && state.backend === "READY" && Boolean(state.r2vPicture));
  const prepMode = state.mode === "prep";
  const prepReady = !prepMode
    || (state.backend === "READY" && Boolean(state.prepSource));
  generateButton.disabled = !promptInput.value.trim()
    || uploading
    || !referenceReady
    || !prepReady
    || state.submitting
    || Boolean(state.activeJob && !TERMINAL.has(state.activeJob.state));
  generateButton.hidden = !cancelButton.hidden;
}

function setDetails(message) {
  if (!message) {
    detailsPanel.hidden = true;
    detailsText.textContent = "";
    return;
  }
  detailsPanel.hidden = false;
  detailsText.textContent = message;
}

function updatePromptCount() {
  $("prompt-count").textContent = `${promptInput.value.length} / 4000`;
  updateGenerateAvailability();
}

const referenceViews = {
  start_frame: {
    file: referenceFile,
    add: referenceAdd,
    replace: referenceReplace,
    remove: referenceRemove,
    empty: $("reference-empty-start"),
    selected: referenceSelected,
    thumbnail: referenceThumbnail,
    name: referenceName,
    status: referenceStatus,
  },
  end_frame: {
    file: endReferenceFile,
    add: endReferenceAdd,
    replace: endReferenceReplace,
    remove: endReferenceRemove,
    empty: endReferenceEmpty,
    selected: endReferenceSelected,
    thumbnail: endReferenceThumbnail,
    name: endReferenceName,
    status: endReferenceStatus,
  },
};

function setStillSourceView(source) {
  state.stillSource = source;
  stillSourceSelected.hidden = !source;
  stillSourceEmpty.hidden = Boolean(source);
  if (!source) {
    stillSourceThumbnail.removeAttribute("src");
    stillSourceName.textContent = "";
    stillSourceStatus.textContent = "";
    updateGenerateAvailability();
    return;
  }
  stillSourceThumbnail.src = `${source.preview_url}?v=${encodeURIComponent(source.id)}`;
  stillSourceName.textContent = source.width && source.height
    ? `${source.width} x ${source.height}`
    : "Source image";
  stillSourceStatus.textContent = "";
  updateGenerateAvailability();
}

async function uploadStillSource(file) {
  if (!file) return;
  const body = new FormData();
  body.append("source", file, file.name);
  state.stillSourceUploading = true;
  stillSourceAdd.disabled = true;
  stillSourceReplace.disabled = true;
  stillSourceStatus.textContent = "Uploading source image…";
  updateGenerateAvailability();
  try {
    const result = await requestJson("/api/still/source", { method: "POST", body });
    if (!result.source || typeof result.source.id !== "string") {
      throw new Error("The Still source was not accepted by the upload boundary.");
    }
    setStillSourceView(result.source);
  } catch (error) {
    stillSourceStatus.textContent = error.message;
    setDetails(error.message);
  } finally {
    state.stillSourceUploading = false;
    stillSourceAdd.disabled = false;
    stillSourceReplace.disabled = false;
    stillSourceFile.value = "";
    updateGenerateAvailability();
  }
}

const prepViews = {
  source: {
    file: prepSourceFile,
    add: prepSourceAdd,
    replace: prepSourceReplace,
    remove: prepSourceRemove,
    empty: prepSourceEmpty,
    selected: prepSourceSelected,
    thumbnail: prepSourceThumbnail,
    name: prepSourceName,
    status: prepSourceStatus,
  },
  donor: {
    file: prepDonorFile,
    add: prepDonorAdd,
    replace: prepDonorReplace,
    remove: prepDonorRemove,
    empty: prepDonorEmpty,
    selected: prepDonorSelected,
    thumbnail: prepDonorThumbnail,
    name: prepDonorName,
    status: prepDonorStatus,
  },
};

function setPrepAssetView(kind, asset) {
  const view = prepViews[kind];
  if (kind === "source") state.prepSource = asset;
  else state.prepDonor = asset;
  view.selected.hidden = !asset;
  view.empty.hidden = Boolean(asset);
  if (!asset) {
    view.thumbnail.removeAttribute("src");
    view.name.textContent = "";
    view.status.textContent = "";
    updateGenerateAvailability();
    return;
  }
  view.thumbnail.src = `${asset.preview_url}?v=${encodeURIComponent(asset.id)}`;
  view.name.textContent = asset.name || (asset.width && asset.height
    ? `${asset.width} x ${asset.height}`
    : "Image");
  view.status.textContent = "";
  updateGenerateAvailability();
}

async function uploadPrepAsset(kind, file) {
  if (!file) return;
  const view = prepViews[kind];
  const body = new FormData();
  body.append(kind, file, file.name);
  state[`${kind === "source" ? "prepSource" : "prepDonor"}Uploading`] = true;
  view.add.disabled = true;
  view.replace.disabled = true;
  view.status.textContent = `Uploading ${kind === "source" ? "source" : "donor"} image…`;
  updateGenerateAvailability();
  try {
    const result = await requestJson(`/api/prep/${kind}`, { method: "POST", body });
    const asset = result[kind];
    if (!asset || typeof asset.id !== "string" || !/^[0-9a-f]{32}$/.test(asset.id)) {
      throw new Error(`The Prep/Edit ${kind} image was not accepted by the upload boundary.`);
    }
    setPrepAssetView(kind, asset);
  } catch (error) {
    view.status.textContent = error.message;
    setDetails(error.message);
  } finally {
    state[`${kind === "source" ? "prepSource" : "prepDonor"}Uploading`] = false;
    view.add.disabled = false;
    view.replace.disabled = false;
    view.file.value = "";
    updateGenerateAvailability();
  }
}

function setR2VPictureView(picture) {
  state.r2vPicture = picture;
  r2vPictureSelected.hidden = !picture;
  r2vPictureEmpty.hidden = Boolean(picture);
  if (!picture) {
    r2vPictureThumbnail.removeAttribute("src");
    r2vPictureName.textContent = "";
    r2vPictureStatus.textContent = "";
    updateGenerateAvailability();
    return;
  }
  r2vPictureThumbnail.src = `${picture.preview_url}?v=${encodeURIComponent(picture.id)}`;
  r2vPictureName.textContent = picture.name || `${picture.width || "?"} x ${picture.height || "?"}`;
  r2vPictureStatus.textContent = "";
  updateGenerateAvailability();
}

function setR2VMotionView(motionVideo) {
  state.r2vMotionVideo = motionVideo;
  r2vMotionSelected.hidden = !motionVideo;
  r2vMotionEmpty.hidden = Boolean(motionVideo);
  if (!motionVideo) {
    r2vMotionName.textContent = "";
    r2vMotionStatus.textContent = "";
    updateGenerateAvailability();
    return;
  }
  r2vMotionName.textContent = motionVideo.name || "MP4 motion reference";
  r2vMotionStatus.textContent = "";
  updateGenerateAvailability();
}

async function uploadR2VPicture(file) {
  if (!file) return;
  const body = new FormData();
  body.append("picture", file, file.name);
  state.r2vPictureUploading = true;
  r2vPictureAdd.disabled = true;
  r2vPictureReplace.disabled = true;
  r2vPictureStatus.textContent = "Uploading Character Image…";
  updateGenerateAvailability();
  try {
    const result = await requestJson("/api/r2v/picture", { method: "POST", body });
    if (!result.picture || typeof result.picture.id !== "string") {
      throw new Error("The Character Image was not accepted by the upload boundary.");
    }
    setR2VPictureView(result.picture);
  } catch (error) {
    r2vPictureStatus.textContent = error.message;
    setDetails(error.message);
  } finally {
    state.r2vPictureUploading = false;
    r2vPictureAdd.disabled = false;
    r2vPictureReplace.disabled = false;
    r2vPictureFile.value = "";
    updateGenerateAvailability();
  }
}

async function uploadR2VMotionVideo(file) {
  if (!file) return;
  const body = new FormData();
  body.append("motion_video", file, file.name);
  state.r2vMotionUploading = true;
  r2vMotionAdd.disabled = true;
  r2vMotionReplace.disabled = true;
  r2vMotionStatus.textContent = "Uploading Motion Video…";
  updateGenerateAvailability();
  try {
    const result = await requestJson("/api/r2v/video", { method: "POST", body });
    if (!result.motion_video || typeof result.motion_video.id !== "string") {
      throw new Error("The Motion Video was not accepted by the upload boundary.");
    }
    setR2VMotionView(result.motion_video);
  } catch (error) {
    r2vMotionStatus.textContent = error.message;
    setDetails(error.message);
  } finally {
    state.r2vMotionUploading = false;
    r2vMotionAdd.disabled = false;
    r2vMotionReplace.disabled = false;
    r2vMotionFile.value = "";
    updateGenerateAvailability();
  }
}

function isFileDrag(event) {
  return Array.from(event.dataTransfer?.types || []).includes("Files");
}

function singleDroppedFile(event, label) {
  const files = Array.from(event.dataTransfer?.files || []);
  if (files.length !== 1) {
    throw new Error(`${label}: drop exactly one local file.`);
  }
  const file = files[0];
  if (typeof File === "undefined" || !(file instanceof File)) {
    throw new Error(`${label}: only a local file can be dropped.`);
  }
  return file;
}

function installR2VDropzone(dropzone, label, upload) {
  if (!dropzone) return;
  const status = $(dropzone.dataset.h3DropStatus)
    || (label === "Character Image" ? r2vPictureStatus : r2vMotionStatus);
  let dragDepth = 0;
  const clearActive = () => {
    dragDepth = 0;
    dropzone.classList.remove("drag-active");
  };
  const activate = (event) => {
    if (!isFileDrag(event)) return;
    event.preventDefault();
    dragDepth += 1;
    dropzone.classList.add("drag-active");
  };
  dropzone.addEventListener("dragenter", activate);
  dropzone.addEventListener("dragover", (event) => {
    if (!isFileDrag(event)) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    dropzone.classList.add("drag-active");
  });
  dropzone.addEventListener("dragleave", (event) => {
    if (!isFileDrag(event)) return;
    if (event.relatedTarget instanceof Node && dropzone.contains(event.relatedTarget)) return;
    dragDepth = Math.max(0, dragDepth - 1);
    if (!dragDepth) clearActive();
  });
  dropzone.addEventListener("drop", async (event) => {
    // This is deliberately scoped to the owning slot so dropping a URL on the
    // rest of the page retains the existing browser behavior.
    if (event.dataTransfer?.types?.length || event.dataTransfer?.files?.length) {
      event.preventDefault();
    }
    clearActive();
    try {
      await upload(singleDroppedFile(event, label));
    } catch (error) {
      status.textContent = error.message;
      setDetails(error.message);
    }
  });
}

function installSingleFileDropzone(dropzone, label, upload, status) {
  if (!dropzone) return;
  dropzone.dataset.h3DropStatus = status?.id || "";
  installR2VDropzone(dropzone, label, upload);
}

function setReferenceSlotView(slot, reference) {
  const view = referenceViews[slot];
  state.references[slot] = reference;
  if (slot === "start_frame") state.reference = reference;
  view.selected.hidden = !reference;
  view.empty.hidden = Boolean(reference);
  if (!reference) {
    view.thumbnail.removeAttribute("src");
    view.name.textContent = "";
    view.status.textContent = "";
    updateGenerateAvailability();
    return;
  }
  view.thumbnail.src = `${reference.preview_url}?v=${encodeURIComponent(reference.id)}`;
  view.name.textContent = reference.width && reference.height
    ? `${reference.width} x ${reference.height}`
    : "Reference image";
  view.status.textContent = "";
  updateGenerateAvailability();
}

// Keep the H1B start-slot helper name for old browser smoke and compatibility.
function setReferenceView(reference) {
  setReferenceSlotView("start_frame", reference);
}

async function uploadReference(slot, file) {
  if (!file) return;
  const view = referenceViews[slot];
  const body = new FormData();
  body.append("slot", slot);
  body.append("reference", file, file.name);
  state.referenceUploading[slot] = true;
  view.add.disabled = true;
  view.replace.disabled = true;
  view.status.textContent = "Uploading reference…";
  updateGenerateAvailability();
  try {
    const response = await fetch("/api/references", { method: "POST", body, cache: "no-store" });
    let result = {};
    try { result = await response.json(); } catch { result = {}; }
    if (!response.ok) throw new Error(result.error || `Reference upload failed (${response.status})`);
    setReferenceSlotView(slot, result.reference);
  } catch (error) {
    view.status.textContent = error.message;
    setDetails(error.message);
  } finally {
    state.referenceUploading[slot] = false;
    view.add.disabled = false;
    view.replace.disabled = false;
    view.file.value = "";
    updateGenerateAvailability();
  }
}

function routeLabelFor(job) {
  return job.route_label || (
    job.references?.start_frame && job.references?.end_frame
      ? "Start + End"
      : job.references?.end_frame
        ? "End Frame"
        : job.reference_used
          ? "Start Frame"
          : "Text only"
  );
}

function renderActiveJobStatus(job) {
  generationStatus.textContent = statusLabelForJob(job);
  setStatusDetail(activeStatusDetail(job));
  cancelButton.hidden = !job.cancel_available;
  if (job.state === "FAILED" || job.state === "DISCONNECTED") {
    setDetails(activeStatusDetail(job));
  } else {
    setDetails("");
  }
  updateGenerateAvailability();
}

function showPreviewJob(job) {
  state.previewJob = job;
  previewState.textContent = statusLabelForJob(job);
  previewElapsed.textContent = `${Number(job.elapsed_seconds || 0).toFixed(1)}s`;
  previewOverlay.hidden = TERMINAL.has(job.state) && job.state !== "COMPLETED";
  const isStill = job.media_kind === "still";
  if (job.state === "COMPLETED" && isStill && job.image_url) {
    previewEmpty.hidden = true;
    previewVideo.hidden = true;
    previewImage.hidden = false;
    if (!previewImage.src.includes(job.image_url)) {
      previewImage.src = `${job.image_url}?v=${encodeURIComponent(job.job_id)}`;
    }
    const request = job.request || {};
    previewMeta.textContent = `${routeLabelFor(job)} · Completed in ${Number(job.elapsed_seconds || 0).toFixed(1)}s · ${request.width} x ${request.height}`;
  } else if (job.state === "COMPLETED" && !isStill && job.video_url) {
    previewEmpty.hidden = true;
    previewImage.hidden = true;
    previewVideo.hidden = false;
    if (!previewVideo.src.includes(job.video_url)) {
      previewVideo.src = `${job.video_url}?v=${encodeURIComponent(job.job_id)}`;
      previewVideo.load();
    }
    previewMeta.textContent = `${routeLabelFor(job)} · Completed in ${Number(job.elapsed_seconds || 0).toFixed(1)}s · ${job.request.width} x ${job.request.height} · ${job.request.duration}s`;
  } else {
    previewEmpty.hidden = false;
    previewVideo.hidden = true;
    previewImage.hidden = true;
    previewMeta.textContent = previewStatusDetail(job);
  }
}

function setActiveJob(job, { selectPreview = false } = {}) {
  state.activeJob = job;
  renderActiveJobStatus(job);
  if (selectPreview) showPreviewJob(job);
}

function updateActiveJob(job) {
  setActiveJob(job);
  if (job.state === "COMPLETED" || state.previewJob?.job_id === job.job_id) showPreviewJob(job);
}

async function pollJob() {
  const activeJobId = state.activeJob?.job_id;
  if (!activeJobId) return;
  try {
    const job = await requestJson(`/api/jobs/${encodeURIComponent(activeJobId)}`);
    if (state.activeJob?.job_id !== activeJobId) return;
    updateActiveJob(job);
    if (TERMINAL.has(job.state)) {
      await loadHistory();
      return;
    }
  } catch (error) {
    setStatusDetail(error.message);
  }
  state.pollTimer = window.setTimeout(pollJob, 1400);
}

async function submitGeneration(event) {
  event.preventDefault();
  if (!promptInput.value.trim()
    || state.submitting
    || Boolean(state.activeJob && !TERMINAL.has(state.activeJob.state))) return;
  const seedText = seedInput.value.trim();
  const seed = seedText === "" ? "random" : seedText;
  setDetails("");
  let accepted = false;
  try {
    let endpoint;
    let payload;
    if (state.mode === "prep") {
      if (state.backend !== "READY") throw new Error("Prep/Edit is waiting for the Native backend.");
      if (!state.prepSource) throw new Error("Source Image is required for Prep/Edit.");
      endpoint = "/api/prep/generate";
      payload = {
        prompt: promptInput.value,
        source_id: state.prepSource.id,
        donor_id: state.prepDonor?.id || null,
        seed,
      };
    } else {
      const [width, height] = resolutionInput.value.split("x").map(Number);
      payload = {
        prompt: promptInput.value,
        width,
        height,
        seed,
        steps: Number(stepsInput.value),
      };
      endpoint = "/api/generate";
    }
    if (state.mode === "still") {
      endpoint = "/api/still/generate";
      if (state.stillSource) payload.source_id = state.stillSource.id;
    } else if (state.mode === "video") {
      payload.duration = Number(durationInput.value);
      if (state.videoType === "reference") {
        if (state.backend !== "READY") throw new Error("Reference Video is waiting for the Native backend.");
        if (!state.r2vPicture) throw new Error("Character Image is required for Reference Video.");
        endpoint = "/api/r2v/generate";
        payload.video_type = "reference";
        payload.picture_id = state.r2vPicture.id;
        payload.motion_video_id = state.r2vMotionVideo?.id || null;
        delete payload.duration;
        payload.duration = 5;
        payload.width = 608;
        payload.height = 352;
      } else {
        payload.references = {
          start_frame: state.references.start_frame
            ? { id: state.references.start_frame.id, role: "start_frame" }
            : null,
          end_frame: state.references.end_frame
            ? { id: state.references.end_frame.id, role: "end_frame" }
            : null,
        };
      }
    }
    state.submitting = true;
    renderSubmittingState();
    const body = await requestJson(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    accepted = true;
    state.submitting = false;
    renderSubmittingState();
    setActiveJob(body.job, { selectPreview: true });
    if (isNarrowViewport()) setNarrowView("result");
    await pollJob();
  } catch (error) {
    state.submitting = false;
    renderSubmittingState();
    if (accepted) {
      setDetails(error.message);
      return;
    }
    state.activeJob = null;
    generationStatus.textContent = "Failed";
    state.backendStatusDetail = "";
    statusDetail.textContent = "Generation was not submitted.";
    setDetails(error.message);
    updateGenerateAvailability();
  }
}

async function cancelGeneration() {
  if (!state.activeJob?.job_id) return;
  try {
    const body = await requestJson(`/api/jobs/${encodeURIComponent(state.activeJob.job_id)}/cancel`, { method: "POST" });
    setActiveJob(body.job, { selectPreview: true });
    await loadHistory();
  } catch (error) {
    setDetails(error.message);
  }
}

async function pollBackend() {
  try {
    const status = await requestJson("/api/status");
    setBackendStatus(status.state, status.backend_profile_detail || status.error || "");
    queueCount.textContent = String(status.queue_count ?? 0);
  } catch (error) {
    setBackendStatus("DISCONNECTED", error.message);
  }
  state.backendTimer = window.setTimeout(pollBackend, 2200);
}

function formatTime(value) {
  if (!value) return "";
  try { return new Date(value).toLocaleString(); } catch { return value; }
}

function setHistoryActionStatus(message, isError = false) {
  historyActionStatus.hidden = !message;
  historyActionStatus.textContent = message;
  historyActionStatus.classList.toggle("error", isError);
}

async function verifyHistoryReference(reference, slot) {
  const label = slot === "start_frame" ? "Start Frame" : "End Frame";
  let response;
  try {
    response = await fetch(reference.preview_url, { cache: "no-store" });
  } catch {
    throw new Error(`${label} reference could not be verified.`);
  }
  if (!response.ok) {
    throw new Error(`${label} reference is no longer available.`);
  }
}

async function verifyStillSource(source) {
  let response;
  try {
    response = await fetch(source.preview_url, { cache: "no-store" });
  } catch {
    throw new Error("Still Source Image could not be verified.");
  }
  if (!response.ok) throw new Error("Still Source Image is no longer available.");
  const contentType = response.headers.get("content-type") || "";
  if (!/^image\/(png|jpeg)(?:;|$)/i.test(contentType)) {
    throw new Error("Still Source Image is not a supported PNG or JPEG.");
  }
}

function normalizePrepAsset(value, kind) {
  const label = kind === "source" ? "Prep Source Image" : "Prep Donor Image";
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${label} metadata is unavailable.`);
  }
  const id = typeof value.id === "string" ? value.id.trim() : "";
  if (!/^[0-9a-f]{32}$/.test(id)) throw new Error(`${label} metadata is invalid.`);
  return {
    ...value,
    id,
    preview_url: `/api/prep/assets/${encodeURIComponent(id)}`,
  };
}

async function verifyPrepAsset(asset, kind) {
  const label = kind === "source" ? "Prep Source Image" : "Prep Donor Image";
  const expected = `/api/prep/assets/${encodeURIComponent(asset.id)}`;
  let response;
  try {
    response = await fetch(expected, { cache: "no-store" });
  } catch {
    throw new Error(`${label} could not be verified.`);
  }
  if (!response.ok) throw new Error(`${label} is no longer available.`);
  const contentType = response.headers.get("content-type") || "";
  if (!/^image\/(png|jpeg|webp)(?:;|$)/i.test(contentType)) {
    throw new Error(`${label} is not a supported PNG, JPEG, or WebP.`);
  }
}

function standardResolutionValues() {
  const configured = state.config?.resolution_options;
  if (Array.isArray(configured) && configured.length) {
    return configuredResolutionOptions(false).map(resolutionValue);
  }
  return ["608x352", "736x416"];
}

function standardDurationValues() {
  const configured = state.config?.duration_options;
  if (Array.isArray(configured) && configured.length) return configured.map((option) => String(option.value));
  return ["5", "15"];
}

function historyScalarOptions() {
  return {
    resolutionValues: standardResolutionValues(),
    durationValues: standardDurationValues(),
    stepsValue: stepsInput.value,
    maxPromptLength: promptInput.maxLength,
  };
}

function normalizeR2VAsset(value, kind) {
  const label = kind === "picture" ? "Character Image" : "Motion Video";
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${label} metadata is unavailable.`);
  }
  const id = typeof value.id === "string" ? value.id.trim() : "";
  if (!/^[0-9a-f]{32}$/.test(id)) throw new Error(`${label} metadata is invalid.`);
  return {
    ...value,
    id,
    preview_url: `/api/r2v/${kind === "picture" ? "pictures" : "videos"}/${encodeURIComponent(id)}`,
  };
}

async function verifyR2VAsset(asset, kind) {
  const label = kind === "picture" ? "Character Image" : "Motion Video";
  const expected = `/api/r2v/${kind === "picture" ? "pictures" : "videos"}/${encodeURIComponent(asset.id)}`;
  let response;
  try {
    response = await fetch(expected, { cache: "no-store" });
  } catch {
    throw new Error(`${label} could not be verified.`);
  }
  if (!response.ok) throw new Error(`${label} is no longer available.`);
  const contentType = response.headers.get("content-type") || "";
  if (kind === "picture" && !/^image\/(png|jpeg|webp)(?:;|$)/i.test(contentType)) {
    throw new Error("Character Image is not a supported PNG, JPEG, or WebP.");
  }
  if (kind === "motion" && !/^video\/mp4(?:;|$)/i.test(contentType)) {
    throw new Error("Motion Video is not a supported MP4.");
  }
}

async function resolveReferenceVideoHistorySettings(entry) {
  if (!entry || entry.video_type !== "reference" || entry.media_kind === "still") {
    throw new Error("Reference Video History settings are invalid.");
  }
  const scalars = resolveHistoryScalars(entry, {
    resolutionValues: ["608x352"],
    durationValues: ["5"],
    stepsValue: "20",
    maxPromptLength: promptInput.maxLength,
  });
  const metadata = entry.reference_video;
  if (!metadata || typeof metadata !== "object" || Array.isArray(metadata)) {
    throw new Error("Reference Video assets are unavailable.");
  }
  const picture = normalizeR2VAsset(metadata.picture, "picture");
  const motionVideo = metadata.motion_video == null
    ? null
    : normalizeR2VAsset(metadata.motion_video, "motion");
  await verifyR2VAsset(picture, "picture");
  if (motionVideo) await verifyR2VAsset(motionVideo, "motion");
  return { ...scalars, picture, motionVideo };
}

function applyHistorySettings(settings) {
  promptInput.value = settings.prompt;
  state.videoResolution = settings.resolution;
  state.videoDuration = settings.duration;
  resolutionInput.value = settings.resolution;
  durationInput.value = settings.duration;
  seedInput.value = settings.seed;
  stepsInput.value = settings.steps;
  setReferenceSlotView("start_frame", settings.references.start_frame);
  setReferenceSlotView("end_frame", settings.references.end_frame);
  captureModeSettings();
  updatePromptCount();
}

function applyReferenceVideoHistorySettings(settings) {
  promptInput.value = settings.prompt;
  seedInput.value = settings.seed;
  stepsInput.value = settings.steps;
  setR2VPictureView(settings.picture);
  setR2VMotionView(settings.motionVideo);
  captureModeSettings();
  updatePromptCount();
}

function applyStillHistorySettings(settings) {
  promptInput.value = settings.prompt;
  state.stillResolution = settings.resolution;
  resolutionInput.value = settings.resolution;
  seedInput.value = settings.seed;
  stepsInput.value = settings.steps;
  setStillSourceView(settings.source);
  captureModeSettings();
  updatePromptCount();
}

function applyPrepHistorySettings(settings) {
  promptInput.value = settings.prompt;
  seedInput.value = settings.seed;
  stepsInput.value = settings.steps;
  setPrepAssetView("source", settings.source);
  setPrepAssetView("donor", settings.donor);
  captureModeSettings();
  updatePromptCount();
}

async function useHistorySettings(entry) {
  setHistoryActionStatus("Checking saved settings…");
  const before = snapshotR2VHandoffState();
  try {
    if (entry.media_kind === "still" && entry.route === "native_image_prep") {
      const settings = await resolvePrepHistorySettings(entry, {
        stepsValue: stepsInput.value,
        maxPromptLength: promptInput.maxLength,
        verifyAsset: verifyPrepAsset,
      });
      setMode("prep");
      applyPrepHistorySettings(settings);
    } else if (entry.media_kind === "still") {
      const settings = await resolveStillHistorySettings(entry, {
        resolutionValues: configuredResolutionOptions(true).map(resolutionValue),
        stepsValue: stepsInput.value,
        maxPromptLength: promptInput.maxLength,
        verifySource: verifyStillSource,
      });
      setMode("still");
      applyStillHistorySettings(settings);
    } else if (entry.video_type === "reference") {
      const settings = await resolveReferenceVideoHistorySettings(entry);
      if (!referenceVideoEnabled()) throw new Error("Reference · Experimental is unavailable in the current Native session.");
      setMode("video");
      setVideoType("reference");
      applyReferenceVideoHistorySettings(settings);
    } else {
      const settings = await resolveHistorySettings(entry, {
        ...historyScalarOptions(),
        verifyReference: verifyHistoryReference,
      });
      setMode("video");
      setVideoType("standard");
      applyHistorySettings(settings);
    }
    setHistoryActionStatus("Settings loaded.");
  } catch (error) {
    restoreR2VHandoffState(before);
    setHistoryActionStatus(`Settings were not changed. ${error.message}`, true);
  }
}

function generationIsActive() {
  return Boolean(state.activeJob && !TERMINAL.has(state.activeJob.state));
}

function snapshotR2VHandoffState() {
  return {
    mode: state.mode,
    videoType: state.videoType,
    videoResolution: state.videoResolution,
    stillResolution: state.stillResolution,
    videoDuration: state.videoDuration,
    prompt: promptInput.value,
    resolution: resolutionInput.value,
    duration: durationInput.value,
    seed: seedInput.value,
    steps: stepsInput.value,
    references: {
      start_frame: state.references.start_frame,
      end_frame: state.references.end_frame,
    },
    stillSource: state.stillSource,
    prepSource: state.prepSource,
    prepDonor: state.prepDonor,
    r2vPicture: state.r2vPicture,
    r2vMotionVideo: state.r2vMotionVideo,
    modeSettings: Object.fromEntries(
      Object.entries(state.modeSettings).map(([mode, settings]) => [mode, { ...settings }]),
    ),
  };
}

function restoreR2VHandoffState(snapshot) {
  state.modeSettings = Object.fromEntries(
    Object.entries(snapshot.modeSettings || {}).map(([mode, settings]) => [mode, { ...settings }]),
  );
  state.mode = snapshot.mode;
  state.videoType = snapshot.videoType;
  setMode(snapshot.mode);
  state.videoType = snapshot.videoType;
  state.videoResolution = snapshot.videoResolution;
  state.stillResolution = snapshot.stillResolution;
  state.videoDuration = snapshot.videoDuration;
  promptInput.value = snapshot.prompt;
  resolutionInput.value = snapshot.resolution;
  durationInput.value = snapshot.duration;
  seedInput.value = snapshot.seed;
  stepsInput.value = snapshot.steps;
  setReferenceSlotView("start_frame", snapshot.references.start_frame);
  setReferenceSlotView("end_frame", snapshot.references.end_frame);
  setStillSourceView(snapshot.stillSource);
  setPrepAssetView("source", snapshot.prepSource);
  setPrepAssetView("donor", snapshot.prepDonor);
  setR2VPictureView(snapshot.r2vPicture);
  setR2VMotionView(snapshot.r2vMotionVideo);
  populateResolutionOptions();
  populateDurationOptions();
  resolutionInput.value = snapshot.resolution;
  durationInput.value = snapshot.duration;
  updatePromptCount();
  updateVideoTypeView();
  updateGenerateAvailability();
}

async function useHistoryHandoff(entry, kind) {
  const isStill = kind === "picture";
  const label = isStill ? "Generated Still" : "Generated Video";
  const expectedMediaKind = isStill ? "still" : "video";
  const sourceUrl = isStill ? entry?.image_url : entry?.video_url;
  if (state.handoffInFlight) return;
  if (generationIsActive()) {
    setHistoryActionStatus("Handoff is unavailable while a generation is active.", true);
    return;
  }
  if (
    !entry
    || entry.state !== "COMPLETED"
    || entry.media_kind !== expectedMediaKind
    || typeof sourceUrl !== "string"
    || !sourceUrl.trim()
  ) {
    setHistoryActionStatus(`${label} is available only for a completed ${isStill ? "Still" : "Video"} result.`, true);
    return;
  }
  const snapshot = snapshotR2VHandoffState();
  state.handoffInFlight = true;
  updateGenerateAvailability();
  setHistoryActionStatus(`Preparing ${label}…`);
  try {
    const endpoint = isStill ? "/api/r2v/from-still" : "/api/r2v/from-video";
    const result = await requestJson(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: entry.job_id }),
    });
    const rawAsset = isStill ? result.picture : result.motion_video;
    const asset = normalizeR2VAsset(rawAsset, isStill ? "picture" : "motion");
    const expectedSourceKind = isStill ? "generated_still" : "generated_video";
    if (asset.source_kind !== expectedSourceKind || asset.source_job_id !== entry.job_id) {
      throw new Error(`${label} provenance could not be verified.`);
    }
    await verifyR2VAsset(asset, isStill ? "picture" : "motion");
    if (generationIsActive()) {
      throw new Error("Handoff was stopped because a generation became active.");
    }
    setMode("video");
    setVideoType("reference");
    if (state.videoType !== "reference") {
      throw new Error("Reference · Experimental is unavailable in the current Native session.");
    }
    if (isStill) setR2VPictureView(asset);
    else setR2VMotionView(asset);
    setHistoryActionStatus(`${label} is ready in Reference.`);
  } catch (error) {
    restoreR2VHandoffState(snapshot);
    setHistoryActionStatus(`Handoff was not applied. ${error.message}`, true);
  } finally {
    state.handoffInFlight = false;
    updateGenerateAvailability();
  }
}

async function usePrepSourceHandoff(entry) {
  if (state.handoffInFlight) return;
  if (generationIsActive()) {
    setHistoryActionStatus("Handoff is unavailable while a generation is active.", true);
    return;
  }
  if (
    !entry
    || entry.state !== "COMPLETED"
    || entry.media_kind !== "still"
    || typeof entry.image_url !== "string"
    || !entry.image_url.trim()
  ) {
    setHistoryActionStatus("Edit in Prep is available only for a completed Still result.", true);
    return;
  }
  const snapshot = snapshotR2VHandoffState();
  state.handoffInFlight = true;
  updateGenerateAvailability();
  setHistoryActionStatus("Preparing Prep Source…");
  try {
    const result = await requestJson("/api/prep/from-still", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: entry.job_id }),
    });
    const asset = normalizePrepAsset(result.source, "source");
    if (asset.source_kind !== "generated_still" || asset.source_job_id !== entry.job_id) {
      throw new Error("Prep Source provenance could not be verified.");
    }
    await verifyPrepAsset(asset, "source");
    if (generationIsActive()) {
      throw new Error("Handoff was stopped because a generation became active.");
    }
    setMode("prep");
    setPrepAssetView("source", asset);
    setHistoryActionStatus("Generated Still is ready as the new Prep Source.");
  } catch (error) {
    restoreR2VHandoffState(snapshot);
    setHistoryActionStatus(`Edit in Prep was not applied. ${error.message}`, true);
  } finally {
    state.handoffInFlight = false;
    updateGenerateAvailability();
  }
}

function captureContinuationFrame(sourceUrl) {
  return new Promise((resolve, reject) => {
    const video = document.createElement("video");
    video.preload = "auto";
    video.muted = true;
    video.playsInline = true;
    video.setAttribute("aria-hidden", "true");
    video.style.position = "fixed";
    video.style.left = "-10000px";
    video.style.width = "1px";
    video.style.height = "1px";
    video.style.opacity = "0";
    video.style.pointerEvents = "none";
    document.body.append(video);
    let settled = false;
    let finalFrameTarget = null;
    let forcedFinalSeek = false;
    let frameWaitTimer = null;
    let frameStabilityTimer = null;

    const cleanup = () => {
      if (frameWaitTimer !== null) window.clearTimeout(frameWaitTimer);
      if (frameStabilityTimer !== null) window.clearTimeout(frameStabilityTimer);
      video.pause();
      video.removeAttribute("src");
      video.load();
      video.remove();
    };
    const fail = (message) => {
      if (settled) return;
      settled = true;
      cleanup();
      reject(new Error(message));
    };
    const finish = (value) => {
      if (settled) return;
      settled = true;
      cleanup();
      resolve(value);
    };
    const capture = (capturedCurrentTime = video.currentTime) => {
      if (!video.videoWidth || !video.videoHeight) {
        fail("The source video has no decodable frame.");
        return;
      }
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const context = canvas.getContext("2d");
      if (!context) {
        fail("The final frame canvas could not be created.");
        return;
      }
      try {
        context.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
      } catch {
        fail("The final frame could not be drawn.");
        return;
      }
      const captureTime = Number.isFinite(capturedCurrentTime) ? capturedCurrentTime : video.currentTime;
      canvas.toBlob((blob) => {
        if (!blob || blob.type !== "image/png") {
          fail("The final frame could not be encoded as PNG.");
          return;
        }
        finish({
          blob,
          duration: video.duration,
          currentTime: captureTime,
          width: video.videoWidth,
          height: video.videoHeight,
        });
      }, "image/png");
    };
    const seekTolerance = Math.max(0.05, 1 / 24);
    const captureAtFinalFrame = (frameTime) => {
      if (finalFrameTarget > 0 && frameTime < finalFrameTarget - seekTolerance) {
        captureDecodedFrame(frameTime);
        return;
      }
      video.pause();
      capture(frameTime);
    };
    const scheduleNextFrame = () => {
      if (typeof video.requestVideoFrameCallback === "function") {
        video.requestVideoFrameCallback((_now, metadata) => {
          const frameTime = Number.isFinite(metadata.mediaTime) ? metadata.mediaTime : video.currentTime;
          captureDecodedFrame(frameTime);
        });
        return;
      }
      frameStabilityTimer = window.setTimeout(() => captureDecodedFrame(video.currentTime), 50);
    };
    function captureDecodedFrame(observedTime) {
      if (!Number.isFinite(finalFrameTarget)) {
        fail("The source video final frame target could not be determined.");
        return;
      }
      const frameTime = Number.isFinite(observedTime) ? observedTime : video.currentTime;
      if (finalFrameTarget > 0 && frameTime < finalFrameTarget - seekTolerance) {
        if (!forcedFinalSeek) {
          forcedFinalSeek = true;
          try {
            video.currentTime = finalFrameTarget;
          } catch {
            fail("The source video could not seek to its final frame.");
            return;
          }
        }
        scheduleNextFrame();
        return;
      }
      if (video.readyState < 2) {
        scheduleNextFrame();
        return;
      }
      if (typeof video.requestVideoFrameCallback === "function") {
        video.requestVideoFrameCallback((_now, metadata) => {
          const decodedTime = Number.isFinite(metadata.mediaTime) ? metadata.mediaTime : video.currentTime;
          captureAtFinalFrame(decodedTime);
        });
        return;
      }
      frameStabilityTimer = window.setTimeout(() => captureAtFinalFrame(video.currentTime), 100);
    }
    video.addEventListener("loadedmetadata", () => {
      if (!Number.isFinite(video.duration) || video.duration <= 0) {
        fail("The source video duration could not be read.");
        return;
      }
      try {
        finalFrameTarget = Math.max(0, video.duration - 0.05);
        video.currentTime = finalFrameTarget;
        frameWaitTimer = window.setTimeout(
          () => fail("The source video could not seek to its final frame."),
          Math.max(10000, (video.duration + 2) * 1000),
        );
        const playback = video.play();
        if (playback && typeof playback.then === "function") {
          playback.then(scheduleNextFrame).catch(() => fail("The source video could not be played."));
        } else {
          scheduleNextFrame();
        }
      } catch {
        fail("The source video could not seek to its final frame.");
      }
    }, { once: true });
    video.addEventListener("error", () => fail("The source video could not be read."), { once: true });
    video.src = sourceUrl;
    video.load();
  });
}

async function uploadContinuationReference(frame, sourceJobId) {
  const body = new FormData();
  body.append("slot", "start_frame");
  body.append("reference", frame.blob, `h1c-${sourceJobId}-end.png`);
  state.referenceUploading.start_frame = true;
  updateGenerateAvailability();
  try {
    const result = await requestJson("/api/references", { method: "POST", body });
    if (!result.reference || typeof result.reference.id !== "string") {
      throw new Error("The bridge frame was not accepted by the Reference upload boundary.");
    }
    return result.reference;
  } finally {
    state.referenceUploading.start_frame = false;
    updateGenerateAvailability();
  }
}

function snapshotFormSettings() {
  return {
    prompt: promptInput.value,
    resolution: resolutionInput.value,
    duration: durationInput.value,
    seed: seedInput.value,
    steps: stepsInput.value,
    references: {
      start_frame: state.references.start_frame,
      end_frame: state.references.end_frame,
    },
  };
}

function restoreFormSettings(snapshot) {
  promptInput.value = snapshot.prompt;
  if (state.mode === "still") state.stillResolution = snapshot.resolution;
  else state.videoResolution = snapshot.resolution;
  state.videoDuration = snapshot.duration;
  resolutionInput.value = snapshot.resolution;
  durationInput.value = snapshot.duration;
  seedInput.value = snapshot.seed;
  stepsInput.value = snapshot.steps;
  setReferenceSlotView("start_frame", snapshot.references.start_frame);
  setReferenceSlotView("end_frame", snapshot.references.end_frame);
  updatePromptCount();
}

function applyContinuationSettings(settings) {
  const before = snapshotFormSettings();
  try {
    promptInput.value = settings.prompt;
    state.videoResolution = settings.resolution;
    state.videoDuration = settings.duration;
    resolutionInput.value = settings.resolution;
    durationInput.value = settings.duration;
    seedInput.value = settings.seed;
    stepsInput.value = settings.steps;
    setReferenceSlotView("start_frame", settings.reference);
    setReferenceSlotView("end_frame", null);
    updatePromptCount();
  } catch (error) {
    restoreFormSettings(before);
    throw error;
  }
}

async function prepareContinuation(entry) {
  setHistoryActionStatus("Preparing continuation…");
  try {
    const scalarSettings = resolveHistoryScalars(entry, historyScalarOptions());
    const sourceUrl = validateContinuationSource(entry);
    const frame = await captureContinuationFrame(sourceUrl);
    const reference = await uploadContinuationReference(frame, entry.job_id);
    setMode("video");
    applyContinuationSettings({ ...scalarSettings, reference });
    historyActionStatus.dataset.continuationDuration = String(frame.duration);
    historyActionStatus.dataset.continuationCurrentTime = String(frame.currentTime);
    historyActionStatus.dataset.continuationWidth = String(frame.width);
    historyActionStatus.dataset.continuationHeight = String(frame.height);
    historyActionStatus.dataset.continuationReferenceId = reference.id;
    setHistoryActionStatus("Continuation prepared. Edit the prompt if needed, then Generate.");
  } catch (error) {
    setHistoryActionStatus(`Continuation was not prepared. ${error.message || "The source video could not be read."}`, true);
  }
}

function createHistoryCard(entry) {
  const card = document.createElement("article");
  card.className = "history-card";
  const isStill = entry.media_kind === "still";
  if (isStill && entry.image_url) {
    const image = document.createElement("img");
    image.className = "history-thumb history-image";
    image.src = entry.image_url;
    image.alt = "Generated Still result";
    image.addEventListener("click", () => {
      showPreviewJob(entry);
      if (isNarrowViewport()) setNarrowView("result");
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    card.append(image);
  } else if (!isStill && entry.video_url) {
    const video = document.createElement("video");
    video.className = "history-thumb";
    video.src = entry.video_url;
    video.muted = true;
    video.loop = true;
    video.preload = "metadata";
    video.addEventListener("mouseenter", () => video.play().catch(() => {}));
    video.addEventListener("mouseleave", () => { video.pause(); video.currentTime = 0; });
    video.addEventListener("click", () => {
      showPreviewJob(entry);
      if (isNarrowViewport()) setNarrowView("result");
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    card.append(video);
  } else {
    const failed = document.createElement("div");
    failed.className = "history-failed";
    failed.textContent = entry.label || entry.state;
    card.append(failed);
  }
  const content = document.createElement("div");
  content.className = "history-content";
  const kindBadge = document.createElement("span");
  const isPrep = isStill && entry.route === "native_image_prep";
  kindBadge.className = `history-kind-badge ${isPrep ? "prep" : isStill ? "still" : "video"}`;
  kindBadge.textContent = isStill ? "Still" : "Video";
  if (isPrep) kindBadge.textContent = "Prep/Edit";
  const open = document.createElement("button");
  open.type = "button";
  const routeLabel = entry.route_label || (
    entry.references?.start_frame && entry.references?.end_frame
      ? "Start + End"
      : entry.references?.end_frame
        ? "End Frame"
        : entry.reference_used
          ? "Start Frame"
          : "Text only"
  );
  open.textContent = `${entry.label || entry.state} · ${routeLabel}`;
  open.addEventListener("click", () => {
    showPreviewJob(entry);
    if (isNarrowViewport()) setNarrowView("result");
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  const prompt = document.createElement("div");
  prompt.className = "history-prompt";
  prompt.textContent = entry.request?.prompt || "";
  const time = document.createElement("time");
  time.className = "history-time";
  time.textContent = formatTime(entry.completed_at || entry.created_at);
  const useSettings = document.createElement("button");
  useSettings.type = "button";
  useSettings.className = "quiet-button history-use-settings";
  useSettings.textContent = "Use settings";
  useSettings.setAttribute("aria-label", `Use settings from ${routeLabel} History result`);
  useSettings.addEventListener("click", () => useHistorySettings(entry));
  const actions = document.createElement("div");
  actions.className = "history-actions";
  actions.append(useSettings);
  if (isStill && entry.state === "COMPLETED" && typeof entry.image_url === "string" && entry.image_url.trim()) {
    const prepButton = document.createElement("button");
    prepButton.type = "button";
    prepButton.className = "quiet-button history-handoff";
    prepButton.textContent = "Edit in Prep";
    prepButton.setAttribute("aria-label", `Use ${routeLabel} Still as the new Prep Source`);
    prepButton.addEventListener("click", () => usePrepSourceHandoff(entry));
    actions.append(prepButton);

    const characterButton = document.createElement("button");
    characterButton.type = "button";
    characterButton.className = "quiet-button history-handoff";
    characterButton.textContent = "Use as Character";
    characterButton.setAttribute("aria-label", `Use ${routeLabel} Still as Character Image`);
    characterButton.addEventListener("click", () => useHistoryHandoff(entry, "picture"));
    actions.append(characterButton);
  }
  if (!isStill && entry.state === "COMPLETED" && typeof entry.video_url === "string" && entry.video_url.trim()) {
    const motionButton = document.createElement("button");
    motionButton.type = "button";
    motionButton.className = "quiet-button history-handoff";
    motionButton.textContent = "Use as Motion";
    motionButton.setAttribute("aria-label", `Use ${routeLabel} Video as Motion Video`);
    motionButton.addEventListener("click", () => useHistoryHandoff(entry, "motion"));
    actions.append(motionButton);
  }
  if (!isStill && entry.state === "COMPLETED" && typeof entry.video_url === "string" && entry.video_url.trim() && entry.video_type !== "reference") {
    const continueButton = document.createElement("button");
    continueButton.type = "button";
    continueButton.className = "quiet-button history-continue";
    continueButton.textContent = "Continue";
    continueButton.title = "Use this result's end frame as the next Start Frame.";
    continueButton.setAttribute("aria-label", `Continue from ${routeLabel} History result`);
    continueButton.addEventListener("click", () => prepareContinuation(entry));
    actions.append(continueButton);
  }
  content.append(kindBadge, open, prompt, time, actions);
  card.append(content);
  return card;
}

async function loadHistory() {
  try {
    const body = await requestJson("/api/history");
    historyCount.textContent = String(body.entries?.length || 0);
    historyList.replaceChildren();
    if (!body.entries?.length) {
      const empty = document.createElement("div");
      empty.className = "history-empty";
      empty.textContent = "Completed results from this session will appear here.";
      historyList.append(empty);
      return;
    }
    body.entries.forEach((entry) => historyList.append(createHistoryCard(entry)));
    if (!state.previewJob) showPreviewJob(body.entries[0]);
  } catch (error) {
    historyCount.textContent = "—";
    setStatusDetail(error.message);
  }
}

async function loadConfig() {
  try {
    const config = await requestJson("/api/config");
    state.config = config;
    videoTypeReference.disabled = !referenceVideoEnabled();
    videoTypeReference.title = referenceVideoEnabled()
      ? "Experimental Reference Video"
      : "Reference Video is unavailable in this Native session";
    populateResolutionOptions();
    populateDurationOptions();
    updateVideoTypeView();
    updateGenerateAvailability();
  } catch (error) {
    setDetails(error.message);
  }
}

promptInput.addEventListener("input", updatePromptCount);
resolutionInput.addEventListener("change", rememberCurrentResolution);
durationInput.addEventListener("change", () => {
  if (state.mode === "video" && state.videoType === "reference") return;
  state.videoDuration = durationInput.value;
});
form.addEventListener("submit", submitGeneration);
cancelButton.addEventListener("click", cancelGeneration);
narrowCreateButton.addEventListener("click", () => setNarrowView("create"));
narrowResultButton.addEventListener("click", () => setNarrowView("result"));
modeVideo.addEventListener("click", () => setMode("video"));
modeStill.addEventListener("click", () => setMode("still"));
modePrep.addEventListener("click", () => setMode("prep"));
videoTypeStandard.addEventListener("click", () => setVideoType("standard"));
videoTypeReference.addEventListener("click", () => setVideoType("reference"));
$("random-seed").addEventListener("click", () => { seedInput.value = ""; seedInput.focus(); });
referenceAdd.addEventListener("click", () => referenceFile.click());
referenceReplace.addEventListener("click", () => referenceFile.click());
referenceFile.addEventListener("change", () => uploadReference("start_frame", referenceFile.files?.[0]));
referenceRemove.addEventListener("click", () => setReferenceView(null));
endReferenceAdd.addEventListener("click", () => endReferenceFile.click());
endReferenceReplace.addEventListener("click", () => endReferenceFile.click());
endReferenceFile.addEventListener("change", () => uploadReference("end_frame", endReferenceFile.files?.[0]));
endReferenceRemove.addEventListener("click", () => setReferenceSlotView("end_frame", null));
stillSourceAdd.addEventListener("click", () => stillSourceFile.click());
stillSourceReplace.addEventListener("click", () => stillSourceFile.click());
stillSourceFile.addEventListener("change", () => uploadStillSource(stillSourceFile.files?.[0]));
stillSourceRemove.addEventListener("click", () => setStillSourceView(null));
prepSourceAdd.addEventListener("click", () => prepSourceFile.click());
prepSourceReplace.addEventListener("click", () => prepSourceFile.click());
prepSourceFile.addEventListener("change", () => uploadPrepAsset("source", prepSourceFile.files?.[0]));
prepSourceRemove.addEventListener("click", () => setPrepAssetView("source", null));
prepDonorAdd.addEventListener("click", () => prepDonorFile.click());
prepDonorReplace.addEventListener("click", () => prepDonorFile.click());
prepDonorFile.addEventListener("change", () => uploadPrepAsset("donor", prepDonorFile.files?.[0]));
prepDonorRemove.addEventListener("click", () => setPrepAssetView("donor", null));
r2vPictureAdd.addEventListener("click", () => r2vPictureFile.click());
r2vPictureReplace.addEventListener("click", () => r2vPictureFile.click());
r2vPictureFile.addEventListener("change", () => uploadR2VPicture(r2vPictureFile.files?.[0]));
r2vPictureRemove.addEventListener("click", () => setR2VPictureView(null));
r2vMotionAdd.addEventListener("click", () => r2vMotionFile.click());
r2vMotionReplace.addEventListener("click", () => r2vMotionFile.click());
r2vMotionFile.addEventListener("change", () => uploadR2VMotionVideo(r2vMotionFile.files?.[0]));
r2vMotionRemove.addEventListener("click", () => setR2VMotionView(null));
installR2VDropzone(r2vPictureDropzone, "Character Image", uploadR2VPicture);
installR2VDropzone(r2vMotionDropzone, "Motion Video", uploadR2VMotionVideo);
installSingleFileDropzone(prepSourceDropzone, "Prep Source Image", (file) => uploadPrepAsset("source", file), prepSourceStatus);
installSingleFileDropzone(prepDonorDropzone, "Prep Donor Image", (file) => uploadPrepAsset("donor", file), prepDonorStatus);

window.addEventListener("resize", syncResponsiveMounts);
syncResponsiveMounts();

updatePromptCount();
setReferenceSlotView("start_frame", null);
setReferenceSlotView("end_frame", null);
setStillSourceView(null);
setPrepAssetView("source", null);
setPrepAssetView("donor", null);
setNarrowView("create");
setMode("video");
loadConfig();
loadHistory();
pollBackend();
