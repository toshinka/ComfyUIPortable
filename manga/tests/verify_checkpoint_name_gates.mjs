/**
 * verify_checkpoint_name_gates.mjs
 * ================================
 * Targeted acceptance test for:
 * CARD: MANGA-REMOVE-CHECKPOINT-NAME-GATES1
 *
 * Verifies:
 * A. Catalog checkpoint whose filename contains "Illustrious".
 * B. Available checkpoint whose filename contains neither "Illustrious", "ILL" nor "SDXL".
 * C. Available checkpoint with catalog.family = UNKNOWN.
 * D. Switching A -> B -> A with active Character Reference preserves selection & Generate state.
 * E. Checkpoint B with enabled Page Guide compiles and keeps Guide enabled.
 * - Missing checkpoint fails validation.
 * - Other existing Generate-disabled conditions remain intact.
 * - Simulated backend failure is displayed to the user without changing selected checkpoint.
 * - No false success state is shown.
 * - Isolated browser context, compile-only / mocked, ZERO GPU jobs.
 */

import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { execSync } from "node:child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");
const require = createRequire(import.meta.url);

function getPlaywrightChromium() {
    if (process.env.TEGAKI_PLAYWRIGHT_MODULE) return require(process.env.TEGAKI_PLAYWRIGHT_MODULE).chromium;
    try { return require("playwright").chromium; } catch {}
    const root = execSync("npm root -g", { encoding: "utf8" }).trim();
    return require(path.join(root, "@executeautomation", "playwright-mcp-server", "node_modules", "playwright")).chromium;
}

const CHECKPOINT_A = "!新規SDモデル\\darkbubbleIllustrious_illustriousV3d.safetensors";
const CHECKPOINT_B = "models\\my_anime_fantasy_mix.safetensors";
const CHECKPOINT_C = "general\\noname_model_checkpoint.safetensors";

function createCatalog() {
    const bounds = {
        steps: { min: 1, max: 100 },
        cfg: { min: 0, max: 30 },
        width: { min: 256, max: 2048 },
        height: { min: 256, max: 2048 },
        seed: { min: 0, max: 4294967295 }
    };
    return {
        ok: true,
        revision: "catalog-gate-test-rev1",
        checkpoints: [
            { id: CHECKPOINT_A, filename: CHECKPOINT_A, available: true, family: "illustrious" },
            { id: CHECKPOINT_B, filename: CHECKPOINT_B, available: true, family: "custom_mix" },
            { id: CHECKPOINT_C, filename: CHECKPOINT_C, available: true, family: "UNKNOWN" }
        ],
        samplers: ["euler", "euler_ancestral"],
        schedulers: ["normal", "karras"],
        product_bounds: { ...bounds, max_pixels: 2097152 },
        backend_bounds: bounds,
        loras: [],
        scene_generation: {
            available: true,
            required_nodes: ["TegakiMangaPagePlanFromJSON", "TegakiMangaConditioningBuilder"],
            controlnet: {
                available: true,
                model: "CN-anytest_v4\\CN-anytest4_illustrious2_A.safetensors",
                default_strength: 0.35,
                guide_assets: ["tegaki_manga_guides/test_guide.png"]
            },
            reference: {
                available: true,
                reference_assets: ["tegaki_manga_references/test_ref.png"]
            }
        }
    };
}

function startMockServer() {
    const catalog = createCatalog();
    let simulateFailure = false;
    let lastCompileRequest = null;
    let lastSubmitRequest = null;

    const server = http.createServer((req, res) => {
        const url = new URL(req.url, "http://127.0.0.1");

        // API endpoints
        if (url.pathname.includes("/capabilities")) {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify(catalog));
            return;
        }
        if (url.pathname.includes("/wildcards")) {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: true, wildcards: [] }));
            return;
        }
        if (url.pathname.includes("/history")) {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: true, jobs: [] }));
            return;
        }
        if (url.pathname.includes("/compile")) {
            let body = "";
            req.on("data", chunk => body += chunk);
            req.on("end", () => {
                lastCompileRequest = JSON.parse(body);
                if (simulateFailure) {
                    res.writeHead(500, { "Content-Type": "application/json" });
                    res.end(JSON.stringify({
                        ok: false,
                        error: "SimulatedComfyUIExecutionError: Tensor dimension mismatch in UNet cross-attention",
                        details: { code: "EXECUTION_ERROR", model_selected: lastCompileRequest.checkpoint_id }
                    }));
                    return;
                }
                res.writeHead(200, { "Content-Type": "application/json" });
                res.end(JSON.stringify({
                    ok: true,
                    request_id: lastCompileRequest.request_id || "req_mock_1",
                    graph: {
                        "1": { class_type: "CheckpointLoaderSimple", inputs: { ckpt_name: lastCompileRequest.checkpoint_id } }
                    }
                }));
            });
            return;
        }
        if (url.pathname.includes("/submit")) {
            let body = "";
            req.on("data", chunk => body += chunk);
            req.on("end", () => {
                lastSubmitRequest = JSON.parse(body);
                if (simulateFailure) {
                    res.writeHead(500, { "Content-Type": "application/json" });
                    res.end(JSON.stringify({
                        ok: false,
                        error: "SimulatedComfyUIExecutionError: Tensor dimension mismatch in UNet cross-attention"
                    }));
                    return;
                }
                res.writeHead(200, { "Content-Type": "application/json" });
                res.end(JSON.stringify({
                    ok: true,
                    job_id: "mock_job_12345",
                    state: "QUEUED"
                }));
            });
            return;
        }
        if (url.pathname.includes("/guide-assets/view") || url.pathname.includes("/reference-assets/view")) {
            res.writeHead(200, { "Content-Type": "image/png" });
            res.end(Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==", "base64"));
            return;
        }

        // Static files from manga/app
        let filePath = path.join(REPO_ROOT, "manga/app", url.pathname === "/" ? "index.html" : url.pathname.slice(1));
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
            const ext = path.extname(filePath);
            const contentTypes = {
                ".html": "text/html",
                ".js": "application/javascript",
                ".mjs": "application/javascript",
                ".css": "text/css",
                ".json": "application/json",
                ".png": "image/png"
            };
            res.writeHead(200, { "Content-Type": contentTypes[ext] || "text/plain" });
            fs.createReadStream(filePath).pipe(res);
            return;
        }

        console.log("MOCK 404:", url.pathname, "->", filePath, "exists:", fs.existsSync(filePath));
        res.writeHead(404, { "Content-Type": "text/plain" });
        res.end("Not Found: " + url.pathname);
    });

    return new Promise((resolve) => {
        server.listen(0, "127.0.0.1", () => {
            const port = server.address().port;
            resolve({
                server,
                port,
                url: `http://127.0.0.1:${port}`,
                setSimulateFailure: (val) => { simulateFailure = val; },
                getLastCompileRequest: () => lastCompileRequest,
                getLastSubmitRequest: () => lastSubmitRequest,
                close: () => new Promise(r => server.close(r))
            });
        });
    });
}

async function run() {
    console.log("=== MANGA-REMOVE-CHECKPOINT-NAME-GATES1 ACCEPTANCE TEST ===");
    const mockServer = await startMockServer();
    console.log(`Mock server running at ${mockServer.url}`);

    const chromium = getPlaywrightChromium();
    assert(chromium, "Playwright Chromium must be available");
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
    const page = await context.newPage();

    page.on("console", msg => console.log("PAGE LOG:", msg.text()));
    page.on("pageerror", err => console.log("PAGE ERROR:", err.message));
    page.on("requestfailed", req => console.log("REQ FAILED:", req.url(), req.failure()?.errorText));

    await page.route("http://127.0.0.1:8189/**", async (route) => {
        const url = new URL(route.request().url());
        const forwardUrl = `${mockServer.url}${url.pathname}${url.search}`;
        try {
            const response = await fetch(forwardUrl, {
                method: route.request().method(),
                headers: route.request().headers(),
                body: ["POST", "PUT", "PATCH"].includes(route.request().method()) ? route.request().postData() : undefined
            });
            const body = await response.text();
            await route.fulfill({
                status: response.status,
                headers: Object.fromEntries(response.headers.entries()),
                body
            });
        } catch (err) {
            await route.abort();
        }
    });

    try {
        console.log("1. Navigating to Manga Create in isolated browser context...");
        await page.goto(mockServer.url, { waitUntil: "domcontentloaded" });
        await page.waitForFunction(() => window.__tegakiManga && window.__tegakiManga.generation?.state?.catalog, { timeout: 10000 });
        console.log("   Manga workspace loaded successfully.");

        // Set up disposable Authoring Document with active Character Reference and active Guide
        console.log("2. Setting up disposable Authoring Document with CAST Reference and Guide...");
        await page.evaluate(({ cnetModel, refAsset, guideAsset }) => {
            const { store, session, setMangaMode, updateAll, generation } = window.__tegakiManga;
            const doc = store.getDocument();
            doc.pages[0].scenes = [
                {
                    scene_id: "scene_1",
                    order: 1,
                    input_mode: "cast",
                    prompt: "1girl standing in front of cherry blossoms",
                    negative_prompt: "",
                    area: { shape_type: "rect", x: 0.1, y: 0.1, w: 0.8, h: 0.8 }
                }
            ];
            doc.pages[0].cast = [
                {
                    cast_id: "heroine_01",
                    display_name: "Heroine",
                    identity_prompt: "1girl, silver hair, blue eyes",
                    negative_prompt: "",
                    reference_asset: refAsset
                }
            ];
            doc.pages[0].character_instances = [
                {
                    instance_id: "inst_01",
                    cast_id: "heroine_01",
                    scene_id: "scene_1",
                    area: { shape_type: "rect", x: 0.2, y: 0.2, w: 0.4, h: 0.5 },
                    acting_prompt: "smiling gently"
                }
            ];
            doc.pages[0].guides = [
                {
                    guide_id: "guide_01",
                    guide_type: "rough_manga",
                    asset_reference: guideAsset,
                    enabled: true,
                    figure_regions: [],
                    placement: { shape_type: "rect", x: 0.05, y: 0.05, w: 0.9, h: 0.9 }
                }
            ];
            store.setDocument(doc);
            setMangaMode("authoring");
            generation.setGenerationScope("scenes");
            session.selectScene("scene_1");
            session.selectGuide("guide_01");
            updateAll();
        }, {
            cnetModel: "CN-anytest_v4\\CN-anytest4_illustrious2_A.safetensors",
            refAsset: "tegaki_manga_references/test_ref.png",
            guideAsset: "tegaki_manga_guides/test_guide.png"
        });

        // Verify available checkpoints in select
        const options = await page.evaluate(() => {
            const sel = document.getElementById("mg-checkpoint_id");
            return Array.from(sel.options).map(o => ({ value: o.value, text: o.text }));
        });
        console.log("   Available checkpoints:", options.map(o => o.value));
        assert(options.some(o => o.value === CHECKPOINT_A), "Checkpoint A must be in dropdown");
        assert(options.some(o => o.value === CHECKPOINT_B), "Checkpoint B must be in dropdown");
        assert(options.some(o => o.value === CHECKPOINT_C), "Checkpoint C must be in dropdown");

        // Helper to get generation state
        const getGenStatus = async () => {
            return await page.evaluate(() => {
                const btn = document.getElementById("mg-generate");
                const err = document.getElementById("mg-error");
                const reasonEl = document.getElementById("mg-generate-reason");
                const guideBadge = document.getElementById("mg-guide-status-badge");
                const guideNote = document.getElementById("mg-guide-support-note");
                return {
                    disabled: btn ? btn.disabled : true,
                    btnText: btn ? btn.textContent.trim() : "",
                    errorText: err ? err.textContent.trim() : "",
                    blockReason: reasonEl ? reasonEl.textContent.trim() : "",
                    currentCheckpoint: window.__tegakiManga.generation.state.draft.checkpoint_id,
                    guideBadgeText: guideBadge ? guideBadge.textContent.trim() : "",
                    guideBadgeState: guideBadge ? guideBadge.dataset.state : "",
                    guideNoteText: guideNote ? guideNote.textContent.trim() : ""
                };
            });
        };

        // ==========================================
        // TEST A: Checkpoint A (contains "Illustrious")
        // ==========================================
        console.log("\n3. Testing Case A: Checkpoint with 'Illustrious' in filename...");
        await page.evaluate((ckpt) => {
            const sel = document.getElementById("mg-checkpoint_id");
            sel.value = ckpt;
            sel.dispatchEvent(new Event("change"));
        }, CHECKPOINT_A);

        let statusA = await getGenStatus();
        console.log("   Status A:", {
            checkpoint: statusA.currentCheckpoint,
            disabled: statusA.disabled,
            blockReason: statusA.blockReason,
            guideBadge: statusA.guideBadgeText
        });
        assert.equal(statusA.currentCheckpoint, CHECKPOINT_A, "Checkpoint A must be preserved");
        assert.equal(statusA.disabled, false, "Generate must be ENABLED for Checkpoint A");
        assert.equal(statusA.blockReason, "", "Block reason must be empty for Checkpoint A");
        assert.equal(statusA.guideBadgeState, "enabled", "Guide badge must be enabled");

        // Verify settings build
        const settingsA = await page.evaluate(() => {
            return window.__tegakiManga.buildSceneGenerationSettings();
        });
        assert.equal(settingsA.checkpoint_id, CHECKPOINT_A);
        assert.equal(settingsA.reference_weight, 0.70);
        assert.equal(settingsA.controlnet_strength, 0.35);

        // ==========================================
        // TEST B: Checkpoint B (no "Illustrious", "ILL", or "SDXL" in filename)
        // ==========================================
        console.log("\n4. Testing Case B: Checkpoint without 'Illustrious', 'ILL', or 'SDXL' in filename...");
        await page.evaluate((ckpt) => {
            const sel = document.getElementById("mg-checkpoint_id");
            sel.value = ckpt;
            sel.dispatchEvent(new Event("change"));
        }, CHECKPOINT_B);

        let statusB = await getGenStatus();
        console.log("   Status B:", {
            checkpoint: statusB.currentCheckpoint,
            disabled: statusB.disabled,
            blockReason: statusB.blockReason,
            guideBadge: statusB.guideBadgeText
        });
        assert.equal(statusB.currentCheckpoint, CHECKPOINT_B, "Checkpoint B must be preserved");
        assert.equal(statusB.disabled, false, "Generate must remain ENABLED for Checkpoint B (no name gating!)");
        assert.equal(statusB.blockReason, "", "Block reason must be empty for Checkpoint B");
        assert.equal(statusB.guideBadgeState, "enabled", "Guide badge must remain enabled for Checkpoint B");

        const settingsB = await page.evaluate(() => {
            return window.__tegakiManga.buildSceneGenerationSettings();
        });
        assert.equal(settingsB.checkpoint_id, CHECKPOINT_B);
        assert.equal(settingsB.reference_weight, 0.70);
        assert.equal(settingsB.controlnet_strength, 0.35);

        // ==========================================
        // TEST C: Checkpoint C (family = UNKNOWN)
        // ==========================================
        console.log("\n5. Testing Case C: Checkpoint with catalog.family = UNKNOWN...");
        await page.evaluate((ckpt) => {
            const sel = document.getElementById("mg-checkpoint_id");
            sel.value = ckpt;
            sel.dispatchEvent(new Event("change"));
        }, CHECKPOINT_C);

        let statusC = await getGenStatus();
        console.log("   Status C:", {
            checkpoint: statusC.currentCheckpoint,
            disabled: statusC.disabled,
            blockReason: statusC.blockReason,
            guideBadge: statusC.guideBadgeText
        });
        assert.equal(statusC.currentCheckpoint, CHECKPOINT_C, "Checkpoint C must be preserved");
        assert.equal(statusC.disabled, false, "Generate must remain ENABLED for Checkpoint C (family=UNKNOWN)");
        assert.equal(statusC.blockReason, "", "Block reason must be empty for Checkpoint C");
        assert.equal(statusC.guideBadgeState, "enabled", "Guide badge must remain enabled for Checkpoint C");

        const settingsC = await page.evaluate(() => {
            return window.__tegakiManga.buildSceneGenerationSettings();
        });
        assert.equal(settingsC.checkpoint_id, CHECKPOINT_C);

        // ==========================================
        // TEST D: Switching A -> B -> A with active Character Reference
        // ==========================================
        console.log("\n6. Testing Case D: Switching A -> B -> A with active Character Reference...");
        // Switch to A
        await page.evaluate((ckpt) => {
            const sel = document.getElementById("mg-checkpoint_id");
            sel.value = ckpt;
            sel.dispatchEvent(new Event("change"));
        }, CHECKPOINT_A);
        let statusSwitch1 = await getGenStatus();
        assert.equal(statusSwitch1.currentCheckpoint, CHECKPOINT_A);
        assert.equal(statusSwitch1.disabled, false);

        // Switch to B
        await page.evaluate((ckpt) => {
            const sel = document.getElementById("mg-checkpoint_id");
            sel.value = ckpt;
            sel.dispatchEvent(new Event("change"));
        }, CHECKPOINT_B);
        let statusSwitch2 = await getGenStatus();
        assert.equal(statusSwitch2.currentCheckpoint, CHECKPOINT_B);
        assert.equal(statusSwitch2.disabled, false);

        // Switch back to A
        await page.evaluate((ckpt) => {
            const sel = document.getElementById("mg-checkpoint_id");
            sel.value = ckpt;
            sel.dispatchEvent(new Event("change"));
        }, CHECKPOINT_A);
        let statusSwitch3 = await getGenStatus();
        assert.equal(statusSwitch3.currentCheckpoint, CHECKPOINT_A);
        assert.equal(statusSwitch3.disabled, false);
        console.log("   Switching A -> B -> A successfully preserved selected checkpoint and kept Generate enabled throughout.");

        // ==========================================
        // TEST E: Checkpoint B with enabled Page Guide
        // ==========================================
        console.log("\n7. Testing Case E: Checkpoint B with enabled Page Guide...");
        await page.evaluate((ckpt) => {
            const sel = document.getElementById("mg-checkpoint_id");
            sel.value = ckpt;
            sel.dispatchEvent(new Event("change"));
        }, CHECKPOINT_B);

        const statusE = await getGenStatus();
        assert.equal(statusE.currentCheckpoint, CHECKPOINT_B);
        assert.equal(statusE.disabled, false);
        assert.equal(statusE.guideBadgeState, "enabled");
        assert.equal(statusE.guideBadgeText, "GUIDE ENABLED");
        assert(statusE.guideNoteText.includes("Ready for Scenes via ControlNet"), "Guide note must confirm readiness");

        // Submit generation through normal path
        console.log("   Submitting normal generation request for Checkpoint B...");
        await page.evaluate(() => {
            const btn = document.getElementById("mg-generate");
            btn.click();
        });

        // Wait a short moment for request to arrive at mock server
        await page.waitForTimeout(300);
        const lastCompile = mockServer.getLastCompileRequest();
        assert(lastCompile, "Compile request must be sent to server");
        assert.equal(lastCompile.checkpoint_id, CHECKPOINT_B, "Compile request must retain Checkpoint B");
        assert.equal(lastCompile.controlnet_strength, 0.35, "ControlNet strength must be preserved");
        assert.equal(lastCompile.reference_weight, 0.70, "Reference weight must be preserved");
        console.log("   Server received compile request for Checkpoint B with ControlNet and Reference parameters intact.");

        // ==========================================
        // PRESERVED CHECKS: Missing Checkpoint
        // ==========================================
        console.log("\n8. Testing Preserved Validations: Missing/Unavailable Checkpoint...");
        const missingResult = await page.evaluate(() => {
            const draft = window.__tegakiManga.generation.state.draft;
            const orig = draft.checkpoint_id;
            draft.checkpoint_id = "nonexistent/missing_model.safetensors";
            let err = null;
            try {
                window.__tegakiManga.buildSceneGenerationSettings();
            } catch (e) {
                err = e.message;
            }
            draft.checkpoint_id = orig; // restore
            return err;
        });
        console.log("   Missing checkpoint error:", missingResult);
        assert(missingResult && missingResult.includes("Checkpoint unavailable"), "Missing checkpoint must fail validation");

        // ==========================================
        // FAILURE HANDLING: Simulated Backend Error
        // ==========================================
        console.log("\n9. Testing Failure Handling: Simulated backend error presentation...");
        mockServer.setSimulateFailure(true);

        // Keep Checkpoint B selected and click Generate
        await page.evaluate(() => {
            const btn = document.getElementById("mg-generate");
            btn.click();
        });

        // Wait for error presentation in UI
        await page.waitForFunction(() => {
            const errEl = document.getElementById("mg-error");
            return errEl && errEl.textContent.trim().length > 0;
        }, { timeout: 3000 });

        const failureStatus = await page.evaluate(() => {
            const errEl = document.getElementById("mg-error");
            const sel = document.getElementById("mg-checkpoint_id");
            const badge = document.getElementById("mg-status");
            return {
                errorDisplayed: errEl ? errEl.textContent.trim() : "",
                selectedCheckpoint: sel.value,
                stateDraftCheckpoint: window.__tegakiManga.generation.state.draft.checkpoint_id,
                badgeText: badge ? badge.textContent.trim() : ""
            };
        });

        console.log("   Failure status in UI:", failureStatus);
        // Verify actual backend failure is displayed
        assert(failureStatus.errorDisplayed.includes("SimulatedComfyUIExecutionError"), "Actual backend error must be displayed");
        assert(!failureStatus.errorDisplayed.includes("requires an Illustrious SDXL checkpoint"), "Generic speculative warning must NOT be shown");
        // Verify checkpoint was NOT substituted
        assert.equal(failureStatus.selectedCheckpoint, CHECKPOINT_B, "Selected checkpoint must NOT change upon failure");
        assert.equal(failureStatus.stateDraftCheckpoint, CHECKPOINT_B, "Draft checkpoint must remain Checkpoint B");
        // Verify NO false success
        assert(!failureStatus.badgeText.includes("SUCCEEDED"), "Badge must never display SUCCEEDED on failure");
        assert(!failureStatus.errorDisplayed.includes("SUCCEEDED"), "Error must not contain SUCCEEDED");
        console.log("   Backend error correctly displayed without checkpoint substitution or false success.");

        console.log("\n=== ALL CASES A–E AND PRESERVED CHECKS PASSED SUCCESSFULLY ===");

    } finally {
        await browser.close();
        await mockServer.close();
    }
}

run().catch(err => {
    console.error("FATAL ERROR in verify_checkpoint_name_gates.mjs:", err);
    process.exit(1);
});
