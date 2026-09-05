import json
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKFLOWS_DIR = os.path.join(ROOT_DIR, "workflows")

TARGET_WORKFLOWS = [
    "07_MANGA_REGION_EDITOR_UI_TEST.json",
    "08_MANGA_SCENE_CONTRACT_TEST.json",
    "09_MANGA_REGIONAL_GENERATION_POC.json",
    "10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json",
    "11_TWO_REGION_CORE_COUPLE_ORACLE.json",
    "12_TWO_REGION_IMPACT_COUPLE_ORACLE.json",
    "13_TWO_REGION_CONTROLNET_LAYOUT_AUX.json",
    "14_MANGA_PANEL_LAYOUT_GUIDE_EDITOR_TEST.json",
    "15_MANGA_PANEL_LAYOUT_CONTROLNET_FUSION_ORACLE.json",
    "16_MANGA_VARIABLE_N_REGION_LAYOUT_FUSION_POC.json",
    "17_MANGA_CAST_MASTER_AND_LOCALITY_VALIDATION.json",
    "18_SINGLE_REGION_PLACEMENT_CORE_VS_IMPACT_ORACLE.json",
    "19_TWO_REGION_SEMANTIC_BINDING_ORACLE.json",
    "20_TWO_REGION_LAYOUT_ASSIST_ORACLE.json",
    "21_MANGA_IMPACT_RECURRENT_CAST_POC.json",
    "22_SINGLE_PANEL_MULTI_SCENE_SAME_CAST_ORACLE.json",
    "23_MANGA_PROGRESSIVE_PANEL_AUTHORING_IMPACT.json",
    "24_SINGLE_PANEL_PROGRESSIVE_SUBSCENE_IMPACT.json",
    "25_VERIFY_SINGLE_A_TOP_LEFT.json",
    "26_VERIFY_SINGLE_A_BOTTOM_RIGHT.json",
    "27_VERIFY_TWO_REGION_DOG_CAT_LEFT_RIGHT.json",
    "28_VERIFY_TWO_REGION_DOG_CAT_SWAP.json",
    "29_VERIFY_SINGLE_A_TOP_LEFT_EXCLUSIVE_BASE.json",
    "30_VERIFY_SINGLE_A_BOTTOM_RIGHT_EXCLUSIVE_BASE.json",
    "31_VERIFY_TWO_REGION_DOG_CAT_LR_EXCLUSIVE_BASE.json",
    "32_VERIFY_TWO_REGION_DOG_CAT_SWAP_EXCLUSIVE_BASE.json",
    "33_VERIFY_AUTHORING_ALICE_LEFT_BOB_RIGHT.json",
    "34_VERIFY_AUTHORING_ALICE_RIGHT_BOB_LEFT.json",
    "35_VERIFY_CONTROLNET_ANYTEST_BASELINE.json",
    "36_VERIFY_CONTROLNET_SCALE_LOCK_SINGLE_CHARACTER.json",
    "37_VERIFY_AUTHORING_ALICE_LEFT_BOB_RIGHT_CN_ASSIST.json",
    "38_VERIFY_AUTHORING_ALICE_RIGHT_BOB_LEFT_CN_ASSIST.json",
    "39_VERIFY_FAST_DRAFT_12_CONTROLNET_REGRESSION.json",
    "40_VERIFY_CN_AUTHORING_REFERENCE_PAIR.json",
    "41_VERIFY_CN_STRENGTH_SANITY.json",
    "42_VERIFY_REGIONAL_CN_PROPAGATION_AB.json",
    "43_VERIFY_BROWSER_STAGING_CAUSALITY.json",
    "44_VERIFY_NATIVE20_BASEONLY_ZERO.json",
    "45_VERIFY_NATIVE12_CONTROL.json",
    "46_VERIFY_HYPER12_CAUSAL_CONTROL.json",
    "47_VERIFY_PER_REGION_HINT_ATTENUATED.json",
    "48_VERIFY_BASE_BACKGROUND_ONLY_CHARACTER_PRESENCE.json",
    "49_VERIFY_ALICE_LEFT_ONLY_HYPER12.json",
    "50_VERIFY_ALICE_RIGHT_ONLY_HYPER12.json",
    "51_VERIFY_BOB_LEFT_ONLY_HYPER12.json",
    "52_VERIFY_BOB_RIGHT_ONLY_HYPER12.json",
    "53_VERIFY_HYPER12_PER_REGION_HINT_SWAP.json",
    "54_VERIFY_ALICE_LEFT_PROMPT_TRUTH_REMAINDER.json",
    "55_VERIFY_ALICE_RIGHT_PROMPT_TRUTH_REMAINDER.json",
    "56_VERIFY_BOB_LEFT_PROMPT_TRUTH_REMAINDER.json",
    "57_VERIFY_BOB_RIGHT_PROMPT_TRUTH_REMAINDER.json",
    "58_VERIFY_TWO_CHARACTER_PROMPT_TRUTH_LR.json",
    "59_VERIFY_TWO_CHARACTER_PROMPT_TRUTH_SWAP.json",
    "60_VERIFY_POSE_FACING_EACH_OTHER.json",
    "61_VERIFY_POSE_FACING_OUTWARD.json",
    "62_VERIFY_POSE_SITTING_SINGLE.json",
    "63_VERIFY_INTERACTION_HANDSHAKE.json",
    "64_VERIFY_CAMERA_DISTANCE_NEAR.json",
    "65_VERIFY_CAMERA_DISTANCE_FAR.json",
    "66_VERIFY_POSE_GUIDE_ONLY_INWARD.json",
    "67_VERIFY_HANDSHAKE_CANONICAL_PAIR_AND_FEATHER.json",
    "68_VERIFY_MAINLINE_SUBSCENE_CONFLICT_FRIENDSHIP.json",
    "69_VERIFY_MAINLINE_SUBSCENE_GEOMETRY_SWAP.json",
    "70_VERIFY_4PANEL_MIXED_SIMPLE_COMPLEX_PAGE.json",
    "71_VERIFY_EXTERNAL_REGIONAL_BACKEND_PARITY.json",
]


def validate_workflow_integrity(wf_path):
    print(f"\n--- Checking Workflow Integrity: {os.path.basename(wf_path)} ---")
    with open(wf_path, "r", encoding="utf-8") as f:
        wf = json.load(f)

    last_node_id = wf.get("last_node_id", 0)
    last_link_id = wf.get("last_link_id", 0)
    nodes = wf.get("nodes", [])
    links = wf.get("links", [])

    node_ids = {n["id"] for n in nodes}
    nodes_by_id = {n["id"]: n for n in nodes}

    # 1. last_node_id >= max(node.id)
    if node_ids:
        max_nid = max(node_ids)
        assert last_node_id >= max_nid, (
            f"last_node_id ({last_node_id}) is less than max node id ({max_nid})"
        )

    # 2. last_link_id >= max(link.id)
    link_ids = {l[0] for l in links} if links else set()
    links_by_id = {l[0]: l for l in links} if links else {}
    if link_ids:
        max_lid = max(link_ids)
        assert last_link_id >= max_lid, (
            f"last_link_id ({last_link_id}) is less than max link id ({max_lid})"
        )

    # 3. リンクの整合性検証
    for l in links:
        lid, src_nid, src_slot, tgt_nid, tgt_slot, link_type = l[0], l[1], l[2], l[3], l[4], l[5]
        assert src_nid in node_ids, f"Link {lid}: source node {src_nid} not in nodes"
        assert tgt_nid in node_ids, f"Link {lid}: target node {tgt_nid} not in nodes"

        src_node = nodes_by_id[src_nid]
        tgt_node = nodes_by_id[tgt_nid]

        src_outputs = src_node.get("outputs", [])
        assert 0 <= src_slot < len(src_outputs), (
            f"Link {lid}: source slot {src_slot} out of range for node {src_nid} ({len(src_outputs)} outputs)"
        )

        tgt_inputs = tgt_node.get("inputs", [])
        assert 0 <= tgt_slot < len(tgt_inputs), (
            f"Link {lid}: target slot {tgt_slot} out of range for node {tgt_nid} ({len(tgt_inputs)} inputs)"
        )

        # input 側の link id が一致しているか
        assert tgt_inputs[tgt_slot].get("link") == lid, (
            f"Link {lid}: target node {tgt_nid} input[{tgt_slot}] has link {tgt_inputs[tgt_slot].get('link')}, expected {lid}"
        )

        # output 側の links 配列に lid が含まれているか
        src_slot_links = src_outputs[src_slot].get("links") or []
        assert lid in src_slot_links, (
            f"Link {lid}: source node {src_nid} output[{src_slot}] links {src_slot_links} missing {lid}"
        )

    # 4. 全ノードの input link が links に実在するか
    for n in nodes:
        for in_idx, inp in enumerate(n.get("inputs", [])):
            link_id = inp.get("link")
            if link_id is not None:
                assert link_id in link_ids, (
                    f"Node {n['id']} input[{in_idx}] references non-existent link id {link_id}"
                )

    print(f"  Nodes: {len(nodes)} (max_id: {max(node_ids) if node_ids else 0}, last_node_id: {last_node_id})")
    print(f"  Links: {len(links)} (max_id: {max(link_ids) if link_ids else 0}, last_link_id: {last_link_id})")
    print("  [PASSED] Full Structural Integrity Verified")


def run_all_workflow_integrity_tests():
    print("================================================================================")
    print("Workflow JSON Structural Integrity Verification (Phase 3B.1.1)")
    print("================================================================================")

    for wf_file in TARGET_WORKFLOWS:
        wf_path = os.path.join(WORKFLOWS_DIR, wf_file)
        if not os.path.exists(wf_path):
            raise FileNotFoundError(f"Workflow file not found: {wf_path}")
        validate_workflow_integrity(wf_path)

    print("\n================================================================================")
    print("[SUCCESS] ALL 4 WORKFLOW INTEGRITY TESTS PASSED PERFECTLY!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all_workflow_integrity_tests())
