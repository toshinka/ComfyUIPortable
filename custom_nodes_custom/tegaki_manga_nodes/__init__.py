from .lora_loader import TegakiLoraPromptLoader, TegakiLoraStackToPrompt

NODE_CLASS_MAPPINGS = {
    "TegakiLoraPromptLoader": TegakiLoraPromptLoader,
    "TegakiLoraStackToPrompt": TegakiLoraStackToPrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TegakiLoraPromptLoader": "Tegaki LoRA Prompt Loader (Manga)",
    "TegakiLoraStackToPrompt": "Tegaki LoRA Stack to Prompt",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
