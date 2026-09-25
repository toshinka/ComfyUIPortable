import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
    MangaDomainRuntime,
    OwnershipClassification,
    MANGA_PROFILE_NODE
} from "../service/manga_domain_runtime.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "../..");

async function createMockServer(handler) {
    const server = http.createServer((req, res) => {
        let body = "";
        req.on("data", chunk => { body += chunk; });
        req.on("end", () => handler(req, res, body));
    });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    const port = server.address().port;
    return {
        port,
        close: () => new Promise((resolve) => server.close(resolve))
    };
}

async function run() {
    console.log("Starting verify_manga_runtime_profile.mjs tests...");

    // Assertion A: Manga runtime no longer requires the H3-only/wrong node identity.
    console.log("Checking Assertion A: Profile node is not TegakiMinimumHandSceneEditor...");
    assert.notEqual(MANGA_PROFILE_NODE, "TegakiMinimumHandSceneEditor", "MANGA_PROFILE_NODE must not be TegakiMinimumHandSceneEditor");
    const defaultRuntime = new MangaDomainRuntime();
    assert.notEqual(defaultRuntime.profileNode, "TegakiMinimumHandSceneEditor", "Default runtime profileNode must not be TegakiMinimumHandSceneEditor");
    console.log("  PASS Assertion A");

    // Assertion B: Expected profile node/capability exactly matches a real Manga export.
    console.log("Checking Assertion B: Profile node matches exported Manga node...");
    assert.equal(MANGA_PROFILE_NODE, "TegakiMangaSceneCompiler");
    assert.equal(defaultRuntime.profileNode, "TegakiMangaSceneCompiler");
    const initPyPath = path.resolve(repoRoot, "custom_nodes_custom/tegaki_manga_nodes/__init__.py");
    const initPyContent = await fs.readFile(initPyPath, "utf-8");
    assert.ok(
        initPyContent.includes(`"${MANGA_PROFILE_NODE}":`),
        `__init__.py NODE_CLASS_MAPPINGS must export ${MANGA_PROFILE_NODE}`
    );
    console.log("  PASS Assertion B");

    // Assertion C: queue success alone is insufficient.
    console.log("Checking Assertion C: queue success alone is insufficient...");
    const serverC = await createMockServer((req, res) => {
        if (req.url === "/queue") {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ queue_running: [], queue_pending: [] }));
        } else {
            res.writeHead(404, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: "not found" }));
        }
    });
    try {
        const runtimeC = new MangaDomainRuntime({ backendPort: serverC.port, probeTimeoutMs: 500 });
        const probeC = await runtimeC.probeBackend();
        assert.equal(probeC.classification, OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE);
        assert.ok(probeC.details.includes("Node TegakiMangaSceneCompiler not found"), probeC.details);
    } finally {
        await serverC.close();
    }
    console.log("  PASS Assertion C");

    // Assertion D: MISSING_DOCUMENT probe alone is insufficient (reproducing partial import defect).
    console.log("Checking Assertion D: MISSING_DOCUMENT probe alone is insufficient...");
    const serverD = await createMockServer((req, res) => {
        if (req.url === "/queue") {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ queue_running: [], queue_pending: [] }));
        } else if (req.url === "/tegaki/manga/generation/prepare") {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error_code: "MISSING_DOCUMENT" }));
        } else {
            // Node info returns 404 or missing
            res.writeHead(404, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: "Node not found" }));
        }
    });
    try {
        const runtimeD = new MangaDomainRuntime({ backendPort: serverD.port, probeTimeoutMs: 500 });
        const probeD = await runtimeD.probeBackend();
        assert.equal(probeD.classification, OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE);
        assert.ok(probeD.details.includes("Node TegakiMangaSceneCompiler not found"), probeD.details);
    } finally {
        await serverD.close();
    }
    console.log("  PASS Assertion D");

    // Assertion E: queue + Manga-specific capability + MISSING_DOCUMENT together permit readiness.
    console.log("Checking Assertion E: queue + capability + MISSING_DOCUMENT together permit readiness...");
    const serverE = await createMockServer((req, res) => {
        if (req.url === "/queue") {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ queue_running: [], queue_pending: [] }));
        } else if (req.url === `/object_info/${MANGA_PROFILE_NODE}`) {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ [MANGA_PROFILE_NODE]: { input: {} } }));
        } else if (req.url === "/tegaki/manga/generation/prepare") {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error_code: "MISSING_DOCUMENT" }));
        } else {
            res.writeHead(404, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: "not found" }));
        }
    });
    try {
        const runtimeE = new MangaDomainRuntime({ backendPort: serverE.port, probeTimeoutMs: 500 });
        const probeE = await runtimeE.probeBackend();
        assert.equal(probeE.classification, OwnershipClassification.PREEXISTING_COMPATIBLE);
        assert.equal(probeE.details, "Positive Manga backend identity verified");
    } finally {
        await serverE.close();
    }
    console.log("  PASS Assertion E");

    // Assertion F: missing Manga capability causes fail-closed profile rejection.
    console.log("Checking Assertion F: missing Manga capability causes fail-closed rejection...");
    const serverF = await createMockServer((req, res) => {
        if (req.url === "/queue") {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ queue_running: [], queue_pending: [] }));
        } else if (req.url === `/object_info/${MANGA_PROFILE_NODE}`) {
            // Returns 200 but without the expected key
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ SomeOtherNode: { input: {} } }));
        } else if (req.url === "/tegaki/manga/generation/prepare") {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error_code: "MISSING_DOCUMENT" }));
        }
    });
    try {
        const runtimeF = new MangaDomainRuntime({ backendPort: serverF.port, probeTimeoutMs: 500 });
        const probeF = await runtimeF.probeBackend();
        assert.equal(probeF.classification, OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE);
        assert.equal(probeF.details, `Node ${MANGA_PROFILE_NODE} not found on server`);
    } finally {
        await serverF.close();
    }
    console.log("  PASS Assertion F");

    // Assertion G: Python source ordering has function definition BEFORE page-composite route registration.
    console.log("Checking Assertion G: Python source ordering...");
    const pyApiPath = path.resolve(repoRoot, "custom_nodes_custom/tegaki_manga_nodes/basic_generation_api.py");
    const pyApiContent = await fs.readFile(pyApiPath, "utf-8");
    const funcDefIdx = pyApiContent.indexOf("def api_manga_page_composite");
    const routeRegIdx = pyApiContent.indexOf('routes.post("/tegaki/manga/page/composite")(api_manga_page_composite)');
    assert.ok(funcDefIdx !== -1, "api_manga_page_composite definition must exist");
    assert.ok(routeRegIdx !== -1, "routes.post registration must exist");
    assert.ok(
        funcDefIdx < routeRegIdx,
        `Function definition (index ${funcDefIdx}) must appear BEFORE route registration (index ${routeRegIdx})`
    );
    console.log("  PASS Assertion G");

    console.log("ALL 7 ASSERTIONS PASSED (A through G).");
}

run().catch((err) => {
    console.error("TEST FAILED:", err);
    process.exit(1);
});
