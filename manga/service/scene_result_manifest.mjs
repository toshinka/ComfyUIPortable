/**
 * scene_result_manifest.mjs — Pure data contract & validator for isolated-Scene result manifests.
 *
 * Defines the schema constants, custom error class, and validation rules for
 * finalized, immutable isolated-Scene result manifests.
 */

export const SCHEMA_ID = "TEGAKI_SCENE_RESULT_MANIFEST";
export const SCHEMA_VERSION = "1.1.0";
export const SCHEMA_VERSION_1_0 = "1.0.0";
export const SCHEMA_VERSION_1_1 = "1.1.0";
export const SUPPORTED_SCHEMA_VERSIONS = Object.freeze(["1.0.0", "1.1.0"]);
export const REQUIRED_DIGEST_CONTRACT_VERSION_V1_1 = "2.0.0";

export class SceneResultManifestError extends Error {
    constructor(code, message) {
        super(message);
        this.name = "SceneResultManifestError";
        this.code = code;
    }
}

const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const UUID_ANY_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SHA256_HEX_REGEX = /^[0-9a-f]{64}$/i;

function isObject(val) {
    return val !== null && typeof val === "object" && !Array.isArray(val);
}

function isNonEmptyString(val) {
    return typeof val === "string" && val.trim().length > 0;
}

function isPositiveInteger(val) {
    return typeof val === "number" && Number.isInteger(val) && val > 0;
}

function isFiniteNumber(val) {
    return typeof val === "number" && Number.isFinite(val);
}

/**
 * Validates and deep-clones a finalized isolated-Scene result manifest.
 *
 * @param {unknown} input - Candidate manifest object.
 * @returns {object} Validated, deeply-cloned manifest object.
 * @throws {SceneResultManifestError} When input fails validation.
 */
export function validateSceneResultManifest(input) {
    if (!isObject(input)) {
        throw new SceneResultManifestError("INVALID_MANIFEST", "Manifest must be a non-null object");
    }

    // 1. Schema header
    if (input.schema_id !== SCHEMA_ID) {
        throw new SceneResultManifestError(
            "SCHEMA_MISMATCH",
            `Invalid schema_id: expected "${SCHEMA_ID}", got "${input.schema_id}"`
        );
    }
    if (input.schema_version !== SCHEMA_VERSION_1_0 && input.schema_version !== SCHEMA_VERSION_1_1) {
        throw new SceneResultManifestError(
            "SCHEMA_VERSION_MISMATCH",
            `Invalid schema_version: expected one of ${SUPPORTED_SCHEMA_VERSIONS.map(v => `"${v}"`).join(", ")}, got "${input.schema_version}"`
        );
    }

    // 2. Manifest identity (strict UUIDv4)
    if (!isNonEmptyString(input.manifest_id) || !UUID_V4_REGEX.test(input.manifest_id)) {
        throw new SceneResultManifestError(
            "INVALID_MANIFEST_ID",
            `manifest_id must be a valid RFC 4122 UUIDv4, got "${input.manifest_id}"`
        );
    }

    // 3. Owner hierarchy
    if (!isObject(input.owner)) {
        throw new SceneResultManifestError("INVALID_OWNER", "owner must be an object");
    }
    const { document_id, page_id, scene_id } = input.owner;
    if (!isNonEmptyString(document_id)) {
        throw new SceneResultManifestError("INVALID_OWNER", "owner.document_id must be a non-empty string");
    }
    if (!isNonEmptyString(page_id)) {
        throw new SceneResultManifestError("INVALID_OWNER", "owner.page_id must be a non-empty string");
    }
    if (!isNonEmptyString(scene_id)) {
        throw new SceneResultManifestError("INVALID_OWNER", "owner.scene_id must be a non-empty string");
    }

    // 4. Input provenance
    if (!isObject(input.input_provenance)) {
        throw new SceneResultManifestError("INVALID_INPUT_PROVENANCE", "input_provenance must be an object");
    }
    const {
        authoring_snapshot_ref,
        authoring_snapshot_digest,
        effective_input_digest,
        effective_input_contract_version,
        reference_content_digest
    } = input.input_provenance;

    if (!isNonEmptyString(authoring_snapshot_ref)) {
        throw new SceneResultManifestError(
            "INVALID_INPUT_PROVENANCE",
            "authoring_snapshot_ref must be a non-empty string"
        );
    }
    if (!isNonEmptyString(authoring_snapshot_digest) || !SHA256_HEX_REGEX.test(authoring_snapshot_digest)) {
        throw new SceneResultManifestError(
            "INVALID_INPUT_PROVENANCE",
            "authoring_snapshot_digest must be a 64-character hex SHA-256 digest"
        );
    }
    if (!isNonEmptyString(effective_input_digest) || !SHA256_HEX_REGEX.test(effective_input_digest)) {
        throw new SceneResultManifestError(
            "INVALID_INPUT_PROVENANCE",
            "effective_input_digest must be a 64-character hex SHA-256 digest"
        );
    }

    if (input.schema_version === SCHEMA_VERSION_1_1) {
        if (!isNonEmptyString(effective_input_contract_version)) {
            throw new SceneResultManifestError(
                "INVALID_INPUT_PROVENANCE",
                `v1.1.0 manifests require non-empty effective_input_contract_version, got "${effective_input_contract_version}"`
            );
        }
        if (effective_input_contract_version !== REQUIRED_DIGEST_CONTRACT_VERSION_V1_1) {
            throw new SceneResultManifestError(
                "INVALID_INPUT_PROVENANCE",
                `Unsupported effective_input_contract_version: expected "${REQUIRED_DIGEST_CONTRACT_VERSION_V1_1}", got "${effective_input_contract_version}"`
            );
        }
    }

    if (reference_content_digest !== null && (!isNonEmptyString(reference_content_digest) || !SHA256_HEX_REGEX.test(reference_content_digest))) {
        throw new SceneResultManifestError(
            "INVALID_INPUT_PROVENANCE",
            "reference_content_digest must be null or a 64-character hex SHA-256 digest"
        );
    }

    // 5. Execution record
    if (!isObject(input.execution)) {
        throw new SceneResultManifestError("INVALID_EXECUTION", "execution must be an object");
    }
    const {
        job_id,
        prompt_id,
        state,
        graph_digest,
        page_compile_plan_digest,
        effective_settings
    } = input.execution;

    if (!isNonEmptyString(job_id) || !UUID_ANY_REGEX.test(job_id)) {
        throw new SceneResultManifestError("INVALID_EXECUTION", "execution.job_id must be a valid UUID");
    }
    if (!isNonEmptyString(prompt_id) || !UUID_ANY_REGEX.test(prompt_id)) {
        throw new SceneResultManifestError("INVALID_EXECUTION", "execution.prompt_id must be a valid UUID");
    }
    if (state !== "SUCCEEDED") {
        throw new SceneResultManifestError(
            "INVALID_EXECUTION_STATE",
            `execution.state must be "SUCCEEDED", got "${state}"`
        );
    }
    if (!isNonEmptyString(graph_digest) || !SHA256_HEX_REGEX.test(graph_digest)) {
        throw new SceneResultManifestError(
            "INVALID_EXECUTION",
            "execution.graph_digest must be a 64-character hex SHA-256 digest"
        );
    }
    if (!isNonEmptyString(page_compile_plan_digest) || !SHA256_HEX_REGEX.test(page_compile_plan_digest)) {
        throw new SceneResultManifestError(
            "INVALID_EXECUTION",
            "execution.page_compile_plan_digest must be a 64-character hex SHA-256 digest"
        );
    }

    if (!isObject(effective_settings)) {
        throw new SceneResultManifestError("INVALID_EXECUTION", "execution.effective_settings must be an object");
    }
    const {
        checkpoint_id: ckpt,
        sampler_id: sampler,
        scheduler_id: scheduler,
        steps,
        cfg,
        seed_requested,
        effective_seed
    } = effective_settings;

    if (!isNonEmptyString(ckpt)) {
        throw new SceneResultManifestError("INVALID_EXECUTION", "effective_settings.checkpoint_id must be non-empty string");
    }
    if (!isNonEmptyString(sampler)) {
        throw new SceneResultManifestError("INVALID_EXECUTION", "effective_settings.sampler_id must be non-empty string");
    }
    if (!isNonEmptyString(scheduler)) {
        throw new SceneResultManifestError("INVALID_EXECUTION", "effective_settings.scheduler_id must be non-empty string");
    }
    if (!isPositiveInteger(steps)) {
        throw new SceneResultManifestError("INVALID_EXECUTION", "effective_settings.steps must be a positive integer");
    }
    if (!isFiniteNumber(cfg) || cfg <= 0) {
        throw new SceneResultManifestError("INVALID_EXECUTION", "effective_settings.cfg must be a positive number");
    }
    if (typeof seed_requested !== "string" && typeof seed_requested !== "number") {
        throw new SceneResultManifestError("INVALID_EXECUTION", "effective_settings.seed_requested must be string or number");
    }
    if (typeof effective_seed !== "number" || !Number.isInteger(effective_seed)) {
        throw new SceneResultManifestError("INVALID_EXECUTION", "effective_settings.effective_seed must be an integer");
    }

    // 6. Artifact facts
    if (!isObject(input.artifact)) {
        throw new SceneResultManifestError("INVALID_ARTIFACT", "artifact must be an object");
    }
    const { locator, dimensions, content_digest } = input.artifact;

    if (!isObject(locator)) {
        throw new SceneResultManifestError("INVALID_ARTIFACT", "artifact.locator must be an object");
    }
    if (!isNonEmptyString(locator.filename) || !locator.filename.endsWith(".png")) {
        throw new SceneResultManifestError("INVALID_ARTIFACT", "artifact.locator.filename must be a .png file name");
    }
    if (!isNonEmptyString(locator.subfolder)) {
        throw new SceneResultManifestError("INVALID_ARTIFACT", "artifact.locator.subfolder must be a non-empty string");
    }
    if (!isNonEmptyString(locator.type)) {
        throw new SceneResultManifestError("INVALID_ARTIFACT", "artifact.locator.type must be a non-empty string");
    }

    if (!isObject(dimensions)) {
        throw new SceneResultManifestError("INVALID_ARTIFACT", "artifact.dimensions must be an object");
    }
    const { width: artW, height: artH } = dimensions;
    if (!isPositiveInteger(artW) || artW % 8 !== 0) {
        throw new SceneResultManifestError(
            "INVALID_ARTIFACT_DIMENSIONS",
            `artifact.dimensions.width must be a positive integer multiple of 8, got ${artW}`
        );
    }
    if (!isPositiveInteger(artH) || artH % 8 !== 0) {
        throw new SceneResultManifestError(
            "INVALID_ARTIFACT_DIMENSIONS",
            `artifact.dimensions.height must be a positive integer multiple of 8, got ${artH}`
        );
    }

    if (!isNonEmptyString(content_digest) || !SHA256_HEX_REGEX.test(content_digest)) {
        throw new SceneResultManifestError(
            "INVALID_ARTIFACT",
            "artifact.content_digest must be a 64-character hex SHA-256 digest"
        );
    }

    // 7. Placement facts
    if (!isObject(input.placement)) {
        throw new SceneResultManifestError("INVALID_PLACEMENT", "placement must be an object");
    }
    const {
        page_target_rect,
        local_source_rect,
        transform,
        target_page_dimensions
    } = input.placement;

    if (!isObject(page_target_rect)) {
        throw new SceneResultManifestError("INVALID_PLACEMENT", "placement.page_target_rect must be an object");
    }
    const { x: px, y: py, w: pw, h: ph } = page_target_rect;
    if (!isFiniteNumber(px) || !isFiniteNumber(py) || !isFiniteNumber(pw) || !isFiniteNumber(ph)) {
        throw new SceneResultManifestError("INVALID_PLACEMENT", "page_target_rect coordinates must be finite numbers");
    }
    if (pw <= 0 || ph <= 0) {
        throw new SceneResultManifestError("INVALID_PLACEMENT", "page_target_rect w and h must be > 0");
    }
    if (px < -0.001 || py < -0.001 || (px + pw) > 1.001 || (py + ph) > 1.001) {
        throw new SceneResultManifestError(
            "INVALID_PLACEMENT",
            `page_target_rect [${px}, ${py}, ${pw}, ${ph}] exceeds normalized unit bounds [0, 1]`
        );
    }

    if (!isObject(local_source_rect)) {
        throw new SceneResultManifestError("INVALID_PLACEMENT", "placement.local_source_rect must be an object");
    }
    const { x: lx, y: ly, w: lw, h: lh } = local_source_rect;
    if (!isFiniteNumber(lx) || !isFiniteNumber(ly) || !isFiniteNumber(lw) || !isFiniteNumber(lh)) {
        throw new SceneResultManifestError("INVALID_PLACEMENT", "local_source_rect coordinates must be finite numbers");
    }
    if (lw <= 0 || lh <= 0) {
        throw new SceneResultManifestError("INVALID_PLACEMENT", "local_source_rect w and h must be > 0");
    }

    if (!isObject(transform)) {
        throw new SceneResultManifestError("INVALID_PLACEMENT", "placement.transform must be an object");
    }
    const { scale_x, scale_y, offset_x, offset_y } = transform;
    if (!isFiniteNumber(scale_x) || !isFiniteNumber(scale_y) || !isFiniteNumber(offset_x) || !isFiniteNumber(offset_y)) {
        throw new SceneResultManifestError("INVALID_PLACEMENT", "transform values must be finite numbers");
    }

    // Consistency check between transform and target rect (tolerance 0.001)
    const EPSILON = 0.001;
    if (
        Math.abs(scale_x - pw) > EPSILON ||
        Math.abs(scale_y - ph) > EPSILON ||
        Math.abs(offset_x - px) > EPSILON ||
        Math.abs(offset_y - py) > EPSILON
    ) {
        throw new SceneResultManifestError(
            "INCONSISTENT_PLACEMENT",
            `transform (${scale_x}, ${scale_y}, ${offset_x}, ${offset_y}) is inconsistent with page_target_rect (${pw}, ${ph}, ${px}, ${py})`
        );
    }

    if (!isObject(target_page_dimensions)) {
        throw new SceneResultManifestError("INVALID_PLACEMENT", "placement.target_page_dimensions must be an object");
    }
    const { width: pageW, height: pageH } = target_page_dimensions;
    if (!isPositiveInteger(pageW) || !isPositiveInteger(pageH)) {
        throw new SceneResultManifestError("INVALID_PLACEMENT", "target_page_dimensions must contain positive integer width and height");
    }

    // 8. Creation timestamp
    if (!isNonEmptyString(input.created_at) || Number.isNaN(Date.parse(input.created_at))) {
        throw new SceneResultManifestError("INVALID_TIMESTAMP", `created_at must be a valid ISO 8601 string, got "${input.created_at}"`);
    }

    // Return deep clone to ensure caller mutations cannot affect returned object
    return structuredClone(input);
}
