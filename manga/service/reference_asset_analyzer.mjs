/**
 * reference_asset_analyzer.mjs — Server-side analyzer for Manga CAST Reference images.
 *
 * Validates canonical relative Reference asset identifiers (tegaki_manga_references/<name>.<ext>),
 * resolves the target file within an explicitly designated permitted asset root,
 * and computes SHA-256 over exact file bytes.
 */

import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
export const DEFAULT_REFERENCE_INPUT_DIR = path.resolve(here, "..", "..", "ComfyUI", "input");

export const REFERENCE_ASSET_PREFIX = "tegaki_manga_references/";
export const SUPPORTED_REFERENCE_EXTENSIONS = Object.freeze([".png", ".jpg", ".jpeg", ".webp"]);

export class ReferenceAssetAnalyzerError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "ReferenceAssetAnalyzerError";
        this.code = code;
    }
}

/**
 * Validates that referenceAsset is a canonical, single-level relative identifier.
 *
 * @param {string} identifier
 * @returns {string} The validated basename.
 * @throws {ReferenceAssetAnalyzerError}
 */
export function validateCanonicalReferenceAsset(identifier) {
    if (typeof identifier !== "string") {
        throw new ReferenceAssetAnalyzerError(
            "INVALID_REFERENCE_IDENTIFIER",
            "reference_asset must be a string"
        );
    }

    if (identifier.includes("\0")) {
        throw new ReferenceAssetAnalyzerError(
            "INVALID_REFERENCE_IDENTIFIER",
            "reference_asset contains embedded null character"
        );
    }

    if (
        identifier.includes("?") ||
        identifier.includes("#") ||
        identifier.startsWith("file://") ||
        identifier.startsWith("http://") ||
        identifier.startsWith("https://")
    ) {
        throw new ReferenceAssetAnalyzerError(
            "INVALID_REFERENCE_IDENTIFIER",
            "reference_asset must be a relative path, not a URL or query string"
        );
    }

    if (identifier.includes("\\")) {
        throw new ReferenceAssetAnalyzerError(
            "INVALID_REFERENCE_IDENTIFIER",
            "reference_asset must use canonical '/' separators, not backslashes"
        );
    }

    if (identifier.startsWith("/") || /^[a-zA-Z]:/.test(identifier)) {
        throw new ReferenceAssetAnalyzerError(
            "INVALID_REFERENCE_IDENTIFIER",
            "reference_asset must be relative, not absolute or drive-prefixed"
        );
    }

    if (!identifier.startsWith(REFERENCE_ASSET_PREFIX)) {
        throw new ReferenceAssetAnalyzerError(
            "INVALID_REFERENCE_IDENTIFIER",
            `reference_asset must start with '${REFERENCE_ASSET_PREFIX}'`
        );
    }

    const basename = identifier.slice(REFERENCE_ASSET_PREFIX.length);
    if (!basename || basename.length === 0) {
        throw new ReferenceAssetAnalyzerError(
            "INVALID_REFERENCE_IDENTIFIER",
            "reference_asset missing filename after prefix"
        );
    }

    if (basename.includes("/")) {
        throw new ReferenceAssetAnalyzerError(
            "INVALID_REFERENCE_IDENTIFIER",
            "reference_asset must be a single-level filename directly under prefix"
        );
    }

    if (basename === "." || basename === ".." || basename.includes("..")) {
        throw new ReferenceAssetAnalyzerError(
            "INVALID_REFERENCE_IDENTIFIER",
            "reference_asset contains invalid path traversal segments"
        );
    }

    if (/[\x00-\x1f\x7f]/.test(basename)) {
        throw new ReferenceAssetAnalyzerError(
            "INVALID_REFERENCE_IDENTIFIER",
            "reference_asset contains invalid control characters"
        );
    }

    // No leading or trailing whitespace allowed
    if (identifier.trim() !== identifier || basename.trim() !== basename) {
        throw new ReferenceAssetAnalyzerError(
            "INVALID_REFERENCE_IDENTIFIER",
            "reference_asset must not contain untrimmed whitespace"
        );
    }

    const ext = path.extname(basename).toLowerCase();
    if (!SUPPORTED_REFERENCE_EXTENSIONS.includes(ext)) {
        throw new ReferenceAssetAnalyzerError(
            "INVALID_REFERENCE_IDENTIFIER",
            `reference_asset extension '${ext}' is not supported. Must be one of: ${SUPPORTED_REFERENCE_EXTENSIONS.join(", ")}`
        );
    }

    return basename;
}

/**
 * Analyzes a CAST Reference asset image, computing its byte-level SHA-256 digest.
 *
 * @param {object} [input]
 * @param {string|null} [input.referenceAsset] - Canonical relative identifier.
 * @param {string|null} [input.reference_asset] - Alternative alias for referenceAsset.
 * @param {string} [input.permittedRoot] - Explicit filesystem root directory.
 * @param {string} [input.permitted_root] - Alternative alias for permittedRoot.
 * @param {boolean} [input.enabled=true] - Set to false for explicit no-reference runs.
 * @param {typeof fs} [fsApi=fs] - Filesystem API implementation for dependency injection / testing.
 * @returns {Promise<{
 *   enabled: boolean,
 *   reference_asset: string|null,
 *   content_digest: string|null,
 *   byte_length: number|null
 * }>}
 */
export async function analyzeReferenceAsset(input = {}, fsApi = fs) {
    if (input === null || typeof input !== "object") {
        return {
            enabled: false,
            reference_asset: null,
            content_digest: null,
            byte_length: null,
        };
    }

    // Explicit disabled reference request
    if (input.enabled === false) {
        return {
            enabled: false,
            reference_asset: null,
            content_digest: null,
            byte_length: null,
        };
    }

    const referenceAsset = input.referenceAsset !== undefined ? input.referenceAsset : input.reference_asset;
    if (referenceAsset === null || referenceAsset === undefined) {
        return {
            enabled: false,
            reference_asset: null,
            content_digest: null,
            byte_length: null,
        };
    }

    const basename = validateCanonicalReferenceAsset(referenceAsset);

    const permittedRoot = input.permittedRoot !== undefined ? input.permittedRoot : input.permitted_root;
    const rootPath = permittedRoot || DEFAULT_REFERENCE_INPUT_DIR;
    if (typeof rootPath !== "string" || !rootPath.trim()) {
        throw new ReferenceAssetAnalyzerError("INVALID_INPUT", "permittedRoot must be a non-empty string");
    }

    const resolvedRoot = path.resolve(rootPath);
    const assetDir = path.basename(resolvedRoot) === "tegaki_manga_references"
        ? resolvedRoot
        : path.join(resolvedRoot, "tegaki_manga_references");

    const targetFile = path.join(assetDir, basename);

    // Lexical path traversal protection
    const rel = path.relative(assetDir, targetFile);
    if (rel.startsWith("..") || path.isAbsolute(rel) || rel !== basename) {
        throw new ReferenceAssetAnalyzerError(
            "PATH_TRAVERSAL",
            `Reference asset path escapes permitted asset directory: ${referenceAsset}`
        );
    }

    // Check existence and file metadata
    let stat;
    try {
        stat = await fsApi.lstat(targetFile);
    } catch (err) {
        if (err.code === "ENOENT") {
            throw new ReferenceAssetAnalyzerError(
                "ASSET_NOT_FOUND",
                `Reference asset not found: ${referenceAsset}`
            );
        }
        throw new ReferenceAssetAnalyzerError(
            "ASSET_READ_FAILED",
            `Failed to inspect reference asset: ${err.message}`,
            { cause: err }
        );
    }

    if (!stat.isFile() && !stat.isSymbolicLink()) {
        throw new ReferenceAssetAnalyzerError(
            "ASSET_READ_FAILED",
            `Reference asset is not a regular file: ${referenceAsset}`
        );
    }

    if (stat.size === 0) {
        throw new ReferenceAssetAnalyzerError(
            "EMPTY_ASSET",
            `Reference asset is empty (0 bytes): ${referenceAsset}`
        );
    }

    // Symlink containment verification: realpath must reside inside real assetDir
    if (stat.isSymbolicLink()) {
        try {
            const realTarget = await fsApi.realpath(targetFile);
            let realAssetDir;
            try {
                realAssetDir = await fsApi.realpath(assetDir);
            } catch {
                realAssetDir = assetDir;
            }

            const isWindows = process.platform === "win32";
            const normDir = isWindows ? realAssetDir.toLowerCase() : realAssetDir;
            const normTarget = isWindows ? realTarget.toLowerCase() : realTarget;
            const relReal = path.relative(normDir, normTarget);

            if (relReal.startsWith("..") || path.isAbsolute(relReal)) {
                throw new ReferenceAssetAnalyzerError(
                    "PATH_TRAVERSAL",
                    `Reference asset symlink escapes permitted directory: ${referenceAsset}`
                );
            }
        } catch (err) {
            if (err instanceof ReferenceAssetAnalyzerError) throw err;
            throw new ReferenceAssetAnalyzerError(
                "ASSET_READ_FAILED",
                `Failed to verify symlink target: ${err.message}`,
                { cause: err }
            );
        }
    }

    // Read exact file bytes and compute SHA-256 digest
    let bytes;
    try {
        bytes = await fsApi.readFile(targetFile);
    } catch (err) {
        if (err.code === "ENOENT") {
            throw new ReferenceAssetAnalyzerError(
                "ASSET_NOT_FOUND",
                `Reference asset not found: ${referenceAsset}`
            );
        }
        throw new ReferenceAssetAnalyzerError(
            "ASSET_READ_FAILED",
            `Failed to read reference asset: ${err.message}`,
            { cause: err }
        );
    }

    if (bytes.length === 0) {
        throw new ReferenceAssetAnalyzerError(
            "EMPTY_ASSET",
            `Reference asset is empty (0 bytes): ${referenceAsset}`
        );
    }

    const content_digest = createHash("sha256").update(bytes).digest("hex");

    return {
        enabled: true,
        reference_asset: referenceAsset,
        content_digest,
        byte_length: bytes.length,
    };
}
