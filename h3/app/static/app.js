const state = {
  backend: "CONNECTING",
  activeJob: null,
  previewJob: null,
  references: { start_frame: null, end_frame: null },
  reference: null,
  referenceUploading: { start_frame: false, end_frame: false },
  pollTimer: null,
  backendTimer: null,
};

const $ = (id) => document.getElementById(id);
const form = $("generate-form");
const promptInput = $("prompt");
const referenceFile = $("reference-file");
const referenceAdd = $("reference-add");
const referenceReplace = $("reference-replace");
const referenceRemove = $("reference-remove");
const referenceEmpty = $("reference-empty");
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
const previewOverlay = $("preview-overlay");
const previewState = $("preview-state");
const previewElapsed = $("preview-elapsed");
const previewMeta = $("preview-meta");
const detailsPanel = $("details-panel");
const detailsText = $("details-text");
const historyList = $("history-list");

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

function updateGenerateAvailability() {
  const uploading = Object.values(state.referenceUploading).some(Boolean);
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

function updateReferenceEmpty() {
  referenceEmpty.hidden = Object.values(state.references).some(Boolean);
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
    updateReferenceEmpty();
    updateGenerateAvailability();
    return;
  }
  view.thumbnail.src = `${reference.preview_url}?v=${encodeURIComponent(reference.id)}`;
  view.name.textContent = `${reference.width} x ${reference.height}`;
  view.status.textContent = "";
  updateReferenceEmpty();
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
  statusDetail.textContent = job.error || (job.state === "COMPLETED" ? "Preview ready." : "Native backend is processing the job.");
  cancelButton.hidden = !job.cancel_available;
  if (job.state === "FAILED" || job.state === "DISCONNECTED") {
    setDetails(job.error || "The Native backend is unavailable.");
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
  if (job.state === "COMPLETED" && job.video_url) {
    previewEmpty.hidden = true;
    previewVideo.hidden = false;
    if (!previewVideo.src.includes(job.video_url)) {
      previewVideo.src = `${job.video_url}?v=${encodeURIComponent(job.job_id)}`;
      previewVideo.load();
    }
    previewMeta.textContent = `${routeLabelFor(job)} · Completed in ${Number(job.elapsed_seconds || 0).toFixed(1)}s · ${job.request.width} x ${job.request.height} · ${job.request.duration}s`;
  } else if (job.state === "FAILED" || job.state === "DISCONNECTED") {
    previewMeta.textContent = "Inputs are retained. Correct the issue or try Generate again.";
  } else if (job.state === "CANCELLED") {
    previewMeta.textContent = "Job cancelled. Inputs are retained.";
  } else {
    previewMeta.textContent = "Native ComfyUI is preparing the preview.";
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
  const seed = seedInput.value.trim() === "" ? "random" : Number(seedInput.value);
  setDetails("");
  try {
    const body = await requestJson("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: promptInput.value,
        width,
        height,
        duration: Number(durationInput.value),
        seed,
        steps: Number(stepsInput.value),
        references: {
          start_frame: state.references.start_frame
            ? { id: state.references.start_frame.id, role: "start_frame" }
            : null,
          end_frame: state.references.end_frame
            ? { id: state.references.end_frame.id, role: "end_frame" }
            : null,
        },
      }),
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

function createHistoryCard(entry) {
  const card = document.createElement("article");
  card.className = "history-card";
  if (entry.video_url) {
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
  content.append(open, prompt, time);
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
    if (config.resolution_options?.length) {
      resolutionInput.replaceChildren();
      config.resolution_options.forEach((item) => {
        const option = document.createElement("option");
        option.value = `${item.width}x${item.height}`;
        option.textContent = item.label;
        resolutionInput.append(option);
      });
    }
  } catch (error) {
    setDetails(error.message);
  }
}

promptInput.addEventListener("input", updatePromptCount);
form.addEventListener("submit", submitGeneration);
cancelButton.addEventListener("click", cancelGeneration);
$("random-seed").addEventListener("click", () => { seedInput.value = ""; seedInput.focus(); });
referenceAdd.addEventListener("click", () => referenceFile.click());
referenceReplace.addEventListener("click", () => referenceFile.click());
referenceFile.addEventListener("change", () => uploadReference("start_frame", referenceFile.files?.[0]));
referenceRemove.addEventListener("click", () => setReferenceView(null));
endReferenceAdd.addEventListener("click", () => endReferenceFile.click());
endReferenceReplace.addEventListener("click", () => endReferenceFile.click());
endReferenceFile.addEventListener("change", () => uploadReference("end_frame", endReferenceFile.files?.[0]));
endReferenceRemove.addEventListener("click", () => setReferenceSlotView("end_frame", null));

updatePromptCount();
setReferenceSlotView("start_frame", null);
setReferenceSlotView("end_frame", null);
loadConfig();
loadHistory();
pollBackend();
