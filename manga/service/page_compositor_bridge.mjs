/**
 * page_compositor_bridge.mjs — Node -> Python Page Compositor Bridge.
 *
 * Bridges the trusted Node composition plan preparation to the Python CPU
 * pixel compositor (/tegaki/manga/page/composite), receives raw PNG bytes,
 * validates dimensions and SHA-256 digest via analyzePngArtifact, and returns
 * ephemeral composite evidence.
 */

import { preparePageComposition } from "./page_compositor_prep.mjs";
import { analyzePngArtifact } from "./png_artifact_analyzer.mjs";

export class PageCompositorBridgeError extends Error {
    constructor(code, message, status = 500, details = null) {
        super(message);
        this.name = "PageCompositorBridgeError";
        this.code = code;
        this.status = status;
        this.details = details;
    }
}

function isObject(val) {
    return val !== null && typeof val === "object" && !Array.isArray(val);
}

function isNonEmptyString(val) {
    return typeof val === "string" && val.trim().length > 0;
}

const FORBIDDEN_CALLER_FIELDS = Object.freeze([
    "composition_plan",
    "backend_url",
    "backend_origin",
    "manifest_id",
    "artifact_locator",
    "output_path",
    "composite_bytes",
    "plan_id",
    "source_digests",
    "expected_digest",
]);

export class PageCompositorBridge {
    /**
     * @param {object} [options]
     * @param {string} [options.backendUrl="http://127.0.0.1:8189"] - Fixed loopback HTTP origin for Manga backend.
     * @param {SceneResultStore} [options.store=null] - Store instance for prep.
     * @param {SceneResultIndex} [options.index=null] - Index instance for prep.
     * @param {typeof fetch} [options.fetchFn=fetch] - Fetch implementation (injectable for testing).
     * @param {number} [options.timeoutMs=15000] - Request timeout.
     * @param {Function} [options.prepFn=preparePageComposition] - Plan prep function (injectable for testing).
     */
    constructor({
        backendUrl = "http://127.0.0.1:8189",
        store = null,
        index = null,
        fetchFn = fetch,
        timeoutMs = 15000,
        prepFn = preparePageComposition,
    } = {}) {
        const target = new URL(backendUrl);
        if (target.protocol !== "http:" || !["127.0.0.1", "localhost"].includes(target.hostname) ||
            target.pathname !== "/" || target.search || target.hash) {
            throw new PageCompositorBridgeError(
                "BACKEND_TARGET_INVALID",
                "Manga backend must be a fixed loopback HTTP origin",
                500
            );
        }
        this.origin = target.origin;
        this.store = store;
        this.index = index;
        this.fetchFn = fetchFn;
        this.timeoutMs = timeoutMs;
        this.prepFn = prepFn;
    }

    /**
     * Composes one Authoring Page by preparing a trusted composition plan, submitting it to
     * the Python CPU pixel compositor, and verifying the returned PNG bytes.
     *
     * @param {object} input
     * @param {object} input.authoring_document
     * @param {object} input.generation_params
     * @param {string} [input.page_id]
     * @param {number} [input.page_index]
     * @returns {Promise<{
     *   plan: object,
     *   composite_bytes: Buffer,
     *   composite: {
     *     content_digest: string,
     *     declared_width: number,
     *     declared_height: number,
     *     byte_length: number
     *   },
     *   statistics: {
     *     total_scenes: number,
     *     composed_scenes: number,
     *     unfilled_scenes: number
     *   }
     * }>}
     */
    async composeCurrentPage(input) {
        if (!isObject(input)) {
            throw new PageCompositorBridgeError("INVALID_REQUEST", "Input must be a non-null object", 400);
        }

        // 1. Enforce strict trust boundary: reject caller-supplied plan/authority fields
        for (const forbidden of FORBIDDEN_CALLER_FIELDS) {
            if (forbidden in input) {
                throw new PageCompositorBridgeError(
                    "FORBIDDEN_CALLER_FIELD",
                    `Caller cannot supply trusted authority field '${forbidden}'`,
                    400
                );
            }
        }

        if (!isObject(input.authoring_document)) {
            throw new PageCompositorBridgeError("INVALID_REQUEST", "authoring_document must be a non-null object", 400);
        }
        if (!isObject(input.generation_params)) {
            throw new PageCompositorBridgeError("INVALID_REQUEST", "generation_params must be a non-null object", 400);
        }

        // 2. Server-side Plan Creation: call preparePageComposition exactly once
        let plan;
        try {
            plan = await this.prepFn({
                authoring_document: input.authoring_document,
                generation_params: input.generation_params,
                page_id: input.page_id,
                page_index: input.page_index,
                store: this.store,
                index: this.index,
                backendUrl: this.origin,
                fetchFn: this.fetchFn,
            });
        } catch (prepErr) {
            throw new PageCompositorBridgeError(
                prepErr.code || "PLAN_PREPARATION_FAILED",
                `Page composition plan preparation failed: ${prepErr.message}`,
                prepErr.status || 400,
                { cause: prepErr }
            );
        }

        if (!isObject(plan) || !isObject(plan.page)) {
            throw new PageCompositorBridgeError(
                "INVALID_PREPARED_PLAN",
                "Prepared plan must be a valid object with page metadata",
                500
            );
        }

        const expectedWidth = plan.page.width;
        const expectedHeight = plan.page.height;
        if (typeof expectedWidth !== "number" || typeof expectedHeight !== "number") {
            throw new PageCompositorBridgeError(
                "INVALID_PLAN_DIMENSIONS",
                "Plan page dimensions must be numbers",
                500
            );
        }

        // 3. Submit exact trusted plan to Python compositor: POST /tegaki/manga/page/composite
        const compositeUrl = `${this.origin}/tegaki/manga/page/composite`;
        let response;
        try {
            response = await this.fetchFn(compositeUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ composition_plan: plan }),
                signal: AbortSignal.timeout(this.timeoutMs),
            });
        } catch (fetchErr) {
            throw new PageCompositorBridgeError(
                "TRANSPORT_FAILURE",
                `Compositor backend transport failed: ${fetchErr.message}`,
                502,
                { cause: fetchErr }
            );
        }

        // 4. Handle non-success responses
        if (!response.ok) {
            let errCode = "BACKEND_COMPOSITE_FAILED";
            let errMsg = `Compositor backend request failed with status ${response.status}`;
            try {
                const errJson = await response.json();
                if (errJson && isNonEmptyString(errJson.error_code)) {
                    errCode = errJson.error_code;
                }
                if (errJson && isNonEmptyString(errJson.error)) {
                    // Strip any path or trace leak
                    if (!errJson.error.includes("Traceback") && !errJson.error.includes(":\\")) {
                        errMsg = errJson.error;
                    }
                }
            } catch {
                // Malformed or non-JSON error body remains generic backend error
            }

            throw new PageCompositorBridgeError(errCode, errMsg, response.status);
        }

        // 5. Verify Content-Type
        const contentType = (response.headers.get("content-type") || "").toLowerCase();
        if (!contentType.includes("image/png")) {
            throw new PageCompositorBridgeError(
                "INVALID_CONTENT_TYPE",
                `Compositor response must be image/png, got '${contentType}'`,
                502
            );
        }

        // 6. Read exact binary body bytes
        let compositeBytes;
        try {
            const arrayBuf = await response.arrayBuffer();
            compositeBytes = Buffer.from(arrayBuf);
        } catch (readErr) {
            throw new PageCompositorBridgeError(
                "BODY_READ_FAILED",
                `Failed to read composite response bytes: ${readErr.message}`,
                502,
                { cause: readErr }
            );
        }

        // 7. Verify output PNG with analyzePngArtifact
        let analyzed;
        try {
            analyzed = analyzePngArtifact(compositeBytes, {
                width: expectedWidth,
                height: expectedHeight,
            });
        } catch (analysisErr) {
            throw new PageCompositorBridgeError(
                analysisErr.code || "COMPOSITE_ANALYSIS_FAILED",
                `Composite artifact validation failed: ${analysisErr.message}`,
                502,
                { cause: analysisErr }
            );
        }

        // 8. Return ephemeral composite evidence
        const scenes = Array.isArray(plan.scenes) ? plan.scenes : [];
        return {
            plan,
            composite_bytes: compositeBytes,
            composite: {
                content_digest: analyzed.content_digest,
                declared_width: analyzed.declared_width,
                declared_height: analyzed.declared_height,
                byte_length: analyzed.byte_length,
            },
            statistics: {
                total_scenes: scenes.length,
                composed_scenes: scenes.filter(s => s.state === "CURRENT_RESULT").length,
                unfilled_scenes: scenes.filter(s => s.state === "UNFILLED").length,
            },
        };
    }
}

/**
 * Functional entry for composeCurrentPage.
 */
export async function composeCurrentPage(input, options = {}) {
    const bridge = new PageCompositorBridge(options);
    return bridge.composeCurrentPage(input);
}
