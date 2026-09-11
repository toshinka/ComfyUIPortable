const READY_DETAIL = "Prompt is ready.";

export function resolveBackendStatusPresentation({
  previousBackendDetail = "",
  next,
  message = "",
  hasActiveJob = false,
  submitting = false,
  currentDetail = "",
} = {}) {
  if (next === "READY") {
    const ownsCurrentDetail = previousBackendDetail && currentDetail === previousBackendDetail;
    return {
      detail: ownsCurrentDetail && !hasActiveJob && !submitting ? READY_DETAIL : currentDetail,
      backendDetail: "",
    };
  }

  if (next === "DISCONNECTED" && message && !hasActiveJob && !submitting) {
    return { detail: message, backendDetail: message };
  }

  return {
    detail: currentDetail,
    backendDetail: next === "DISCONNECTED" || next === "CONNECTING" ? previousBackendDetail : "",
  };
}
