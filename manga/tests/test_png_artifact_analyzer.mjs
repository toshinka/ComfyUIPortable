import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";

import {
    PNG_SIGNATURE,
    PngArtifactAnalyzerError,
    computePngCrc32,
    analyzePngArtifact,
} from "../service/png_artifact_analyzer.mjs";

/**
 * Creates a valid synthetic PNG buffer in memory without disk access.
 *
 * @param {number} [width=512]
 * @param {number} [height=768]
 * @param {object} [options]
 * @returns {Buffer}
 */
function makeTestPng(width = 512, height = 768, options = {}) {
    const signature = Buffer.from(options.signature || PNG_SIGNATURE);

    const ihdrLength = options.ihdrLength !== undefined ? options.ihdrLength : 13;
    const chunkType = Buffer.from(options.chunkType || "IHDR", "ascii");

    const ihdrData = Buffer.alloc(13);
    if (options.rawWidth !== undefined) {
        ihdrData.writeUInt32BE(options.rawWidth, 0);
    } else {
        ihdrData.writeUInt32BE(width, 0);
    }
    if (options.rawHeight !== undefined) {
        ihdrData.writeUInt32BE(options.rawHeight, 4);
    } else {
        ihdrData.writeUInt32BE(height, 4);
    }
    ihdrData[8] = options.bitDepth !== undefined ? options.bitDepth : 8;
    ihdrData[9] = options.colorType !== undefined ? options.colorType : 2; // RGB
    ihdrData[10] = 0; // compression
    ihdrData[11] = 0; // filter
    ihdrData[12] = 0; // interlace

    const payload = Buffer.concat([chunkType, ihdrData]);
    const crc = options.crc !== undefined ? options.crc : computePngCrc32(payload, 0, payload.length);

    const ihdrChunk = Buffer.alloc(4 + 4 + 13 + 4);
    ihdrChunk.writeUInt32BE(ihdrLength, 0);
    ihdrChunk.set(chunkType, 4);
    ihdrChunk.set(ihdrData, 8);
    ihdrChunk.writeUInt32BE(crc, 21);

    const iendChunk = Buffer.from([
        0x00, 0x00, 0x00, 0x00,
        0x49, 0x45, 0x4E, 0x44, // "IEND"
        0xAE, 0x42, 0x60, 0x82,
    ]);

    return Buffer.concat([signature, ihdrChunk, iendChunk]);
}

test("A. A valid PNG Buffer returns the SHA-256 of its exact bytes", () => {
    const buf = makeTestPng(512, 768);
    const expectedDigest = createHash("sha256").update(buf).digest("hex");

    const result = analyzePngArtifact(buf);
    assert.equal(result.content_digest, expectedDigest);
});

test("B. IHDR dimensions are parsed correctly", () => {
    const buf = makeTestPng(1024, 1536);
    const result = analyzePngArtifact(buf);

    assert.equal(result.declared_width, 1024);
    assert.equal(result.declared_height, 1536);
});

test("C. Byte length matches the input", () => {
    const buf = makeTestPng(640, 480);
    const result = analyzePngArtifact(buf);

    assert.equal(result.byte_length, buf.length);
});

test("D. Incorrect PNG signature fails", () => {
    const badSignature = Buffer.from([0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77]);
    const buf = makeTestPng(512, 768, { signature: badSignature });

    assert.throws(
        () => analyzePngArtifact(buf),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "INVALID_PNG_SIGNATURE"
    );
});

test("E. Truncated signature or IHDR fails explicitly", () => {
    // Shorter than signature
    const shortSig = Buffer.from([0x89, 0x50, 0x4E]);
    assert.throws(
        () => analyzePngArtifact(shortSig),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "TRUNCATED_PNG"
    );

    // Signature present but cut off before IHDR completes (< 33 bytes)
    const truncatedIhdr = makeTestPng(512, 768).subarray(0, 25);
    assert.throws(
        () => analyzePngArtifact(truncatedIhdr),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "TRUNCATED_PNG"
    );
});

test("F. Non-IHDR first chunk fails", () => {
    const buf = makeTestPng(512, 768, { chunkType: "IDAT" });

    assert.throws(
        () => analyzePngArtifact(buf),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "INVALID_FIRST_CHUNK"
    );
});

test("G. Invalid IHDR length fails", () => {
    // IHDR length declared as 12 instead of 13
    const buf = makeTestPng(512, 768, { ihdrLength: 12 });

    assert.throws(
        () => analyzePngArtifact(buf),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "INVALID_IHDR_LENGTH"
    );
});

test("H. Invalid IHDR CRC fails", () => {
    const buf = makeTestPng(512, 768, { crc: 0x12345678 });

    assert.throws(
        () => analyzePngArtifact(buf),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "INVALID_IHDR_CRC"
    );
});

test("I. Zero or invalid dimensions fail", () => {
    // Zero width
    const zeroW = makeTestPng(0, 768, { rawWidth: 0 });
    assert.throws(
        () => analyzePngArtifact(zeroW),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "INVALID_PNG_DIMENSIONS"
    );

    // Zero height
    const zeroH = makeTestPng(512, 0, { rawHeight: 0 });
    assert.throws(
        () => analyzePngArtifact(zeroH),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "INVALID_PNG_DIMENSIONS"
    );

    // Exceeds 2^31 - 1
    const hugeW = makeTestPng(0, 768, { rawWidth: 0x80000000 });
    assert.throws(
        () => analyzePngArtifact(hugeW),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "INVALID_PNG_DIMENSIONS"
    );
});

test("J. Supplied expected dimensions match and succeed", () => {
    const buf = makeTestPng(512, 768);

    // With { width, height }
    const res1 = analyzePngArtifact(buf, { width: 512, height: 768 });
    assert.equal(res1.declared_width, 512);
    assert.equal(res1.declared_height, 768);

    // With { expected_width, expected_height }
    const res2 = analyzePngArtifact(buf, { expected_width: 512, expected_height: 768 });
    assert.equal(res2.declared_width, 512);
    assert.equal(res2.declared_height, 768);
});

test("K. Expected dimension mismatch fails explicitly", () => {
    const buf = makeTestPng(512, 768);

    // Width mismatch
    assert.throws(
        () => analyzePngArtifact(buf, { width: 1024, height: 768 }),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "DIMENSION_MISMATCH"
    );

    // Height mismatch
    assert.throws(
        () => analyzePngArtifact(buf, { width: 512, height: 1024 }),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "DIMENSION_MISMATCH"
    );
});

test("L. The source Buffer is unchanged", () => {
    const buf = makeTestPng(512, 768);
    const snapshot = Buffer.from(buf);

    analyzePngArtifact(buf);

    assert.ok(buf.equals(snapshot), "Source buffer must remain completely unmodified");
});

test("M. No filesystem, network, service or GPU operation is required", () => {
    // Non-buffer input rejection
    assert.throws(
        () => analyzePngArtifact("path/to/image.png"),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "INVALID_PNG_INPUT"
    );

    assert.throws(
        () => analyzePngArtifact(null),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "INVALID_PNG_INPUT"
    );

    assert.throws(
        () => analyzePngArtifact(Buffer.alloc(0)),
        (err) => err instanceof PngArtifactAnalyzerError && err.code === "EMPTY_PNG_INPUT"
    );
});
