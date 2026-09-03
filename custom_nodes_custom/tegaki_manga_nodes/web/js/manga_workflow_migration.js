/**
 * Tegaki Manga Workflow Migration & Widget Compatibility Extension (Phase 3B.1.1)
 * 
 * 過去のワークフロー (Phase 3B, Phase 3B.1 initial) に保存された TegakiMangaConditioningBuilder の
 * widgets_values を自動検知し、Append-Only Canonical 順序へ透過的にマイグレーション・NaN自動修復します。
 */

import { app } from "../../../scripts/app.js";

function migrateConditioningBuilderValues(wv) {
    if (!Array.isArray(wv)) return wv;

    // 1. Generation 1 (Legacy Phase 3B): [1.0, 1.0, "default"] (長さ 3)
    if (wv.length === 3 && typeof wv[0] === "number" && typeof wv[1] === "number" && typeof wv[2] === "string") {
        console.warn("[Tegaki] Migrated ConditioningBuilder widgets_values: Phase 3B -> Canonical Phase 3B.1.1", wv);
        return [wv[0], wv[1], wv[2], 1.0, 0];
    }

    // 2. Generation 2 (Phase 3B.1 initial): [1.0, 1.0, 1.0, "default", 0] (長さ 5 で index 2 が数値, index 3 が文字列)
    if (wv.length >= 5 && typeof wv[2] === "number" && typeof wv[3] === "string") {
        console.warn("[Tegaki] Migrated ConditioningBuilder widgets_values: Phase 3B.1 initial -> Canonical Phase 3B.1.1", wv);
        const p = wv[0];
        const c = wv[1];
        const lr = wv[2];
        const area = wv[3];
        const feather = typeof wv[4] === "number" ? wv[4] : 0;
        return [p, c, area, lr, feather];
    }

    // 3. Generation 3 (Canonical Phase 3B.1.1): [1.0, 1.0, "default", 1.0, 0]
    // NaN や不正な文字列が紛れ込んでいる場合の安全自動修復
    if (wv.length >= 3) {
        let p = Number(wv[0]);
        let c = Number(wv[1]);
        let area = typeof wv[2] === "string" ? wv[2] : "default";
        let lr = wv.length > 3 ? Number(wv[3]) : 1.0;
        let feather = wv.length > 4 ? Number(wv[4]) : 0;

        let healed = false;
        if (isNaN(p) || !isFinite(p)) { p = 1.0; healed = true; }
        if (isNaN(c) || !isFinite(c)) { c = 1.0; healed = true; }
        if (isNaN(lr) || !isFinite(lr)) { lr = 1.0; healed = true; }
        if (isNaN(feather) || !isFinite(feather)) { feather = 0; healed = true; }

        if (healed || wv.length < 5) {
            console.warn("[Tegaki] Healed NaN/incomplete widgets_values in ConditioningBuilder -> Canonical", [p, c, area, lr, feather]);
            return [p, c, area, lr, feather];
        }
    }

    return wv;
}

app.registerExtension({
    name: "Tegaki.WorkflowMigration",

    // A. ワークフローデータ読み込み時の生データ変換 (beforeConfigureGraph)
    async beforeConfigureGraph(graphData) {
        if (!graphData || !Array.isArray(graphData.nodes)) return;

        for (const node of graphData.nodes) {
            if (node.type === "TegakiMangaConditioningBuilder" && node.widgets_values) {
                node.widgets_values = migrateConditioningBuilderValues(node.widgets_values);
            }
        }
    },

    // B. ノード構築時のフック (nodeCreated / onConfigure)
    async nodeCreated(node) {
        if (node.comfyClass === "TegakiMangaConditioningBuilder") {
            const origOnConfigure = node.onConfigure;
            node.onConfigure = function (info) {
                if (info && info.widgets_values) {
                    info.widgets_values = migrateConditioningBuilderValues(info.widgets_values);
                }
                if (origOnConfigure) {
                    origOnConfigure.apply(this, arguments);
                }
                // Widget への値同期と NaN 防御
                if (this.widgets && this.widgets.length >= 5) {
                    const wv = this.widgets_values || [];
                    if (wv.length >= 5) {
                        for (let i = 0; i < Math.min(this.widgets.length, wv.length); i++) {
                            if (this.widgets[i] && wv[i] !== undefined) {
                                if (typeof this.widgets[i].value === "number" && (isNaN(wv[i]) || !isFinite(wv[i]))) {
                                    this.widgets[i].value = (i === 4 ? 0 : 1.0);
                                } else {
                                    this.widgets[i].value = wv[i];
                                }
                            }
                        }
                    }
                }
            };
        }
    }
});
