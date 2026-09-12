"""H3-PLAY1: capability-owned model names and deterministic model-only LoRAs."""
from __future__ import annotations
import math
import re
from typing import Mapping

DEFAULT_MODELS = {
    "standard": "minimax_h3_fl2va_pruned_int8_convrot.safetensors",
    "reference": "minimax_h3_ref2va_pruned_int8_convrot.safetensors",
}
MAX_LORAS = 3

def invalid(message):
    from h3.adapters.native_t2v import RequestValidationError
    raise RequestValidationError(message)

def safe_name(name):
    return (isinstance(name, str) and bool(name) and not name.startswith(("/", "\\"))
            and not any(c in name for c in (":", "\0", "\n", "\r"))
            and all(part not in ("", ".", "..") for part in name.replace("\\", "/").split("/")))

def model_family(name):
    if not safe_name(name):
        return None
    match = re.fullmatch(r"minimax[_-]h3[_-](fl2va|ref2va)(?:[_-][a-z0-9_.-]+)?\.safetensors",
                         name.replace("\\", "/").split("/")[-1].lower())
    return {"fl2va": "standard", "ref2va": "reference"}.get(match[1]) if match else None

def choices(info, node, field):
    try:
        value = info[node]["input"]["required"][field][0]
    except (KeyError, TypeError, IndexError):
        return []
    return list(dict.fromkeys(n for n in value if safe_name(n))) if isinstance(value, list) else []

def capability_from_object_info(info):
    info = info if isinstance(info, Mapping) else {}
    models = choices(info, "UNETLoader", "unet_name")
    try:
        loader = info["LoraLoaderModelOnly"]
        required = loader["input"]["required"]
        strength_options = required["strength_model"][1]
        compatible = (set(required) == {"model", "lora_name", "strength_model"}
                      and required["model"][0] == "MODEL"
                      and required["strength_model"][0] == "FLOAT"
                      and isinstance(required["lora_name"][0], list)
                      and strength_options.get("min", -2) <= -2
                      and strength_options.get("max", 2) >= 2
                      and loader.get("output") == ["MODEL"]
                      and not loader["input"].get("optional"))
    except (KeyError, TypeError, IndexError, AttributeError):
        compatible = False
    return {
        "state": "AVAILABLE", "defaults": DEFAULT_MODELS.copy(),
        "models": {route: [n for n in models if model_family(n) == route] for route in DEFAULT_MODELS},
        "lora": {"state": "AVAILABLE" if compatible else "UNAVAILABLE",
                 "names": choices(info, "LoraLoaderModelOnly", "lora_name") if compatible else [],
                 "max_entries": MAX_LORAS, "min_strength": -2.0, "max_strength": 2.0},
    }

def validate_selection(model_name=None, loras=()):
    if model_name is not None and not safe_name(model_name):
        invalid("Model must be a Native capability name.")
    if not isinstance(loras, (list, tuple)) or len(loras) > MAX_LORAS:
        invalid("LoRA stack must contain at most 3 entries.")
    result = []
    for item in loras:
        if not isinstance(item, Mapping) or set(item) != {"name", "strength"} or not safe_name(item.get("name")):
            invalid("LoRA must contain a Native name and strength.")
        strength = item["strength"]
        if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not -2 <= strength <= 2:
            invalid("LoRA strength must be a finite number between -2 and 2.")
        result.append({"name": item["name"], "strength": float(strength)})
    return model_name, tuple(result)

def validate_available_selection(model_name, loras, family, capability=None):
    model_name, loras = validate_selection(model_name, loras)
    if model_name is None and not loras:
        return
    if not isinstance(capability, Mapping) or capability.get("state") != "AVAILABLE":
        invalid("Native model capability is unavailable; selections were retained.")
    selected = model_name or DEFAULT_MODELS[family]
    if model_family(selected) != family or selected not in capability.get("models", {}).get(family, []):
        invalid("Selected model is missing or incompatible with this Video route.")
    lora_cap = capability.get("lora", {})
    if loras and lora_cap.get("state") != "AVAILABLE":
        invalid("LoRA is unavailable for this Native profile.")
    if any(item["name"] not in lora_cap.get("names", []) for item in loras):
        invalid("Selected LoRA is no longer available.")
    return selected


def materialize_model(graph, roles, model_name, loras, family, capability=None):
    selected = validate_available_selection(model_name, loras, family, capability)
    if selected is None:
        return
    _, loras = validate_selection(model_name, loras)
    model_id = str(roles["model"]["id"])
    graph[model_id]["inputs"]["unet_name"] = selected
    consumers = [(node["inputs"], key) for node in graph.values()
                 for key, value in node.get("inputs", {}).items() if value == [model_id, 0]]
    edge = [model_id, 0]
    for index, item in enumerate(loras):
        node_id = f"h3_play1_lora_{index + 1}"
        if node_id in graph:
            invalid("Workflow has a conflicting LoRA node.")
        graph[node_id] = {"class_type": "LoraLoaderModelOnly", "inputs": {
            "model": edge, "lora_name": item["name"], "strength_model": item["strength"]}}
        edge = [node_id, 0]
    for inputs, key in consumers:
        inputs[key] = edge
