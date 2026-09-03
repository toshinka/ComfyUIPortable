import sys
import os
import inspect
import hashlib
from pathlib import Path

# ComfyUI を sys.path の先頭に追加してインポートを模倣
comfy_dir = os.path.abspath("ComfyUI")
sys.path.insert(0, comfy_dir)

from custom_nodes.tegaki_manga_nodes.region_editor import TegakiMangaRegionEditor
from custom_nodes.tegaki_manga_nodes.lora_loader import TegakiLoraPromptLoader

def get_file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_source_identity():
    print("================================================================================")
    print("Runtime Source Identity Verification")
    print("================================================================================")

    git_target_dir = Path("custom_nodes_custom/tegaki_manga_nodes").resolve()
    print(f"Expected Git Canonical Source Dir: {git_target_dir}\n")

    modules_to_test = [
        ("TegakiMangaRegionEditor", TegakiMangaRegionEditor),
        ("TegakiLoraPromptLoader", TegakiLoraPromptLoader),
    ]

    all_passed = True
    for class_name, cls in modules_to_test:
        raw_source_file = inspect.getsourcefile(cls)
        raw_path = Path(raw_source_file).absolute()
        resolved_path = raw_path.resolve()

        sha256_hash = get_file_sha256(str(resolved_path))

        print(f"Class: {class_name}")
        print(f"  Import Path:   {raw_path}")
        print(f"  Resolved Path: {resolved_path}")
        print(f"  SHA256:        {sha256_hash}")

        # 検証: resolved_path の親ディレクトリが git_target_dir と一致するか
        is_identical = (resolved_path.parent == git_target_dir)
        print(f"  Canonical Match: {'PASSED' if is_identical else 'FAILED'}\n")

        if not is_identical:
            all_passed = False

    if all_passed:
        print("[SUCCESS] All runtime custom nodes resolve to Git canonical source (custom_nodes_custom)!")
        return 0
    else:
        print("[ERROR] Runtime custom nodes do NOT resolve to custom_nodes_custom!")
        return 1

if __name__ == "__main__":
    sys.exit(test_source_identity())
