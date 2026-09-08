const state = {
  backend: "CONNECTING",
  currentJob: null,
  reference: null,
  referenceUploading: false,
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
  if (message && !state.currentJob) statusDetail.textContent = message;
}

function updateGenerateAvailability() {
  generateButton.disabled = !promptInput.value.trim() || state.referenceUploading || Boolean(state.currentJob && !TERMINAL.has(state.currentJob.state));
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

function setReferenceView(reference) {
  state.reference = reference;
  referenceSelected.hidden = !reference;
  referenceEmpty.hidden = Boolean(reference);
  if (!reference) {
    referenceThumbnail.removeAttribute("src");
    referenceName.textContent = "";
    referenceStatus.textContent = "";
    updateGenerateAvailability();
    return;
  }
  referenceThumbnail.src = `${reference.preview_url}?v=${encodeURIComponent(reference.id)}`;
  referenceName.textContent = `${reference.width} x ${reference.height}`;
  referenceStatus.textContent = "";
  updateGenerateAvailability();
}

async function uploadReference(file) {
  if (!file) return;
  const body = new FormData();
  body.append("reference", file, file.name);
  state.referenceUploading = true;
  referenceAdd.disabled = true;
  referenceReplace.disabled = true;
  referenceStatus.textContent = "Uploading reference…";
  updateGenerateAvailability();
  try {
    const response = await fetch("/api/references", { method: "POST", body, cache: "no-store" });
    let result = {};
    try { result = await response.json(); } catch { result = {}; }
    if (!response.ok) throw new Error(result.error || `Reference upload failed (${response.status})`);
    setReferenceView(result.reference);
  } catch (error) {
    referenceStatus.textContent = error.message;
    setDetails(error.message);
  } finally {
    state.referenceUploading = false;
    referenceAdd.disabled = false;
    referenceReplace.disabled = false;
    referenceFile.value = "";
    updateGenerateAvailability();
  }
}

function setJobView(job) {
  state.currentJob = job;
  generationStatus.textContent = job.label || job.state;
  previewState.textContent = job.label || job.state;
  previewElapsed.textContent = `${Number(job.elapsed_seconds || 0).toFixed(1)}s`;
  statusDetail.textContent = job.error || (job.state === "COMPLETED" ? "Preview ready." : "Native backend is processing the job.");
  previewOverlay.hidden = TERMINAL.has(job.state) && job.state !== "COMPLETED";
  cancelButton.hidden = !job.cancel_available;
  if (job.state === "COMPLETED" && job.video_url) {
    previewEmpty.hidden = true;
    previewVideo.hidden = false;
    if (!previewVideo.src.endsWith(job.video_url)) {
      previewVideo.src = `${job.video_url}?v=${encodeURIComponent(job.job_id)}`;
      previewVideo.load();
    }
    const routeLabel = job.route_label || (job.reference_used ? "Start Frame" : "T2V");
    previewMeta.textContent = `${routeLabel} · Completed in ${Number(job.elapsed_seconds || 0).toFixed(1)}s · ${job.request.width} x ${job.request.height} · ${job.request.duration}s`;
    setDetails("");
  } else if (job.state === "FAILED" || job.state === "DISCONNECTED") {
    previewMeta.textContent = "Inputs are retained. Correct the issue or try Generate again.";
    setDetails(job.error || "The Native backend is unavailable.");
  } else if (job.state === "CANCELLED") {
    previewMeta.textContent = "Job cancelled. Inputs are retained.";
    setDetails("");
  } else {
    previewMeta.textContent = "Native ComfyUI is preparing the preview.";
  }
  updateGenerateAvailability();
}

async function pollJob() {
  if (!state.currentJob?.job_id) return;
  try {
    const job = await requestJson(`/api/jobs/${encodeURIComponent(state.currentJob.job_id)}`);
    setJobView(job);
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
        reference: state.reference ? { id: state.reference.id, role: state.reference.role } : null,
      }),
    });
    setJobView(body.job);
    await pollJob();
  } catch (error) {
    state.currentJob = null;
    generationStatus.textContent = "Failed";
    statusDetail.textContent = "Generation was not submitted.";
    setDetails(error.message);
    updateGenerateAvailability();
  }
}

async function cancelGeneration() {
  if (!state.currentJob?.job_id) return;
  try {
    const body = await requestJson(`/api/jobs/${encodeURIComponent(state.currentJob.job_id)}/cancel`, { method: "POST" });
    setJobView(body.job);
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
    video.addEventListener("click", () => {
      state.currentJob = entry;
      setJobView(entry);
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
  const open = document.createElement("button");
  open.type = "button";
  open.textContent = `${entry.label || entry.state} · ${entry.route_label || (entry.reference_used ? "Start Frame" : "T2V")}`;
  open.addEventListener("click", () => { state.currentJob = entry; setJobView(entry); window.scrollTo({ top: 0, behavior: "smooth" }); });
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
    if (!state.currentJob) setJobView(body.entries[0]);
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
referenceFile.addEventListener("change", () => uploadReference(referenceFile.files?.[0]));
referenceRemove.addEventListener("click", () => setReferenceView(null));

updatePromptCount();
loadConfig();
loadHistory();
pollBackend();
