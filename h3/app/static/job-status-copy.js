const ACTIVE_STATUS_COPY = Object.freeze({
  SUBMITTING: "Submitting the generation request to Native H3.",
  QUEUED: "Waiting in the Native queue.",
  RUNNING: "Native backend is generating.",
  COMPLETED: "Preview ready.",
  FAILED: "Generation failed. Inputs are retained.",
  CANCELLED: "Job cancelled. Inputs are retained.",
  DISCONNECTED: "Backend connection lost. Current job status is unknown. Waiting for the backend to reconnect.",
});

const PREVIEW_STATUS_COPY = Object.freeze({
  QUEUED: "Native ComfyUI is preparing the preview.",
  RUNNING: "Native ComfyUI is preparing the preview.",
  COMPLETED: "Preview ready.",
  FAILED: "Generation failed. Inputs are retained.",
  CANCELLED: "Job cancelled. Inputs are retained.",
  DISCONNECTED: "Backend connection lost. Current job status is unknown.",
});

export function activeStatusDetail(job) {
  const state = job?.state;
  if (state === "FAILED" && job?.error) {
    return `${ACTIVE_STATUS_COPY.FAILED} ${job.error}`;
  }
  return ACTIVE_STATUS_COPY[state] || job?.error || "Job status is unavailable.";
}

export function previewStatusDetail(job) {
  const state = job?.state;
  return PREVIEW_STATUS_COPY[state] || job?.error || "Job status is unavailable.";
}

export { ACTIVE_STATUS_COPY, PREVIEW_STATUS_COPY };
