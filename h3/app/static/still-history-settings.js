const STILL_SOURCE_ID = /^[0-9a-f]{32}$/;

function invalidSettings(message) {
  throw new Error(message);
}

function optionValue(values, target, label) {
  const match = (Array.isArray(values) ? values : [])
    .map((value) => String(value))
    .find((value) => value === target);
  if (match === undefined) invalidSettings(`${label} cannot be restored with the current UI.`);
  return match;
}

export function normalizeStillSource(value) {
  if (value == null) return null;
  if (typeof value !== "object" || Array.isArray(value)) {
    invalidSettings("Still Source Image metadata is invalid.");
  }
  const id = typeof value.id === "string" ? value.id.trim() : "";
  if (!STILL_SOURCE_ID.test(id)) {
    invalidSettings("Still Source Image metadata is invalid.");
  }
  const width = Number(value.width);
  const height = Number(value.height);
  return {
    id,
    preview_url: `/api/still/sources/${encodeURIComponent(id)}`,
    width: Number.isInteger(width) && width > 0 ? width : null,
    height: Number.isInteger(height) && height > 0 ? height : null,
  };
}

function sourceValue(entry, request) {
  if (Object.prototype.hasOwnProperty.call(entry, "source")) {
    const entrySource = entry.source;
    const requestSourceId = request.source_id || null;
    const entrySourceId = entrySource && typeof entrySource === "object" && !Array.isArray(entrySource)
      ? entrySource.id
      : null;
    if (Boolean(requestSourceId) !== Boolean(entrySource) || (requestSourceId && entrySourceId !== requestSourceId)) {
      invalidSettings("Still Source Image metadata is inconsistent.");
    }
    return entrySource;
  }
  if (request.source_id) return { id: request.source_id };
  return null;
}

export async function resolveStillHistorySettings(entry, {
  resolutionValues = [],
  stepsValue,
  maxPromptLength = 4000,
  verifySource,
} = {}) {
  if (!entry || typeof entry !== "object" || Array.isArray(entry) || entry.media_kind !== "still") {
    invalidSettings("Still History settings are invalid.");
  }
  const request = entry.request;
  if (!request || typeof request !== "object" || Array.isArray(request)) {
    invalidSettings("Still History settings are unavailable.");
  }
  if (typeof request.prompt !== "string" || !request.prompt.trim()) {
    invalidSettings("Prompt cannot be restored from this Still History entry.");
  }
  if (request.prompt.length > maxPromptLength) {
    invalidSettings("Prompt cannot be restored with the current UI.");
  }

  const width = Number(request.width);
  const height = Number(request.height);
  if (!Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0) {
    invalidSettings("Resolution metadata is invalid.");
  }
  const resolution = optionValue(resolutionValues, `${width}x${height}`, "Resolution");

  if (Object.prototype.hasOwnProperty.call(request, "duration")) {
    invalidSettings("Still Duration metadata is invalid.");
  }
  if (typeof request.seed !== "number" || !Number.isSafeInteger(request.seed) || request.seed < 0) {
    invalidSettings("Seed cannot be restored as a safe numeric value.");
  }
  if (typeof request.steps !== "number" || !Number.isSafeInteger(request.steps) || request.steps < 0) {
    invalidSettings("Steps metadata is invalid.");
  }
  if (!Number.isSafeInteger(Number(stepsValue)) || Number(stepsValue) !== request.steps) {
    invalidSettings("Steps cannot be restored with the current UI.");
  }

  const source = normalizeStillSource(sourceValue(entry, request));
  if (source && typeof verifySource !== "function") {
    invalidSettings("Still Source Image availability could not be verified.");
  }
  if (source) await verifySource(source);

  return {
    prompt: request.prompt,
    resolution,
    seed: String(request.seed),
    steps: String(request.steps),
    source,
  };
}
