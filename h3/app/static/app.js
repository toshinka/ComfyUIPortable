import { activeStatusDetail, previewStatusDetail } from "./job-status-copy.js";
import { resolveHistorySettings } from "./history-settings.js";
import { resolveHistoryScalars } from "./history-settings.js";
import { resolveStillHistorySettings } from "./still-history-settings.js";
import { validateContinuationSource } from "./continuation-source.js";

const state = {
  mode: "video",
  backend: "CONNECTING",
  config: null,
  videoResolution: "608x352",
  stillResolution: "608x352",
  videoDuration: "5",
  activeJob: null,
  previewJob: null,
  references: { start_frame: null, end_frame: null },
  reference: null,
  referenceUploading: { start_frame: false, end_frame: false },
  stillSource: null,
  stillSourceUploading: false,
  pollTimer: null,
  backendTimer: null,
};

const $ = (id) => document.getElementById(id);
const form = $("generate-form");
const promptInput = $("prompt");
const brandMode = $("brand-mode");
const modeVideo = $("mode-video");
const modeStill = $("mode-still");
const controlColumn = $("control-column");
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
const durationInput = $("duration");
const seedInput = $("seed");
const stepsInput = $("steps");
const generateButton = $("generate-button");
const cancelButton = $("cancel-button");
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
  backendLabel.textContent = next === "READY" ? "Ready" : next === "DISCONNECTED" ? "Backend disconnected" : "Connecting";
  if (message && !state.activeJob) statusDetail.textContent = message;
}

function resolutionValue(option) {
  return `${Number(option.width)}x${Number(option.height)}`;
}

function configuredResolutionOptions(still = false) {
  const configured = still
    ? state.config?.still?.resolution_options
    : state.config?.resolution_options;
  if (Array.isArray(configured) && configured.length) return configured;
  return [{ label: "608 x 352", width: 608, height: 352 }];
}

function configuredDurationOptions() {
  const configured = state.config?.duration_options;
  if (Array.isArray(configured) && configured.length) return configured;
  return [{ label: "5 seconds", value: 5 }];
}

function rememberCurrentResolution() {
  const key = state.mode === "still" ? "stillResolution" : "videoResolution";
  if (resolutionInput.value) state[key] = resolutionInput.value;
}

function populateResolutionOptions() {
  const still = state.mode === "still";
  const key = still ? "stillResolution" : "videoResolution";
  const options = configuredResolutionOptions(still).filter((item) =>
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
  state[key] = values.includes(state[key]) ? state[key] : values[0];
  resolutionInput.value = state[key];
}

function populateDurationOptions() {
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
  state.videoDuration = values.includes(state.videoDuration) ? state.videoDuration : values[0];
  durationInput.value = state.videoDuration;
}

function setMode(nextMode) {
  if (nextMode !== "video" && nextMode !== "still") return;
  rememberCurrentResolution();
  state.mode = nextMode;
  const still = nextMode === "still";
  modeVideo.classList.toggle("active", !still);
  modeStill.classList.toggle("active", still);
  modeVideo.setAttribute("aria-pressed", String(!still));
  modeStill.setAttribute("aria-pressed", String(still));
  brandMode.textContent = still ? "Still" : "Video";
  document.title = `TEGAKI / ${still ? "Still" : "Video"}`;
  document.body.dataset.mode = nextMode;
  videoReferenceCard.hidden = still;
  stillSourceCard.hidden = !still;
  durationField.hidden = still;
  durationInput.disabled = still;
  populateResolutionOptions();
  controlColumn.setAttribute("aria-label", `${still ? "Still" : "Video"} controls`);
  previewEmpty.querySelector("#preview-heading").textContent = still
    ? "Your still will appear here"
    : "Your video will appear here";
  $("preview-empty-copy").textContent = still
    ? "Enter a prompt and generate a Native H3 still."
    : "Enter a prompt and generate a short Native H3 video.";
  footerMode.textContent = `H3 / Native ${still ? "Still" : "Video"}`;
  updateGenerateAvailability();
}

function updateGenerateAvailability() {
  const uploading = Object.values(state.referenceUploading).some(Boolean) || state.stillSourceUploading;
  generateButton.disabled = !promptInput.value.trim() || uploading || Boolean(state.activeJob && !TERMINAL.has(state.activeJob.state));
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
  generationStatus.textContent = job.label || job.state;
  statusDetail.textContent = activeStatusDetail(job);
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
  previewState.textContent = job.label || job.state;
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
    statusDetail.textContent = error.message;
  }
  state.pollTimer = window.setTimeout(pollJob, 1400);
}

async function submitGeneration(event) {
  event.preventDefault();
  if (!promptInput.value.trim()) return;
  const [width, height] = resolutionInput.value.split("x").map(Number);
  const seedText = seedInput.value.trim();
  const seed = seedText === "" ? "random" : seedText;
  setDetails("");
  try {
    const payload = {
      prompt: promptInput.value,
      width,
      height,
      seed,
      steps: Number(stepsInput.value),
    };
    let endpoint = "/api/generate";
    if (state.mode === "still") {
      endpoint = "/api/still/generate";
      if (state.stillSource) payload.source_id = state.stillSource.id;
    } else {
      payload.duration = Number(durationInput.value);
      payload.references = {
        start_frame: state.references.start_frame
          ? { id: state.references.start_frame.id, role: "start_frame" }
          : null,
        end_frame: state.references.end_frame
          ? { id: state.references.end_frame.id, role: "end_frame" }
          : null,
      };
    }
    const body = await requestJson(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setActiveJob(body.job, { selectPreview: true });
    await pollJob();
  } catch (error) {
    state.activeJob = null;
    generationStatus.textContent = "Failed";
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
    setBackendStatus(status.state, status.error || "");
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

function historyScalarOptions() {
  return {
    resolutionValues: configuredResolutionOptions(false).map(resolutionValue),
    durationValues: configuredDurationOptions().map((option) => String(option.value)),
    stepsValue: stepsInput.value,
    maxPromptLength: promptInput.maxLength,
  };
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
  updatePromptCount();
}

function applyStillHistorySettings(settings) {
  promptInput.value = settings.prompt;
  state.stillResolution = settings.resolution;
  resolutionInput.value = settings.resolution;
  seedInput.value = settings.seed;
  stepsInput.value = settings.steps;
  setStillSourceView(settings.source);
  updatePromptCount();
}

async function useHistorySettings(entry) {
  setHistoryActionStatus("Checking saved settings…");
  try {
    if (entry.media_kind === "still") {
      const settings = await resolveStillHistorySettings(entry, {
        resolutionValues: configuredResolutionOptions(true).map(resolutionValue),
        stepsValue: stepsInput.value,
        maxPromptLength: promptInput.maxLength,
        verifySource: verifyStillSource,
      });
      setMode("still");
      applyStillHistorySettings(settings);
    } else {
      const settings = await resolveHistorySettings(entry, {
        ...historyScalarOptions(),
        verifyReference: verifyHistoryReference,
      });
      setMode("video");
      applyHistorySettings(settings);
    }
    setHistoryActionStatus("Settings loaded.");
  } catch (error) {
    setHistoryActionStatus(`Settings were not changed. ${error.message}`, true);
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
    image.addEventListener("click", () => { showPreviewJob(entry); window.scrollTo({ top: 0, behavior: "smooth" }); });
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
    video.addEventListener("click", () => { showPreviewJob(entry); window.scrollTo({ top: 0, behavior: "smooth" }); });
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
  kindBadge.className = `history-kind-badge ${isStill ? "still" : "video"}`;
  kindBadge.textContent = isStill ? "Still" : "Video";
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
  open.addEventListener("click", () => { showPreviewJob(entry); window.scrollTo({ top: 0, behavior: "smooth" }); });
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
  if (!isStill && entry.state === "COMPLETED" && typeof entry.video_url === "string" && entry.video_url.trim()) {
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
    statusDetail.textContent = error.message;
  }
}

async function loadConfig() {
  try {
    const config = await requestJson("/api/config");
    state.config = config;
    populateResolutionOptions();
    populateDurationOptions();
  } catch (error) {
    setDetails(error.message);
  }
}

promptInput.addEventListener("input", updatePromptCount);
resolutionInput.addEventListener("change", rememberCurrentResolution);
durationInput.addEventListener("change", () => { state.videoDuration = durationInput.value; });
form.addEventListener("submit", submitGeneration);
cancelButton.addEventListener("click", cancelGeneration);
modeVideo.addEventListener("click", () => setMode("video"));
modeStill.addEventListener("click", () => setMode("still"));
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

updatePromptCount();
setReferenceSlotView("start_frame", null);
setReferenceSlotView("end_frame", null);
setStillSourceView(null);
setMode("video");
loadConfig();
loadHistory();
pollBackend();
