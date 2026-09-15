/**
 * LOW-PRIORITY RESERVE-DERIVED HEADLESS CAPABILITY.
 * NO UI OR SETTINGS APPLICATION AUTHORIZED.  PROPOSAL ONLY.
 *
 * Convert the bounded result shape from result_metadata_recovery.mjs into a
 * deterministic, reviewable list of settings candidates.  This module has no
 * filesystem, catalog, backend, queue, or runtime dependency.
 */

export const IMPORT_PROPOSAL_VERSION = 1;

export const IMPORT_FIELDS = Object.freeze([
    "positive_prompt",
    "negative_prompt",
    "checkpoint",
    "loras",
    "seed",
    "steps",
    "cfg",
    "sampler",
    "scheduler",
    "width",
    "height",
    "dimensions"
]);

export const EVIDENCE_CLASSES = Object.freeze({
    RECOVERED_EXPLICIT: "RECOVERED_EXPLICIT",
    DERIVED_RELIABLY: "DERIVED_RELIABLY",
    AMBIGUOUS: "AMBIGUOUS",
    UNAVAILABLE: "UNAVAILABLE"
});

export const READINESS = Object.freeze({
    READY_TO_REVIEW: "READY_TO_REVIEW",
    NEEDS_RESOURCE_RESOLUTION: "NEEDS_RESOURCE_RESOLUTION",
    AMBIGUOUS: "AMBIGUOUS",
    UNSUPPORTED: "UNSUPPORTED"
});

const RESOURCE_FIELDS = new Set(["checkpoint", "loras", "sampler", "scheduler"]);

function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}

function hasOwn(value, key) {
    return isRecord(value) && Object.hasOwn(value, key);
}

function cloneValue(value, depth = 0) {
    if (depth > 64) return null;
    if (Array.isArray(value)) return value.map(item => cloneValue(item, depth + 1));
    if (!isRecord(value)) return value;
    const copy = {};
    for (const key of Object.keys(value)) copy[key] = cloneValue(value[key], depth + 1);
    return copy;
}

function diagnostic(code, message, details = {}) {
    return { code, message, ...cloneValue(details) };
}

function cloneDiagnostics(value, defaultCode = "RECOVERY_WARNING") {
    if (!Array.isArray(value)) return [];
    return value.map(item => {
        if (typeof item === "string") return diagnostic(defaultCode, item);
        if (isRecord(item)) return cloneValue(item);
        return diagnostic(defaultCode, String(item));
    });
}

function finiteNumber(value) {
    return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function validNumeric(field, value) {
    if (finiteNumber(value) === null) return false;
    if (field === "width" || field === "height") return Number.isInteger(value) && value > 0;
    if (field === "steps") return Number.isInteger(value) && value > 0;
    if (field === "seed") return Number.isInteger(value);
    return true;
}

function nonEmptyString(value) {
    return typeof value === "string" && value.trim().length > 0;
}

function hintValue(hints, key) {
    return hasOwn(hints, key) ? hints[key] : undefined;
}

function warningForField(warnings, field) {
    const fieldName = field.toUpperCase();
    return warnings.filter(item => {
        const code = typeof item?.code === "string" ? item.code.toUpperCase() : "";
        const message = typeof item?.message === "string" ? item.message.toUpperCase() : "";
        const text = `${code} ${message}`;
        if (!text.includes("AMBIGU") && !text.includes("CONFLICT") && !text.includes("INCOMPLETE")) return false;
        if (field === "positive_prompt") {
            return text.includes("PROMPT") && !text.includes("NEGATIVE") || text.includes("POSITIVE");
        }
        if (field === "negative_prompt") return text.includes("NEGATIVE");
        if (field === "loras") return text.includes("LORA");
        if (field === "checkpoint") return text.includes("CHECKPOINT");
        return text.includes(fieldName);
    });
}

function fieldWarning(code, message, details = {}) {
    return diagnostic(code, message, details);
}

function baseField(field, {
    value = null,
    source = null,
    evidence = EVIDENCE_CLASSES.UNAVAILABLE,
    availability = "NOT_APPLICABLE",
    readiness = READINESS.UNSUPPORTED,
    warnings = [],
    ...extra
} = {}) {
    const copiedWarnings = cloneDiagnostics(warnings);
    return {
        field,
        value: cloneValue(value),
        source,
        evidence,
        availability,
        readiness,
        warnings: copiedWarnings,
        warning: copiedWarnings[0] || null,
        ...cloneValue(extra)
    };
}

function unavailableField(field, warnings = [], extra = {}) {
    return baseField(field, {
        evidence: EVIDENCE_CLASSES.UNAVAILABLE,
        readiness: READINESS.UNSUPPORTED,
        warnings,
        ...extra
    });
}

function supportedField(options, field) {
    const vocabulary = options?.supportedSettings
        ?? options?.supportedFields
        ?? options?.vocabulary;
    if (vocabulary === undefined || vocabulary === null) return true;
    if (Array.isArray(vocabulary)) return vocabulary.includes(field);
    if (!isRecord(vocabulary) || !hasOwn(vocabulary, field)) return true;
    const entry = vocabulary[field];
    if (typeof entry === "boolean") return entry;
    if (isRecord(entry) && typeof entry.supported === "boolean") return entry.supported;
    return true;
}

function availabilitySource(options) {
    return options?.availability ?? options?.resourceAvailability ?? null;
}

function fieldAliases(field) {
    if (field === "checkpoint") return ["checkpoint", "checkpoints"];
    if (field === "loras") return ["loras", "lora"];
    return [field, `${field}s`];
}

function exactFact(container, requestedId) {
    if (container instanceof Map) return container.has(requestedId) ? container.get(requestedId) : undefined;
    if (!isRecord(container) || !Object.hasOwn(container, requestedId)) return undefined;
    return container[requestedId];
}

function normalizeAvailabilityFact(fact) {
    if (fact === undefined) return { availability: "UNKNOWN", state: "UNKNOWN" };
    if (fact === true) return { availability: "AVAILABLE", state: "AVAILABLE" };
    if (fact === false) return { availability: "MISSING", state: "MISSING" };
    if (typeof fact === "string") {
        const state = fact.toUpperCase();
        if (["AVAILABLE", "PRESENT", "OK", "EXACT_MATCH"].includes(state)) {
            return { availability: "AVAILABLE", state };
        }
        if (["MISSING", "NOT_FOUND", "UNAVAILABLE", "STALE_SELECTION"].includes(state)) {
            return { availability: "MISSING", state };
        }
        return { availability: "UNKNOWN", state };
    }
    if (!isRecord(fact)) return { availability: "UNKNOWN", state: "UNKNOWN" };
    const rawState = fact.availability
        ?? fact.state
        ?? fact.status
        ?? (fact.ok === true ? "AVAILABLE" : fact.ok === false ? "MISSING" : undefined);
    const normalized = normalizeAvailabilityFact(rawState);
    const canonicalId = typeof fact.canonical_id === "string" ? fact.canonical_id : null;
    return { ...normalized, canonical_id: canonicalId, reason: typeof fact.reason === "string" ? fact.reason : null };
}

function lookupAvailability(options, field, requestedId) {
    const root = availabilitySource(options);
    if (root === null || root === undefined) return normalizeAvailabilityFact(undefined);

    if (Array.isArray(root)) {
        const match = root.find(item => isRecord(item)
            && (item.field === field || item.kind?.toLowerCase?.() === field.replace(/s$/, ""))
            && (item.requested_id === requestedId || item.requestedId === requestedId));
        return normalizeAvailabilityFact(match);
    }

    let byField;
    for (const alias of fieldAliases(field)) {
        if (hasOwn(root, alias)) {
            byField = root[alias];
            break;
        }
    }
    if (byField === undefined) return normalizeAvailabilityFact(undefined);
    if (typeof byField === "string" || typeof byField === "boolean") {
        return normalizeAvailabilityFact(byField);
    }
    if (isRecord(byField)
        && (hasOwn(byField, "availability") || hasOwn(byField, "state") || hasOwn(byField, "status") || hasOwn(byField, "ok"))) {
        return normalizeAvailabilityFact(byField);
    }
    const fact = exactFact(byField, requestedId);
    return normalizeAvailabilityFact(fact);
}

function resourceWarnings(info, requestedId) {
    const warnings = [];
    if (info.canonical_id !== undefined && info.canonical_id !== null && info.canonical_id !== requestedId) {
        warnings.push(fieldWarning(
            "CANONICAL_ID_MISMATCH",
            "Caller availability names a different canonical resource; the requested value was preserved",
            { requested_id: requestedId, canonical_id: info.canonical_id }
        ));
        info.availability = "UNKNOWN";
        info.state = "CANONICAL_ID_MISMATCH";
    }
    if (info.state === "STALE_SELECTION") {
        warnings.push(fieldWarning("STALE_RESOURCE_SELECTION", "Resource selection is stale and requires strict re-resolution", { requested_id: requestedId }));
    }
    if (info.availability === "UNKNOWN") {
        warnings.push(fieldWarning("RESOURCE_AVAILABILITY_UNKNOWN", "Resource availability was not established by the caller", { requested_id: requestedId }));
    }
    if (info.availability === "MISSING") {
        warnings.push(fieldWarning("RESOURCE_MISSING", "Requested resource was reported missing or unavailable", { requested_id: requestedId, state: info.state }));
    }
    return warnings;
}

function resourceField(field, value, options, {
    source,
    evidence = EVIDENCE_CLASSES.DERIVED_RELIABLY,
    warnings = []
} = {}) {
    if (value === undefined || value === null) return unavailableField(field, warnings);
    if (!nonEmptyString(value)) {
        return unavailableField(field, [
            ...warnings,
            fieldWarning("INVALID_RESOURCE_HINT", "Recovered resource identifier is not a non-empty string", { field })
        ]);
    }
    const requestedId = value;
    const info = lookupAvailability(options, field, requestedId);
    const resourceIssues = [...warnings, ...resourceWarnings(info, requestedId)];
    const supported = supportedField(options, field);
    if (!supported) {
        resourceIssues.push(fieldWarning("UNSUPPORTED_SETTING", "The caller vocabulary does not support this recovered setting", { field }));
    }
    const readiness = !supported
        ? READINESS.UNSUPPORTED
        : info.availability === "AVAILABLE"
            ? READINESS.READY_TO_REVIEW
            : READINESS.NEEDS_RESOURCE_RESOLUTION;
    return baseField(field, {
        value: requestedId,
        requested_id: requestedId,
        source,
        evidence,
        availability: info.availability,
        resolution_state: info.state,
        readiness,
        warnings: resourceIssues
    });
}

function simpleField(field, value, {
    source,
    evidence = EVIDENCE_CLASSES.DERIVED_RELIABLY,
    warnings = [],
    valid = value !== undefined && value !== null,
    emptyIsValid = false
} = {}, options) {
    if (!valid || (!emptyIsValid && typeof value === "string" && !nonEmptyString(value))) {
        return unavailableField(field, warnings);
    }
    const issues = [...warnings];
    if (!supportedField(options, field)) {
        issues.push(fieldWarning("UNSUPPORTED_SETTING", "The caller vocabulary does not support this recovered setting", { field }));
        return baseField(field, {
            value,
            source,
            evidence,
            readiness: READINESS.UNSUPPORTED,
            warnings: issues
        });
    }
    return baseField(field, {
        value,
        source,
        evidence,
        readiness: READINESS.READY_TO_REVIEW,
        warnings: issues
    });
}

function promptField(field, hints, recoveryWarnings, options) {
    const ambiguous = warningForField(recoveryWarnings, field);
    if (ambiguous.length) {
        return baseField(field, {
            source: "PNG prompt graph",
            evidence: EVIDENCE_CLASSES.AMBIGUOUS,
            readiness: READINESS.AMBIGUOUS,
            warnings: ambiguous
        });
    }
    const value = hintValue(hints, field);
    return simpleField(field, value, {
        source: "PNG prompt graph",
        evidence: EVIDENCE_CLASSES.DERIVED_RELIABLY,
        emptyIsValid: field === "negative_prompt",
        valid: typeof value === "string"
    }, options);
}

function numericField(field, hints, recoveryWarnings, options) {
    const value = hintValue(hints, field);
    if (value === undefined) return unavailableField(field);
    if (!validNumeric(field, value)) {
        return unavailableField(field, [fieldWarning("INVALID_NUMERIC_HINT", "Recovered numeric hint was non-finite or outside its basic type boundary", { field })]);
    }
    const source = (field === "width" || field === "height") && hints.dimension_source === "png"
        ? "PNG dimensions"
        : "PNG workflow";
    const evidence = source === "PNG dimensions"
        ? EVIDENCE_CLASSES.RECOVERED_EXPLICIT
        : EVIDENCE_CLASSES.DERIVED_RELIABLY;
    return simpleField(field, value, { source, evidence, warnings: warningForField(recoveryWarnings, field) }, options);
}

function normalizeLoraEntries(hints, recoveryWarnings, options) {
    const groups = [
        { key: "lora_references", source: "PNG workflow", sourceKind: "workflow" },
        { key: "prompt_lora_references", source: "PNG prompt graph", sourceKind: "prompt" }
    ];
    const entries = [];
    const issues = [...warningForField(recoveryWarnings, "loras")];
    let malformed = false;

    for (const group of groups) {
        if (!hasOwn(hints, group.key)) continue;
        const raw = hints[group.key];
        if (!Array.isArray(raw)) {
            malformed = true;
            issues.push(fieldWarning("MALFORMED_LORA_HINT", "Recovered LoRA references are not a list", { metadata_key: group.key }));
            continue;
        }
        for (const item of raw) {
            if (!isRecord(item) || !nonEmptyString(item.name)) {
                malformed = true;
                issues.push(fieldWarning("MALFORMED_LORA_HINT", "A recovered LoRA entry has no usable requested identifier", { metadata_key: group.key }));
                continue;
            }
            const requestedId = item.name;
            const strengthValue = group.sourceKind === "prompt" ? item.weight : item.strength_model;
            const strength = finiteNumber(strengthValue);
            const itemWarnings = [];
            if (strengthValue !== undefined && strength === null) {
                itemWarnings.push(fieldWarning("INVALID_LORA_STRENGTH", "LoRA strength was not finite and was omitted", { requested_id: requestedId }));
            }
            if (strengthValue === undefined || strengthValue === null) {
                itemWarnings.push(fieldWarning("LORA_STRENGTH_UNAVAILABLE", "LoRA identity was recovered without a reliable strength", { requested_id: requestedId }));
            }
            const info = lookupAvailability(options, "loras", requestedId);
            const availabilityWarnings = resourceWarnings(info, requestedId);
            const entry = {
                requested_id: requestedId,
                strength: strength,
                source: group.source,
                provenance: { metadata_key: group.key, source: group.source },
                availability: info.availability,
                resolution_state: info.state,
                warnings: [...itemWarnings, ...availabilityWarnings]
            };
            if (finiteNumber(item.strength_clip) !== null) entry.strength_clip = item.strength_clip;
            if (finiteNumber(item.strength_model) !== null) entry.strength_model = item.strength_model;
            entries.push(entry);
        }
    }

    if (malformed) {
        return baseField("loras", {
            source: "PNG workflow / PNG prompt graph",
            evidence: EVIDENCE_CLASSES.AMBIGUOUS,
            readiness: READINESS.AMBIGUOUS,
            warnings: issues
        });
    }
    if (!entries.length) return unavailableField("loras", issues);
    if (!supportedField(options, "loras")) {
        issues.push(fieldWarning("UNSUPPORTED_SETTING", "The caller vocabulary does not support recovered LoRA settings", { field: "loras" }));
    }
    const hasUnresolved = entries.some(entry => entry.availability !== "AVAILABLE");
    const readiness = !supportedField(options, "loras")
        ? READINESS.UNSUPPORTED
        : hasUnresolved
            ? READINESS.NEEDS_RESOURCE_RESOLUTION
            : READINESS.READY_TO_REVIEW;
    const fieldAvailability = entries.some(entry => entry.availability === "MISSING")
        ? "MISSING"
        : entries.every(entry => entry.availability === "AVAILABLE")
            ? "AVAILABLE"
            : "UNKNOWN";
    return baseField("loras", {
        value: entries,
        source: "PNG workflow / PNG prompt graph",
        evidence: EVIDENCE_CLASSES.DERIVED_RELIABLY,
        availability: fieldAvailability,
        readiness,
        warnings: [...issues, ...entries.flatMap(entry => entry.warnings)]
    });
}

function dimensionField(widthField, heightField) {
    const widthAvailable = widthField.evidence !== EVIDENCE_CLASSES.UNAVAILABLE;
    const heightAvailable = heightField.evidence !== EVIDENCE_CLASSES.UNAVAILABLE;
    if (!widthAvailable && !heightAvailable) return unavailableField("dimensions");
    const partial = !(widthAvailable && heightAvailable);
    const warnings = [];
    if (partial) warnings.push(fieldWarning("PARTIAL_DIMENSIONS", "Only one dimension was recovered; no aspect ratio or missing value was invented"));
    const source = widthField.source === heightField.source ? widthField.source : "mixed PNG/workflow dimensions";
    const evidence = widthAvailable && heightAvailable
        ? (widthField.evidence === EVIDENCE_CLASSES.RECOVERED_EXPLICIT && heightField.evidence === EVIDENCE_CLASSES.RECOVERED_EXPLICIT
            ? EVIDENCE_CLASSES.RECOVERED_EXPLICIT
            : EVIDENCE_CLASSES.DERIVED_RELIABLY)
        : EVIDENCE_CLASSES.AMBIGUOUS;
    return baseField("dimensions", {
        value: {
            width: widthAvailable ? widthField.value : null,
            height: heightAvailable ? heightField.value : null
        },
        source,
        evidence,
        readiness: READINESS.READY_TO_REVIEW,
        partial,
        warnings
    });
}

function emptyProposal(error = null) {
    return {
        ok: false,
        status: "INVALID_INPUT",
        proposal_version: IMPORT_PROPOSAL_VERSION,
        proposal_only: true,
        fields: {},
        field_list: [],
        candidates: [],
        warnings: error ? [error] : [],
        summary: {
            candidate_count: 0,
            warning_count: error ? 1 : 0,
            resource_check_required: false,
            ambiguous_fields: []
        },
        error
    };
}

/**
 * Build a deterministic review proposal from one result_metadata_recovery
 * result.  The returned value is data only: it never applies a setting,
 * resolves a file, selects a resource, or calls a backend.
 */
export function buildSettingsImportProposal(recoveredMetadata, options = {}) {
    if (!isRecord(recoveredMetadata)) {
        return emptyProposal(diagnostic("INVALID_METADATA_RESULT", "Metadata recovery result must be an object"));
    }
    const safeOptions = isRecord(options) ? options : {};
    const hints = isRecord(recoveredMetadata.normalized_hints) ? recoveredMetadata.normalized_hints : {};
    const recoveryWarnings = cloneDiagnostics(recoveredMetadata.warnings);
    const warnings = [...recoveryWarnings];
    if (isRecord(recoveredMetadata.error) && recoveredMetadata.error.code) warnings.push(cloneValue(recoveredMetadata.error));

    const fields = {};
    fields.positive_prompt = promptField("positive_prompt", hints, recoveryWarnings, safeOptions);
    fields.negative_prompt = promptField("negative_prompt", hints, recoveryWarnings, safeOptions);
    fields.checkpoint = resourceField("checkpoint", hintValue(hints, "checkpoint"), safeOptions, {
        source: "PNG workflow",
        warnings: warningForField(recoveryWarnings, "checkpoint")
    });
    fields.loras = normalizeLoraEntries(hints, recoveryWarnings, safeOptions);
    fields.seed = numericField("seed", hints, recoveryWarnings, safeOptions);
    fields.steps = numericField("steps", hints, recoveryWarnings, safeOptions);
    fields.cfg = numericField("cfg", hints, recoveryWarnings, safeOptions);
    fields.sampler = resourceField("sampler", hintValue(hints, "sampler"), safeOptions, {
        source: "PNG workflow",
        warnings: warningForField(recoveryWarnings, "sampler")
    });
    fields.scheduler = resourceField("scheduler", hintValue(hints, "scheduler"), safeOptions, {
        source: "PNG workflow",
        warnings: warningForField(recoveryWarnings, "scheduler")
    });
    fields.width = numericField("width", hints, recoveryWarnings, safeOptions);
    fields.height = numericField("height", hints, recoveryWarnings, safeOptions);
    fields.dimensions = dimensionField(fields.width, fields.height);

    for (const field of Object.keys(fields)) {
        const fieldWarnings = fields[field].warnings || [];
        warnings.push(...fieldWarnings.filter(item => !recoveryWarnings.some(existing => JSON.stringify(existing) === JSON.stringify(item))));
    }

    const fieldList = IMPORT_FIELDS.map(field => fields[field]);
    const candidates = fieldList.filter(item => item.field !== "dimensions"
        && item.value !== null
        && item.evidence !== EVIDENCE_CLASSES.AMBIGUOUS
        && item.readiness !== READINESS.UNSUPPORTED);
    const ambiguousFields = fieldList
        .filter(item => item.evidence === EVIDENCE_CLASSES.AMBIGUOUS)
        .map(item => item.field);
    const resourceCheckRequired = fieldList.some(item => RESOURCE_FIELDS.has(item.field)
        && item.value !== null
        && item.readiness === READINESS.NEEDS_RESOURCE_RESOLUTION);

    return {
        ok: true,
        status: "PROPOSAL_READY",
        proposal_version: IMPORT_PROPOSAL_VERSION,
        proposal_only: true,
        fields,
        field_list: fieldList,
        candidates,
        warnings,
        recovery: {
            ok: recoveredMetadata.ok === true,
            status: typeof recoveredMetadata.status === "string" ? recoveredMetadata.status : null
        },
        summary: {
            candidate_count: candidates.length,
            warning_count: warnings.length,
            resource_check_required: resourceCheckRequired,
            ambiguous_fields: ambiguousFields
        }
    };
}
