import os
import sys
import json
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.abspath("custom_nodes_custom"))
from tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler
from tegaki_manga_nodes.layout_guide_generator import TegakiMangaLayoutGuideGenerator
from tegaki_manga_nodes.character_staging_editor import TegakiMangaCharacterStagingEditor

compiler = TegakiMangaPageCompiler()
generator = TegakiMangaLayoutGuideGenerator()
staging_editor = TegakiMangaCharacterStagingEditor()

out_dir = os.path.join("output", "debug_guides")
os.makedirs(out_dir, exist_ok=True)

for num in [35, 36, 37, 38, 39]:
    wf_fn = [f for f in os.listdir("workflows") if f.startswith(str(num))][0]
    wf = json.load(open(os.path.join("workflows", wf_fn), encoding="utf-8"))

    cast_w = next(n for n in wf["nodes"] if n["type"] == "TegakiMangaCastMaster")["widgets_values"][0]
    content_w = next(n for n in wf["nodes"] if n["type"] == "TegakiMangaPanelContentEditor")["widgets_values"][0]
    staging_w = next(n for n in wf["nodes"] if n["type"] == "TegakiMangaCharacterStagingEditor")["widgets_values"][0]
    guide_w = next(n for n in wf["nodes"] if n["type"] == "TegakiMangaLayoutGuideGenerator")["widgets_values"]
    layout_node = next(n for n in wf["nodes"] if n["type"] == "TegakiMangaPanelLayoutEditor")
    # LayoutEditor widgets_values are [width, height, preset, custom_json]
    from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
    layout_dict = get_default_panel_layout_spec(1024, 1024, "1_full")

    from tegaki_manga_nodes.panel_content_editor import TegakiMangaPanelContentEditor
    content_editor = TegakiMangaPanelContentEditor()
    region_spec, _, _ = content_editor.process(content_w)

    # 1. Staging editor
    staged_spec, _, _ = staging_editor.process(region_spec, layout_dict, staging_w)
    
    # 2. Page compiler
    plan, _, _, _ = compiler.compile_page(staged_spec, cast_w)

    guide_mode = guide_w[1]
    img_t, _, _ = generator.generate_guide(plan, target_panel_id=1, guide_style=guide_mode, color_mode="Black on White", line_thickness=4, include_panel_border=True, width=1024, height=1024)
    img = Image.fromarray((img_t[0].cpu().numpy() * 255.0).astype(np.uint8))
    out_path = os.path.join(out_dir, f"guide_wf{num}.png")
    img.save(out_path)
    from tegaki_manga_nodes.layout_guide_generator import extract_staging_boxes
    panel_b, boxes = extract_staging_boxes(plan, 1)
    print(f"WF{num} ({guide_mode}): saved {out_path}, extracted boxes: {boxes}")
