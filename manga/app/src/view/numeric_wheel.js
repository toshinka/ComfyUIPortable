/**
 * TEGAKI Numeric Wheel Control Helper
 *
 * Implements the reusable TEGAKI numeric-control interaction convention:
 * - Direct typing remains available.
 * - Native keyboard navigation (Arrow Up/Down) is preserved.
 * - Mouse wheel adjustments occur ONLY when the input has keyboard focus.
 * - Wheel up increases value by step; wheel down decreases.
 * - Respects declared min and max bounds without wrapping.
 * - Formats to step decimal precision to avoid floating-point artifacts.
 * - Consumes the wheel event and prevents page scrolling only when the focused field consumes it.
 * - Preserves normal page scrolling outside eligible focused fields or when unfocused.
 * - Does not change disabled or read-only inputs.
 * - Preserves modifier keys (Ctrl/Alt/Meta) for browser zoom and accessibility.
 * - Supports an optional canUpdate(candidateVal, input) validator to reject invalid transitions (e.g. Start < End).
 */

export function setupNumericWheelControl(input, options = {}) {
    if (!input) return;

    function handleWheel(e) {
        // Safety: Change value only while the numeric input has keyboard focus
        if (document.activeElement !== input) return;

        // Safety: Never modify disabled or read-only inputs
        if (input.disabled || input.readOnly) return;

        // Safety: Do not interfere with browser zoom (Ctrl+wheel) or other modifier combinations
        if (e.ctrlKey || e.altKey || e.metaKey) return;

        // Ignore pure horizontal wheel events
        if (!e.deltaY) return;

        // Prevent page scrolling while adjusting the focused numeric control
        e.preventDefault();
        e.stopPropagation();

        const step = options.step !== undefined ? options.step : (parseFloat(input.step) || 1);
        const min = options.min !== undefined ? options.min : (input.min !== "" ? parseFloat(input.min) : -Infinity);
        const max = options.max !== undefined ? options.max : (input.max !== "" ? parseFloat(input.max) : Infinity);

        let current = parseFloat(input.value);
        if (!Number.isFinite(current)) {
            current = Number.isFinite(min) ? min : 0;
        }

        const direction = e.deltaY < 0 ? 1 : -1;
        let candidate = current + direction * step;

        // Calculate decimal places to eliminate floating-point artifacts (e.g. 0.35 + 0.05 = 0.4)
        const stepStr = String(step);
        const decimals = stepStr.includes(".") ? stepStr.split(".")[1].length : 0;
        candidate = parseFloat(candidate.toFixed(decimals));

        // Respect min and max boundaries without wrapping
        if (candidate < min) candidate = min;
        if (candidate > max) candidate = max;

        // If at boundary and no change, do nothing
        if (candidate === current) return;

        // Validate candidate before applying (e.g. Start must remain strictly less than End)
        if (typeof options.canUpdate === "function") {
            if (!options.canUpdate(candidate, input)) {
                return; // Reject step, keep last valid value
            }
        }

        input.value = String(candidate);
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));

        if (typeof options.onUpdate === "function") {
            options.onUpdate(candidate, input);
        }
    }

    input.addEventListener("wheel", handleWheel, { passive: false });

    return () => {
        input.removeEventListener("wheel", handleWheel);
    };
}
