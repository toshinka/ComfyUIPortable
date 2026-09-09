const REFERENCE_SLOTS = ["start_frame", "end_frame"];
const REFERENCE_LABELS = {
  start_frame: "Start Frame",
  end_frame: "End Frame",
};

const hasOwn = (value, key) => Object.prototype.hasOwnProperty.call(value, key);

function invalidSettings(message) {
  throw new Error(message);
}

function optionValue(values, target, label) {
  const match = (Array.isArray(values) ? values : [])
    .map((value) => String(value))
    .find((value) => value === target);
  if (match === undefined) {
    invalidSettings(`${label} cannot be restored with the current UI.`);
  }
  return match;
}

export function normalizeHistoryReference(value, slot) {
  if (value == null) return null;
  if (typeof value !== "object" || Array.isArray(value)) {
    invalidSettings(`${REFERENCE_LABELS[slot]} reference metadata is invalid.`);
  }
  const id = typeof value.id === "string" ? value.id.trim() : "";
  if (!id || !REFERENCE_SLOTS.includes(slot)) {
    invalidSettings(`${REFERENCE_LABELS[slot] || "Reference"} reference metadata is invalid.`);
  }
  if (value.role !== undefined && value.role !== slot) {
    invalidSettings(`${REFERENCE_LABELS[slot]} reference role is invalid.`);
  }
  const width = Number(value.width);
  const height = Number(value.height);
  return {
    id,
    role: slot,
    preview_url: `/api/references/${encodeURIComponent(id)}`,
    width: Number.isInteger(width) && width > 0 ? width : null,
    height: Number.isInteger(height) && height > 0 ? height : null,
  };
}

function historyReferenceValue(entry, references, slot) {
  if (references && hasOwn(references, slot)) return references[slot];
  if (slot === "start_frame" && entry.reference != null && (!references || !hasOwn(references, slot))) {
    return entry.reference;
  }
  return null;
}

export function resolveHistoryScalars(entry, {
  resolutionValues = [],
  durationValues = [],
  stepsValue,
  maxPromptLength = 4000,
} = {}) {
  if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
    invalidSettings("History settings are invalid.");
  }
  const request = entry.request;
  if (!request || typeof request !== "object" || Array.isArray(request)) {
    invalidSettings("History settings are unavailable.");
  }
  if (typeof request.prompt !== "string" || !request.prompt.trim()) {
    invalidSettings("Prompt cannot be restored from this History entry.");
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

  const duration = Number(request.duration);
  if (!Number.isFinite(duration) || duration <= 0) {
    invalidSettings("Duration metadata is invalid.");
  }
  const durationOption = optionValue(durationValues, String(duration), "Duration");

  if (typeof request.seed !== "number" || !Number.isSafeInteger(request.seed) || request.seed < 0) {
    invalidSettings("Seed cannot be restored as a safe numeric value.");
  }

  if (typeof request.steps !== "number" || !Number.isSafeInteger(request.steps) || request.steps < 0) {
    invalidSettings("Steps metadata is invalid.");
  }
  if (!Number.isSafeInteger(Number(stepsValue)) || Number(stepsValue) !== request.steps) {
    invalidSettings("Steps cannot be restored with the current UI.");
  }

  return {
    prompt: request.prompt,
    resolution,
    duration: durationOption,
    seed: String(request.seed),
    steps: String(request.steps),
  };
}

export async function resolveHistorySettings(entry, options = {}) {
  const {
    resolutionValues = [],
    durationValues = [],
    stepsValue,
    maxPromptLength = 4000,
    verifyReference,
  } = options;
  const scalars = resolveHistoryScalars(entry, {
    resolutionValues,
    durationValues,
    stepsValue,
    maxPromptLength,
  });

  const references = entry.references && typeof entry.references === "object" && !Array.isArray(entry.references)
    ? entry.references
    : null;
  const normalizedReferences = Object.fromEntries(
    REFERENCE_SLOTS.map((slot) => [
      slot,
      normalizeHistoryReference(historyReferenceValue(entry, references, slot), slot),
    ]),
  );

  if (Object.values(normalizedReferences).some(Boolean) && typeof verifyReference !== "function") {
    invalidSettings("Reference availability could not be verified.");
  }
  for (const slot of REFERENCE_SLOTS) {
    const reference = normalizedReferences[slot];
    if (reference) await verifyReference(reference, slot);
  }

  return {
    ...scalars,
    references: normalizedReferences,
  };
}
