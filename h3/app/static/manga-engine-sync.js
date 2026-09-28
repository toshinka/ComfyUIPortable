/**
 * H3 shell <-> embedded Manga workspace: engine selection and EasyReforge availability (pure; no DOM).
 * Card TEGAKI-MULTI-ENGINE-LAUNCHER-AND-AVAILABILITY-SYNC-1.
 *
 * Contract:
 *   - EASYREFORGE is operational exactly when the workspace reports `available === true`
 *     (the workspace derives it as installed && ready).  Ownership is irrelevant: a verified
 *     external Integration runtime (owned=false) is fully usable.
 *   - Every availability report replaces the previous one, so a late `available` converges the
 *     shell to ENABLED; there is no sticky false state and no timer.
 *   - The selected engine is user state: no message ever switches EASYREFORGE -> COMFYUI.
 *     The shell only re-sends its own pending/selected engine or mirrors the engine the frame uses.
 */
export const MANGA_FRAME_ENGINES = Object.freeze(["comfyui", "easyreforge"]);
export const UNAVAILABLE_TITLE = "Not available yet";

/** Normalise the `easyreforge` block of a frame availability message; null when malformed. */
export function easyreforgeAvailability(report) {
  if (!report || typeof report !== "object") return null;
  return {
    available: report.available === true,
    state: String(report.state || "unknown"),
    reason: String(report.reason || ""),
  };
}

/** Button presentation for the shell's EASYREFORGE engine control. */
export function easyreforgeControl(availability) {
  const available = availability?.available === true;
  return {
    disabled: !available,
    title: available ? "Legacy EasyReforge (MANGA only)" : (availability?.reason || UNAVAILABLE_TITLE),
  };
}

/**
 * Reduce one message from the Manga frame.
 *   shell: { creationMode, engine, pendingMangaEngine, easyreforge }
 * Returns { handled, easyreforge, pendingMangaEngine, post, mirror } where `post` is an engine the
 * shell must (re)send to the frame and `mirror` an engine the shell header must reflect.
 */
export function reduceMangaFrameMessage(shell, data) {
  const out = {
    handled: false,
    easyreforge: shell.easyreforge,
    pendingMangaEngine: shell.pendingMangaEngine ?? null,
    post: null,
    mirror: null,
  };
  const frameEngine = MANGA_FRAME_ENGINES.includes(data?.engine) ? data.engine : null;
  if (data?.type === "tegaki:manga-engine-availability") {
    const availability = easyreforgeAvailability(data.easyreforge);
    if (!availability) return out;
    out.handled = true;
    out.easyreforge = availability;
    if (out.pendingMangaEngine) {
      // The frame (re)loaded before applying the shell's request: send it again.
      if (frameEngine !== out.pendingMangaEngine) out.post = out.pendingMangaEngine;
    } else if (shell.creationMode === "manga" && shell.engine === "easyreforge"
        && frameEngine !== "easyreforge" && availability.available) {
      out.post = "easyreforge";   // frame reloaded: re-apply the user's selection (never a downgrade)
    } else {
      out.mirror = frameEngine;
    }
  } else if (data?.type === "tegaki:manga-engine-applied") {
    out.handled = true;
    out.pendingMangaEngine = null;
    out.mirror = frameEngine;
  }
  return out;
}
