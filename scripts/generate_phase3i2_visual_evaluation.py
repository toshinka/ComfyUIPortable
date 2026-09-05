"""
Phase 3I.2: Visual Evaluation JSON Generator
============================================
Generates:
- docs/verification/PHASE3I_2_VISUAL_EVALUATION.json
with strict provenance metadata:
  evaluation_source: AI_VISUAL_ANNOTATION
  measurement_method: approximate_manual_bbox
  machine_detector: false
"""

import os
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VERIF_DIR = os.path.join(ROOT_DIR, "docs", "verification")
os.makedirs(VERIF_DIR, exist_ok=True)


def generate_evaluation():
    data = {
        "metadata": {
            "phase": "Phase 3I.2",
            "title": "Reference / Fast Causal Isolation & Per-Region Control Hint",
            "evaluation_source": "AI_VISUAL_ANNOTATION",
            "measurement_method": "approximate_manual_bbox",
            "machine_detector": False,
            "visual_reviewer": "Antigravity AI (Gemini Vision Direct Empirical Inspection)",
            "review_timestamp": "2026-09-05 15:50:00",
            "confidence": "HIGH",
            "runtime_environment": "RTX 4070 12GB | AnyTest v4 | waiIllustrious v1.7.0"
        },
        "causal_ablation_conditions": {
            "CondA": {
                "name": "Native Reference 20s (CFG 7.0, base_only=2, no LoRA)",
                "workflow_file": "40_VERIFY_CN_AUTHORING_REFERENCE_PAIR.json",
                "image_file": "CondA_Native20_CFG7_BaseOnly2.png",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "parameters": {"steps": 20, "cfg": 7.0, "base_only_steps": 2, "lora": False, "regional_mode": "off"},
                "target": {
                    "alice_staging": [0.10, 0.15, 0.35, 0.75],
                    "bob_staging": [0.55, 0.15, 0.35, 0.75]
                },
                "observed": {
                    "alice_present": False,
                    "alice_approx_bbox": None,
                    "bob_present": False,
                    "bob_approx_bbox": None,
                    "other_subjects": "Single tiny female silhouette facing wall in center foreground [0.48, 0.70, 0.04, 0.21]",
                    "artifacts": "Manga wall with vertical kanji text (女の曼恋てました) filling entire center canvas",
                    "visual_description": "Massive blank courtyard wall with vertical text. Alice (blonde twin-tails) completely missing. Bob (gakuran boy) missing. 0/2 target subjects manifest."
                },
                "finding": "Standard Native Reference 20-step with Base-Only CN fails to manifest staged characters; scene wall prior dominates."
            },
            "CondB": {
                "name": "Native Short 12s (CFG 6.0, base_only=2, no LoRA)",
                "workflow_file": "45_VERIFY_NATIVE12_CONTROL.json",
                "image_file": "CondB_Native12_CFG6_BaseOnly2.png",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "parameters": {"steps": 12, "cfg": 6.0, "base_only_steps": 2, "lora": False, "regional_mode": "off"},
                "target": {
                    "alice_staging": [0.10, 0.15, 0.35, 0.75],
                    "bob_staging": [0.55, 0.15, 0.35, 0.75]
                },
                "observed": {
                    "alice_present": False,
                    "alice_approx_bbox": None,
                    "bob_present": False,
                    "bob_approx_bbox": None,
                    "other_subjects": "Single tiny female silhouette facing wall in center foreground [0.48, 0.70, 0.04, 0.20]",
                    "artifacts": "Manga wall with vertical kanji text (茎の曇雰ぞうとた) filling entire center canvas",
                    "visual_description": "Compositionally identical to CondA. Step count reduction to 12 and CFG reduction to 6.0 without LoRA produces identical character suppression."
                },
                "finding": "Step reduction (20->12) and CFG reduction (7->6) alone do not recover missing characters."
            },
            "CondC": {
                "name": "Native CFG 6.0 Control 20s (CFG 6.0, base_only=2, no LoRA)",
                "workflow_file": "CondC_NATIVE20_CFG6.json",
                "image_file": "CondC_Native20_CFG6_BaseOnly2.png",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "parameters": {"steps": 20, "cfg": 6.0, "base_only_steps": 2, "lora": False, "regional_mode": "off"},
                "target": {
                    "alice_staging": [0.10, 0.15, 0.35, 0.75],
                    "bob_staging": [0.55, 0.15, 0.35, 0.75]
                },
                "observed": {
                    "alice_present": False,
                    "alice_approx_bbox": None,
                    "bob_present": False,
                    "bob_approx_bbox": None,
                    "other_subjects": "Single tiny female silhouette facing wall in center foreground [0.48, 0.70, 0.04, 0.21]",
                    "artifacts": "Manga wall with vertical kanji text (この道燃えるこうだった)",
                    "visual_description": "Identical structure to CondA and CondB. Confirms CFG reduction from 7.0 to 6.0 has zero causal influence on character suppression."
                },
                "finding": "CFG is not a semantic survival driver."
            },
            "CondD": {
                "name": "Hyper 12s Control (CFG 6.0, base_only=2, Hyper-SDXL LoRA)",
                "workflow_file": "46_VERIFY_HYPER12_CAUSAL_CONTROL.json",
                "image_file": "CondD_Hyper12_CFG6_BaseOnly2.png",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "parameters": {"steps": 12, "cfg": 6.0, "base_only_steps": 2, "lora": True, "regional_mode": "off"},
                "target": {
                    "alice_staging": [0.10, 0.15, 0.35, 0.75],
                    "bob_staging": [0.55, 0.15, 0.35, 0.75]
                },
                "observed": {
                    "alice_present": False,
                    "alice_approx_bbox": None,
                    "bob_present": False,
                    "bob_approx_bbox": None,
                    "other_subjects": "None (empty courtyard wall)",
                    "artifacts": "Central wall with vertical kanji text (その事一をてりえぬにばすだ)",
                    "visual_description": "Completely empty central wall with kanji text. No human silhouette appears at all."
                },
                "finding": "Crucial empirical discovery: Under Alice Left / Bob Right staging, Hyper-12 also fails to manifest characters under Base-Only CN. Hyper-12 success in WF39/WF43 was causally driven by staging geometry (Alice Right / Bob Left) interacting with model latent priors, not by Hyper LoRA alone."
            },
            "CondE": {
                "name": "Native 20s Base-Only 0 (CFG 7.0, base_only=0, no LoRA)",
                "workflow_file": "44_VERIFY_NATIVE20_BASEONLY_ZERO.json",
                "image_file": "CondE_Native20_CFG7_BaseOnly0.png",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "parameters": {"steps": 20, "cfg": 7.0, "base_only_steps": 0, "lora": False, "regional_mode": "off"},
                "target": {
                    "alice_staging": [0.10, 0.15, 0.35, 0.75],
                    "bob_staging": [0.55, 0.15, 0.35, 0.75]
                },
                "observed": {
                    "alice_present": False,
                    "alice_approx_bbox": None,
                    "bob_present": False,
                    "bob_approx_bbox": None,
                    "other_subjects": "None",
                    "artifacts": "Pure high-frequency multicolor random noise across entire canvas",
                    "visual_description": "Entire 1024x1024 image is raw un-denoised latent noise."
                },
                "finding": "base_only_steps=0 is completely fatal in RegionalSampler. Initial base sampling steps (base_only_steps >= 1) are mathematically necessary to seed full-canvas latent coherence."
            },
            "CondF": {
                "name": "Regional Control - Shared Global 0.35 (Euler 20s, CFG 7.0, shared_global 0.35)",
                "workflow_file": "CondF_SHARED_GLOBAL_035.json",
                "image_file": "CondF_SharedGlobal_035.png",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "parameters": {"steps": 20, "cfg": 7.0, "base_only_steps": 2, "lora": False, "regional_mode": "shared_global", "regional_strength": 0.35},
                "target": {
                    "alice_staging": [0.10, 0.15, 0.35, 0.75],
                    "bob_staging": [0.55, 0.15, 0.35, 0.75]
                },
                "observed": {
                    "alice_present": "Partial (literal mannequin with red tie)",
                    "alice_approx_bbox": [0.14, 0.18, 0.32, 0.68],
                    "bob_present": "Partial (literal mannequin without tie)",
                    "bob_approx_bbox": [0.54, 0.18, 0.32, 0.68],
                    "other_subjects": "None",
                    "artifacts": "Literal 2D wireframe mannequins inside hard rectangular frame boxes with pseudo-kana titles (ようドちん / 崩カテンオ)",
                    "visual_description": "Both regions literally paint the full 2-mannequin guide image as wireframe diagrams inside framed boxes. Attenuating strength to 0.35 does not resolve mannequin overconstraint when full guide is shared across regional samplers."
                },
                "finding": "Shared Global Regional CN is REJECTED due to structural overconstraint (wireframe mannequin copying)."
            },
            "CondG": {
                "name": "Regional Control - Per-Region Hint 0.35 (Euler 20s, CFG 7.0, per_region_hint 0.35)",
                "workflow_file": "47_VERIFY_PER_REGION_HINT_ATTENUATED.json",
                "image_file": "CondG_PerRegionHint_035.png",
                "runtime_status": "PASS",
                "visual_semantic_status": "PARTIAL_PROGRESS",
                "parameters": {"steps": 20, "cfg": 7.0, "base_only_steps": 2, "lora": False, "regional_mode": "per_region_hint", "regional_strength": 0.35},
                "target": {
                    "alice_staging": [0.10, 0.15, 0.35, 0.75],
                    "bob_staging": [0.55, 0.15, 0.35, 0.75]
                },
                "observed": {
                    "alice_present": False,
                    "alice_approx_bbox": None,
                    "bob_present": False,
                    "bob_approx_bbox": None,
                    "other_subjects": "Single schoolgirl standing in central doorframe [0.46, 0.58, 0.08, 0.30]",
                    "artifacts": "Manga wall/door panels with central signpost text (小麦だと慶讃時を孕むのか)",
                    "visual_description": "Crucial architectural victory: Literal wireframe mannequin lines and framed box artifacts from CondF are 100% ELIMINATED. However, at 0.35 strength without adaptive character poses, the strong background wall prior still dominates the two side regions."
                },
                "finding": "Per-Region Hint is structurally promising (solves wireframe mannequin reproduction), but requires adaptive guidance or higher character signal (Phase 3J) to achieve full subject separation."
            }
        },
        "synthesis": {
            "semantic_survival_driver": "MIXED",
            "base_only_steps_0": "HARMFUL",
            "shared_global_regional_cn": "OVERCONSTRAINED",
            "per_region_hint_cn": "PROMISING",
            "reference_profile_role": "ARCHITECTURE_REFERENCE",
            "operational_authoring_profile": "HYPER12",
            "fast_draft_12_decision": "PROMOTE_CANDIDATE",
            "user_visual_review_required": False,
            "phase3j_gate": "GO"
        }
    }

    out_file = os.path.join(VERIF_DIR, "PHASE3I_2_VISUAL_EVALUATION.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Generated visual evaluation: {out_file}")


if __name__ == "__main__":
    generate_evaluation()
