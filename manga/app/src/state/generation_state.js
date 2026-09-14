/** PLAY1c session-only generation draft and observed Manga jobs. Never enters authoring JSON. */
export const ACTIVE_JOB_STATES = new Set(["VALIDATING", "SUBMITTING", "QUEUED", "RUNNING", "UNKNOWN"]);
const STORAGE_KEY = "tegaki.manga.play1c.jobIds";
const FIELDS = ["checkpoint_id", "positive_raw", "negative_raw", "sampler_id", "scheduler_id",
    "steps", "cfg", "width", "height", "seed_requested"];

export class GenerationState {
    constructor(storage = globalThis.sessionStorage) {
        this.storage = storage;
        this.catalog = null;
        this.catalogError = "";
        this.draft = {
            checkpoint_id: "", positive_raw: "", negative_raw: "", sampler_id: "", scheduler_id: "",
            steps: "20", cfg: "7", width: "832", height: "1216", seed_requested: "0"
        };
        this.mode = "basic";
        this.sceneDraft = { mask_feather: "16", panel_strength: "1" };
        this.touched = new Set();
        this.jobs = [];
        this.jobIds = this._savedIds();
        this.activeJob = null;
        this.localBusy = false;
        this.historyLoading = true;
        this.submitUnconfirmed = false;
        this.preview = { jobId: null, url: null };
        this.error = "";
    }

    _savedIds() {
        try {
            const ids = JSON.parse(this.storage?.getItem(STORAGE_KEY) || "[]");
            return Array.isArray(ids) ? ids.filter(id => typeof id === "string" &&
                /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(id)).slice(0, 30) : [];
        } catch { return []; }
    }

    setDraft(field, value) {
        if (!FIELDS.includes(field)) throw new Error(`Unknown generation field: ${field}`);
        this.draft[field] = String(value);
        this.touched.add(field);
        if (!this.submitUnconfirmed) this.error = "";
    }

    setMode(mode) {
        if (mode !== "basic" && mode !== "scene") throw new Error(`Unknown Manga generation mode: ${mode}`);
        this.mode = mode;
        this.error = "";
    }

    setCatalog(catalog) {
        if (!catalog || catalog.ok !== true || !Array.isArray(catalog.checkpoints) ||
            !Array.isArray(catalog.samplers) || !Array.isArray(catalog.schedulers) ||
            typeof catalog.revision !== "string" || !catalog.backend_bounds || !catalog.product_bounds) {
            throw new Error("Manga capabilities are incomplete");
        }
        this.catalog = catalog;
        this.catalogError = "";
        if (!this.draft.checkpoint_id && !this.touched.has("checkpoint_id")) {
            this.draft.checkpoint_id = catalog.checkpoints.find(item => item.available)?.id || "";
        }
        if (!this.draft.sampler_id && !this.touched.has("sampler_id")) {
            this.draft.sampler_id = catalog.samplers[0] || "";
        }
        if (!this.draft.scheduler_id && !this.touched.has("scheduler_id")) {
            this.draft.scheduler_id = catalog.schedulers[0] || "";
        }
        for (const field of ["steps", "cfg", "width", "height"]) {
            if (this.touched.has(field)) continue;
            const product = catalog.product_bounds[field];
            const backend = catalog.backend_bounds[field];
            if (!product || !backend) continue;
            const low = Math.max(Number(product.min), Number(backend.min));
            const high = Math.min(Number(product.max), Number(backend.max));
            let value = Math.min(high, Math.max(low, Number(this.draft[field])));
            if (field === "width" || field === "height") value = Math.ceil(value / 8) * 8;
            if (Number.isFinite(value) && value >= low && value <= high) this.draft[field] = String(value);
        }
    }

    beginAttempt() {
        if (this.isBusy()) return false;
        this.localBusy = true;
        this.error = "";
        return true;
    }

    endAttempt() { this.localBusy = false; }
    isBusy() { return this.historyLoading || this.localBusy || this.submitUnconfirmed ||
        Boolean(this.activeJob && ACTIVE_JOB_STATES.has(this.activeJob.state)); }

    setJob(job, makeActive = true) {
        if (!job || typeof job.job_id !== "string") throw new Error("Invalid Manga job");
        this.jobs = [job, ...this.jobs.filter(existing => existing.job_id !== job.job_id)].slice(0, 30);
        if (makeActive) this.activeJob = job;
        this.jobIds = [job.job_id, ...this.jobIds.filter(id => id !== job.job_id)].slice(0, 30);
        try { this.storage?.setItem(STORAGE_KEY, JSON.stringify(this.jobIds)); } catch {}
        this.localBusy = false;
    }

    restore(job) {
        const settings = job?.requested_settings;
        if (!settings || typeof settings !== "object") throw new Error("This job has no restorable settings");
        if (settings.mode === "scene") {
            for (const field of ["checkpoint_id", "sampler_id", "scheduler_id", "steps", "cfg", "seed_requested"]) {
                if (!Object.hasOwn(settings, field)) throw new Error(`Recorded Scene job lacks ${field}`);
                this.draft[field] = String(settings[field]);
                this.touched.add(field);
            }
            for (const field of ["mask_feather", "panel_strength"]) {
                if (!Object.hasOwn(settings, field)) throw new Error(`Recorded Scene job lacks ${field}`);
                this.sceneDraft[field] = String(settings[field]);
            }
            this.mode = "scene";
        } else {
            for (const field of FIELDS) {
                if (!Object.hasOwn(settings, field)) throw new Error(`Recorded job lacks ${field}`);
                this.draft[field] = String(settings[field]);
                this.touched.add(field);
            }
            this.mode = "basic";
        }
        this.error = "";
    }

    setPreview(jobId, url) { this.preview = { jobId, url }; }
}
