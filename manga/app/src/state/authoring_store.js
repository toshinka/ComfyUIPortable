/**
 * authoring_store.js — Authoring Document Store & IO Manager
 * ==========================================================
 * TEGAKI Manga Authoring Workspace (M1A)
 * 
 * Invariants:
 * - Owns the current TEGAKI_AUTHORING_DOCUMENT 1.0.0.
 * - Enforces schema validation on import and set.
 * - Protects document from session state pollution during export.
 */

import {
    createDefaultAuthoringDocument,
    createRichAuthoringFixture,
    validateAuthoringDocument,
    cloneDocument
} from "../domain/authoring_document.js";

export class AuthoringStore {
    constructor(initialDoc = null) {
        this.document = initialDoc ? cloneDocument(initialDoc) : createDefaultAuthoringDocument();
        this.listeners = new Set();
    }

    getDocument() {
        return cloneDocument(this.document);
    }

    getPage(pageIndex = 0) {
        return this.document.pages[pageIndex] || null;
    }

    setDocument(newDoc) {
        const validation = validateAuthoringDocument(newDoc);
        if (!validation.valid) {
            throw new Error("Invalid authoring document: " + validation.errors.join(", "));
        }
        this.document = cloneDocument(newDoc);
        this.notify();
    }

    resetDefault() {
        this.setDocument(createDefaultAuthoringDocument());
    }

    loadRichFixture() {
        this.setDocument(createRichAuthoringFixture());
    }

    exportJson(pretty = true) {
        // Enforce validation before export
        const validation = validateAuthoringDocument(this.document);
        if (!validation.valid) {
            throw new Error("Cannot export invalid document: " + validation.errors.join(", "));
        }
        return pretty ? JSON.stringify(this.document, null, 2) : JSON.stringify(this.document);
    }

    importJson(jsonString) {
        let parsed;
        try {
            parsed = JSON.parse(jsonString);
        } catch (e) {
            return { ok: false, error: "JSON parse error: " + e.message };
        }
        const validation = validateAuthoringDocument(parsed);
        if (!validation.valid) {
            return { ok: false, error: validation.errors.join("; ") };
        }
        this.setDocument(parsed);
        return { ok: true, document: this.getDocument() };
    }

    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    notify() {
        for (const listener of this.listeners) {
            try {
                listener(this.getDocument());
            } catch (err) {
                console.error("[AuthoringStore listener error]", err);
            }
        }
    }
}
