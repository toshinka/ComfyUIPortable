// LoRA panel for the MANGA / Illustrious Positive Prompt (Card MANGA-ILLUSTRIOUS-LORA-PRODUCTION1).
//
// The Positive Prompt text is the single source of truth: selecting a card writes a
// visible `<lora:CANONICAL_ID:STRENGTH>` directive, and card state is read back
// from the prompt.  The token helpers below only LOCATE directives for editing;
// the backend compiler (basic_generation._compile_prompt) is the one parser that
// resolves them against the trusted catalog.  The pattern mirrors LORA_RE there.

import { LOAD_FAILED, loadLoraCatalog, queryLoraCatalog } from "./tag_autocomplete.js";

const LORA_TOKEN_SOURCE = "<lora:([^:<>]+):([+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+))>";

export const LORA_STRENGTH_BOUNDS = Object.freeze({ min: -4, max: 4, step: 0.05, default: 1 });

export function formatLoraStrength(value) {
    const n = Number(value);
    if (!Number.isFinite(n) || n < LORA_STRENGTH_BOUNDS.min || n > LORA_STRENGTH_BOUNDS.max) {
        throw new RangeError("LoRA strength must be a finite number within -4..4");
    }
    let text = (n === 0 ? 0 : n).toFixed(4).replace(/0+$/, "");
    if (text.endsWith(".")) text += "0";
    return text;
}

function assertLoraId(id) {
    if (typeof id !== "string" || !id || id.trim() !== id || /[:<>]/.test(id) || /[\x00-\x1f\x7f]/.test(id)) {
        throw new TypeError(`Invalid canonical LoRA ID: ${JSON.stringify(id)}`);
    }
}

export function formatLoraToken(id, strength = LORA_STRENGTH_BOUNDS.default) {
    assertLoraId(id);
    return `<lora:${id}:${formatLoraStrength(strength)}>`;
}

export function findLoraTokens(text) {
    const source = typeof text === "string" ? text : "";
    const re = new RegExp(LORA_TOKEN_SOURCE, "g");
    const tokens = [];
    let match;
    while ((match = re.exec(source)) !== null) {
        tokens.push({
            id: match[1],
            strength: Number(match[2]),
            strengthText: match[2],
            start: match.index,
            end: match.index + match[0].length,
            token: match[0],
        });
    }
    return tokens;
}

// A LoRA can appear under several names that resolve to it: its portable alias
// ("foo"), canonical ID without extension, or full canonical ID.  Editing helpers
// accept one name or a list of such names; resolution itself stays backend-side.
const nameSet = ids => new Set(Array.isArray(ids) ? ids.filter(Boolean) : [ids]);

export function loraNamesFor(lora) {
    const id = String(lora?.id || "");
    return [...new Set([lora?.token, id, id.replace(/\.[^./]+$/, "")].filter(Boolean))];
}

export function addLoraToken(text, id, strength = LORA_STRENGTH_BOUNDS.default, aliases = [id]) {
    const source = typeof text === "string" ? text : "";
    const token = formatLoraToken(id, strength);
    const names = nameSet([id, ...aliases]);
    if (findLoraTokens(source).some(item => names.has(item.id))) return source;
    let separator = ", ";
    if (source === "" || /\s$/.test(source)) separator = "";
    else if (/,$/.test(source)) separator = " ";
    return source + separator + token;
}

export function updateLoraTokenStrength(text, ids, strength) {
    const source = typeof text === "string" ? text : "";
    const names = nameSet(ids);
    formatLoraStrength(strength);
    let result = source;
    for (const item of findLoraTokens(source).filter(entry => names.has(entry.id)).reverse()) {
        // Keep the name the Owner (or asset) wrote; only the strength changes.
        result = result.slice(0, item.start) + formatLoraToken(item.id, strength) + result.slice(item.end);
    }
    return result;
}

export function removeLoraToken(text, ids) {
    const source = typeof text === "string" ? text : "";
    const names = nameSet(ids);
    let result = source;
    for (const item of findLoraTokens(source).filter(entry => names.has(entry.id)).reverse()) {
        let start = item.start;
        let end = item.end;
        if (result.slice(start - 2, start) === ", ") start -= 2;
        else if (start === 0 && result.slice(end, end + 2) === ", ") end += 2;
        result = result.slice(0, start) + result.slice(end);
    }
    return result;
}

/**
 * Bulk strength (Card MANGA-LORA-UX-PRODUCTION1): set ONE strength on every valid
 * LoRA directive already in the given prompt text.  Names (portable alias or
 * canonical ID), order and all other text are kept byte-for-byte; directives the
 * token contract rejects (bad name spacing, out-of-range strength) and malformed
 * `<lora...>` text are left untouched for diagnostics to report.
 */
export function applyBulkLoraStrength(text, strength) {
    const source = typeof text === "string" ? text : "";
    formatLoraStrength(strength);
    let result = source;
    let count = 0;
    for (const item of findLoraTokens(source).reverse()) {
        if (item.strength < LORA_STRENGTH_BOUNDS.min || item.strength > LORA_STRENGTH_BOUNDS.max) continue;
        let token;
        try { token = formatLoraToken(item.id, strength); } catch { continue; }
        result = result.slice(0, item.start) + token + result.slice(item.end);
        count += 1;
    }
    return { value: result, count };
}

export function countBulkEditableLoras(text) {
    return findLoraTokens(text).filter(item => {
        if (item.strength < LORA_STRENGTH_BOUNDS.min || item.strength > LORA_STRENGTH_BOUNDS.max) return false;
        try { formatLoraToken(item.id, 1); return true; } catch { return false; }
    }).length;
}

export async function fetchLoraFolder(dir, { engine = "illustrious", fetchImpl = globalThis.fetch } = {}) {
    const url = `/api/manga/resources/lora?engine=${encodeURIComponent(engine)}&dir=${encodeURIComponent(dir || "")}`;
    const res = await fetchImpl(url, { headers: { Accept: "application/json" } });
    let data = null;
    try { data = await res.json(); } catch { /* handled below */ }
    if (!res.ok || !data || data.ok !== true) {
        const error = new Error((data && data.error) || `LoRA folder request failed (${res.status})`);
        error.code = (data && data.error_code) || "LORA_BROWSE_FAILED";
        throw error;
    }
    return data;
}

/** Bounded preview route: addressed by canonical LoRA ID, never by a filesystem path. */
export function loraPreviewUrl(id, { engine = "illustrious" } = {}) {
    return `/api/manga/resources/lora/preview?engine=${encodeURIComponent(engine)}&id=${encodeURIComponent(id)}`;
}

function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}

export const LORA_SEARCH_LIMIT = 60;

/**
 * LoRA search (Card MANGA-PROMPT-VALIDATION-COHERENCE1) over the already-loaded TRUSTED
 * index (/api/manga/resources/lora/index — the resolver generation uses).  No disk scan,
 * no safetensors reads, no other ComfyUI roots.  Case-insensitive for display only.
 * Preview availability comes from folder listings already loaded (existing data).
 */
export function searchLoraIndex(index, query, { limit = LORA_SEARCH_LIMIT, folderCache = new Map() } = {}) {
    const q = String(query ?? "").trim();
    if (!q || !Array.isArray(index)) return { items: [], total: 0 };
    const all = queryLoraCatalog(index, q, { limit: Number.MAX_SAFE_INTEGER });
    const items = all.slice(0, limit).map(match => {
        const folder = match.id.includes("/") ? match.id.slice(0, match.id.lastIndexOf("/")) : "";
        const listed = folderCache.get(folder)?.loras?.find(entry => entry.id === match.id);
        return { id: match.id, name: match.label, token: match.tag, folder, available: true,
            preview: listed?.preview === true, fromSearch: true };
    });
    return { items, total: all.length };
}

export function mountLoraPanel({ panel, toggle, body, status, breadcrumb, folders, cards, count, prompt,
    bulkInput = null, bulkApply = null, bulkStatus = null, fetchFolder = fetchLoraFolder,
    search = null, loadIndex = () => loadLoraCatalog() }) {
    const cache = new Map();
    const draftStrength = new Map();
    let currentFolder = "";
    let listing = null;
    let enabled = true;
    let disabledReason = "";
    let loadSeq = 0;
    let searchQuery = "";
    let searchResult = null; // { items, total } while a search is active
    let searchSeq = 0;
    let searchTimer = null;

    const applyPrompt = (nextText) => {
        if (nextText === prompt.value) return;
        prompt.value = nextText;
        prompt.dispatchEvent(new Event("input", { bubbles: true }));
        renderCards();
    };

    const setStatus = (text, isError = false) => {
        status.textContent = text || "";
        status.classList.toggle("mg-lora-status-error", Boolean(isError));
    };

    const renderCount = () => {
        const n = findLoraTokens(prompt.value).length;
        count.textContent = n ? `(${n})` : "";
        if (bulkApply) {
            const editable = countBulkEditableLoras(prompt.value);
            bulkApply.disabled = !enabled || editable === 0;
            bulkApply.title = editable ? `Set this strength on the ${editable} LoRA(s) in the active prompt`
                : "No LoRAs added to the active prompt";
        }
    };

    if (bulkApply && bulkInput) {
        bulkApply.addEventListener("click", () => {
            const value = Number(bulkInput.value);
            if (bulkInput.value.trim() === "" || !Number.isFinite(value) ||
                value < LORA_STRENGTH_BOUNDS.min || value > LORA_STRENGTH_BOUNDS.max) {
                if (bulkStatus) bulkStatus.textContent = "Strength must be between -4 and 4.";
                return;
            }
            const { value: next, count: changed } = applyBulkLoraStrength(prompt.value, value);
            const text = formatLoraStrength(value);
            bulkInput.value = text;
            if (bulkStatus) bulkStatus.textContent = changed ? `Applied ${text} to ${changed} LoRA${changed > 1 ? "s" : ""}` : "No LoRAs to update";
            if (changed) applyPrompt(next);
        });
        bulkInput.addEventListener("input", () => { if (bulkStatus) bulkStatus.textContent = ""; });
    }

    const renderBreadcrumb = () => {
        breadcrumb.replaceChildren();
        const parts = currentFolder ? currentFolder.split("/") : [];
        const crumbs = [{ id: "", name: "LoRA" }];
        parts.forEach((name, i) => crumbs.push({ id: parts.slice(0, i + 1).join("/"), name }));
        crumbs.forEach((crumb, i) => {
            if (i) breadcrumb.appendChild(el("span", "mg-lora-crumb-sep", "/"));
            const button = el("button", "mg-lora-crumb", crumb.name);
            button.type = "button";
            button.dataset.folder = crumb.id;
            if (i === crumbs.length - 1) button.setAttribute("aria-current", "location");
            button.onclick = () => openFolder(crumb.id);
            breadcrumb.appendChild(button);
        });
    };

    const renderFolders = () => {
        folders.replaceChildren();
        for (const folder of (listing && listing.folders) || []) {
            const button = el("button", "mg-lora-folder", `📁 ${folder.name}`);
            button.type = "button";
            button.setAttribute("role", "listitem");
            button.dataset.folder = folder.id;
            button.title = folder.id;
            button.onclick = () => openFolder(folder.id);
            folders.appendChild(button);
        }
        folders.hidden = !folders.childElementCount;
    };

    function renderCards() {
        renderCount();
        cards.replaceChildren();
        const tokens = findLoraTokens(prompt.value);
        const searching = Boolean(searchQuery);
        const items = searching ? (searchResult?.items || []) : ((listing && listing.loras) || []);
        for (const lora of items) {
            const names = loraNamesFor(lora);
            const token = tokens.find(item => names.includes(item.id));
            const card = el("div", "mg-lora-card");
            card.setAttribute("role", "listitem");
            card.dataset.loraId = lora.id;
            card.classList.toggle("is-selected", Boolean(token));
            card.classList.toggle("is-unavailable", lora.available === false);
            card.title = lora.token && lora.token !== lora.id ? `${lora.id} (inserts ${lora.token})` : lora.id;
            card.dataset.loraToken = lora.token || lora.id;
            // Fixed-size image slot: preview when a sidecar exists, otherwise a subdued placeholder.
            const placeholder = () => el("div", "mg-lora-card-thumb mg-lora-card-noimg", "NO PREVIEW");
            let thumb;
            if (lora.preview === true) {
                // Sidecar <stem>.preview.png; loaded lazily and only for the opened folder.
                card.classList.add("has-preview");
                thumb = el("img", "mg-lora-card-thumb");
                thumb.alt = "";
                thumb.loading = "lazy";
                thumb.decoding = "async";
                thumb.src = loraPreviewUrl(lora.id);
                thumb.onerror = () => {
                    card.classList.remove("has-preview");
                    thumb.replaceWith(placeholder());
                };
            } else {
                thumb = placeholder();
            }
            const name = el("span", "mg-lora-card-name", lora.name);
            name.title = lora.id;
            // Duplicate basenames insert a canonical token; show the folder so they are distinguishable.
            const context = (lora.fromSearch || (lora.token && lora.token !== lora.name)) && lora.folder
                ? el("span", "mg-lora-card-folder", lora.folder) : null;
            const strength = el("input", "mg-lora-strength");
            strength.type = "number";
            strength.min = String(LORA_STRENGTH_BOUNDS.min);
            strength.max = String(LORA_STRENGTH_BOUNDS.max);
            strength.step = String(LORA_STRENGTH_BOUNDS.step);
            strength.value = token ? token.strengthText : (draftStrength.get(lora.id) ?? "1.0");
            strength.setAttribute("aria-label", `Strength for ${lora.name}`);
            strength.disabled = !enabled;
            strength.onchange = () => {
                const value = Number(strength.value);
                if (!Number.isFinite(value) || value < LORA_STRENGTH_BOUNDS.min || value > LORA_STRENGTH_BOUNDS.max) {
                    setStatus("Strength must be between -4 and 4.", true);
                    renderCards();
                    return;
                }
                draftStrength.set(lora.id, formatLoraStrength(value));
                if (token) applyPrompt(updateLoraTokenStrength(prompt.value, names, value));
                else renderCards();
            };
            const action = el("button", "mg-lora-card-action", token ? "Remove" : "Add");
            action.type = "button";
            action.setAttribute("aria-pressed", token ? "true" : "false");
            action.disabled = !enabled || (!token && lora.available === false);
            action.onclick = () => {
                if (token) {
                    applyPrompt(removeLoraToken(prompt.value, names));
                } else {
                    // Portable alias when unique in the trusted root, else the canonical form (backend-chosen).
                    const value = Number(strength.value);
                    applyPrompt(addLoraToken(prompt.value, lora.token || lora.id, Number.isFinite(value) ? value : 1, names));
                }
            };
            const controls = el("div", "mg-lora-card-controls");
            controls.append(strength, action);
            card.append(thumb, name);
            if (context) card.append(context);
            card.append(controls);
            cards.appendChild(card);
        }
        if (searching && searchResult && !items.length) cards.appendChild(el("div", "mg-hint mg-lora-empty", "No trusted LoRA matches this search."));
        else if (!searching && !items.length && listing) cards.appendChild(el("div", "mg-hint mg-lora-empty", "No LoRA files in this folder."));
    }

    // --- search: results span folders; clearing returns to the current folder view ---
    const setSearchMode = (on) => {
        panel.classList.toggle("is-searching", on);
        breadcrumb.hidden = on;
        if (on) folders.hidden = true;
        else renderFolders();
    };

    async function runSearch(query) {
        searchQuery = String(query ?? "").trim();
        const seq = ++searchSeq;
        if (!searchQuery) {
            searchResult = null;
            setSearchMode(false);
            setStatus(enabled ? "" : disabledReason);
            renderCards();
            return;
        }
        setSearchMode(true);
        setStatus("Searching trusted LoRAs…");
        const index = await loadIndex();
        if (seq !== searchSeq) return; // a newer query (or a clear) won
        if (!Array.isArray(index) || index[LOAD_FAILED]) {
            searchResult = { items: [], total: 0 };
            setStatus("LoRA index is unavailable; search needs the trusted index.", true);
            renderCards();
            return;
        }
        searchResult = searchLoraIndex(index, searchQuery, { folderCache: cache });
        const shown = searchResult.items.length;
        setStatus(enabled ? (searchResult.total > shown
            ? `Search: ${shown} of ${searchResult.total} matches — refine to narrow`
            : `Search: ${searchResult.total} match${searchResult.total === 1 ? "" : "es"} across folders`) : disabledReason);
        renderCards();
    }

    if (search) {
        search.addEventListener("input", () => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => runSearch(search.value), 120);
        });
        search.addEventListener("keydown", event => {
            if (event.key === "Escape" && search.value) {
                event.preventDefault();
                search.value = "";
                clearTimeout(searchTimer);
                runSearch("");
            }
        });
    }

    async function openFolder(folderId, { refresh = false } = {}) {
        const seq = ++loadSeq;
        currentFolder = folderId || "";
        renderBreadcrumb();
        if (!refresh && cache.has(currentFolder)) {
            listing = cache.get(currentFolder);
        } else {
            setStatus("Loading…");
            try {
                const data = await fetchFolder(currentFolder);
                if (seq !== loadSeq) return;
                cache.set(currentFolder, data);
                listing = data;
            } catch (err) {
                if (seq !== loadSeq) return;
                listing = { folders: [], loras: [] };
                setStatus(err.message || "LoRA folder is unavailable.", true);
                renderFolders();
                renderCards();
                return;
            }
        }
        if (searchQuery) return; // folder data arrived while searching; keep the search view
        setStatus(enabled ? "" : disabledReason);
        renderFolders();
        renderCards();
    }

    const setExpanded = (expanded) => {
        if (toggle) toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
        body.hidden = !expanded;
        panel.classList.toggle("is-expanded", expanded);
        if (expanded && listing === null) openFolder(currentFolder);
    };

    // When a Prompt Assist host owns the toggle, it drives setExpanded instead.
    if (toggle) toggle.addEventListener("click", () => setExpanded(toggle.getAttribute("aria-expanded") !== "true"));
    prompt.addEventListener("input", () => renderCards());
    setExpanded(false);
    renderCount();

    return {
        openFolder,
        setExpanded,
        search: runSearch,
        refresh: () => openFolder(currentFolder, { refresh: true }),
        // Called whenever the composer swaps the prompt target/value.
        sync({ enabled: nextEnabled = true, reason = "" } = {}) {
            enabled = Boolean(nextEnabled);
            disabledReason = enabled ? "" : reason;
            panel.classList.toggle("is-disabled", !enabled);
            if (listing !== null || !enabled) setStatus(disabledReason);
            renderCards();
        },
    };
}


// ---------------------------------------------------------------------------
// LoRA diagnostics (Card MANGA-LORA-PORTABLE-COMPAT-DIAGNOSTICS1).
// The browser only gathers prompt text; the backend resolver (the one used for
// generation) decides resolved / missing / ambiguous / out-of-root.
// ---------------------------------------------------------------------------

const STATUS_LABEL = {
    RESOLVED: "OK", LORA_UNAVAILABLE: "NOT FOUND", LORA_AMBIGUOUS: "AMBIGUOUS",
    INVALID_LORA_SYNTAX: "INVALID SYNTAX", INVALID_STRENGTH: "INVALID STRENGTH",
    OUTSIDE_RESOURCE_ROOT: "OUTSIDE LORA ROOT", LORA_DUPLICATE: "DUPLICATE",
    SCENE_LORA_UNSUPPORTED: "NOT ALLOWED HERE",
};
const SOURCE_LABEL = { page_positive: "Global", scene_positive: "Scene", page_negative: "Global negative", scene_negative: "Scene negative" };
STATUS_LABEL.DYNAMIC_LORA = "RESOLVED AT GENERATION";

/** Only definite problems block; {a|b}-conditional or dynamic directives are reported, not blocking. */
export function isBlockingProblem(entry) {
    return entry?.status !== "RESOLVED" && entry?.blocking !== false;
}

/** Wildcard references (`__name__`) in LoRA-bearing sources: their LoRAs exist only after expansion. */
export function sourcesHaveWildcards(sources) {
    // "__" inside a <lora:...> name is literal, never a Wildcard reference.
    return Array.isArray(sources) && sources.some(source => source?.lora_allowed !== false &&
        /__[^_\s,][^\s,]*?__/.test(String(source?.text || "").replace(/<lora:[^<>]*>/gi, " ")));
}

export function sourcesHaveLora(sources) {
    return Array.isArray(sources) && sources.some(source => /<lora/i.test(String(source?.text || "")));
}

/**
 * ONE authoritative LoRA validation snapshot per exact prompt-source content
 * (Card MANGA-PROMPT-VALIDATION-COHERENCE1).  The key IS the prompt state (source
 * labels + texts), so a late reply for an older prompt can only fill its own entry —
 * it can never answer, overwrite or block a newer prompt.  Every settle calls
 * `onSettled` so BOTH consumers (LoRA status and the Generate gate) re-read the
 * snapshot for the CURRENT prompt; transport failures expire so they are retried.
 */
export function createLoraValidator({ engine = "illustrious", fetchImpl = (...args) => globalThis.fetch(...args),
    onSettled = () => {}, failureTtlMs = 5000, now = () => Date.now() } = {}) {
    const cache = new Map();
    const inflight = new Map();
    const keyOf = sources => JSON.stringify(sources);
    const fresh = key => {
        const hit = cache.get(key);
        if (!hit) return null;
        if (hit.result?.ok !== true && now() - hit.at > failureTtlMs) {
            cache.delete(key);
            return null;
        }
        return hit.result;
    };
    return {
        keyOf,
        peek(sources) {
            return fresh(keyOf(sources));
        },
        pending(sources) {
            return inflight.has(keyOf(sources));
        },
        request(sources) {
            const key = keyOf(sources);
            const hit = fresh(key);
            if (hit) return Promise.resolve(hit);
            if (inflight.has(key)) return inflight.get(key);
            const promise = Promise.resolve().then(() => fetchImpl(
                `/api/manga/resources/lora/validate?engine=${encodeURIComponent(engine)}`,
                { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sources }) },
            )).then(async res => {
                const data = await res.json().catch(() => null);
                return data && typeof data === "object" ? data : { ok: false, error: `LoRA validation failed (${res.status})` };
            }).catch(err => ({ ok: false, error: err?.message || "LoRA validation unavailable" })).then(result => {
                cache.set(key, { result, at: now() });
                if (cache.size > 24) cache.delete(cache.keys().next().value);
                inflight.delete(key);
                try { onSettled(result, sources); } catch { /* a consumer error must not poison the snapshot */ }
                return result;
            });
            inflight.set(key, promise);
            return promise;
        },
    };
}

/** Generate-gate reason from a backend validation result ("" when nothing blocks). */
export function loraBlockReasonFromDiagnostics(result) {
    if (!result || result.ok !== true || !Array.isArray(result.entries)) return "";
    const problems = result.entries.filter(isBlockingProblem);
    if (!problems.length) return "";
    const first = problems[0];
    const more = problems.length > 1 ? ` (+${problems.length - 1} more)` : "";
    return `Generate disabled — unresolved LoRA: ${first.name || first.raw} ${STATUS_LABEL[first.status] || first.status}${more}. See LoRA status under the prompt.`;
}

export function loraStatusSummary(result, { wildcardsOnly = false } = {}) {
    if (wildcardsOnly) return "LoRA status · Wildcards may add LoRAs (resolved at generation)";
    if (!result) return "LoRA status · checking…";
    if (result.ok !== true) return "LoRA status · unavailable";
    const blocking = (result.entries || []).filter(isBlockingProblem).length;
    const notes = (result.entries || []).filter(entry => entry.status !== "RESOLVED" && entry.blocking === false).length;
    return `LoRA status${blocking ? ` · ${blocking} problem${blocking > 1 ? "s" : ""}` : " · all resolved"}${notes ? ` · ${notes} conditional` : ""}`;
}

export function mountLoraDiagnostics({ container, validator, getSources, onResult = () => {}, expanded = true }) {
    let timer = null;
    let currentKey = "";
    let isExpanded = Boolean(expanded);

    // Collapsible (the header always states the result); collapsing never stops validation.
    const frame = (summary, bodyNodes, { problem = false } = {}) => {
        container.replaceChildren();
        const head = el("button", `mg-lora-diag-head mg-lora-diag-toggle${problem ? " has-problem" : ""}`, summary);
        head.type = "button";
        head.setAttribute("aria-expanded", isExpanded ? "true" : "false");
        head.onclick = () => {
            isExpanded = !isExpanded;
            head.setAttribute("aria-expanded", isExpanded ? "true" : "false");
            body.hidden = !isExpanded;
            container.classList.toggle("is-collapsed", !isExpanded);
        };
        const body = el("div", "mg-lora-diag-body");
        body.append(...bodyNodes);
        body.hidden = !isExpanded;
        container.classList.toggle("is-collapsed", !isExpanded);
        container.append(head, body);
    };

    const render = (result, { wildcardsOnly = false, hasWildcards = false } = {}) => {
        const summary = loraStatusSummary(result, { wildcardsOnly });
        if (wildcardsOnly) {
            frame(summary, [el("div", "mg-hint", "The prompt has Wildcards but no explicit LoRA. LoRAs a Wildcard emits are resolved when generation expands it; use Expand in the Wildcard preview to inspect them here.")]);
            return;
        }
        if (!result) {
            frame(summary, [el("div", "mg-hint", "LoRA status: checking…")]);
            return;
        }
        if (result.ok !== true) {
            frame(summary, [el("div", "mg-hint mg-lora-status-error", `LoRA status unavailable: ${result.error || "validation failed"}`)], { problem: true });
            return;
        }
        const list = el("ul", "mg-lora-diag-list");
        for (const entry of result.entries) {
            const ok = entry.status === "RESOLVED";
            const row = el("li", `mg-lora-diag-row ${ok ? "is-ok" : isBlockingProblem(entry) ? "is-problem" : "is-note"}`);
            if (entry.conditional) row.dataset.conditional = "true";
            row.dataset.status = entry.status;
            row.dataset.loraName = entry.name || entry.raw;
            const main = el("span", "mg-lora-diag-main",
                `${ok ? "✓" : isBlockingProblem(entry) ? "✕" : "…"} ${entry.name || entry.raw}${entry.strength_text ? ` ${entry.strength_text}` : ""}${ok ? "" : ` — ${STATUS_LABEL[entry.status] || entry.status}`}${entry.conditional ? " (only if this {…|…} choice is picked)" : ""}`);
            row.appendChild(main);
            let detail = "";
            if (ok) detail = `→ ${entry.resolved_id}`;
            else if (entry.candidates?.length) detail = `${entry.status === "LORA_AMBIGUOUS" ? "matches" : "found outside the LoRA root as"}: ${entry.candidates.join(", ")}`;
            else if (entry.message) detail = entry.message;
            if (detail) row.appendChild(el("span", "mg-lora-diag-detail", detail));
            row.title = `${SOURCE_LABEL[entry.source] || entry.source}: ${entry.raw}${ok ? `\nresolved to ${entry.resolved_id}` : `\n${entry.status}${entry.message ? ` — ${entry.message}` : ""}`}`;
            list.appendChild(row);
        }
        const chain = el("details", "mg-lora-chain");
        chain.appendChild(el("summary", "", `Resolved LoRA chain (${result.chain.length}) — generation order`));
        const ol = el("ol", "mg-lora-chain-list");
        for (const link of result.chain) {
            const li = el("li", "", `${link.name} → ${link.resolved_id} · ${Number(link.strength).toFixed(2)}`);
            li.dataset.resolvedId = link.resolved_id;
            li.title = SOURCE_LABEL[link.source] || link.source;
            ol.appendChild(li);
        }
        chain.appendChild(ol);
        const nodes = [list, chain];
        if (result.has_wildcards || hasWildcards) {
            nodes.push(el("div", "mg-hint", "Wildcards present: LoRAs they emit are resolved the same way at generation time (Expand a Wildcard to inspect them here)."));
        }
        frame(summary, nodes, { problem: (result.entries || []).some(isBlockingProblem) });
    };

    const refresh = () => {
        const sources = getSources();
        if (!sources || !sourcesHaveLora(sources)) {
            clearTimeout(timer);
            currentKey = "";
            if (sources && sourcesHaveWildcards(sources)) {
                container.hidden = false;
                render(null, { wildcardsOnly: true });
                return;
            }
            container.hidden = true;
            container.replaceChildren();
            return;
        }
        container.hidden = false;
        const key = validator.keyOf ? validator.keyOf(sources) : JSON.stringify(sources);
        currentKey = key;
        const cached = validator.peek(sources);
        render(cached, { hasWildcards: sourcesHaveWildcards(sources) });
        if (cached) return;
        clearTimeout(timer);
        timer = setTimeout(() => {
            validator.request(sources).then(result => {
                // Latest wins: a reply for an older prompt never renders over the current one.
                if (currentKey === key) render(result, { hasWildcards: sourcesHaveWildcards(sources) });
                onResult(result);
            });
        }, 250);
    };

    return { refresh, get expanded() { return isExpanded; } };
}
