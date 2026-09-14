/**
 * Manga-owned contextual prompt autocomplete.
 *
 * Supports three contextual provider modes:
 * - Normal comma-delimited text -> Danbooru tag catalog (manga/app/data/danbooru_tags.json)
 * - <lora:NAME:WEIGHT> -> Manga-authoritative LoRA catalog (/api/manga/generation/capabilities)
 * - __NAME__ -> Manga-authoritative Wildcard catalog (/api/manga/wildcards)
 *
 * Special syntax {choice|options} remains strictly suppressed.
 *
 * The controller deliberately knows nothing about generation execution or the
 * authoring document. It edits only the active token and emits the standard
 * "input" event so the existing owner (GenerationState or Store) keeps authority.
 */

const DEFAULT_CATALOG_URL = new URL("../../data/danbooru_tags.json", import.meta.url).href;
const DEFAULT_LORA_URL = "/api/manga/generation/capabilities";
const DEFAULT_WILDCARD_URL = "/api/manga/wildcards";
const DEFAULT_MIN_QUERY_LENGTH = 2;
const DEFAULT_LIMIT = 10;

const catalogPromises = new Map();
const loraPromises = new Map();
const wildcardPromises = new Map();
let popupSequence = 0;

function finiteNumber(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
}

function normalizeEntry(entry) {
    const tag = typeof entry === "string" ? entry : entry?.tag;
    if (typeof tag !== "string" || !tag.trim()) return null;
    return {
        tag: tag.trim(),
        category: typeof entry === "object" && entry?.category != null ? String(entry.category) : "",
        ranking: finiteNumber(typeof entry === "object" ? entry?.ranking : 0)
    };
}

/** Normalize and deterministically order a static Danbooru tag catalog. */
export function normalizeTagCatalog(value) {
    const entries = Array.isArray(value) ? value : Array.isArray(value?.tags) ? value.tags : [];
    return entries.map(normalizeEntry).filter(Boolean).sort((a, b) =>
        b.ranking - a.ranking || a.tag.localeCompare(b.tag));
}

/** Load the static tag catalog once per URL. */
export function loadTagCatalog(url = DEFAULT_CATALOG_URL, fetchImpl = globalThis.fetch) {
    if (!url) return Promise.reject(new Error("Tag catalog is not configured"));
    if (catalogPromises.has(url)) return catalogPromises.get(url);
    const promise = Promise.resolve().then(() => {
        if (typeof fetchImpl !== "function") throw new Error("Fetch is unavailable");
        return fetchImpl(url, { cache: "force-cache" });
    }).then(async response => {
        if (!response?.ok) throw new Error(`Tag catalog unavailable (${response?.status || "request failed"})`);
        const payload = await response.json();
        if (!Array.isArray(payload) && !Array.isArray(payload?.tags)) {
            throw new Error("Tag catalog has an invalid format");
        }
        return normalizeTagCatalog(payload);
    });
    catalogPromises.set(url, promise);
    return promise;
}

/** Normalize a list of LoRA names or catalog entries into a sorted, deduplicated string array. */
export function normalizeLoraList(raw) {
    const list = Array.isArray(raw) ? raw : (Array.isArray(raw?.loras) ? raw.loras : []);
    const result = new Set();
    for (const item of list) {
        if (typeof item === "string" && item.trim()) {
            result.add(item.trim());
        } else if (item && typeof item === "object" && typeof item.id === "string" && item.id.trim()) {
            if (item.available !== false) {
                result.add(item.id.trim());
            }
        }
    }
    return [...result].sort((a, b) => a.localeCompare(b));
}

/** Load available LoRAs from the Manga capability catalog endpoint. */
export function loadLoraCatalog(url = DEFAULT_LORA_URL, fetchImpl = globalThis.fetch) {
    if (!url) return Promise.resolve([]);
    if (loraPromises.has(url)) return loraPromises.get(url);
    const promise = Promise.resolve().then(() => {
        if (typeof fetchImpl !== "function") return [];
        return fetchImpl(url, { cache: "no-cache" });
    }).then(async response => {
        if (!response?.ok) return [];
        const payload = await response.json();
        return normalizeLoraList(payload);
    }).catch(() => []);
    loraPromises.set(url, promise);
    return promise;
}

/** Normalize a list of Wildcard names into a sorted, deduplicated string array. */
export function normalizeWildcardList(raw) {
    const list = Array.isArray(raw) ? raw : (Array.isArray(raw?.wildcards) ? raw.wildcards : []);
    const result = new Set();
    for (const item of list) {
        if (typeof item === "string" && item.trim()) {
            result.add(item.trim().replaceAll("\\", "/"));
        }
    }
    return [...result].sort((a, b) => a.localeCompare(b));
}

/** Load available Wildcards from the Manga wildcard listing endpoint. */
export function loadWildcardCatalog(url = DEFAULT_WILDCARD_URL, fetchImpl = globalThis.fetch) {
    if (!url) return Promise.resolve([]);
    if (wildcardPromises.has(url)) return wildcardPromises.get(url);
    const promise = Promise.resolve().then(() => {
        if (typeof fetchImpl !== "function") return [];
        return fetchImpl(url, { cache: "no-cache" });
    }).then(async response => {
        if (!response?.ok) return [];
        const payload = await response.json();
        return normalizeWildcardList(payload);
    }).catch(() => []);
    wildcardPromises.set(url, promise);
    return promise;
}

/**
 * Return the comma-delimited token around the caret for ordinary TAG context.
 */
export function findActivePromptToken(text, caret) {
    const value = String(text ?? "");
    const position = Math.max(0, Math.min(value.length, Number.isFinite(caret) ? caret : value.length));
    const commaBefore = value.lastIndexOf(",", Math.max(0, position - 1));
    const commaAfter = value.indexOf(",", position);
    const start = commaBefore + 1;
    const end = commaAfter === -1 ? value.length : commaAfter;
    const raw = value.slice(start, end);
    const leading = raw.match(/^\s*/)?.[0] || "";
    const trailing = raw.match(/\s*$/)?.[0] || "";
    const token = raw.slice(leading.length, Math.max(leading.length, raw.length - trailing.length));
    return {
        start,
        end,
        tokenStart: start + leading.length,
        tokenEnd: end - trailing.length,
        raw,
        leading,
        trailing,
        query: token,
        caret: position
    };
}

function insideAngleToken(text, caret) {
    const value = String(text ?? "");
    let open = false;
    for (let index = 0; index < Math.min(value.length, caret); index += 1) {
        if (value[index] === "<") open = true;
        else if (value[index] === ">") open = false;
    }
    return open;
}

function insideDoubleDelimiter(text, caret, delimiter) {
    const value = String(text ?? "");
    let open = false;
    let index = 0;
    while ((index = value.indexOf(delimiter, index)) !== -1 && index < caret) {
        open = !open;
        index += delimiter.length;
    }
    return open;
}

function insideChoiceBraces(text, caret) {
    const value = String(text ?? "");
    let depth = 0;
    for (let index = 0; index < Math.min(value.length, caret); index += 1) {
        if (value[index] === "{") depth += 1;
        else if (value[index] === "}") depth = Math.max(0, depth - 1);
    }
    return depth > 0;
}

/** Return the suppression reason, or an empty string when completion is safe. Backward-compatible. */
export function suppressedPromptContext(text, caret) {
    if (insideAngleToken(text, caret)) return "angle-token";
    if (insideDoubleDelimiter(text, caret, "__")) return "wildcard";
    if (insideChoiceBraces(text, caret)) return "dynamic-choice";
    return "";
}

/**
 * Detect the active prompt completion context around the caret.
 * Returns an object with `type`: "tag" | "lora" | "wildcard" | "suppressed".
 */
export function detectPromptCompletionContext(text, caret) {
    const value = String(text ?? "");
    const pos = Math.max(0, Math.min(value.length, Number.isFinite(caret) ? caret : value.length));

    // 1. Dynamic Choice context { ... } is always suppressed
    if (insideChoiceBraces(value, pos)) {
        return {
            type: "suppressed",
            reason: "dynamic-choice",
            start: pos,
            end: pos,
            query: "",
            caret: pos
        };
    }

    // 2. LoRA context <lora:...>
    const lastOpenAngle = value.lastIndexOf("<", Math.max(0, pos - 1));
    if (lastOpenAngle !== -1) {
        const nextCloseAngle = value.indexOf(">", lastOpenAngle);
        if (nextCloseAngle === -1 || pos <= nextCloseAngle) {
            const angleSlice = value.slice(lastOpenAngle, nextCloseAngle === -1 ? value.length : nextCloseAngle + 1);
            if (/^<lora:/i.test(angleSlice)) {
                const prefixLen = 6; // "<lora:".length
                const nameStart = lastOpenAngle + prefixLen;
                if (pos >= nameStart) {
                    const contentAfterPrefix = angleSlice.slice(prefixLen, nextCloseAngle === -1 ? undefined : -1);
                    const colonIdx = contentAfterPrefix.indexOf(":");
                    const stopCharIdx = contentAfterPrefix.search(/[\r\n,]/);

                    let nameEnd;
                    let tokenEnd;
                    let weight = null;

                    if (nextCloseAngle !== -1) {
                        tokenEnd = nextCloseAngle + 1;
                        nameEnd = colonIdx === -1 ? nextCloseAngle : (nameStart + colonIdx);
                        if (colonIdx !== -1) {
                            weight = contentAfterPrefix.slice(colonIdx + 1);
                        }
                    } else {
                        // Unclosed angle token: stops at comma, newline, or end of string
                        const limit = stopCharIdx === -1 ? contentAfterPrefix.length : stopCharIdx;
                        if (colonIdx !== -1 && colonIdx < limit) {
                            nameEnd = nameStart + colonIdx;
                            tokenEnd = nameStart + limit;
                            weight = contentAfterPrefix.slice(colonIdx + 1, limit);
                        } else {
                            nameEnd = nameStart + limit;
                            tokenEnd = nameEnd;
                        }
                    }

                    if (pos <= nameEnd) {
                        const query = value.slice(nameStart, nameEnd);
                        return {
                            type: "lora",
                            start: lastOpenAngle,
                            end: tokenEnd,
                            nameStart,
                            nameEnd,
                            weight,
                            hasClosingAngle: nextCloseAngle !== -1,
                            query,
                            caret: pos
                        };
                    } else {
                        // Caret is in weight or after colon
                        return {
                            type: "suppressed",
                            reason: "lora-weight",
                            start: pos,
                            end: pos,
                            query: "",
                            caret: pos
                        };
                    }
                } else {
                    return {
                        type: "suppressed",
                        reason: "angle-token",
                        start: pos,
                        end: pos,
                        query: "",
                        caret: pos
                    };
                }
            } else {
                return {
                    type: "suppressed",
                    reason: "angle-token",
                    start: pos,
                    end: pos,
                    query: "",
                    caret: pos
                };
            }
        }
    }

    // 3. Wildcard context __...__
    const lastOpenWildcard = value.lastIndexOf("__", Math.max(0, pos - 1));
    if (lastOpenWildcard !== -1) {
        let countBefore = 0;
        let scan = 0;
        while ((scan = value.indexOf("__", scan)) !== -1 && scan < lastOpenWildcard) {
            countBefore += 1;
            scan += 2;
        }
        const isOpening = (countBefore % 2 === 0);
        if (isOpening) {
            const nextCloseWildcard = value.indexOf("__", lastOpenWildcard + 2);
            const nameStart = lastOpenWildcard + 2;
            const hasClose = nextCloseWildcard !== -1;
            const limit = hasClose ? nextCloseWildcard : value.length;
            const segment = value.slice(nameStart, limit);
            const stopChar = segment.search(/[\r\n,]/);
            const actualEnd = stopChar === -1 ? limit : (nameStart + stopChar);

            if (pos >= nameStart && pos <= actualEnd) {
                const query = value.slice(nameStart, actualEnd);
                return {
                    type: "wildcard",
                    start: lastOpenWildcard,
                    end: hasClose && stopChar === -1 ? (nextCloseWildcard + 2) : actualEnd,
                    nameStart,
                    nameEnd: actualEnd,
                    hasClosingDelimiter: hasClose && stopChar === -1,
                    query,
                    caret: pos
                };
            }
        }
    }

    // 4. Ordinary Tag context (comma-delimited)
    const active = findActivePromptToken(value, pos);
    return {
        type: "tag",
        ...active
    };
}

function boundaryPrefix(tag, query) {
    if (!query) return false;
    const lowerTag = String(tag).toLowerCase();
    return lowerTag.includes(`_${query}`) || lowerTag.includes(` ${query}`) ||
        lowerTag.includes(`-${query}`) || lowerTag.includes(`/${query}`);
}

/**
 * Query a normalized Danbooru catalog. Prefix matches win, then boundary prefixes,
 * then substring matches. Ranking breaks ties.
 */
export function queryTagCatalog(catalog, query, { limit = DEFAULT_LIMIT, minQueryLength = DEFAULT_MIN_QUERY_LENGTH } = {}) {
    const normalizedQuery = String(query ?? "").trim().toLowerCase();
    if (normalizedQuery.length < minQueryLength || !Array.isArray(catalog)) return [];
    const matches = [];
    for (const entry of catalog) {
        const tag = String(entry?.tag || "");
        const lower = tag.toLowerCase();
        let matchRank = -1;
        if (lower.startsWith(normalizedQuery)) matchRank = 0;
        else if (boundaryPrefix(tag, normalizedQuery)) matchRank = 1;
        else if (lower.includes(normalizedQuery)) matchRank = 2;
        if (matchRank === -1) continue;
        matches.push({ ...entry, type: "tag", matchRank });
    }
    matches.sort((a, b) => a.matchRank - b.matchRank ||
        finiteNumber(b.ranking) - finiteNumber(a.ranking) ||
        String(a.tag).localeCompare(String(b.tag)));
    return matches.slice(0, Math.max(1, limit));
}

/**
 * Query available LoRA names.
 */
export function queryLoraCatalog(loras, query, { limit = DEFAULT_LIMIT } = {}) {
    if (!Array.isArray(loras) || loras.length === 0) return [];
    const normalizedQuery = String(query ?? "").trim().toLowerCase();
    const matches = [];
    for (const name of loras) {
        const lower = name.toLowerCase();
        let matchRank = -1;
        if (!normalizedQuery) {
            matchRank = 0;
        } else if (lower.startsWith(normalizedQuery)) {
            matchRank = 0;
        } else if (boundaryPrefix(name, normalizedQuery)) {
            matchRank = 1;
        } else if (lower.includes(normalizedQuery)) {
            matchRank = 2;
        }
        if (matchRank === -1) continue;
        matches.push({
            tag: name,
            category: "lora",
            type: "lora",
            matchRank
        });
    }
    matches.sort((a, b) => a.matchRank - b.matchRank || String(a.tag).localeCompare(String(b.tag)));
    return matches.slice(0, Math.max(1, limit));
}

/**
 * Query available Wildcard names.
 */
export function queryWildcardCatalog(wildcards, query, { limit = DEFAULT_LIMIT } = {}) {
    if (!Array.isArray(wildcards) || wildcards.length === 0) return [];
    const normalizedQuery = String(query ?? "").trim().toLowerCase();
    const matches = [];
    for (const name of wildcards) {
        const lower = name.toLowerCase();
        let matchRank = -1;
        if (!normalizedQuery) {
            matchRank = 0;
        } else if (lower.startsWith(normalizedQuery)) {
            matchRank = 0;
        } else if (boundaryPrefix(name, normalizedQuery)) {
            matchRank = 1;
        } else if (lower.includes(normalizedQuery)) {
            matchRank = 2;
        }
        if (matchRank === -1) continue;
        matches.push({
            tag: name,
            category: "wildcard",
            type: "wildcard",
            matchRank
        });
    }
    matches.sort((a, b) => a.matchRank - b.matchRank || String(a.tag).localeCompare(String(b.tag)));
    return matches.slice(0, Math.max(1, limit));
}

/**
 * Insert a normal Danbooru tag, replacing only the active comma token.
 */
export function insertPromptTag(text, caret, tag) {
    const value = String(text ?? "");
    const active = findActivePromptToken(value, caret);
    if (!String(tag || "").trim() || suppressedPromptContext(value, active.caret)) return null;
    const replacementTag = String(tag).trim();
    const after = value.slice(active.end);
    const hasFollowingComma = /^\s*,/.test(after);
    const replacement = hasFollowingComma
        ? `${active.leading}${replacementTag}${active.trailing}`
        : `${active.leading}${replacementTag}, `;
    const nextValue = value.slice(0, active.start) + replacement + after;
    return {
        value: nextValue,
        caret: active.start + replacement.length,
        active,
        replacement
    };
}

/**
 * Insert a LoRA name inside <lora:NAME:WEIGHT>, preserving existing weight or using default 1.
 */
export function insertPromptLora(text, context, loraName) {
    const value = String(text ?? "");
    if (!context || context.type !== "lora" || !loraName) return null;
    const name = String(loraName).trim();
    if (!name) return null;
    const weight = context.weight !== null ? context.weight : "1";
    const replacement = `<lora:${name}:${weight}>`;
    const nextValue = value.slice(0, context.start) + replacement + value.slice(context.end);
    const nextCaret = context.start + replacement.length;
    return {
        value: nextValue,
        caret: nextCaret,
        replacement
    };
}

/**
 * Insert a Wildcard name inside __NAME__, without duplicating delimiters.
 */
export function insertPromptWildcard(text, context, wildcardName) {
    const value = String(text ?? "");
    if (!context || context.type !== "wildcard" || !wildcardName) return null;
    const name = String(wildcardName).trim();
    if (!name) return null;
    let nextValue;
    let nextCaret;
    let replacement;
    if (context.hasClosingDelimiter) {
        replacement = name;
        nextValue = value.slice(0, context.nameStart) + replacement + value.slice(context.nameEnd);
        nextCaret = context.nameStart + replacement.length + 2;
    } else {
        replacement = `__${name}__`;
        nextValue = value.slice(0, context.start) + replacement + value.slice(context.end);
        nextCaret = context.start + replacement.length;
    }
    return {
        value: nextValue,
        caret: nextCaret,
        replacement
    };
}

function createPopup(textarea) {
    const host = textarea.parentElement || textarea;
    host.classList.add("tag-autocomplete-host");
    const popup = document.createElement("div");
    popup.className = "tag-autocomplete-popup";
    popup.id = `tag-autocomplete-${++popupSequence}`;
    popup.setAttribute("role", "listbox");
    popup.hidden = true;
    host.appendChild(popup);
    textarea.setAttribute("aria-autocomplete", "list");
    textarea.setAttribute("aria-controls", popup.id);
    textarea.setAttribute("aria-expanded", "false");
    return popup;
}

export class TagAutocompleteController {
    constructor(textarea, {
        catalog = null,
        catalogUrl = DEFAULT_CATALOG_URL,
        catalogLoader = null,
        loras = null,
        loraUrl = DEFAULT_LORA_URL,
        loraLoader = null,
        wildcards = null,
        wildcardUrl = DEFAULT_WILDCARD_URL,
        wildcardLoader = null,
        minQueryLength = DEFAULT_MIN_QUERY_LENGTH,
        limit = DEFAULT_LIMIT
    } = {}) {
        if (!textarea || typeof textarea.addEventListener !== "function") {
            throw new TypeError("Tag autocomplete requires a textarea");
        }
        this.textarea = textarea;
        this.minQueryLength = minQueryLength;
        this.limit = limit;

        this.catalog = catalog == null ? null : normalizeTagCatalog(catalog);
        this.catalogError = "";

        this.loras = loras == null ? [] : normalizeLoraList(loras);
        this.loraError = "";

        this.wildcards = wildcards == null ? [] : normalizeWildcardList(wildcards);
        this.wildcardError = "";

        this.suggestions = [];
        this.selectedIndex = 0;
        this.activeContext = null;
        this.activeToken = null;
        this.popup = createPopup(textarea);

        this._onInput = () => this.refresh();
        this._onFocus = () => this.refresh();
        this._onKeydown = event => this.handleKeydown(event);
        this._onOutsidePointer = event => {
            if (event.target !== this.textarea && !this.popup.contains(event.target)) this.close();
        };

        textarea.addEventListener("input", this._onInput);
        textarea.addEventListener("focus", this._onFocus);
        textarea.addEventListener("click", this._onFocus);
        textarea.addEventListener("keydown", this._onKeydown);
        document.addEventListener("pointerdown", this._onOutsidePointer);

        textarea.dataset.tagAutocompleteState = this.catalog ? "ready" : "loading";

        // Load Tag catalog
        if (!this.catalog) {
            this.catalogPromise = Promise.resolve().then(() => catalogLoader
                ? catalogLoader()
                : loadTagCatalog(catalogUrl)).then(value => {
                this.catalog = normalizeTagCatalog(value);
                this.catalogError = "";
                this.textarea.dataset.tagAutocompleteState = "ready";
                this.refresh();
                return this.catalog;
            }).catch(error => {
                this.catalogError = error?.message || "Tag catalog unavailable";
                this.textarea.dataset.tagAutocompleteState = "unavailable";
                this.close();
                return null;
            });
        } else {
            this.catalogPromise = Promise.resolve(this.catalog);
        }

        // Load LoRA catalog if not provided
        if (loras == null) {
            this.loraPromise = Promise.resolve().then(() => loraLoader
                ? loraLoader()
                : loadLoraCatalog(loraUrl)).then(list => {
                this.loras = normalizeLoraList(list);
                this.loraError = "";
                return this.loras;
            }).catch(error => {
                this.loraError = error?.message || "LoRA catalog unavailable";
                this.loras = [];
                return [];
            });
        } else {
            this.loraPromise = Promise.resolve(this.loras);
        }

        // Load Wildcard catalog if not provided
        if (wildcards == null) {
            this.wildcardPromise = Promise.resolve().then(() => wildcardLoader
                ? wildcardLoader()
                : loadWildcardCatalog(wildcardUrl)).then(list => {
                this.wildcards = normalizeWildcardList(list);
                this.wildcardError = "";
                return this.wildcards;
            }).catch(error => {
                this.wildcardError = error?.message || "Wildcard catalog unavailable";
                this.wildcards = [];
                return [];
            });
        } else {
            this.wildcardPromise = Promise.resolve(this.wildcards);
        }
    }

    setLoras(loras) {
        this.loras = normalizeLoraList(loras);
        this.refresh();
    }

    setWildcards(wildcards) {
        this.wildcards = normalizeWildcardList(wildcards);
        this.refresh();
    }

    refresh() {
        const caret = Number.isFinite(this.textarea.selectionStart)
            ? this.textarea.selectionStart : this.textarea.value.length;
        const context = detectPromptCompletionContext(this.textarea.value, caret);
        this.activeContext = context;
        this.activeToken = context.type === "tag" ? context : null;

        if (context.type === "suppressed") {
            this.close();
            return [];
        }

        let suggestions = [];
        if (context.type === "lora") {
            suggestions = queryLoraCatalog(this.loras, context.query, {
                limit: this.limit
            });
        } else if (context.type === "wildcard") {
            suggestions = queryWildcardCatalog(this.wildcards, context.query, {
                limit: this.limit
            });
        } else if (context.type === "tag") {
            if (!this.catalog) {
                this.close();
                return [];
            }
            suggestions = queryTagCatalog(this.catalog, context.query, {
                limit: this.limit,
                minQueryLength: this.minQueryLength
            });
        }

        this.suggestions = suggestions;
        this.selectedIndex = 0;
        this.render();
        return suggestions;
    }

    render() {
        this.popup.replaceChildren();
        if (!this.suggestions.length) {
            this.close();
            return;
        }
        this.suggestions.forEach((entry, index) => {
            const option = document.createElement("button");
            option.type = "button";
            option.className = "tag-autocomplete-option";
            option.setAttribute("role", "option");
            option.setAttribute("aria-selected", String(index === this.selectedIndex));
            option.dataset.tagIndex = String(index);
            const label = document.createElement("span");
            label.className = "tag-autocomplete-label";
            label.textContent = entry.tag;
            option.appendChild(label);
            if (entry.category) {
                const badge = document.createElement("span");
                badge.className = "tag-autocomplete-category";
                badge.textContent = entry.category;
                option.appendChild(badge);
            }
            option.addEventListener("pointerdown", event => event.preventDefault());
            option.addEventListener("click", () => this.accept(index));
            this.popup.appendChild(option);
        });
        this.popup.hidden = false;
        this.textarea.setAttribute("aria-expanded", "true");
        this.textarea.setAttribute("aria-activedescendant", this.popup.children[this.selectedIndex].id || "");
        this.syncSelectionAttributes();
    }

    syncSelectionAttributes() {
        [...this.popup.children].forEach((option, index) =>
            option.setAttribute("aria-selected", String(index === this.selectedIndex)));
        const active = this.popup.children[this.selectedIndex];
        if (active) {
            if (!active.id) active.id = `${this.popup.id}-option-${this.selectedIndex}`;
            this.textarea.setAttribute("aria-activedescendant", active.id);
        }
    }

    close() {
        this.suggestions = [];
        this.activeToken = null;
        this.activeContext = null;
        this.popup.hidden = true;
        this.textarea.setAttribute("aria-expanded", "false");
        this.textarea.removeAttribute("aria-activedescendant");
    }

    moveSelection(delta) {
        if (!this.suggestions.length) return;
        const count = this.suggestions.length;
        this.selectedIndex = (this.selectedIndex + delta + count) % count;
        this.syncSelectionAttributes();
    }

    handleKeydown(event) {
        const open = !this.popup.hidden && this.suggestions.length > 0;
        if (event.key === "Escape" && open) {
            event.preventDefault();
            this.close();
            return;
        }
        if (!open) return;
        if (event.key === "ArrowDown") {
            event.preventDefault();
            this.moveSelection(1);
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            this.moveSelection(-1);
        } else if (event.key === "Enter" || event.key === "Tab") {
            event.preventDefault();
            this.accept(this.selectedIndex);
        }
    }

    accept(index = this.selectedIndex) {
        const entry = this.suggestions[index];
        if (!entry || !this.activeContext) return false;
        let result = null;
        if (this.activeContext.type === "lora") {
            result = insertPromptLora(this.textarea.value, this.activeContext, entry.tag);
        } else if (this.activeContext.type === "wildcard") {
            result = insertPromptWildcard(this.textarea.value, this.activeContext, entry.tag);
        } else {
            result = insertPromptTag(this.textarea.value, this.textarea.selectionStart, entry.tag);
        }
        if (!result) return false;
        this.textarea.value = result.value;
        this.textarea.setSelectionRange(result.caret, result.caret);
        this.textarea.dispatchEvent(new Event("input", { bubbles: true }));
        this.close();
        this.textarea.focus();
        return true;
    }

    dispose() {
        this.textarea.removeEventListener("input", this._onInput);
        this.textarea.removeEventListener("focus", this._onFocus);
        this.textarea.removeEventListener("click", this._onFocus);
        this.textarea.removeEventListener("keydown", this._onKeydown);
        document.removeEventListener("pointerdown", this._onOutsidePointer);
        this.popup.remove();
        this.textarea.removeAttribute("aria-controls");
        this.textarea.removeAttribute("aria-autocomplete");
        this.textarea.removeAttribute("aria-expanded");
        this.textarea.removeAttribute("aria-activedescendant");
    }
}

export function createTagAutocomplete(textarea, options) {
    return new TagAutocompleteController(textarea, options);
}

export const TAG_AUTOCOMPLETE_DEFAULTS = Object.freeze({
    catalogUrl: DEFAULT_CATALOG_URL,
    loraUrl: DEFAULT_LORA_URL,
    wildcardUrl: DEFAULT_WILDCARD_URL,
    minQueryLength: DEFAULT_MIN_QUERY_LENGTH,
    limit: DEFAULT_LIMIT
});
