/**
 * png_artifact_analyzer.mjs — Pure PNG artifact analyzer.
 *
 * Inspects a retrieved PNG byte Buffer to extract declared IHDR dimensions
 * and calculate the byte-level SHA-256 content digest.
 * Performs strict structural validation over PNG signature, chunk sequence,
 * IHDR length, and IHDR CRC without external dependencies.
 */

import { createHash } from "node:crypto";

export const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
const MINIMUM_PNG_HEADER_LENGTH = 33; // 8 (sig) + 4 (len) + 4 (IHDR) + 13 (data) + 4 (crc)

// Precomputed CRC-32 table for ISO 3309 / ITU-T V.42 / PNG chunk checksums
const CRC_TABLE = new Uint32Array(256);
for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
        c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    }
    CRC_TABLE[n] = c >>> 0;
}

/**
 * Computes CRC-32 checksum for a slice of buffer bytes.
 *
 * @param {Buffer} buf
 * @param {number} start - Offset inclusive.
 * @param {number} end - Offset exclusive.
 * @returns {number} Unsigned 32-bit integer.
 */
export function computePngCrc32(buf, start, end) {
    let crc = 0xffffffff;
    for (let i = start; i < end; i++) {
        crc = CRC_TABLE[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8);
    }
    return (crc ^ 0xffffffff) >>> 0;
}

export class PngArtifactAnalyzerError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "PngArtifactAnalyzerError";
        this.code = code;
    }
}

/**
 * Analyzes an in-memory PNG Buffer to extract declared dimensions and SHA-256 digest.
 *
 * @param {Buffer} bytes - Exact PNG bytes.
 * @param {object} [expectedDimensions] - Optional expected canvas dimensions { width, height }.
 * @returns {{
 *   content_digest: string,
 *   declared_width: number,
 *   declared_height: number,
 *   byte_length: number
 * }}
 */
export function analyzePngArtifact(bytes, expectedDimensions = null) {
    // 1. Input contract validation
    if (!Buffer.isBuffer(bytes)) {
        throw new PngArtifactAnalyzerError(
            "INVALID_PNG_INPUT",
            "Input must be a Node.js Buffer"
        );
    }
    if (bytes.length === 0) {
        throw new PngArtifactAnalyzerError(
            "EMPTY_PNG_INPUT",
            "PNG buffer must not be empty"
        );
    }

    // 2. Minimum length check for signature + complete IHDR chunk
    if (bytes.length < MINIMUM_PNG_HEADER_LENGTH) {
        throw new PngArtifactAnalyzerError(
            "TRUNCATED_PNG",
            `PNG buffer is truncated: length ${bytes.length} is less than minimum header size ${MINIMUM_PNG_HEADER_LENGTH}`
        );
    }

    // 3. PNG signature check
    if (!bytes.subarray(0, 8).equals(PNG_SIGNATURE)) {
        throw new PngArtifactAnalyzerError(
            "INVALID_PNG_SIGNATURE",
            "Buffer does not start with standard PNG signature"
        );
    }

    // 4. IHDR length check (offset 8..11)
    const ihdrLength = bytes.readUInt32BE(8);
    if (ihdrLength !== 13) {
        throw new PngArtifactAnalyzerError(
            "INVALID_IHDR_LENGTH",
            `IHDR chunk data length must be 13, got ${ihdrLength}`
        );
    }

    // 5. First chunk type check (offset 12..15)
    const chunkType = bytes.toString("ascii", 12, 16);
    if (chunkType !== "IHDR") {
        throw new PngArtifactAnalyzerError(
            "INVALID_FIRST_CHUNK",
            `First PNG chunk must be IHDR, got "${chunkType}"`
        );
    }

    // 6. IHDR CRC check (offset 29..32 covers bytes 12..28 inclusive)
    const expectedCrc = bytes.readUInt32BE(29);
    const actualCrc = computePngCrc32(bytes, 12, 29);
    if (actualCrc !== expectedCrc) {
        throw new PngArtifactAnalyzerError(
            "INVALID_IHDR_CRC",
            `IHDR CRC mismatch: expected 0x${expectedCrc.toString(16).padStart(8, "0")}, calculated 0x${actualCrc.toString(16).padStart(8, "0")}`
        );
    }

    // 7. Width and height extraction and validation (offsets 16..19, 20..23)
    const declared_width = bytes.readUInt32BE(16);
    const declared_height = bytes.readUInt32BE(20);

    // PNG spec: width and height are integers in 1 .. 2^31 - 1
    if (declared_width === 0 || declared_width > 0x7fffffff || declared_height === 0 || declared_height > 0x7fffffff) {
        throw new PngArtifactAnalyzerError(
            "INVALID_PNG_DIMENSIONS",
            `Declared PNG dimensions must be non-zero positive integers up to 2^31-1, got width=${declared_width}, height=${declared_height}`
        );
    }

    // 8. Optional expected dimensions check
    if (expectedDimensions !== null && typeof expectedDimensions === "object") {
        let expW = null;
        let expH = null;

        if ("width" in expectedDimensions || "height" in expectedDimensions) {
            expW = expectedDimensions.width;
            expH = expectedDimensions.height;
        } else if ("expected_width" in expectedDimensions || "expected_height" in expectedDimensions) {
            expW = expectedDimensions.expected_width;
            expH = expectedDimensions.expected_height;
        } else if ("expectedDimensions" in expectedDimensions && typeof expectedDimensions.expectedDimensions === "object") {
            expW = expectedDimensions.expectedDimensions.width;
            expH = expectedDimensions.expectedDimensions.height;
        }

        if (expW !== null || expH !== null) {
            if (typeof expW !== "number" || !Number.isInteger(expW) || expW <= 0 ||
                typeof expH !== "number" || !Number.isInteger(expH) || expH <= 0) {
                throw new PngArtifactAnalyzerError(
                    "INVALID_EXPECTED_DIMENSIONS",
                    `Expected dimensions must be positive integers, got width=${expW}, height=${expH}`
                );
            }
            if (declared_width !== expW || declared_height !== expH) {
                throw new PngArtifactAnalyzerError(
                    "DIMENSION_MISMATCH",
                    `Declared PNG dimensions (${declared_width}x${declared_height}) do not match expected dimensions (${expW}x${expH})`
                );
            }
        }
    }

    // 9. Full-buffer SHA-256 calculation
    const content_digest = createHash("sha256").update(bytes).digest("hex");

    return {
        content_digest,
        declared_width,
        declared_height,
        byte_length: bytes.length,
    };
}
