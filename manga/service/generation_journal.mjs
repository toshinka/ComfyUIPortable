/** Manga execution facts only. One validated JSON record per job, replaced atomically. */
import fs from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
export const DEFAULT_JOURNAL_DIR = path.resolve(here, "..", "data", "generation");
export const JOB_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
export const STATES = new Set(["VALIDATING", "SUBMITTING", "QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "UNKNOWN"]);

export class JournalError extends Error {
    constructor(code, message) {
        super(message);
        this.code = code;
    }
}

function validate(record, expectedId) {
    if (!record || typeof record !== "object" || Array.isArray(record) ||
        !JOB_ID.test(record.job_id) || record.job_id !== expectedId ||
        !JOB_ID.test(record.request_id) || !STATES.has(record.state) ||
        typeof record.idempotency_key !== "string" || !record.idempotency_key ||
        typeof record.graph_digest !== "string" || !/^[0-9a-f]{64}$/.test(record.graph_digest) ||
        typeof record.ownership_token !== "string" || !/^[0-9a-f]{64}$/.test(record.ownership_token) ||
        typeof record.created_at !== "string" ||
        !record.requested_settings || typeof record.requested_settings !== "object" ||
        !Object.hasOwn(record, "effective_settings") ||
        !Object.hasOwn(record, "prompt_id") ||
        (record.prompt_id !== null && (typeof record.prompt_id !== "string" || !JOB_ID.test(record.prompt_id))) ||
        (["QUEUED", "RUNNING", "SUCCEEDED"].includes(record.state) && record.prompt_id === null) ||
        (["VALIDATING", "SUBMITTING"].includes(record.state) && record.prompt_id !== null) ||
        !Object.hasOwn(record, "output_locator")) {
        throw new JournalError("JOURNAL_CORRUPT", `Invalid Manga job record ${expectedId}`);
    }
    const output = record.output_locator;
    if (record.state === "SUCCEEDED" && (!output || output.type !== "output" ||
        output.subfolder !== "Manga/Playable" || typeof output.filename !== "string" ||
        !new RegExp(`^${expectedId}_[0-9]{5}_\\.png$`).test(output.filename) ||
        typeof record.finished_at !== "string" || !record.effective_settings)) {
        throw new JournalError("JOURNAL_CORRUPT", `Incomplete successful Manga job ${expectedId}`);
    }
    return record;
}

export class GenerationJournal {
    constructor(directory = DEFAULT_JOURNAL_DIR) {
        this.directory = path.resolve(directory);
    }

    _file(jobId) {
        if (!JOB_ID.test(jobId)) throw new JournalError("INVALID_JOB_ID", "Invalid Manga job ID");
        return path.join(this.directory, `${jobId}.json`);
    }

    async get(jobId) {
        const file = this._file(jobId);
        let raw;
        try {
            raw = await fs.readFile(file, "utf8");
        } catch (error) {
            if (error.code === "ENOENT") return null;
            throw error;
        }
        try {
            return validate(JSON.parse(raw), jobId);
        } catch (error) {
            if (error instanceof JournalError) throw error;
            throw new JournalError("JOURNAL_CORRUPT", `Unreadable Manga job record ${jobId}`);
        }
    }

    async list() {
        await fs.mkdir(this.directory, { recursive: true });
        const files = await fs.readdir(this.directory);
        const records = [];
        for (const name of files) {
            if (!/^[0-9a-f-]+\.json$/.test(name)) {
                throw new JournalError("JOURNAL_CORRUPT", `Unexpected file in Manga journal: ${name}`);
            }
            const jobId = name.slice(0, -5);
            const record = await this.get(jobId);
            if (!record) throw new JournalError("JOURNAL_CORRUPT", `Manga job vanished during scan: ${jobId}`);
            records.push(record);
        }
        return records;
    }

    async put(record) {
        validate(record, record?.job_id);
        await fs.mkdir(this.directory, { recursive: true });
        const target = this._file(record.job_id);
        const temporary = path.join(this.directory, `${record.job_id}.${randomUUID()}.tmp`);
        const handle = await fs.open(temporary, "wx");
        try {
            await handle.writeFile(JSON.stringify(record, null, 2) + "\n", "utf8");
            await handle.sync();
        } finally {
            await handle.close();
        }
        try {
            await fs.rename(temporary, target);
        } catch (error) {
            // A remaining temporary file blocks future operations instead of becoming success.
            throw new JournalError("JOURNAL_WRITE_FAILED", `Atomic Manga journal replace failed: ${error.message}`);
        }
        return record;
    }
}
