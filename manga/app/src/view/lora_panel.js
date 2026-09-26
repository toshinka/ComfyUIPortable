// LoRA panel for the MANGA / Illustrious Positive Prompt (Card MANGA-ILLUSTRIOUS-LORA-PRODUCTION1).
//
// The Positive Prompt text is the single source of truth: selecting a card writes a
// visible `<lora:CANONICAL_ID:STRENGTH>` directive, and card state is read back
// from the prompt.  The token helpers below only LOCATE directives for editing;
// the backend compiler (basic_generation._compile_prompt) is the one parser that
// resolves them against the trusted catalog.  The pattern mirrors LORA_RE there.

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

export function mountLoraPanel({ panel, toggle, body, status, breadcrumb, folders, cards, count, prompt, fetchFolder = fetchLoraFolder }) {
    const cache = new Map();
    const draftStrength = new Map();
    let currentFolder = "";
    let listing = null;
    let enabled = true;
    let disabledReason = "";
    let loadSeq = 0;

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
    };

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
        const items = (listing && listing.loras) || [];
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
            let thumb = null;
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
                    thumb.remove();
                };
            }
            const name = el("span", "mg-lora-card-name", lora.name);
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
            if (thumb) card.append(thumb);
            card.append(name, strength, action);
            cards.appendChild(card);
        }
        if (!items.length && listing) cards.appendChild(el("div", "mg-hint mg-lora-empty", "No LoRA files in this folder."));
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

export function sourcesHaveLora(sources) {
    return Array.isArray(sources) && sources.some(source => /<lora/i.test(String(source?.text || "")));
}

export function createLoraValidator({ engine = "illustrious", fetchImpl = (...args) => globalThis.fetch(...args) } = {}) {
    const cache = new Map();
    const inflight = new Map();
    const keyOf = sources => JSON.stringify(sources);
    return {
        peek(sources) {
            return cache.get(keyOf(sources)) ?? null;
        },
        request(sources) {
            const key = keyOf(sources);
            if (cache.has(key)) return Promise.resolve(cache.get(key));
            if (inflight.has(key)) return inflight.get(key);
            const promise = Promise.resolve().then(() => fetchImpl(
                `/api/manga/resources/lora/validate?engine=${encodeURIComponent(engine)}`,
                { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sources }) },
            )).then(async res => {
                const data = await res.json().catch(() => null);
                return data && typeof data === "object" ? data : { ok: false, error: `LoRA validation failed (${res.status})` };
            }).catch(err => ({ ok: false, error: err?.message || "LoRA validation unavailable" })).then(result => {
                cache.set(key, result);
                if (cache.size > 24) cache.delete(cache.keys().next().value);
                inflight.delete(key);
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
    const problems = result.entries.filter(entry => entry.status !== "RESOLVED");
    if (!problems.length) return "";
    const first = problems[0];
    const more = problems.length > 1 ? ` (+${problems.length - 1} more)` : "";
    return `Generate disabled — unresolved LoRA: ${first.name || first.raw} ${STATUS_LABEL[first.status] || first.status}${more}. See LoRA status under the prompt.`;
}

export function mountLoraDiagnostics({ container, validator, getSources, onResult = () => {} }) {
    let timer = null;
    let currentKey = "";

    const render = (result) => {
        container.replaceChildren();
        if (!result) {
            container.appendChild(el("div", "mg-hint", "LoRA status: checking…"));
            return;
        }
        if (result.ok !== true) {
            container.appendChild(el("div", "mg-hint mg-lora-status-error", `LoRA status unavailable: ${result.error || "validation failed"}`));
            return;
        }
        const head = el("div", "mg-lora-diag-head", `LoRA status${result.problems ? ` · ${result.problems} problem${result.problems > 1 ? "s" : ""}` : " · all resolved"}`);
        const list = el("ul", "mg-lora-diag-list");
        for (const entry of result.entries) {
            const ok = entry.status === "RESOLVED";
            const row = el("li", `mg-lora-diag-row ${ok ? "is-ok" : "is-problem"}`);
            row.dataset.status = entry.status;
            row.dataset.loraName = entry.name || entry.raw;
            const main = el("span", "mg-lora-diag-main",
                `${ok ? "✓" : "✕"} ${entry.name || entry.raw}${entry.strength_text ? ` ${entry.strength_text}` : ""}${ok ? "" : ` — ${STATUS_LABEL[entry.status] || entry.status}`}`);
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
        container.append(head, list, chain);
        if (result.has_wildcards) {
            container.appendChild(el("div", "mg-hint", "Wildcards present: LoRAs they emit are resolved the same way at generation time."));
        }
    };

    const refresh = () => {
        const sources = getSources();
        if (!sources || !sourcesHaveLora(sources)) {
            currentKey = "";
            container.hidden = true;
            container.replaceChildren();
            return;
        }
        container.hidden = false;
        const key = JSON.stringify(sources);
        currentKey = key;
        const cached = validator.peek(sources);
        render(cached);
        if (cached) return;
        clearTimeout(timer);
        timer = setTimeout(() => {
            validator.request(sources).then(result => {
                if (currentKey === key) render(result);
                onResult(result);
            });
        }, 250);
    };

    return { refresh };
}
