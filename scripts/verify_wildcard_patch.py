import os
import sys
from pathlib import Path

"""
verify_wildcard_patch.py
========================
ComfyUI-WildcardOrganizer に対する Windows Junction 対応ローカルパッチが
適用されているかを検証するスクリプト。
"""

def verify_patch():
    target_file = Path("ComfyUI/custom_nodes/ComfyUI-WildcardOrganizer/nodes.py").resolve()
    print("================================================================================")
    print("ComfyUI-WildcardOrganizer Patch Verification")
    print("================================================================================")
    print(f"Target File: {target_file}")

    if not target_file.exists():
        print("[ERROR] Target file does not exist. ComfyUI-WildcardOrganizer is not installed!")
        return 1

    content = target_file.read_text(encoding="utf-8", errors="replace")

    # 検査マーカー 1: key_text fallback (Junctionドライブ跨ぎ耐性)
    has_marker_1 = "if not path_text and key_text:" in content
    # 検査マーカー 2: PromptServer getattr (初期化順序耐性)
    has_marker_2 = "server_instance = getattr(PromptServer, \"instance\", None)" in content

    print(f"  Marker 1 (Key-based junction fallback): {'FOUND' if has_marker_1 else 'MISSING'}")
    print(f"  Marker 2 (Safe PromptServer route bind): {'FOUND' if has_marker_2 else 'MISSING'}")

    if has_marker_1 and has_marker_2:
        print("\n[SUCCESS] Status: PATCH PRESENT (All required patch lines are active)")
        return 0
    else:
        print("\n[WARNING] Status: PATCH MISSING (Patch needs to be applied from patches/ directory)")
        return 1

if __name__ == "__main__":
    sys.exit(verify_patch())
