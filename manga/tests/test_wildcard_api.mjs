import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const close = server => new Promise(resolve => server.close(resolve));

test("Manga Workspace Server: /api/manga/wildcards endpoint", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-wildcards-test-"));
    await fs.writeFile(path.join(tmpDir, "simple.txt"), "red\nblue\n", "utf-8");
    await fs.mkdir(path.join(tmpDir, "nested"), { recursive: true });
    await fs.writeFile(path.join(tmpDir, "nested", "leaf.txt"), "cat\ndog\n", "utf-8");
    await fs.writeFile(path.join(tmpDir, "ignored.md"), "# ignored\n", "utf-8");

    const oldEnv = process.env.TEGAKI_MANGA_WILDCARDS_DIR;
    const oldPort = process.env.MANGA_WORKSPACE_PORT;
    process.env.TEGAKI_MANGA_WILDCARDS_DIR = tmpDir;
    process.env.MANGA_WORKSPACE_PORT = "0";

    const { server: workspace } = await import(`../service/manga_workspace_server.mjs?wildcards=${Date.now()}`);
    if (!workspace.listening) await new Promise(resolve => workspace.once("listening", resolve));
    const origin = `http://127.0.0.1:${workspace.address().port}`;

    try {
        // 1. GET returns valid wildcard list
        const res = await fetch(`${origin}/api/manga/wildcards`);
        assert.equal(res.status, 200);
        const data = await res.json();
        assert.equal(data.ok, true);
        assert.equal(data.root_available, true);
        assert.deepEqual(data.wildcards, ["nested/leaf", "simple"]);

        // 2. POST rejected with 405
        const postRes = await fetch(`${origin}/api/manga/wildcards`, { method: "POST" });
        assert.equal(postRes.status, 405);
        assert.equal((await postRes.json()).error_code, "METHOD_NOT_ALLOWED");

        // 3. Foreign Origin rejected with 403
        const forbiddenRes = await fetch(`${origin}/api/manga/wildcards`, {
            headers: { Origin: "http://attacker.example" }
        });
        assert.equal(forbiddenRes.status, 403);
        assert.equal((await forbiddenRes.json()).error_code, "ORIGIN_FORBIDDEN");
    } finally {
        await close(workspace);
        if (oldEnv === undefined) delete process.env.TEGAKI_MANGA_WILDCARDS_DIR;
        else process.env.TEGAKI_MANGA_WILDCARDS_DIR = oldEnv;
        if (oldPort === undefined) delete process.env.MANGA_WORKSPACE_PORT;
        else process.env.MANGA_WORKSPACE_PORT = oldPort;
        await fs.rm(tmpDir, { recursive: true, force: true }).catch(() => {});
    }
});

test("Manga Workspace Server: /api/manga/wildcards/preview is bounded, read-only and root-safe", async () => {
    const crypto = await import("node:crypto");
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-wildcard-preview-"));
    const lines = ["# comment", "", ...Array.from({ length: 30 }, (_, i) => `entry ${i}`), "  {red|blue} hair  "];
    await fs.writeFile(path.join(tmpDir, "big.txt"), "\ufeff" + lines.join("\r\n") + "\n", "utf-8");
    await fs.mkdir(path.join(tmpDir, "character"), { recursive: true });
    await fs.writeFile(path.join(tmpDir, "character", "hair.txt"), "long hair\nshort hair\n", "utf-8");
    const LONG = Array.from({ length: 120 }, (_, i) => `(artist_${i}:0.${i % 9 + 1})`).join(", ");
    await fs.writeFile(path.join(tmpDir, "long.txt"), LONG + "\n", "utf-8");
    // > 1 MB: the true total cannot be established within the read cap.
    await fs.writeFile(path.join(tmpDir, "huge.txt"), Array.from({ length: 70000 }, (_, i) => `line ${i} padding padding`).join("\n"), "utf-8");
    const outside = await fs.mkdtemp(path.join(os.tmpdir(), "manga-wildcard-outside-"));
    await fs.writeFile(path.join(outside, "secret.txt"), "secret\n", "utf-8");
    const digest = async file => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
    const before = [await digest(path.join(tmpDir, "big.txt")), await digest(path.join(tmpDir, "character", "hair.txt"))];

    const oldEnv = process.env.TEGAKI_MANGA_WILDCARDS_DIR;
    const oldPort = process.env.MANGA_WORKSPACE_PORT;
    process.env.TEGAKI_MANGA_WILDCARDS_DIR = tmpDir;
    process.env.MANGA_WORKSPACE_PORT = "0";
    const { server: workspace } = await import(`../service/manga_workspace_server.mjs?preview=${Date.now()}`);
    if (!workspace.listening) await new Promise(resolve => workspace.once("listening", resolve));
    const origin = `http://127.0.0.1:${workspace.address().port}`;
    const get = async name => {
        const res = await fetch(`${origin}/api/manga/wildcards/preview?name=${encodeURIComponent(name)}`);
        return { status: res.status, body: await res.json() };
    };
    try {
        const big = await get("big");
        assert.equal(big.status, 200);
        assert.equal(big.body.token, "__big__");
        assert.equal(big.body.entries.length, 31, "B: every usable line is returned (no 12-entry sample)");
        assert.deepEqual(big.body.entries.slice(0, 2), ["entry 0", "entry 1"], "comments/blank lines skipped, BOM stripped");
        assert.equal(big.body.entries[30], "{red|blue} hair", "choice syntax shown as source, not expanded");
        assert.equal(big.body.total, 31, "total usable entries");
        assert.ok(!JSON.stringify(big.body).includes(tmpDir), "no physical path exposed");

        const long = await get("long");
        assert.deepEqual([long.status, long.body.entries, long.body.total], [200, [LONG], 1], "A: long single entry returned whole");
        assert.ok(long.body.entries[0].length > 1500);

        const huge = await get("huge");
        assert.equal(huge.status, 200);
        assert.equal(huge.body.truncated, true);
        assert.equal(huge.body.total, null, "past the 1 MB cap the total is reported unknown, not invented");
        assert.ok(huge.body.entries.length > 30000 && huge.body.entries.length < 70000);
        assert.equal(huge.body.entries.at(-1).endsWith("padding padding"), true, "no cut-off partial line");

        const nested = await get("character/hair");
        assert.deepEqual([nested.status, nested.body.token, nested.body.entries, nested.body.total],
            [200, "__character/hair__", ["long hair", "short hair"], 2]);
        assert.equal((await get("character\\hair")).status, 200, "backslash normalises to the canonical name");

        for (const bad of ["../" + path.basename(outside) + "/secret", "/etc/passwd", "a/../big", "C:/x", "", "x*"]) {
            const r = await get(bad);
            assert.ok(r.status === 400 && r.body.ok === false, `${bad} -> ${r.status}`);
        }
        assert.equal((await get("missing")).status, 404);
        const forbidden = await fetch(`${origin}/api/manga/wildcards/preview?name=big`, { headers: { Origin: "http://attacker.example" } });
        assert.equal(forbidden.status, 403);
        assert.deepEqual([await digest(path.join(tmpDir, "big.txt")), await digest(path.join(tmpDir, "character", "hair.txt"))], before,
            "wildcard files are never modified");
    } finally {
        await close(workspace);
        if (oldEnv === undefined) delete process.env.TEGAKI_MANGA_WILDCARDS_DIR;
        else process.env.TEGAKI_MANGA_WILDCARDS_DIR = oldEnv;
        if (oldPort === undefined) delete process.env.MANGA_WORKSPACE_PORT;
        else process.env.MANGA_WORKSPACE_PORT = oldPort;
        await fs.rm(tmpDir, { recursive: true, force: true }).catch(() => {});
        await fs.rm(outside, { recursive: true, force: true }).catch(() => {});
    }
});
