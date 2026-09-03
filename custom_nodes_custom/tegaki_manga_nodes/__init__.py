from .lora_loader import TegakiLoraPromptLoader, TegakiLoraStackToPrompt
from .region_editor import TegakiMangaRegionEditor
from .scene_compiler import TegakiMangaSceneCompiler, TegakiMangaPageCompiler, TegakiCompilePlanInspector
from .mask_builder import TegakiMangaMaskBuilder
from .conditioning_builder import TegakiMangaConditioningBuilder

NODE_CLASS_MAPPINGS = {
    "TegakiLoraPromptLoader": TegakiLoraPromptLoader,
    "TegakiLoraStackToPrompt": TegakiLoraStackToPrompt,
    "TegakiMangaRegionEditor": TegakiMangaRegionEditor,
    "TegakiMangaSceneCompiler": TegakiMangaSceneCompiler,
    "TegakiMangaPageCompiler": TegakiMangaPageCompiler,
    "TegakiCompilePlanInspector": TegakiCompilePlanInspector,
    "TegakiMangaMaskBuilder": TegakiMangaMaskBuilder,
    "TegakiMangaConditioningBuilder": TegakiMangaConditioningBuilder,
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
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
