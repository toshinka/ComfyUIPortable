// Prompt Assist (Card MANGA-PROMPT-ASSIST-PRODUCTION1): one compact area under the
// Positive Prompt that switches between the LoRA browser and a Wildcard browser.
//
// Wildcards come from the existing Manga owner (/api/manga/wildcards via
// loadWildcardCatalog, the same cached list the autocomplete uses) and are
// inserted as the existing visible `__name__` token.  Expansion stays in the
// backend compiler; nothing here parses or expands wildcard contents.

import { LOAD_FAILED, insertWildcardAtCursor, loadWildcardCatalog } from "./tag_autocomplete.js";

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
