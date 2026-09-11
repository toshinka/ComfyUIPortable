const PREP_ROUTE = "native_image_prep";
const PREP_ID = /^[0-9a-f]{32}$/;

function invalidSettings(message) {
  throw new Error(message);
}

function normalizeSeed(value) {
  let text;
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value) || value < 0) {
      invalidSettings("Seed cannot be restored as a safe numeric value.");
    }
    text = String(value);
  } else if (typeof value === "string" && /^\d+$/.test(value)) {
    text = value;
  } else {
    invalidSettings("Seed cannot be restored as a safe numeric value.");
  }
  try {
    const seed = BigInt(text);
    if (seed < 0n || seed > 9223372036854775807n) {
      invalidSettings("Seed cannot be restored as a safe numeric value.");
    }
    return seed.toString();
  } catch {
    invalidSettings("Seed cannot be restored as a safe numeric value.");
  }
}

function normalizePrepAsset(value, label) {
  if (value == null) return null;
  if (typeof value !== "object" || Array.isArray(value)) {
    invalidSettings(`${label} metadata is invalid.`);
  }
  const id = typeof value.id === "string" ? value.id.trim() : "";
  if (!PREP_ID.test(id)) invalidSettings(`${label} metadata is invalid.`);
  const width = Number(value.width);
  const height = Number(value.height);
  return {
    ...value,
    id,
    preview_url: `/api/prep/assets/${encodeURIComponent(id)}`,
    width: Number.isInteger(width) && width > 0 ? width : null,
    height: Number.isInteger(height) && height > 0 ? height : null,
  };
}

function entryAssetValue(entry, request, key, label, required, idKey = `${key}_id`) {
  const entryAsset = entry[key];
  const requestId = request[idKey] == null || request[idKey] === ""
    ? null
    : request[idKey];
  const entryAssetId = entryAsset && typeof entryAsset === "object" && !Array.isArray(entryAsset)
    ? entryAsset.id
    : null;
  if (Boolean(requestId) !== Boolean(entryAsset)) {
    invalidSettings(`${label} metadata is inconsistent.`);
  }
  if (requestId && entryAssetId !== requestId) {
    invalidSettings(`${label} metadata is inconsistent.`);
  }
  if (required && !entryAsset) invalidSettings(`${label} is required for this History entry.`);
  return entryAsset;
}

export async function resolvePrepHistorySettings(entry, {
  stepsValue,
  maxPromptLength = 4000,
  verifyAsset,
} = {}) {
  if (
    !entry
    || typeof entry !== "object"
    || Array.isArray(entry)
    || entry.media_kind !== "still"
    || entry.route !== PREP_ROUTE
  ) {
    invalidSettings("Prep/Edit History settings are invalid.");
  }
  const request = entry.request;
  if (!request || typeof request !== "object" || Array.isArray(request)) {
    invalidSettings("Prep/Edit History settings are unavailable.");
  }
  if (typeof request.prompt !== "string" || !request.prompt.trim()) {
    invalidSettings("Prompt cannot be restored from this Prep/Edit History entry.");
  }
  if (request.prompt.length > maxPromptLength) {
    invalidSettings("Prompt cannot be restored with the current UI.");
  }
  if (Object.prototype.hasOwnProperty.call(request, "duration")) {
    invalidSettings("Prep/Edit Duration metadata is invalid.");
  }
  const width = Number(request.width);
  const height = Number(request.height);
  if (width !== 608 || height !== 352) {
    invalidSettings("Prep/Edit resolution is outside the fixed Native baseline.");
  }
  const seed = normalizeSeed(request.seed);
  if (typeof request.steps !== "number" || !Number.isSafeInteger(request.steps) || request.steps !== 20) {
    invalidSettings("Prep/Edit steps are outside the fixed Native baseline.");
  }
  if (!Number.isSafeInteger(Number(stepsValue)) || Number(stepsValue) !== 20) {
    invalidSettings("Prep/Edit steps cannot be restored with the current UI.");
  }

  const sourceValue = entryAssetValue(entry, request, "prep_source", "Prep Source Image", true, "source_id");
  const donorValue = entryAssetValue(entry, request, "prep_donor", "Prep Donor Image", false, "donor_id");
  const source = normalizePrepAsset(sourceValue, "Prep Source Image");
  const donor = normalizePrepAsset(donorValue, "Prep Donor Image");
  if (typeof verifyAsset !== "function") invalidSettings("Prep/Edit asset availability could not be verified.");
  await verifyAsset(source, "source");
  if (donor) await verifyAsset(donor, "donor");

  return {
    prompt: request.prompt,
    resolution: "608x352",
    seed,
    steps: "20",
    source,
    donor,
  };
}
