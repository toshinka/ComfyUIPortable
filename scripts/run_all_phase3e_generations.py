"""
Phase 3E Combined Generation Runner
===================================
Sequentially executes:
1. Region Order Oracle (scene_first vs character_first)
2. Recurrent Cast 4-Panel Generation & Cropped Contact Sheet
3. Single Panel Multi-Scene Hostile Test & Contact Sheet

Under a single ComfyUI server lifecycle, ensuring prompt server cleanup upon completion.
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.comfy_runtime_helper import ensure_server, stop_server
from scripts.test_impact_region_order import run_oracle
from scripts.test_manga_impact_recurrent_cast_runtime import run_recurrent_cast_test
from scripts.generate_recurrent_cast_contact_sheet import generate_contact_sheet
from scripts.test_single_panel_multiscene_runtime import run_hostile_test


def main():
    print("================================================================================")
    print("  Phase 3E: Combined Runtime Execution & Oracle Verification")
    print("================================================================================")

    ensure_server(timeout=60)

    try:
        # Step 1: Region Order Oracle
        print("\n>>> STEP 1: Running Region Order Oracle (scene_first vs character_first)...")
        t0 = time.time()
        order_results = run_oracle(keep_server=True)
        print(f">>> STEP 1 Completed in {time.time() - t0:.1f}s.")

        # Step 2: Recurrent Cast 4-Panel Generation
        print("\n>>> STEP 2: Running Manga Impact Recurrent Cast 4-Panel Test...")
        t0 = time.time()
        recurrent_results = run_recurrent_cast_test(seed=42, keep_server=True)
        print(f">>> STEP 2 Completed in {time.time() - t0:.1f}s.")

        # Step 3: Recurrent Cast Contact Sheet
        print("\n>>> STEP 3: Compiling Recurrent Cast Contact Sheet...")
        t0 = time.time()
        generate_contact_sheet()
        print(f">>> STEP 3 Completed in {time.time() - t0:.1f}s.")

        # Step 4: Single Panel Multi-Scene Hostile Test
        print("\n>>> STEP 4: Running Single Panel Multi-Scene Hostile Test...")
        t0 = time.time()
        hostile_results = run_hostile_test(seed=42, keep_server=True)
        print(f">>> STEP 4 Completed in {time.time() - t0:.1f}s.")

        print("\n================================================================================")
        print("  ALL PHASE 3E RUNTIME GENERATIONS COMPLETED SUCCESSFULLY!")
        print("================================================================================")

    finally:
        print("\n[Runner] Enforcing strict server process termination...")
        stop_server()


if __name__ == "__main__":
    main()
