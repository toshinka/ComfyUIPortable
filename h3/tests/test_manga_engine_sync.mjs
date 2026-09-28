// Card TEGAKI-MULTI-ENGINE-LAUNCHER-AND-AVAILABILITY-SYNC-1: shell <-> Manga frame availability sync.
// Pure reducer + source contract for the cross-origin frame channel.  No browser, no services.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
    UNAVAILABLE_TITLE, easyreforgeAvailability, easyreforgeControl, reduceMangaFrameMessage,
} from "../app/static/manga-engine-sync.js";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const INITIAL = Object.freeze({ available: false, state: "unknown", reason: "" });
const report = (easyreforge, engine = "comfyui") => ({ type: "tegaki:manga-engine-availability", engine, easyreforge });

/** Replays frame messages through the reducer exactly like app.js does. */
function shellHarness(start = {}) {
    const shell = { creationMode: "movie", engine: "h3", pendingMangaEngine: null, easyreforge: INITIAL, ...start };
    const posted = [];
    const receive = data => {
        const next = reduceMangaFrameMessage(shell, data);
        if (!next.handled) return next;
        shell.easyreforge = next.easyreforge;
        shell.pendingMangaEngine = next.pendingMangaEngine;
        if (next.post) { posted.push(next.post); shell.pendingMangaEngine = next.post; }
        else if (next.mirror && shell.creationMode === "manga") shell.engine = next.mirror;
        return next;
    };
    return { shell, posted, receive, control: () => easyreforgeControl(shell.easyreforge) };
}

test("ready + available + owned=false (verified external Integration runtime) => EASYREFORGE enabled", () => {
    const h = shellHarness();
    h.receive(report({ available: true, state: "ready", reason: "", owned: false }));
    assert.deepEqual(h.control(), { disabled: false, title: "Legacy EasyReforge (MANGA only)" });
    assert.equal(easyreforgeAvailability({ available: true, state: "ready", owned: false }).available, true,
        "ownership never participates in availability");
});

test("available=false => disabled (stopped, not ready, installed-only, malformed)", () => {
    for (const block of [
        { available: false, state: "stopped", reason: "" },
        { available: false, state: "starting", reason: "" },
        { available: false, state: "ready", reason: "installed but API not verified" },
        { available: "true", state: "ready" },          // not strictly true
        { installed: true, state: "stopped" },          // installed alone is insufficient
    ]) {
        const h = shellHarness();
        h.receive(report(block));
        assert.equal(h.control().disabled, true, JSON.stringify(block));
    }
    assert.equal(easyreforgeControl(INITIAL).title, UNAVAILABLE_TITLE);
    assert.equal(easyreforgeControl({ available: false, reason: "Integration Runtime is incomplete" }).title,
        "Integration Runtime is incomplete");
    const h = shellHarness();
    assert.equal(h.receive({ type: "tegaki:manga-engine-availability", engine: "comfyui" }).handled, false,
        "a message without an easyreforge block is ignored");
    assert.deepEqual(h.shell.easyreforge, INITIAL);
});

test("initial unavailable then available => shell converges to enabled (and back), no sticky state", () => {
    const h = shellHarness();
    h.receive(report({ available: false, state: "stopped" }));
    assert.equal(h.control().disabled, true);
    h.receive(report({ available: false, state: "starting" }));
    assert.equal(h.control().disabled, true);
    h.receive(report({ available: true, state: "ready" }));
    assert.equal(h.control().disabled, false, "a later available report enables the control");
    h.receive(report({ available: false, state: "stopped" }));
    assert.equal(h.control().disabled, true, "truthful in both directions");
});

test("availability loss never switches EASYREFORGE -> COMFYUI; reload re-applies the user's selection", () => {
    const h = shellHarness({ creationMode: "manga", engine: "easyreforge",
        easyreforge: { available: true, state: "ready", reason: "" } });
    let next = h.receive(report({ available: false, state: "failed" }, "easyreforge"));
    assert.equal(h.shell.engine, "easyreforge");
    assert.equal(next.post, null);
    assert.equal(h.control().disabled, true);
    // Frame reloaded (engine reset to its default) while EasyReforge is available: re-apply, never downgrade.
    next = h.receive(report({ available: true, state: "ready" }, "comfyui"));
    assert.equal(next.post, "easyreforge");
    assert.equal(h.shell.engine, "easyreforge");
    // Frame reloaded while EasyReforge is unavailable: the header truthfully mirrors the frame.
    const u = shellHarness({ creationMode: "manga", engine: "easyreforge" });
    next = u.receive(report({ available: false, state: "stopped" }, "comfyui"));
    assert.equal(next.post, null);
    assert.equal(next.mirror, "comfyui", "mirror only reflects the frame; it is not a generation fallback");
});

test("pending request is re-sent until applied; applied mirrors the frame engine", () => {
    const h = shellHarness({ creationMode: "manga", engine: "easyreforge", pendingMangaEngine: "easyreforge" });
    let next = h.receive(report({ available: true, state: "ready" }, "comfyui"));
    assert.equal(next.post, "easyreforge");
    next = h.receive({ type: "tegaki:manga-engine-applied", engine: "easyreforge", ok: true });
    assert.equal(next.pendingMangaEngine, null);
    assert.equal(next.mirror, "easyreforge");
    next = h.receive({ type: "tegaki:manga-engine-applied", engine: "h3", ok: true });
    assert.equal(next.mirror, null, "unknown engines are never mirrored");
    for (const data of [null, {}, { type: "other" }, { type: "tegaki:manga-engine" , engine: "comfyui" }]) {
        assert.equal(reduceMangaFrameMessage(h.shell, data).handled, false);
    }
});

test("cross-origin frame channel: shell sends its origin; frame accepts only a loopback parent; shell queries on focus", async () => {
    const [shellHtml, app, mangaHtml] = await Promise.all([
        fs.readFile(path.join(ROOT, "h3", "app", "static", "index.html"), "utf8"),
        fs.readFile(path.join(ROOT, "h3", "app", "static", "app.js"), "utf8"),
        fs.readFile(path.join(ROOT, "manga", "app", "index.html"), "utf8"),
    ]);
    // Root cause of the permanently disabled button: referrerpolicy="same-origin" on a cross-port iframe
    // sends no referrer, so the frame had no shell origin and never published availability.
    assert.match(shellHtml, /<iframe id="manga-workspace-frame"[^>]*referrerpolicy="origin"/);
    assert.doesNotMatch(shellHtml, /referrerpolicy="(same-origin|no-referrer)"/);
    assert.match(mangaHtml, /const fromReferrer = document\.referrer \? loopback\(document\.referrer\) : null;/);
    assert.match(mangaHtml, /window\.location\.ancestorOrigins/);
    assert.match(mangaHtml, /url\.protocol === "http:" && \["127\.0\.0\.1", "localhost"\]\.includes\(url\.hostname\)/);
    assert.match(mangaHtml, /data\?\.type === "tegaki:manga-engine-query"/, "frame re-publishes on request");
    assert.match(app, /import \{ easyreforgeControl, reduceMangaFrameMessage \} from "\.\/manga-engine-sync\.js";/);
    assert.match(app, /postMessage\(\{ type: "tegaki:manga-engine-query" \}, origin\)/);
    assert.match(app, /window\.addEventListener\("focus", queryMangaEngineAvailability\)/);
    assert.match(app, /document\.visibilityState === "visible"\) queryMangaEngineAvailability\(\)/);
    assert.doesNotMatch(app, /setTimeout\([^)]*queryMangaEngineAvailability/, "no timer-based convergence");
});
