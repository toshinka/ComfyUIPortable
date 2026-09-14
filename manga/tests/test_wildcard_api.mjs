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
