const SAFE_JOB_ID = /^[A-Za-z0-9_-]+$/;

function invalidSource(message) {
  throw new Error(message);
}

export function validateContinuationSource(entry) {
  if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
    invalidSource("The source History result is invalid.");
  }
  if (entry.state !== "COMPLETED") {
    invalidSource("Only completed History results can continue.");
  }

  const jobId = typeof entry.job_id === "string" ? entry.job_id.trim() : "";
  if (!jobId || !SAFE_JOB_ID.test(jobId)) {
    invalidSource("The source History job is invalid.");
  }
  if (typeof entry.video_url !== "string" || !entry.video_url.trim()) {
    invalidSource("The source video is unavailable.");
  }

  const expected = `/api/jobs/${encodeURIComponent(jobId)}/video`;
  if (entry.video_url !== expected) {
    invalidSource("The source video must be a same-origin H3 output.");
  }
  return expected;
}
