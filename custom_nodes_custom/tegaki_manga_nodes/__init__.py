from .lora_loader import TegakiLoraPromptLoader, TegakiLoraStackToPrompt
from .region_editor import TegakiMangaRegionEditor
from .scene_compiler import TegakiMangaSceneCompiler

NODE_CLASS_MAPPINGS = {
    "TegakiLoraPromptLoader": TegakiLoraPromptLoader,
    "TegakiLoraStackToPrompt": TegakiLoraStackToPrompt,
    "TegakiMangaRegionEditor": TegakiMangaRegionEditor,
    "TegakiMangaSceneCompiler": TegakiMangaSceneCompiler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TegakiLoraPromptLoader": "Tegaki LoRA Prompt Loader (Manga)",
    "TegakiLoraStackToPrompt": "Tegaki LoRA Stack to Prompt",
    "TegakiMangaRegionEditor": "Tegaki Manga Region Editor",
    "TegakiMangaSceneCompiler": "Tegaki Manga Scene Compiler (Prototype)",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
