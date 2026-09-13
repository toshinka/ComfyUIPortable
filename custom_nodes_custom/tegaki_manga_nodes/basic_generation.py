"""PLAY1a pure Manga txt2img catalog and graph compiler; no ComfyUI imports or execution."""

from __future__ import annotations

import hashlib
import json
import math
import re
import secrets
from pathlib import PurePosixPath
from typing import Any, Callable

SCHEMA_VERSION = "1"
NODE_IDENTITY = "TegakiMinimumHandSceneEditor"
CORE_NODES = (
    "CheckpointLoaderSimple", "LoraLoader", "CLIPTextEncode",
    "EmptyLatentImage", "KSampler", "VAEDecode", "SaveImage",
)
PRODUCT_BOUNDS = {
    "steps": {"min": 1, "max": 100},
    "cfg": {"min": 0.0, "max": 30.0},
    "width": {"min": 256, "max": 2048, "step": 8},
    "height": {"min": 256, "max": 2048, "step": 8},
    "max_pixels": 2097152,
    "seed": {"min": 0, "max": 4294967295, "random_sentinel": "-1"},
}
REQUEST_FIELDS = frozenset({
    "request_id", "mode", "checkpoint_id", "positive_raw", "negative_raw",
    "sampler_id", "scheduler_id", "steps", "cfg", "width", "height",
    "seed_requested", "capability_revision",
})
TAG_RE = re.compile(r"<[^<>]*>")
LORA_RE = re.compile(r"<lora:([^:<>]+):([+-]?(?:\d+(?:\.\d*)?|\.\d+))>")
REQUEST_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")
SEED_RE = re.compile(r"(?:0|[1-9][0-9]*)")


class GenerationContractError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _fail(code: str, message: str) -> None:
    raise GenerationContractError(code, message)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _safe_catalog_id(value: Any) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        _fail("INVALID_CATALOG_ID", "Catalog ID must be a non-empty relative name")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        _fail("INVALID_CATALOG_ID", "Catalog ID contains a control character")
    if ":" in value or "<" in value or ">" in value or value.startswith(("/", "\\")):
        _fail("INVALID_CATALOG_ID", "Catalog ID contains an absolute path or unsupported character")
    parts = value.replace("\\", "/").split("/")
    if any(part in ("", ".", "..") for part in parts):
        _fail("INVALID_CATALOG_ID", "Catalog ID contains an unsafe path segment")
    return value


def _required(inputs: dict, node: str, field: str) -> Any:
    try:
        return inputs[node]["required"][field]
    except (KeyError, TypeError):
        _fail("BACKEND_CAPABILITY_UNAVAILABLE", f"Required {node}.{field} capability is unavailable")


def _numeric_backend_bound(inputs: dict, node: str, field: str) -> dict:
    data = _required(inputs, node, field)
    if not isinstance(data, (list, tuple)) or len(data) < 2 or not isinstance(data[1], dict):
        _fail("BACKEND_CAPABILITY_UNAVAILABLE", f"Invalid {node}.{field} bounds")
    options = data[1]
    if not all(type(options.get(k)) in (int, float) and math.isfinite(options[k]) for k in ("min", "max")):
        _fail("BACKEND_CAPABILITY_UNAVAILABLE", f"Missing {node}.{field} bounds")
    maximum = str(int(options["max"])) if node == "KSampler" and field == "seed" else options["max"]
    return {"min": options["min"], "max": maximum, **({"step": options["step"]} if "step" in options else {})}


def _choices(inputs: dict, node: str, field: str) -> list[str]:
    data = _required(inputs, node, field)
    if not isinstance(data, (list, tuple)) or not data or not isinstance(data[0], (list, tuple)):
        _fail("BACKEND_CAPABILITY_UNAVAILABLE", f"Invalid {node}.{field} choices")
    values = data[0]
    if not values or any(not isinstance(v, str) or not v for v in values) or len(values) != len(set(values)):
        _fail("BACKEND_CAPABILITY_UNAVAILABLE", f"Empty or invalid {node}.{field} choices")
    return list(values)


def build_catalog(
    checkpoint_names: list[str], lora_names: list[str], node_inputs: dict,
    is_available: Callable[[str, str], bool],
) -> dict:
    """Build a deterministic catalog from registered node inputs and server-owned names."""
    if not isinstance(node_inputs, dict) or any(node not in node_inputs for node in CORE_NODES + (NODE_IDENTITY,)):
        _fail("BACKEND_CAPABILITY_UNAVAILABLE", "Manga identity or required core nodes are missing")
    if not isinstance(checkpoint_names, list) or not isinstance(lora_names, list):
        _fail("BACKEND_CAPABILITY_UNAVAILABLE", "Model catalog is unavailable")
    checkpoint_choices = set(_choices(node_inputs, "CheckpointLoaderSimple", "ckpt_name")) if checkpoint_names else set()
    lora_choices = set(_choices(node_inputs, "LoraLoader", "lora_name")) if lora_names else set()
    samplers = _choices(node_inputs, "KSampler", "sampler_name")
    schedulers = _choices(node_inputs, "KSampler", "scheduler")
    backend_bounds = {
        "steps": _numeric_backend_bound(node_inputs, "KSampler", "steps"),
        "cfg": _numeric_backend_bound(node_inputs, "KSampler", "cfg"),
        "width": _numeric_backend_bound(node_inputs, "EmptyLatentImage", "width"),
        "height": _numeric_backend_bound(node_inputs, "EmptyLatentImage", "height"),
        "seed": _numeric_backend_bound(node_inputs, "KSampler", "seed"),
    }
    if _numeric_backend_bound(node_inputs, "EmptyLatentImage", "batch_size")["min"] > 1:
        _fail("BACKEND_CAPABILITY_UNAVAILABLE", "Backend cannot create a one-image latent")
    for node, field in (("CLIPTextEncode", "text"), ("CLIPTextEncode", "clip"),
                        ("VAEDecode", "samples"), ("VAEDecode", "vae"),
                        ("SaveImage", "images"), ("SaveImage", "filename_prefix")):
        _required(node_inputs, node, field)
    for field in ("model", "clip", "strength_model", "strength_clip"):
        _required(node_inputs, "LoraLoader", field)
    for field in ("model", "positive", "negative", "latent_image", "denoise"):
        _required(node_inputs, "KSampler", field)

    def entries(kind: str, names: list[str], choices: set[str]) -> list[dict]:
        if len(names) != len(set(names)):
            _fail("BACKEND_CAPABILITY_UNAVAILABLE", f"Duplicate {kind} catalog IDs")
        result = []
        for name in sorted(names):
            _safe_catalog_id(name)
            available = name in choices and is_available(kind, name)
            result.append({"id": name, "available": bool(available),
                           "family": "UNKNOWN", "family_confidence": "UNKNOWN"})
        return result

    catalog = {
        "ok": True, "schema_version": SCHEMA_VERSION,
        "backend_node_identity": NODE_IDENTITY,
        "required_nodes": list(CORE_NODES),
        "checkpoints": entries("checkpoints", checkpoint_names, checkpoint_choices),
        "loras": entries("loras", lora_names, lora_choices),
        "samplers": samplers, "schedulers": schedulers,
        "product_bounds": PRODUCT_BOUNDS,
        "backend_bounds": backend_bounds,
    }
    catalog["revision"] = _digest(catalog)
    return catalog


def _check_int(value: Any, label: str, lower: int, upper: int, step: int = 1) -> int:
    if type(value) is not int or not lower <= value <= upper or value % step:
        _fail("INVALID_PARAMETER", f"{label} must be an integer in {lower}..{upper} with step {step}")
    return value


def _resolve_lora(name: str, catalog: dict) -> str:
    _safe_catalog_id(name)
    available = [entry["id"] for entry in catalog["loras"] if entry["available"]]
    if name in available:
        return name
    normalized = name.replace("\\", "/")
    exact_path = [item for item in available if item.replace("\\", "/") == normalized]
    if len(exact_path) == 1:
        return exact_path[0]
    if len(exact_path) > 1:
        _fail("LORA_AMBIGUOUS", f"LoRA '{name}' matches multiple catalog IDs")
    stem = PurePosixPath(normalized).stem
    filename = PurePosixPath(normalized).name
    has_parent = "/" in normalized
    matches = []
    for item in available:
        item_path = PurePosixPath(item.replace("\\", "/"))
        if has_parent:
            if item_path.with_suffix("").as_posix() == normalized or item_path.as_posix() == normalized:
                matches.append(item)
        elif item_path.name == filename or (not PurePosixPath(normalized).suffix and item_path.stem == stem):
            matches.append(item)
    if len(matches) == 1:
        return matches[0]
    if matches:
        _fail("LORA_AMBIGUOUS", f"LoRA '{name}' matches multiple catalog IDs")
    _fail("LORA_UNAVAILABLE", f"LoRA '{name}' is unavailable")


def _compile_prompt(raw: str, catalog: dict) -> tuple[str, list[dict]]:
    output = []
    resolved = []
    cursor = 0
    for match in TAG_RE.finditer(raw):
        output.append(raw[cursor:match.start()])
        tag = LORA_RE.fullmatch(match.group(0))
        if tag is None:
            _fail("UNSUPPORTED_PROMPT_TAG", f"Unsupported or malformed tag: {match.group(0)}")
        name = tag.group(1).strip()
        if name != tag.group(1):
            _fail("INVALID_LORA", "LoRA name must not have surrounding whitespace")
        weight = float(tag.group(2))
        if not math.isfinite(weight) or not -4 <= weight <= 4:
            _fail("INVALID_LORA", "LoRA weight must be finite and within -4..4")
        catalog_id = _resolve_lora(name, catalog)
        resolved.append({"id": catalog_id, "weight_model": weight, "weight_clip": weight})
        cursor = match.end()
    output.append(raw[cursor:])
    clean = "".join(output)
    if any(char in clean for char in "<>"):
        _fail("UNSUPPORTED_PROMPT_TAG", "Malformed or unsupported angle-bracket tag")
    return clean, resolved


def compile_basic(request: dict, catalog: dict, random_seed: Callable[[], int] | None = None) -> dict:
    """Compile only. Never imports models, queues, runs, or writes files."""
    if not isinstance(request, dict):
        _fail("INVALID_REQUEST", "Request must be a JSON object")
    missing = REQUEST_FIELDS - request.keys()
    unknown = request.keys() - REQUEST_FIELDS
    if missing or unknown:
        _fail("INVALID_REQUEST", f"Missing fields: {sorted(missing)}; unknown fields: {sorted(unknown)}")
    if not isinstance(catalog, dict) or catalog.get("ok") is not True or not isinstance(catalog.get("revision"), str):
        _fail("CATALOG_UNAVAILABLE", "Backend catalog is unavailable")
    if request["capability_revision"] != catalog["revision"]:
        _fail("CAPABILITY_CHANGED", "Backend capability revision changed; refresh the catalog")
    if not isinstance(request["request_id"], str) or not REQUEST_ID_RE.fullmatch(request["request_id"]):
        _fail("INVALID_REQUEST", "request_id must be 1..64 ASCII letters, digits, underscore, or hyphen")
    if request["mode"] != "txt2img":
        _fail("INVALID_REQUEST", "Only txt2img is supported")
    for key in ("checkpoint_id", "sampler_id", "scheduler_id", "positive_raw", "negative_raw", "seed_requested"):
        if not isinstance(request[key], str):
            _fail("INVALID_REQUEST", f"{key} must be a string")
    if len(request["positive_raw"]) > 16000 or len(request["negative_raw"]) > 16000:
        _fail("INVALID_REQUEST", "Prompt text exceeds 16000 characters")
    selected = request["checkpoint_id"]
    if not selected or selected not in {entry["id"] for entry in catalog["checkpoints"] if entry["available"]}:
        _fail("CHECKPOINT_UNAVAILABLE", f"Selected checkpoint '{selected}' is unavailable")
    if request["sampler_id"] not in catalog["samplers"] or request["scheduler_id"] not in catalog["schedulers"]:
        _fail("SAMPLING_UNAVAILABLE", "Selected sampler or scheduler is unavailable")
    bounds = catalog["backend_bounds"]
    steps = _check_int(request["steps"], "steps", max(1, int(bounds["steps"]["min"])),
                       min(100, int(bounds["steps"]["max"])))
    width = _check_int(request["width"], "width", max(256, int(bounds["width"]["min"])),
                       min(2048, int(bounds["width"]["max"])), 8)
    height = _check_int(request["height"], "height", max(256, int(bounds["height"]["min"])),
                        min(2048, int(bounds["height"]["max"])), 8)
    for dimension, value in (("width", width), ("height", height)):
        backend_step = bounds[dimension].get("step", 1)
        if type(backend_step) not in (int, float) or backend_step <= 0 or value % backend_step:
            _fail("INVALID_PARAMETER", f"{dimension} violates the backend step")
    if width * height > PRODUCT_BOUNDS["max_pixels"]:
        _fail("INVALID_PARAMETER", "Resolution exceeds the 2097152-pixel product limit")
    cfg = request["cfg"]
    if type(cfg) not in (int, float) or not math.isfinite(cfg) or not max(0, bounds["cfg"]["min"]) <= cfg <= min(30, bounds["cfg"]["max"]):
        _fail("INVALID_PARAMETER", "cfg is outside finite product/backend bounds")
    seed_text = request["seed_requested"]
    if seed_text != "-1" and (not SEED_RE.fullmatch(seed_text) or int(seed_text) > PRODUCT_BOUNDS["seed"]["max"]):
        _fail("INVALID_SEED", "seed_requested must be '-1' or a decimal string 0..4294967295")
    positive, pos_loras = _compile_prompt(request["positive_raw"], catalog)
    negative, neg_loras = _compile_prompt(request["negative_raw"], catalog)
    loras = pos_loras + neg_loras
    if len({item["id"] for item in loras}) != len(loras):
        _fail("LORA_DUPLICATE", "The same resolved LoRA appears more than once")
    if seed_text == "-1":
        seed = (random_seed or (lambda: secrets.randbelow(1 << 32)))()
        _check_int(seed, "resolved seed", 0, PRODUCT_BOUNDS["seed"]["max"])
    else:
        seed = int(seed_text)
    if seed > int(bounds["seed"]["max"]) or seed < bounds["seed"]["min"]:
        _fail("INVALID_SEED", "Seed is outside backend bounds")

    graph = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": selected}}}
    model, clip = ["1", 0], ["1", 1]
    next_id = 2
    for item in loras:
        node_id = str(next_id)
        graph[node_id] = {"class_type": "LoraLoader", "inputs": {
            "model": model, "clip": clip, "lora_name": item["id"],
            "strength_model": item["weight_model"], "strength_clip": item["weight_clip"],
        }}
        model, clip = [node_id, 0], [node_id, 1]
        next_id += 1
    pos_id, neg_id, latent_id, sampler_id, decode_id, save_id = [str(i) for i in range(next_id, next_id + 6)]
    graph[pos_id] = {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": clip}}
    graph[neg_id] = {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": clip}}
    graph[latent_id] = {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}}
    graph[sampler_id] = {"class_type": "KSampler", "inputs": {
        "model": model, "seed": seed, "steps": steps, "cfg": cfg,
        "sampler_name": request["sampler_id"], "scheduler": request["scheduler_id"],
        "positive": [pos_id, 0], "negative": [neg_id, 0],
        "latent_image": [latent_id, 0], "denoise": 1.0,
    }}
    graph[decode_id] = {"class_type": "VAEDecode", "inputs": {"samples": [sampler_id, 0], "vae": ["1", 2]}}
    graph[save_id] = {"class_type": "SaveImage", "inputs": {
        "images": [decode_id, 0], "filename_prefix": "Manga/Playable/compiled",
    }}
    return {
        "ok": True, "schema_version": SCHEMA_VERSION,
        "normalized_request": dict(request), "requested_seed": seed_text, "effective_seed": seed,
        "positive_raw": request["positive_raw"], "negative_raw": request["negative_raw"],
        "positive_clean": positive, "negative_clean": negative,
        "resolved_loras": loras, "capability_revision": catalog["revision"],
        "graph": graph, "graph_digest": _digest(graph),
    }
