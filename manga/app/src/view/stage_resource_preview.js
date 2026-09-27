/**
 * Transient resource preview in the Stage (Card MANGA-RESOURCE-STAGE-HOVER-PREVIEW1).
 *
 * One overlay layer is appended to the existing Stage host.  It never replaces, hides or
 * mutates Stage content: showing it covers the Stage visually; hiding it simply reveals the
 * untouched Stage underneath, so nothing has to be snapshotted or restored.
 *
 * The overlay only mirrors an <img> that a resource card is ALREADY displaying (same URL,
 * served from the browser cache).  Missing / failed / not-yet-loaded thumbnails do nothing
 * except clear a previous overlay, so no fallback lookup or request storm can happen.
 * Hover never selects, adds, removes or changes any state.
 */

let controller = null;

export function mountStageResourcePreview(host, { doc = host?.ownerDocument } = {}) {
    if (!host || !doc) return null;
    const layer = doc.createElement("div");
    layer.className = "mg-stage-resource-preview";
    layer.hidden = true;
    layer.setAttribute("aria-hidden", "true");
    const image = doc.createElement("img");
    image.className = "mg-stage-resource-preview-image";
    image.alt = "";
    image.decoding = "async";
    const label = doc.createElement("span");
    label.className = "mg-stage-resource-preview-label";
    layer.append(image, label);
    host.append(layer);
    let owner = null;

    const hide = (from = null) => {
        if (from && owner && from !== owner) return;   // a stale leave never hides a newer hover
        owner = null;
        layer.hidden = true;
        image.removeAttribute?.("src");
        label.textContent = "";
    };

    const show = (source, text = "", from = null) => {
        const tag = String(source?.tagName || "").toLowerCase();
        const url = source?.currentSrc || source?.src || "";
        const displayed = tag === "img" && !source.hidden && source.isConnected !== false &&
            source.complete === true && Number(source.naturalWidth) > 0 && url;
        if (!displayed) { hide(); return false; }
        owner = from || source;
        image.src = url;
        label.textContent = String(text || "");
        label.hidden = !label.textContent;
        layer.hidden = false;
        return true;
    };

    controller = { show, hide, layer, image, label, get owner() { return owner; } };
    return controller;
}

export function getStageResourcePreview() { return controller; }

/** Test/teardown hook: forget the registered Stage host. */
export function resetStageResourcePreview() {
    controller?.hide();
    controller?.layer?.remove?.();
    controller = null;
}

/**
 * Bind hover inspection to one visible card thumbnail.  `getImage` returns the element the card
 * currently displays (an <img> or a NO PREVIEW placeholder).  No-op without a registered Stage.
 */
export function bindStagePreviewHover(target, { getImage, label = "" } = {}) {
    if (!target?.addEventListener || typeof getImage !== "function") return;
    target.addEventListener("pointerenter", () => controller?.show(getImage(), label, target));
    target.addEventListener("pointerleave", () => controller?.hide(target));
}

/** Cards are about to be rebuilt: a removed thumbnail can never fire pointerleave. */
export function clearStagePreview() { controller?.hide(); }
