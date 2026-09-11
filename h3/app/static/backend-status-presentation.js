const READY_DETAIL = "Prompt is ready.";
const PROFILE_DETAIL_STATES = new Set([
  "DISCONNECTED",
  "PROFILE_MISMATCH",
  "PROFILE_UNVERIFIABLE",
]);

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

  if (PROFILE_DETAIL_STATES.has(next) && message && !hasActiveJob && !submitting) {
    return { detail: message, backendDetail: message };
  }

  return {
    detail: currentDetail,
    backendDetail: PROFILE_DETAIL_STATES.has(next) || next === "CONNECTING" ? previousBackendDetail : "",
  };
}
