/** M3B-LR1 pure Guide operation checks. */
import assert from "node:assert";
import {
    getNextGuideId,
    getNextFigureId,
    calculateContainPlacement,
    clampGuideFigureArea,
    clampGuideFigureDrag,
    resizeGuideFigure,
    calculateNewGuideFigureArea,
    createGuideFigure,
    associateGuideFigure,
    unassignGuideInstance
} from "../custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_authoring_ops.js";

const placement = calculateContainPlacement(1600, 900, 832, 1216);
assert.deepStrictEqual(placement, {
    shape_type: "rect",
    x: 0,
    y: 0.3076,
    w: 1,
    h: 0.3849
});

assert.strictEqual(getNextGuideId([{ guide_id: "guide_1" }, { guide_id: "guide_4" }]), "guide_5");
assert.strictEqual(getNextFigureId([{ figure_id: "figure_1" }, { figure_id: "figure_3" }]), "figure_4");

const clamped = clampGuideFigureArea({ x: -0.2, y: 0.9, w: 0.5, h: 0.5 });
assert.deepStrictEqual(clamped, { shape_type: "rect", x: 0, y: 0.5, w: 0.5, h: 0.5 });
assert.deepStrictEqual(clampGuideFigureDrag({ x: 0.1, y: 0.1, w: 0.3, h: 0.3 }, 0.9, -0.2), { x: 0.7, y: 0 });
assert.deepStrictEqual(resizeGuideFigure({ x: 0.2, y: 0.2, w: 0.3, h: 0.3 }, "se", 0.2, 0.1), {
    shape_type: "rect", x: 0.2, y: 0.2, w: 0.5, h: 0.4
});

const figure = createGuideFigure([]);
assert.strictEqual(figure.figure_id, "figure_1");
assert.deepStrictEqual(figure.area, calculateNewGuideFigureArea([]));

const guide = {
    guide_id: "guide_1",
    figure_regions: [figure, { figure_id: "figure_2", area: calculateNewGuideFigureArea([figure]), instance_id: null }]
};
let associated = associateGuideFigure(guide, "figure_1", "inst_1");
assert.strictEqual(associated.ok, true);
associated = associateGuideFigure(associated.guide, "figure_2", "inst_1");
assert.strictEqual(associated.ok, false);
assert.strictEqual(associated.reason, "DUPLICATE_INSTANCE_ASSOCIATION");
const unassigned = unassignGuideInstance({ ...guide, figure_regions: [{ ...figure, instance_id: "inst_1" }] }, "inst_1");
assert.strictEqual(unassigned.figure_regions[0].instance_id, null);

console.log("M3B-LR1 Guide operations: PASS");
