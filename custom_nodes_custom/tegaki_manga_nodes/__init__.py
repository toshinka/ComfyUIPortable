from .lora_loader import TegakiLoraPromptLoader, TegakiLoraStackToPrompt
from .region_editor import TegakiMangaRegionEditor
from .scene_compiler import TegakiMangaSceneCompiler, TegakiMangaPageCompiler, TegakiCompilePlanInspector
from .mask_builder import TegakiMangaMaskBuilder
from .conditioning_builder import TegakiMangaConditioningBuilder
from .two_region_editor import TegakiTwoRegionCoupleEditor
from .two_region_core_conditioner import TegakiTwoRegionCoreConditioner
from .two_region_impact_adapter import TegakiTwoRegionImpactAdapter
from .two_region_layout_guide import TegakiTwoRegionLayoutGuide
from .panel_layout_editor import TegakiMangaPanelLayoutEditor
from .layout_aware_conditioning import TegakiMangaLayoutAwareConditioningBuilder
from . import panel_layout_api

NODE_CLASS_MAPPINGS = {
    "TegakiLoraPromptLoader": TegakiLoraPromptLoader,
    "TegakiLoraStackToPrompt": TegakiLoraStackToPrompt,
    "TegakiMangaRegionEditor": TegakiMangaRegionEditor,
    "TegakiMangaSceneCompiler": TegakiMangaSceneCompiler,
    "TegakiMangaPageCompiler": TegakiMangaPageCompiler,
    "TegakiCompilePlanInspector": TegakiCompilePlanInspector,
    "TegakiMangaMaskBuilder": TegakiMangaMaskBuilder,
    "TegakiMangaConditioningBuilder": TegakiMangaConditioningBuilder,
    "TegakiTwoRegionCoupleEditor": TegakiTwoRegionCoupleEditor,
    "TegakiTwoRegionCoreConditioner": TegakiTwoRegionCoreConditioner,
    "TegakiTwoRegionImpactAdapter": TegakiTwoRegionImpactAdapter,
    "TegakiTwoRegionLayoutGuide": TegakiTwoRegionLayoutGuide,
    "TegakiMangaPanelLayoutEditor": TegakiMangaPanelLayoutEditor,
    "TegakiMangaLayoutAwareConditioningBuilder": TegakiMangaLayoutAwareConditioningBuilder,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TegakiLoraPromptLoader": "Tegaki LoRA Prompt Loader (Manga)",
    "TegakiLoraStackToPrompt": "Tegaki LoRA Stack to Prompt",
    "TegakiMangaRegionEditor": "Tegaki Manga Region Editor",
    "TegakiMangaSceneCompiler": "Tegaki Manga Scene Compiler (Single Panel)",
    "TegakiMangaPageCompiler": "Tegaki Manga Page Compiler (Whole Page)",
    "TegakiCompilePlanInspector": "Tegaki Compile Plan Inspector",
    "TegakiMangaMaskBuilder": "Tegaki Manga Mask Builder",
    "TegakiMangaConditioningBuilder": "Tegaki Manga Conditioning Builder",
    "TegakiTwoRegionCoupleEditor": "Tegaki Two Region Couple Editor (Oracle)",
    "TegakiTwoRegionCoreConditioner": "Tegaki Two Region Core Conditioner (Oracle)",
    "TegakiTwoRegionImpactAdapter": "Tegaki Two Region Impact Adapter (Oracle)",
    "TegakiTwoRegionLayoutGuide": "Tegaki Two Region Layout Guide (Oracle)",
    "TegakiMangaPanelLayoutEditor": "Tegaki Manga Panel Layout Editor (Guide)",
    "TegakiMangaLayoutAwareConditioningBuilder": "Tegaki Manga Layout-Aware Conditioning Builder",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]


