/**
 * Manga-owned offline Danbooru-style tag autocomplete.
 *
 * The controller deliberately knows nothing about generation or the
 * authoring document. It only edits the active textarea token and emits the
 * normal input event so the existing owner (GenerationState or Store) keeps
 * authority over the value.
 */

const DEFAULT_CATALOG_URL = new URL("../../data/danbooru_tags.json", import.meta.url).href;
const DEFAULT_MIN_QUERY_LENGTH = 2;
const DEFAULT_LIMIT = 10;
const catalogPromises = new Map();
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

/** Normalize and deterministically order a static catalog. */
export function normalizeTagCatalog(value) {
    const entries = Array.isArray(value) ? value : Array.isArray(value?.tags) ? value.tags : [];
    return entries.map(normalizeEntry).filter(Boolean).sort((a, b) =>
        b.ranking - a.ranking || a.tag.localeCompare(b.tag));
}

/**
 * Load the static catalog once per URL. A missing/unreadable asset rejects the
 * promise; callers keep the textarea usable and simply close autocomplete.
 */
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

/**
 * Return the comma-delimited token around the caret. `start` and `end`
 * include only the current token segment; the comma delimiters remain outside
 * the replacement range.
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

/** Return the suppression reason, or an empty string when completion is safe. */
export function suppressedPromptContext(text, caret) {
    if (insideAngleToken(text, caret)) return "angle-token";
    if (insideDoubleDelimiter(text, caret, "__")) return "wildcard";
    if (insideChoiceBraces(text, caret)) return "dynamic-choice";
    return "";
}

function boundaryPrefix(tag, query) {
    if (!query) return false;
    const lowerTag = String(tag).toLowerCase();
    return lowerTag.includes(`_${query}`) || lowerTag.includes(` ${query}`) ||
        lowerTag.includes(`-${query}`);
}

/**
 * Query a normalized catalog. Prefix matches win, then underscore/word
 * boundary prefixes, then a bounded substring fallback. Ranking breaks ties.
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
        matches.push({ ...entry, matchRank });
    }
    matches.sort((a, b) => a.matchRank - b.matchRank ||
        finiteNumber(b.ranking) - finiteNumber(a.ranking) ||
        String(a.tag).localeCompare(String(b.tag)));
    return matches.slice(0, Math.max(1, limit));
}

/**
 * Replace only the active comma-delimited token. Existing delimiters and all
 * text outside that token remain byte-for-byte intact.
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
        this.suggestions = [];
        this.selectedIndex = 0;
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
    }

    refresh() {
        if (!this.catalog) {
            this.close();
            return [];
        }
        const caret = Number.isFinite(this.textarea.selectionStart)
            ? this.textarea.selectionStart : this.textarea.value.length;
        const active = findActivePromptToken(this.textarea.value, caret);
        if (suppressedPromptContext(this.textarea.value, caret)) {
            this.close();
            return [];
        }
        const suggestions = queryTagCatalog(this.catalog, active.query, {
            limit: this.limit,
            minQueryLength: this.minQueryLength
        });
        this.activeToken = active;
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
        if (!entry) return false;
        const result = insertPromptTag(this.textarea.value, this.textarea.selectionStart, entry.tag);
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
    minQueryLength: DEFAULT_MIN_QUERY_LENGTH,
    limit: DEFAULT_LIMIT
});
