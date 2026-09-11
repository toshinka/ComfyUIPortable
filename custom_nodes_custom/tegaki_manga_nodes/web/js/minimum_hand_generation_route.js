/**
 * minimum_hand_generation_route.js — Frontend Generation Route Preview Helper (M3B-PI2)
 * ====================================================================================
 * Pure preview helper for display/status in Minimum-Hand Scene Editor UI.
 * Mirrors the deterministic backend routing contract in product_generation_router.py:
 * - GUIDED_CLEAN_GLOBAL: >=1 enabled rough_manga guide with >=1 valid figure region.
 * - STANDARD_NO_GUIDE: all other cases.
 */

export const ROUTE_STANDARD = "STANDARD_NO_GUIDE";
export const ROUTE_GUIDED = "GUIDED_CLEAN_GLOBAL";

export const ROUTE_LABELS = {
    [ROUTE_STANDARD]: "Generation: Standard",
    [ROUTE_GUIDED]: "Generation: Guide-assisted"
};

/**
 * Evaluates the current Authoring Document to determine the generation route for preview/UI status.
 * @param {Object} document Authoring Document
 * @param {number} pageIndex 0-indexed page number (default 0)
 * @returns {{ route: string, displayLabel: string, reason: string, eligibleGuideCount: number, figureCount: number }}
 */
export function previewGenerationRoute(document, pageIndex = 0) {
    if (!document || !Array.isArray(document.pages) || pageIndex < 0 || pageIndex >= document.pages.length) {
        return {
            route: ROUTE_STANDARD,
            displayLabel: ROUTE_LABELS[ROUTE_STANDARD],
            reason: "Invalid document or page index",
            eligibleGuideCount: 0,
            figureCount: 0
        };
    }

    const page = document.pages[pageIndex];
    if (!page || typeof page !== "object") {
        return {
            route: ROUTE_STANDARD,
            displayLabel: ROUTE_LABELS[ROUTE_STANDARD],
            reason: "Invalid page object",
            eligibleGuideCount: 0,
            figureCount: 0
        };
    }

    const guides = Array.isArray(page.guides) ? page.guides : [];
    if (guides.length === 0) {
        return {
            route: ROUTE_STANDARD,
            displayLabel: ROUTE_LABELS[ROUTE_STANDARD],
            reason: "No guides present on page",
            eligibleGuideCount: 0,
            figureCount: 0
        };
    }

    let eligibleGuideCount = 0;
    let totalFigures = 0;
    let totalRoughGuides = 0;
    let disabledRoughGuides = 0;
    let zeroFigureRoughGuides = 0;

    for (const g of guides) {
        if (!g || typeof g !== "object") continue;
        if (g.guide_type !== "rough_manga") continue;

        totalRoughGuides++;
        const isEnabled = g.enabled !== false;
        if (!isEnabled) {
            disabledRoughGuides++;
            continue;
        }

        const figRegions = Array.isArray(g.figure_regions) ? g.figure_regions : [];
        const validFigs = figRegions.filter(f => {
            if (!f || typeof f !== "object" || !f.area) return false;
            const w = f.area.w;
            const h = f.area.h;
            return typeof w === "number" && typeof h === "number" && w > 0 && h > 0;
        });

        if (validFigs.length > 0) {
            eligibleGuideCount++;
            totalFigures += validFigs.length;
        } else {
            zeroFigureRoughGuides++;
        }
    }

    if (eligibleGuideCount > 0) {
        return {
            route: ROUTE_GUIDED,
            displayLabel: ROUTE_LABELS[ROUTE_GUIDED],
            reason: `Eligible rough_manga guide found with ${totalFigures} figure region(s)`,
            eligibleGuideCount,
            figureCount: totalFigures
        };
    }

    let reason = "No eligible rough_manga guide with valid figures";
    if (totalRoughGuides === 0) {
        reason = "No rough_manga guides present";
    } else if (disabledRoughGuides > 0 && eligibleGuideCount === 0) {
        reason = "Guide is disabled";
    } else if (zeroFigureRoughGuides > 0 && eligibleGuideCount === 0) {
        reason = "Guide has zero figure regions";
    }

    return {
        route: ROUTE_STANDARD,
        displayLabel: ROUTE_LABELS[ROUTE_STANDARD],
        reason,
        eligibleGuideCount: 0,
        figureCount: 0
    };
}
