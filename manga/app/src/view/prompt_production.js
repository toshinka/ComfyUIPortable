// Prompt Production UX (Card MANGA-PROMPT-PRODUCTION-UX1).
//
// A. Global prompt presets (Positive + Negative pairs) and B. a user default prompt are
//    USER/APPLICATION PREFERENCES kept in one versioned browser-local key.  They are
//    never written into the Authoring Document, Scenes, SceneResult or Page Composite,
//    and prompt text is stored verbatim (no Wildcard expansion, no LoRA resolution).
// C. Ctrl+ArrowUp / Ctrl+ArrowDown weight editing for (text:weight) groups and the
//    strength of a valid <lora:NAME:STRENGTH> token, applied as one undoable text edit.

import { LORA_STRENGTH_BOUNDS, findLoraTokens, formatLoraStrength } from "./lora_panel.js";

export const PROMPT_PREFS_KEY = "tegaki.manga.promptPrefs.v1";
export const MAX_PRESETS = 50;
// Same bound as the backend LoRA validation text limit; long prompts fit, nothing is truncated.
export const MAX_PROMPT_CHARS = 16000;
export const WEIGHT_STEP = 0.1;

function emptyPrefs() {
    return { version: 1, presets: [], default: null };
}

function validPair(pair) {
    return pair && typeof pair.positive === "string" && typeof pair.negative === "string";
}

function readPrefs(storage) {
    try {
        const raw = storage?.getItem(PROMPT_PREFS_KEY);
        if (!raw) return emptyPrefs();
        const data = JSON.parse(raw);
        if (!data || data.version !== 1 || !Array.isArray(data.presets)) return emptyPrefs();
        return {
            version: 1,
            presets: data.presets.filter(p => p && typeof p.name === "string" && validPair(p))
                .map(p => ({ name: p.name, positive: p.positive, negative: p.negative })),
            default: validPair(data.default) ? { positive: data.default.positive, negative: data.default.negative } : null,
        };
    } catch {
        return emptyPrefs();
    }
}

/**
 * Preset + default preference store.  Every mutation computes the next state, persists it,
 * and only then replaces the in-memory state: a failed write leaves old data intact.
 */
export function createPromptPrefs({ storage = (() => { try { return globalThis.localStorage; } catch { return null; } })() } = {}) {
    let state = readPrefs(storage);
    const commit = (next) => {
        try {
            if (!storage) throw new Error("Browser storage is unavailable");
            storage.setItem(PROMPT_PREFS_KEY, JSON.stringify(next));
        } catch (err) {
            return { ok: false, code: "STORAGE_FAILED", error: `Could not save prompt preferences (${err?.message || "storage error"}). Existing presets were kept.` };
        }
        state = next;
        return { ok: true };
    };
    const checkPair = (pair) => {
        if (!validPair(pair)) return { ok: false, code: "INVALID_PAIR", error: "Prompt pair is invalid" };
        if (pair.positive.length > MAX_PROMPT_CHARS || pair.negative.length > MAX_PROMPT_CHARS) {
            return { ok: false, code: "TOO_LARGE", error: `Prompt is longer than ${MAX_PROMPT_CHARS} characters; nothing was saved.` };
        }
        return null;
    };
    return {
        list: () => state.presets.map(p => ({ ...p })),
        get: (name) => { const p = state.presets.find(item => item.name === name); return p ? { ...p } : null; },
        getDefault: () => (state.default ? { ...state.default } : null),
        save(rawName, pair, { replace = false } = {}) {
            const name = String(rawName ?? "").trim();
            if (!name) return { ok: false, code: "EMPTY_NAME", error: "Enter a preset name." };
            if (name.length > 80) return { ok: false, code: "NAME_TOO_LONG", error: "Preset name is too long (max 80)." };
            const bad = checkPair(pair);
            if (bad) return bad;
            const exists = state.presets.some(p => p.name === name);
            if (exists && !replace) return { ok: false, code: "EXISTS", error: `"${name}" already exists. Replace it?` };
            if (!exists && state.presets.length >= MAX_PRESETS) {
                return { ok: false, code: "LIMIT", error: `Preset limit reached (${MAX_PRESETS}). Delete one first.` };
            }
            const entry = { name, positive: pair.positive, negative: pair.negative };
            const presets = exists ? state.presets.map(p => (p.name === name ? entry : p)) : [...state.presets, entry];
            return commit({ ...state, presets });
        },
        remove(name) {
            if (!state.presets.some(p => p.name === name)) return { ok: false, code: "MISSING", error: "Preset not found." };
            return commit({ ...state, presets: state.presets.filter(p => p.name !== name) });
        },
        setDefault(pair) {
            const bad = checkPair(pair);
            if (bad) return bad;
            return commit({ ...state, default: { positive: pair.positive, negative: pair.negative } });
        },
        clearDefault() {
            return commit({ ...state, default: null });
        },
    };
}

/**
 * Apply the custom default ONLY to the brand-new session document created at page start:
 * it must still hold the built-in Global pair and contain no Scenes/CAST.  Anything else
 * (imported, fixture, restored or edited work) is left untouched.
 */
export function applyDefaultToNewDocument(store, prefs, builtIn) {
    const custom = prefs.getDefault();
    const page = store.getPage();
    if (!custom || !page) return false;
    const pristine = page.style_prompt === builtIn.positive && page.style_negative_prompt === builtIn.negative &&
        !(page.scenes || []).length && !(page.cast || []).length;
    if (!pristine) return false;
    store.setStyleMetadata({ stylePrompt: custom.positive, styleNegativePrompt: custom.negative });
    return true;
}

// ---------------------------------------------------------------------------
// Ctrl+Up / Ctrl+Down weights
// ---------------------------------------------------------------------------

const NUMBER = "[-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)";
const WEIGHT_GROUP = new RegExp(`\\(([^()<>]*):(${NUMBER})\\)`, "g");

/** Compact, float-artifact-free weight text: 1, 1.1, 0.9, -0.2. */
export function formatPromptWeight(value) {
    const rounded = Math.round(Number(value) * 10000) / 10000;
    return String(Object.is(rounded, -0) ? 0 : rounded);
}

function stepped(current, direction) {
    return Math.round((current + direction * WEIGHT_STEP) * 10000) / 10000;
}

/** Explicit (text:number) groups without nested parentheses, with positions. */
export function findWeightGroups(text) {
    const groups = [];
    for (const match of String(text).matchAll(WEIGHT_GROUP)) {
        if (!match[1].trim()) continue;
        const start = match.index;
        const innerStart = start + 1;
        groups.push({ start, end: start + match[0].length, innerStart, innerEnd: innerStart + match[1].length,
            inner: match[1], weight: Number(match[2]) });
    }
    return groups.filter(g => Number.isFinite(g.weight));
}

/**
 * Compute ONE weight edit.  Returns { start, end, replacement, selStart, selEnd } in
 * original-text coordinates for the replaced range and the post-edit selection, or null
 * (no-op) when there is no supported, unambiguous target.
 */
export function computeWeightEdit(text, selStart, selEnd, direction) {
    const value = String(text ?? "");
    const dir = direction > 0 ? 1 : -1;
    const s = Math.max(0, Math.min(selStart, selEnd));
    const e = Math.min(value.length, Math.max(selStart, selEnd));
    const groups = findWeightGroups(value);
    const editGroup = (g, keepInnerSelected) => {
        const next = formatPromptWeight(stepped(g.weight, dir));
        const replacement = `(${g.inner}:${next})`;
        return keepInnerSelected
            ? { start: g.start, end: g.end, replacement, selStart: g.innerStart, selEnd: g.innerEnd }
            : { start: g.start, end: g.end, replacement, selStart: g.start, selEnd: g.start + replacement.length };
    };
    if (e > s) {
        const selected = value.slice(s, e);
        // exactly one whole group selected
        const whole = groups.find(g => g.start === s && g.end === e);
        if (whole) return editGroup(whole, false);
        // the inner text of a group selected (the state left after wrapping)
        const inner = groups.find(g => g.innerStart === s && g.innerEnd === e);
        if (inner) return editGroup(inner, true);
        // plain text only; anything with prompt syntax is left alone (no guessing)
        if (!selected.trim() || /[()[\]{}<>|:]/.test(selected) || /\n/.test(selected)) return null;
        const replacement = `(${selected}:${formatPromptWeight(1 + dir * WEIGHT_STEP)})`;
        return { start: s, end: e, replacement, selStart: s + 1, selEnd: s + 1 + selected.length };
    }
    // caret: smallest explicit group containing it
    const around = groups.filter(g => g.start <= s && s <= g.end).sort((a, b) => (a.end - a.start) - (b.end - b.start))[0];
    if (around) {
        const edit = editGroup(around, false);
        const caret = Math.min(s, around.start + edit.replacement.length);
        return { ...edit, selStart: caret, selEnd: caret };
    }
    // caret inside a valid LoRA token: step its strength within the accepted LoRA domain
    const lora = findLoraTokens(value).find(t => t.start <= s && s <= t.end);
    if (lora) {
        const next = stepped(lora.strength, dir);
        if (next < LORA_STRENGTH_BOUNDS.min || next > LORA_STRENGTH_BOUNDS.max) return null;
        let strengthText;
        try { strengthText = formatLoraStrength(next); } catch { return null; }
        const replacement = `<lora:${lora.id}:${strengthText}>`; // name kept byte-for-byte
        const caret = Math.min(s, lora.start + replacement.length);
        return { start: lora.start, end: lora.end, replacement, selStart: caret, selEnd: caret };
    }
    return null;
}

/** Replace a range as an undoable edit (execCommand) with an "input"-event fallback. */
export function applyTextEdit(textarea, { start, end, replacement, selStart, selEnd }, doc = globalThis.document) {
    const expected = textarea.value.slice(0, start) + replacement + textarea.value.slice(end);
    let done = false;
    try {
        textarea.focus?.();
        textarea.setSelectionRange(start, end);
        // execCommand edits the FOCUSED element; never use it unless that is this textarea
        // (e.g. a collapsed/hidden Negative field cannot take focus).
        if (doc?.activeElement === textarea) {
            done = Boolean(doc.execCommand?.("insertText", false, replacement)) && textarea.value === expected;
        }
    } catch { done = false; }
    if (!done) {
        textarea.value = expected;
        textarea.dispatchEvent(new Event("input", { bubbles: true }));
    }
    textarea.setSelectionRange(selStart, selEnd);
    return expected;
}

/** Replace the whole value as one undoable edit. */
export function replaceTextareaValue(textarea, value, doc = globalThis.document) {
    if (textarea.value === value) return;
    applyTextEdit(textarea, { start: 0, end: textarea.value.length, replacement: value, selStart: value.length, selEnd: value.length }, doc);
}

/** Ctrl+ArrowUp/Down on a prompt textarea; never during IME or while autocomplete owns the keys. */
export function attachWeightKeys(textarea, { isAutocompleteOpen = () => false, doc = globalThis.document } = {}) {
    const onKeydown = (event) => {
        if (event.key !== "ArrowUp" && event.key !== "ArrowDown") return;
        if (!(event.ctrlKey || event.metaKey) || event.altKey || event.shiftKey) return;
        if (event.isComposing || event.keyCode === 229) return;
        if (event.defaultPrevented || isAutocompleteOpen()) return;
        event.preventDefault();
        const edit = computeWeightEdit(textarea.value, textarea.selectionStart, textarea.selectionEnd,
            event.key === "ArrowUp" ? 1 : -1);
        if (edit) applyTextEdit(textarea, edit, doc);
    };
    textarea.addEventListener("keydown", onKeydown);
    return () => textarea.removeEventListener("keydown", onKeydown);
}

// ---------------------------------------------------------------------------
// Compact preset / default UI
// ---------------------------------------------------------------------------

function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}

/**
 * `getGlobalPair()` reads the current Global Positive/Negative from the document;
 * `applyGlobalPair(pair)` writes them through the existing prompt mutation path.
 */
export function mountPromptPresets({ container, prefs, getGlobalPair, applyGlobalPair }) {
    container.replaceChildren();
    const summary = el("summary", "mg-prompt-presets-summary", "Prompt presets");
    const row = el("div", "mg-prompt-presets-row");
    const select = el("select", "mg-prompt-preset-select");
    select.setAttribute("aria-label", "Prompt preset");
    const applyBtn = el("button", "mg-pp-btn", "Apply");
    const deleteBtn = el("button", "mg-pp-btn", "Delete");
    const nameInput = el("input", "mg-prompt-preset-name");
    nameInput.type = "text";
    nameInput.placeholder = "Preset name";
    nameInput.maxLength = 80;
    nameInput.setAttribute("aria-label", "New preset name");
    const saveBtn = el("button", "mg-pp-btn", "Save current");
    const row2 = el("div", "mg-prompt-presets-row");
    const setDefaultBtn = el("button", "mg-pp-btn", "Set current as default");
    const applyDefaultBtn = el("button", "mg-pp-btn", "Apply default");
    const clearDefaultBtn = el("button", "mg-pp-btn", "Clear custom default");
    const status = el("div", "mg-hint mg-prompt-presets-status");
    status.setAttribute("role", "status");
    for (const b of [applyBtn, deleteBtn, saveBtn, setDefaultBtn, applyDefaultBtn, clearDefaultBtn]) b.type = "button";
    row.append(select, applyBtn, deleteBtn, nameInput, saveBtn);
    row2.append(setDefaultBtn, applyDefaultBtn, clearDefaultBtn);
    container.append(summary, row, row2, status);

    let pendingReplace = null; // name awaiting explicit Replace
    let pendingDelete = null;  // name awaiting explicit Delete confirmation
    const say = (text, isError = false) => {
        status.textContent = text || "";
        status.classList.toggle("mg-lora-status-error", Boolean(isError));
    };
    const renderList = (selected = select.value) => {
        select.replaceChildren();
        const none = el("option", "", prefs.list().length ? "Choose preset…" : "No presets yet");
        none.value = "";
        select.appendChild(none);
        for (const p of prefs.list()) {
            const option = el("option", "", p.name);
            option.value = p.name;
            select.appendChild(option);
        }
        select.value = prefs.get(selected) ? selected : "";
        applyBtn.disabled = deleteBtn.disabled = !select.value;
        const hasDefault = Boolean(prefs.getDefault());
        applyDefaultBtn.disabled = clearDefaultBtn.disabled = !hasDefault;
        container.dataset.customDefault = hasDefault ? "on" : "off";
    };
    const resetConfirm = () => {
        pendingReplace = null;
        pendingDelete = null;
        saveBtn.textContent = "Save current";
        deleteBtn.textContent = "Delete";
    };
    select.onchange = () => { resetConfirm(); renderList(select.value); say(""); };
    nameInput.oninput = () => { if (pendingReplace) resetConfirm(); };
    applyBtn.onclick = () => {
        const preset = prefs.get(select.value);
        if (!preset) return;
        resetConfirm();
        applyGlobalPair({ positive: preset.positive, negative: preset.negative });
        say(`Applied "${preset.name}" to the Global prompt.`);
    };
    deleteBtn.onclick = () => {
        const name = select.value;
        if (!name) return;
        if (pendingDelete !== name) {
            resetConfirm();
            pendingDelete = name;
            deleteBtn.textContent = "Confirm delete";
            say(`Delete preset "${name}"? Click Confirm delete. The current prompt is not changed.`);
            return;
        }
        const result = prefs.remove(name);
        resetConfirm();
        renderList("");
        say(result.ok ? `Deleted preset "${name}".` : result.error, !result.ok);
    };
    saveBtn.onclick = () => {
        const name = nameInput.value.trim();
        const replace = pendingReplace !== null && pendingReplace === name;
        const result = prefs.save(name, getGlobalPair(), { replace });
        if (!result.ok && result.code === "EXISTS") {
            pendingReplace = name;
            pendingDelete = null;
            deleteBtn.textContent = "Delete";
            saveBtn.textContent = "Replace";
            say(`"${name}" already exists. Click Replace to overwrite it, or change the name.`, true);
            return;
        }
        resetConfirm();
        if (!result.ok) { say(result.error, true); return; }
        nameInput.value = "";
        renderList(name);
        say(`${replace ? "Replaced" : "Saved"} preset "${name}".`);
    };
    setDefaultBtn.onclick = () => {
        resetConfirm();
        const result = prefs.setDefault(getGlobalPair());
        renderList();
        say(result.ok ? "Current Global prompt saved as the default for new documents." : result.error, !result.ok);
    };
    applyDefaultBtn.onclick = () => {
        resetConfirm();
        const pair = prefs.getDefault();
        if (!pair) return;
        applyGlobalPair(pair);
        say("Applied the custom default to the Global prompt.");
    };
    clearDefaultBtn.onclick = () => {
        resetConfirm();
        const result = prefs.clearDefault();
        renderList();
        say(result.ok ? "Custom default cleared; new documents use the built-in prompt." : result.error, !result.ok);
    };
    renderList("");
    return { refresh: () => renderList() };
}
