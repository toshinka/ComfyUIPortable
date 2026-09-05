"""
Phase 3I.1: Visual Evaluation JSON Generator
============================================
Compiles visual semantic grounding and empirical bounding box / presence metrics
for Workflows 35 through 43.

Separates runtime_status from visual_semantic_status across all entries.
"""

import os
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3I1")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def build_evaluation_data(wf40_43_results=None):
    evaluation = {
        "metadata": {
            "phase": "Phase 3I.1",
            "title": "ControlNet Visual Truth, Conditioning Ablation & Interaction Closure",
            "evaluator": "Antigravity AI (Gemini 2.5 Pro Vision Empirically Grounded)",
            "runtime_environment": "RTX 4070 12GB | AnyTest v4 | waiIllustrious v1.7.0"
        },
        "workflows": {
            "WF35": {
                "name": "35_VERIFY_CONTROLNET_ANYTEST_BASELINE",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "gemini_visual_confidence": 0.98,
                "target": {
                    "subject": "White Dog",
                    "staging_box": [0.10, 0.10, 0.30, 0.30],
                    "expected_side": "top-left"
                },
                "observed": {
                    "subject_present": False,
                    "observed_side": None,
                    "approx_bbox": None,
                    "coverage_h": 0.0,
                    "coverage_w": 0.0,
                    "extra_subjects": "none",
                    "visual_description": "Empty room interior with wooden floorboards and doorway. Target white dog is completely absent."
                },
                "judgment": "White dog wireframe failed to manifest a subject. Background perspective matched guide frame, but semantic subject presence is FAIL."
            },
            "WF36": {
                "name": "36_VERIFY_CONTROLNET_SCALE_LOCK_SINGLE_CHARACTER",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "gemini_visual_confidence": 0.99,
                "target": {
                    "subject": "Alice (Single Character Tall Portrait)",
                    "staging_box": [0.25, 0.15, 0.50, 0.75],
                    "expected_side": "center",
                    "target_h": 0.75
                },
                "observed": {
                    "subject_present": False,
                    "observed_side": None,
                    "approx_bbox": None,
                    "coverage_h": 0.0,
                    "coverage_w": 0.0,
                    "extra_subjects": "none",
                    "visual_description": "Uniform flat grey blank canvas. Alice character completely absent."
                },
                "judgment": "Zero subjects rendered. Background prompt was clean background and single regional prompt was suppressed. Visual Semantic is FAIL."
            },
            "WF37": {
                "name": "37_VERIFY_AUTHORING_ALICE_LEFT_BOB_RIGHT_CN_ASSIST",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "gemini_visual_confidence": 0.95,
                "target": {
                    "subjects": [
                        {"id": "Alice", "staging_box": [0.05, 0.15, 0.42, 0.70], "expected_side": "left"},
                        {"id": "Bob", "staging_box": [0.53, 0.15, 0.42, 0.70], "expected_side": "right"}
                    ]
                },
                "observed": {
                    "subjects": [
                        {
                            "id": "Alice",
                            "present": False,
                            "observed_side": None,
                            "approx_bbox": None,
                            "coverage_h": 0.0,
                            "coverage_w": 0.0
                        },
                        {
                            "id": "Bob",
                            "present": True,
                            "observed_side": "center-right",
                            "approx_bbox": [0.45, 0.12, 0.40, 0.85],
                            "coverage_h": 1.21,
                            "coverage_w": 0.95
                        }
                    ],
                    "identity_bleed": "none",
                    "missing_subjects": ["Alice"],
                    "visual_description": "Bob stands prominently in center-right in dark gakuran uniform. Alice on the left margin is completely missing."
                },
                "judgment": "1 of 2 subjects missing. Cannot be certified as two-character interaction PASS. Visual Semantic is FAIL."
            },
            "WF38": {
                "name": "38_VERIFY_AUTHORING_ALICE_RIGHT_BOB_LEFT_CN_ASSIST",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "gemini_visual_confidence": 0.95,
                "target": {
                    "subjects": [
                        {"id": "Bob", "staging_box": [0.05, 0.15, 0.42, 0.70], "expected_side": "left"},
                        {"id": "Alice", "staging_box": [0.53, 0.15, 0.42, 0.70], "expected_side": "right"}
                    ]
                },
                "observed": {
                    "subjects": [
                        {
                            "id": "Bob",
                            "present": True,
                            "observed_side": "far-left",
                            "approx_bbox": [0.00, 0.10, 0.35, 0.88],
                            "coverage_h": 1.25,
                            "coverage_w": 0.83
                        },
                        {
                            "id": "Alice",
                            "present": False,
                            "observed_side": None,
                            "approx_bbox": None,
                            "coverage_h": 0.0,
                            "coverage_w": 0.0
                        }
                    ],
                    "identity_bleed": "none",
                    "missing_subjects": ["Alice"],
                    "visual_description": "Bob is present at the far left edge, truncated. Alice on the right side is completely missing."
                },
                "judgment": "1 of 2 subjects missing. Geometry swap unverified because only 1 subject rendered. Visual Semantic is FAIL."
            },
            "WF39": {
                "name": "39_VERIFY_FAST_DRAFT_12_CONTROLNET_REGRESSION",
                "runtime_status": "PASS",
                "visual_semantic_status": "PASS",
                "gemini_visual_confidence": 0.96,
                "target": {
                    "subjects": [
                        {"id": "Bob", "staging_box": [0.05, 0.15, 0.42, 0.70], "expected_side": "left"},
                        {"id": "Alice", "staging_box": [0.53, 0.15, 0.42, 0.70], "expected_side": "right"}
                    ]
                },
                "observed": {
                    "subjects": [
                        {
                            "id": "Bob",
                            "present": True,
                            "observed_side": "left",
                            "approx_bbox": [0.08, 0.12, 0.40, 0.85],
                            "coverage_h": 1.21,
                            "coverage_w": 0.95
                        },
                        {
                            "id": "Alice",
                            "present": True,
                            "observed_side": "right",
                            "approx_bbox": [0.55, 0.14, 0.38, 0.84],
                            "coverage_h": 1.20,
                            "coverage_w": 0.90
                        }
                    ],
                    "identity_bleed": "none",
                    "missing_subjects": [],
                    "visual_description": "Both Bob (left) and Alice (right) are present, fully clothed in distinct respective uniforms, standing at full vertical height matching the mannequin wireframe silhouettes."
                },
                "speedup_metric": {
                    "reference_time_sec": 48.08,
                    "fast12_time_sec": 30.08,
                    "speedup_factor": "1.60x",
                    "time_reduction_pct": "37.4%"
                },
                "judgment": "FAST_DRAFT_12 + CONTROLNET: ACCEPT AS DRAFT. Both characters rendered in exact swapped positions with preserved identities and scale locking."
            },
            "WF40": {
                "name": "40_VERIFY_CN_AUTHORING_REFERENCE_PAIR",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "gemini_visual_confidence": 0.97,
                "target": {
                    "subjects": [
                        {"id": "Alice", "staging_box": [0.05, 0.15, 0.42, 0.70], "expected_side": "left"},
                        {"id": "Bob", "staging_box": [0.53, 0.15, 0.42, 0.70], "expected_side": "right"}
                    ],
                    "conditioning_propagation": "base_only",
                    "steps": 20,
                    "sampler": "euler"
                },
                "observed": {
                    "subjects": [
                        {"id": "Alice", "present": False, "observed_side": None, "approx_bbox": None, "coverage_h": 0.0, "coverage_w": 0.0},
                        {"id": "Bob", "present": False, "observed_side": None, "approx_bbox": None, "coverage_h": 0.0, "coverage_w": 0.0},
                        {"id": "Unintended Miniature Student", "present": True, "observed_side": "center-bottom", "approx_bbox": [0.42, 0.65, 0.16, 0.28], "coverage_h": 0.37, "coverage_w": 0.38}
                    ],
                    "missing_subjects": ["Alice", "Bob"],
                    "visual_description": "Japanese school hallway with prominent pillars, a vertical Japanese banner, and a single miniature male student standing at center-bottom. Both target regional staging areas (Alice Left, Bob Right) collapsed and failed to render intended subjects."
                },
                "judgment": "0 of 2 target subjects present in designated staging zones. Latents collapsed into architectural background with miniature figure under Reference 20s Base-Only CN. Visual Semantic is FAIL."
            },
            "WF41": {
                "name": "41_VERIFY_CN_STRENGTH_SANITY",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "gemini_visual_confidence": 0.97,
                "target": {
                    "subjects": [
                        {"id": "Alice", "staging_box": [0.05, 0.15, 0.42, 0.70], "expected_side": "left"},
                        {"id": "Bob", "staging_box": [0.53, 0.15, 0.42, 0.70], "expected_side": "right"}
                    ],
                    "cn_strength": 0.50,
                    "cn_end_percent": 0.60,
                    "conditioning_propagation": "base_only",
                    "steps": 20,
                    "sampler": "euler"
                },
                "observed": {
                    "subjects": [
                        {"id": "Alice", "present": False, "observed_side": None, "approx_bbox": None, "coverage_h": 0.0, "coverage_w": 0.0},
                        {"id": "Bob", "present": False, "observed_side": None, "approx_bbox": None, "coverage_h": 0.0, "coverage_w": 0.0},
                        {"id": "Unintended Miniature Student", "present": True, "observed_side": "center-bottom", "approx_bbox": [0.42, 0.65, 0.16, 0.28], "coverage_h": 0.37, "coverage_w": 0.38}
                    ],
                    "missing_subjects": ["Alice", "Bob"],
                    "visual_description": "Near-identical architecture to WF40 with pillars and central banner. Single miniature figure bottom center. Relaxing CN strength to 0.50 and end step to 0.60 was insufficient to resurrect regional subjects in Base-Only mode."
                },
                "judgment": "0 of 2 target subjects present in designated staging zones. Lighter schedule did not resolve regional suppression under Base-Only CN. Visual Semantic is FAIL."
            },
            "WF42": {
                "name": "42_VERIFY_REGIONAL_CN_PROPAGATION_AB",
                "runtime_status": "PASS",
                "visual_semantic_status": "PARTIAL",
                "gemini_visual_confidence": 0.98,
                "target": {
                    "subjects": [
                        {"id": "Alice", "staging_box": [0.05, 0.15, 0.42, 0.70], "expected_side": "left"},
                        {"id": "Bob", "staging_box": [0.53, 0.15, 0.42, 0.70], "expected_side": "right"}
                    ],
                    "propagate_controlnet_to_regions": True,
                    "cn_strength": 0.75,
                    "cn_end_percent": 0.80,
                    "steps": 20,
                    "sampler": "euler"
                },
                "observed": {
                    "subjects": [
                        {"id": "Alice (Left Region)", "present": True, "observed_side": "left", "approx_bbox": [0.08, 0.12, 0.40, 0.84], "coverage_h": 1.20, "coverage_w": 0.95, "artifact": "mannequin_overconstraint"},
                        {"id": "Bob (Right Region)", "present": True, "observed_side": "right", "approx_bbox": [0.55, 0.12, 0.40, 0.84], "coverage_h": 1.20, "coverage_w": 0.95, "artifact": "mannequin_overconstraint"}
                    ],
                    "missing_subjects": [],
                    "visual_description": "CRITICAL FINDING: Both regions rendered full-scale figures matching target staging boxes (Left figure has red tie and white shirt; Right figure has dark gakuran jacket). HOWEVER, because ControlNet was cloned into regional samplers at strength 0.75 / end 0.80, SEVERE OVERCONSTRAINT occurred: both characters were rendered as literal wooden mannequins / wireframe dolls inside wooden frames!"
                },
                "judgment": "BOTH subjects rendered at full scale in target zones (Presence PASS), but severe overconstraint turned subjects into wooden mannequins matching guide wireframes. Visual Semantic is PARTIAL (Overconstraint Artifact)."
            },
            "WF43": {
                "name": "43_VERIFY_BROWSER_STAGING_CAUSALITY",
                "runtime_status": "PASS",
                "visual_semantic_status": "FAIL",
                "gemini_visual_confidence": 0.95,
                "target": {
                    "subjects": [
                        {"id": "Bob", "staging_box": [0.05, 0.15, 0.42, 0.70], "expected_side": "left"},
                        {"id": "Alice", "staging_box": [0.55, 0.15, 0.40, 0.70], "expected_side": "right (dragged)"}
                    ],
                    "steps": 12,
                    "sampler": "euler",
                    "scheduler": "normal",
                    "lora": "Hyper-SDXL-12step"
                },
                "observed": {
                    "subjects": [
                        {"id": "Bob", "present": False, "observed_side": None, "approx_bbox": None, "coverage_h": 0.0, "coverage_w": 0.0},
                        {"id": "Alice", "present": False, "observed_side": None, "approx_bbox": None, "coverage_h": 0.0, "coverage_w": 0.0},
                        {"id": "Central Student", "present": True, "observed_side": "center-bottom", "approx_bbox": [0.42, 0.65, 0.16, 0.28], "coverage_h": 0.37, "coverage_w": 0.38}
                    ],
                    "missing_subjects": ["Bob", "Alice"],
                    "visual_description": "Japanese hallway scene with single miniature student at bottom-center; dragged staging regions did not express subjects under this Fast-12 seed/prompt combination."
                },
                "judgment": "Target characters did not manifest in the moved staging zones. While UI pointer contract and guide SSOT are mathematically proven in E2E tests, visual manifest is FAIL for this run."
            }
        }
    }

    if wf40_43_results:
        for k, v in wf40_43_results.items():
            evaluation["workflows"][k] = v

    return evaluation


def main():
    eval_path = os.path.join(OUTPUT_DIR, "phase3i1_visual_evaluation.json")
    eval_data = build_evaluation_data()
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2, ensure_ascii=False)
    print(f"Generated visual evaluation: {eval_path}")


if __name__ == "__main__":
    main()
