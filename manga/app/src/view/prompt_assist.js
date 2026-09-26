// Prompt Assist (Card MANGA-PROMPT-ASSIST-PRODUCTION1): one compact area under the
// Positive Prompt that switches between the LoRA browser and a Wildcard browser.
//
// Wildcards come from the existing Manga owner (/api/manga/wildcards via
// loadWildcardCatalog, the same cached list the autocomplete uses) and are
// inserted as the existing visible `__name__` token.  Expansion stays in the
// backend compiler; nothing here parses or expands wildcard contents.

import { LOAD_FAILED, formatWildcardToken, insertWildcardAtCursor, loadWildcardCatalog } from "./tag_autocomplete.js";

function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}

/** Immediate children of one wildcard folder, derived from canonical relative names. */
export function listWildcardFolder(names, folder = "") {
    const prefix = folder ? `${folder}/` : "";
    const folders = new Set();
    const entries = [];
    for (const name of names || []) {
        if (!name.startsWith(prefix)) continue;
        const rest = name.slice(prefix.length);
        const slash = rest.indexOf("/");
        if (slash === -1) entries.push({ id: name, name: rest });
        else folders.add(rest.slice(0, slash));
    }
    return {
        folders: [...folders].sort((a, b) => a.localeCompare(b)).map(name => ({ id: prefix + name, name })),
        entries: entries.sort((a, b) => a.name.localeCompare(b.name)),
    };
}

export function mountPromptAssist({
    panel, toggle, tabs, loraPanel, prompt,
    wildcardBody, wildcardStatus, wildcardBreadcrumb, wildcardFolders, wildcardEntries,
    loadWildcards = () => loadWildcardCatalog(),
}) {
    let expanded = false;
    let active = "lora";
    let enabled = true;
    let wildcardNames = null;
    let wildcardFolder = "";
    let loading = null;

    const setStatus = (text, isError = false) => {
        wildcardStatus.textContent = text || "";
        wildcardStatus.classList.toggle("mg-lora-status-error", Boolean(isError));
    };

    const insertWildcard = (name) => {
        if (!enabled) return;
        const start = Number.isFinite(prompt.selectionStart) ? prompt.selectionStart : prompt.value.length;
        const end = Number.isFinite(prompt.selectionEnd) ? prompt.selectionEnd : start;
        const result = insertWildcardAtCursor(prompt.value, start, end, name);
        prompt.value = result.value;
        prompt.setSelectionRange(result.caret, result.caret);
        prompt.dispatchEvent(new Event("input", { bubbles: true }));
        prompt.dispatchEvent(new CustomEvent("tegaki:wildcard-inserted",
            { bubbles: true, detail: { name, start: result.caret - result.token.length } }));
    };

    const renderWildcards = () => {
        wildcardBreadcrumb.replaceChildren();
        const parts = wildcardFolder ? wildcardFolder.split("/") : [];
        [{ id: "", name: "Wildcards" }, ...parts.map((name, i) => ({ id: parts.slice(0, i + 1).join("/"), name }))]
            .forEach((crumb, i, all) => {
                if (i) wildcardBreadcrumb.appendChild(el("span", "mg-lora-crumb-sep", "/"));
                const button = el("button", "mg-lora-crumb", crumb.name);
                button.type = "button";
                button.dataset.folder = crumb.id;
                if (i === all.length - 1) button.setAttribute("aria-current", "location");
                button.onclick = () => { wildcardFolder = crumb.id; renderWildcards(); };
                wildcardBreadcrumb.appendChild(button);
            });
        const listing = listWildcardFolder(wildcardNames || [], wildcardFolder);
        wildcardFolders.replaceChildren(...listing.folders.map(folder => {
            const button = el("button", "mg-lora-folder", `📁 ${folder.name}`);
            button.type = "button";
            button.setAttribute("role", "listitem");
            button.dataset.folder = folder.id;
            button.onclick = () => { wildcardFolder = folder.id; renderWildcards(); };
            return button;
        }));
        wildcardFolders.hidden = !listing.folders.length;
        wildcardEntries.replaceChildren(...listing.entries.map(entry => {
            const button = el("button", "mg-wildcard-entry", `__${entry.id}__`);
            button.type = "button";
            button.setAttribute("role", "listitem");
            button.dataset.wildcardId = entry.id;
            button.title = `Insert __${entry.id}__`;
            button.disabled = !enabled;
            // Keep the prompt caret/selection while clicking.
            button.addEventListener("pointerdown", event => event.preventDefault());
            button.onclick = () => insertWildcard(entry.id);
            return button;
        }));
        if (wildcardNames && !listing.entries.length && !listing.folders.length) {
            wildcardEntries.appendChild(el("div", "mg-hint mg-lora-empty", "No wildcards in this folder."));
        }
    };

    const ensureWildcards = () => {
        if (wildcardNames !== null || loading) return;
        setStatus("Loading…");
        loading = Promise.resolve(loadWildcards()).then(list => {
            if (list && list[LOAD_FAILED]) throw new Error("Wildcard list is unavailable.");
            wildcardNames = Array.isArray(list) ? list : [];
            setStatus(enabled ? "" : panel.dataset.disabledReason || "");
        }).catch(err => {
            setStatus(err.message || "Wildcard list is unavailable.", true);
        }).finally(() => {
            loading = null;
            renderWildcards();
        });
    };

    const apply = () => {
        toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
        panel.classList.toggle("is-expanded", expanded);
        for (const tab of tabs) {
            const selected = tab.dataset.assistTab === active;
            tab.setAttribute("aria-selected", selected ? "true" : "false");
            tab.tabIndex = selected ? 0 : -1;
        }
        loraPanel.setExpanded(expanded && active === "lora");
        wildcardBody.hidden = !(expanded && active === "wildcard");
        if (expanded && active === "wildcard") ensureWildcards();
    };

    toggle.addEventListener("click", () => { expanded = !expanded; apply(); });
    for (const tab of tabs) {
        tab.addEventListener("click", () => { active = tab.dataset.assistTab; expanded = true; apply(); });
    }
    apply();

    return {
        // Same enablement as the LoRA panel: Global/Scene prompts only; CAST unchanged.
        sync(options = {}) {
            enabled = options.enabled !== false;
            panel.dataset.disabledReason = enabled ? "" : (options.reason || "");
            loraPanel.sync(options);
            if (wildcardNames !== null) {
                setStatus(enabled ? "" : panel.dataset.disabledReason);
                renderWildcards();
            }
        },
        show(tab) { active = tab; expanded = true; apply(); },
    };
}


/**
 * Read-only Wildcard SOURCE preview shown outside the prompt textarea
 * (Card MANGA-WILDCARD-AUTOCOMPLETE-PRODUCTION1 + WILDCARD-PREVIEW-OWNER-UX1).  It lists
 * every usable line returned by the trusted wildcard resource, wrapped in full; it never
 * expands, selects or edits anything.  Hover preview is a possible future option only.
 */
/**
 * Which `__name__` occurrence an explicit Expand replaces: the one recorded at insertion
 * when it is still there, otherwise the ONLY occurrence.  Several candidates and no
 * recorded match -> null (refuse; never replace an arbitrary occurrence).
 */
export function locateWildcardOccurrence(text, name, start) {
    const value = String(text ?? "");
    const token = formatWildcardToken(name);
    if (Number.isInteger(start) && start >= 0 && value.slice(start, start + token.length) === token) {
        return { start, end: start + token.length, token };
    }
    const first = value.indexOf(token);
    if (first === -1) return { error: "missing", token };
    if (value.indexOf(token, first + 1) !== -1) return { error: "ambiguous", token };
    return { start: first, end: first + token.length, token };
}

/** Replace exactly that occurrence with one concrete expansion; all other text unchanged. */
export function applyWildcardExpansion(text, name, start, expandedText) {
    const found = locateWildcardOccurrence(text, name, start);
    if (found.error) return found;
    const value = String(text);
    return { value: value.slice(0, found.start) + String(expandedText) + value.slice(found.end),
        start: found.start, end: found.start + String(expandedText).length, token: found.token };
}

/** Ask the backend's existing dynamicprompts owner for ONE expansion of __name__ (never writes files). */
export async function fetchWildcardExpansion(name, fetchImpl = (...args) => globalThis.fetch(...args)) {
    const res = await fetchImpl("/api/manga/wildcards/expand", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok || !data || data.ok !== true || typeof data.expanded_text !== "string") {
        throw new Error((data && data.error) || `Wildcard expansion failed (${res.status})`);
    }
    return data;
}

/**
 * Explicit Owner action: replace the tracked `__name__` in `prompt` with one expansion,
 * as an undoable edit when the browser supports it; the normal "input" event then drives
 * the store and LoRA diagnostics for the expanded, explicit LoRA tokens.
 */
export async function expandWildcardInPrompt({ prompt, name, start, fetchImpl, doc = globalThis.document }) {
    const before = locateWildcardOccurrence(prompt.value, name, start);
    if (before.error === "missing") return { ok: false, message: `${before.token} is no longer in this prompt.` };
    if (before.error) return { ok: false, message: `${before.token} appears more than once; place the caret by re-inserting it, then Expand.` };
    const snapshot = prompt.value;
    const data = await fetchWildcardExpansion(name, fetchImpl);
    if (prompt.value !== snapshot) return { ok: false, message: "The prompt changed while expanding; nothing was replaced." };
    const next = applyWildcardExpansion(snapshot, name, before.start, data.expanded_text);
    if (next.error) return { ok: false, message: "Wildcard occurrence could not be identified; nothing was replaced." };
    let applied = false;
    try {
        prompt.focus();
        prompt.setSelectionRange(next.start, next.start + next.token.length);
        applied = Boolean(doc?.execCommand?.("insertText", false, data.expanded_text)) && prompt.value === next.value;
    } catch { applied = false; }
    if (!applied) {
        prompt.value = next.value;
        prompt.dispatchEvent(new Event("input", { bubbles: true }));
    }
    prompt.setSelectionRange(next.end, next.end);
    return { ok: true, value: next.value, expanded_text: data.expanded_text };
}

export function mountWildcardPreview({ container, keepOpenWithin = [],
    fetchImpl = (...args) => globalThis.fetch(...args), doc = globalThis.document, expand = null }) {
    // Owner UX (WILDCARD-PREVIEW-OWNER-UX1): no time-based dismissal.  The preview stays
    // until another Wildcard replaces it, the Owner clicks outside it (and outside the
    // Prompt Assist area / autocomplete popup given in keepOpenWithin), a scroll moves
    // it, × is pressed, the prompt target changes, or the page context goes stale.
    let seq = 0;
    let listening = false;
    const inside = (node) => {
        if (!node || typeof node !== "object") return false;
        if (container.contains(node)) return true;
        for (const item of keepOpenWithin) {
            const root = typeof item === "string" ? doc?.querySelector?.(item) : item;
            if (root && root.contains(node)) return true;
        }
        const popup = node.closest?.(".tag-autocomplete-popup");
        return Boolean(popup);
    };
    const onPointerDown = (event) => { if (!inside(event.target)) hide(); };
    const onScroll = (event) => {
        const target = event.target;
        // Only a scroll that moves the preview (document or an ancestor scroller) dismisses;
        // scrolling the preview's own list or the prompt textarea does not.
        if (target === doc || target === doc?.documentElement || target === doc?.body ||
                (target && typeof target.contains === "function" && target !== container &&
                    !container.contains(target) && target.contains(container))) hide();
    };
    const onStale = () => hide();
    const listen = (on) => {
        if (!doc || on === listening) return;
        listening = on;
        const method = on ? "addEventListener" : "removeEventListener";
        // pointerdown is registered only after the preview renders, so the gesture that
        // selected the Wildcard (already dispatched) can never dismiss its own preview.
        doc[method]("pointerdown", onPointerDown, true);
        doc[method]("scroll", onScroll, true);
        const win = doc.defaultView;
        if (win) {
            win[method]("hashchange", onStale);
            win[method]("popstate", onStale);
            win[method]("pagehide", onStale);
        }
    };
    const hide = () => {
        seq += 1;
        listen(false);
        container.hidden = true;
        container.replaceChildren();
        delete container.dataset.wildcard;
    };
    let occurrence = null;
    const show = async (name, { start = null } = {}) => {
        occurrence = Number.isInteger(start) ? start : null;
        const current = ++seq;
        let data = null;
        try {
            const res = await fetchImpl(`/api/manga/wildcards/preview?name=${encodeURIComponent(name)}`);
            data = await res.json().catch(() => null);
        } catch { data = null; }
        if (current !== seq) return; // replaced by a newer selection (or dismissed meanwhile)
        container.replaceChildren();
        container.dataset.wildcard = name;
        const head = el("div", "mg-wildcard-preview-head");
        head.append(el("span", "mg-wildcard-preview-title", "Wildcard preview"),
            el("code", "mg-wildcard-preview-token", `__${name}__`));
        const close = el("button", "mg-wildcard-preview-close", "×");
        close.type = "button";
        close.setAttribute("aria-label", "Dismiss wildcard preview");
        close.onclick = hide;
        if (typeof expand === "function") {
            // Explicit, Owner-initiated: one concrete expansion replaces THIS occurrence only.
            let note = null;
            const expandButton = el("button", "mg-wildcard-preview-expand", "Expand");
            expandButton.type = "button";
            expandButton.title = `Replace this __${name}__ in the prompt with one expansion (existing Wildcard rules)`;
            expandButton.onclick = async () => {
                expandButton.disabled = true;
                let outcome;
                try { outcome = await expand(name, occurrence); }
                catch (err) { outcome = { ok: false, message: err?.message || "Wildcard expansion failed" }; }
                if (current !== seq) return;
                if (outcome?.ok) { hide(); return; }
                expandButton.disabled = false;
                if (!note) {
                    note = el("div", "mg-hint mg-lora-status-error mg-wildcard-preview-expand-note");
                    container.insertBefore ? container.insertBefore(note, head.nextSibling ?? null) : container.appendChild(note);
                }
                note.textContent = outcome?.message || "Wildcard expansion failed";
            };
            head.appendChild(expandButton);
        }
        head.appendChild(close);
        container.appendChild(head);
        if (!data || data.ok !== true) {
            container.appendChild(el("div", "mg-hint", (data && data.error) || "Wildcard preview unavailable."));
        } else {
            const entries = Array.isArray(data.entries) ? data.entries : [];
            const list = el("ul", "mg-wildcard-preview-list");
            for (const entry of entries) list.appendChild(el("li", "", entry));
            container.appendChild(list);
            container.appendChild(el("div", "mg-hint mg-wildcard-preview-count", wildcardPreviewCountText(data)));
        }
        container.hidden = false;
        listen(true);
    };
    return { show, hide, get visible() { return !container.hidden; } };
}

/** "1 entry" / "24 entries"; past the read cap the true total is unknown and said so. */
export function wildcardPreviewCountText(data) {
    const shown = Array.isArray(data?.entries) ? data.entries.length : 0;
    if (data?.total === null || data?.total === undefined) {
        return `${shown} entr${shown === 1 ? "y" : "ies"} shown — file exceeds the preview read limit, total unknown`;
    }
    return `${data.total} entr${data.total === 1 ? "y" : "ies"}`;
}
