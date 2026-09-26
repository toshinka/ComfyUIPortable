"""PLAY1a pure Manga txt2img catalog and graph compiler; no ComfyUI imports or execution."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
from copy import deepcopy
from dataclasses import fields, is_dataclass
from importlib import metadata
from pathlib import Path, PurePosixPath
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
WILDCARD_ENV = "TEGAKI_MANGA_WILDCARDS_DIR"
WILDCARD_TOKEN_RE = re.compile(r"__(.+?)__")
# dynamicprompts 0.31.0 does not consume backslash escapes itself.  Protect
# the two brace escapes before handing the template to its parser, then restore
# them in the effective prompt.  This is a compatibility shim, not a second
# dynamic-prompt parser.
ESCAPED_OPEN = "\ue000"
ESCAPED_CLOSE = "\ue001"


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
    try:
        from .engine_resources import resolve_engine_lora, ResourceContractError
    except (ImportError, ValueError):
        from engine_resources import resolve_engine_lora, ResourceContractError
    try:
        return resolve_engine_lora(
            name,
            catalog.get("loras", []),
            root=catalog.get("lora_root"),
            registered_roots=catalog.get("registered_roots"),
            comfy_full_path=catalog.get("comfy_full_path"),
        )
    except ResourceContractError as exc:
        _fail(exc.code, str(exc))


def _wildcard_root(override: Path | str | None = None) -> Path:
    """Resolve Manga's owned wildcard root without coupling it to Forge."""
    configured = str(override).strip() if override is not None else os.environ.get(WILDCARD_ENV, "").strip()
    if override is not None and not configured:
        _fail("WILDCARD_ROOT_UNAVAILABLE", "Manga wildcard root override is empty")
    root = Path(configured) if configured else Path(__file__).resolve().parents[2] / "manga" / "wildcards"
    try:
        root = root.expanduser().resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        _fail("WILDCARD_ROOT_UNAVAILABLE", f"Manga wildcard root cannot be resolved: {exc}")
    if not root.is_dir():
        _fail("WILDCARD_ROOT_UNAVAILABLE", f"Manga wildcard root is unavailable: {root}")
    return root


def _dynamic_prompt_api():
    """Load the installed dynamicprompts API lazily and fail capability-closed."""
    try:
        import dynamicprompts
        from dynamicprompts.commands import Command, WildcardCommand
        from dynamicprompts.generators import RandomPromptGenerator
        from dynamicprompts.parser.parse import parse
        from dynamicprompts.wildcards import WildcardManager
    except Exception as exc:
        _fail("DYNAMIC_PROMPTS_UNAVAILABLE", f"Installed dynamicprompts is unavailable: {exc}")
    try:
        version = metadata.version("dynamicprompts")
    except metadata.PackageNotFoundError:
        version = str(getattr(dynamicprompts, "__version__", "unknown"))
    return dynamicprompts, Command, WildcardCommand, RandomPromptGenerator, parse, WildcardManager, version


def _iter_dataclass_values(value: Any):
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            yield getattr(value, field.name)
    elif isinstance(value, dict):
        yield from value.values()
    elif isinstance(value, (list, tuple, set, frozenset)):
        yield from value


def _iter_wildcard_commands(command: Any, wildcard_type: type):
    if isinstance(command, wildcard_type):
        yield command
    for child in _iter_dataclass_values(command):
        if isinstance(child, str) or child is None:
            continue
        yield from _iter_wildcard_commands(child, wildcard_type)


def _safe_wildcard_name(value: Any) -> str:
    if not isinstance(value, str) or not value:
        _fail("INVALID_WILDCARD_PATH", "Wildcard identifier must be a non-empty relative name")
    if "\x00" in value or any(ord(char) < 32 or ord(char) == 127 for char in value):
        _fail("INVALID_WILDCARD_PATH", "Wildcard identifier contains a control character")
    normalized = value.replace("\\", "/")
    if value.startswith(("/", "\\")) or normalized.startswith("//") or re.match(r"^[A-Za-z]:", normalized):
        _fail("INVALID_WILDCARD_PATH", "Wildcard identifier must remain relative to the Manga wildcard root")
    parts = normalized.split("/")
    if any(part in ("", ".", "..") for part in parts) or ".." in normalized:
        _fail("INVALID_WILDCARD_PATH", "Wildcard identifier contains an unsafe path segment")
    if any(char in normalized for char in ("<", ">", "#", "$", ":", "*", "?", "[", "]")):
        _fail("INVALID_WILDCARD_PATH", "Wildcard identifier contains unsupported syntax")
    return normalized


def _protect_escaped_braces(raw: str) -> str:
    if ESCAPED_OPEN in raw or ESCAPED_CLOSE in raw:
        _fail("INVALID_PROMPT_SYNTAX", "Prompt contains reserved dynamic-prompt escape markers")
    return raw.replace(r"\{", ESCAPED_OPEN).replace(r"\}", ESCAPED_CLOSE)


def _restore_escaped_braces(value: str) -> str:
    return value.replace(ESCAPED_OPEN, "{").replace(ESCAPED_CLOSE, "}")


# LoRA directives are literal to the dynamic-prompt layer (Card
# MANGA-WILDCARD-LORA-DOUBLE-UNDERSCORE-COLLISION1).  A valid <lora:NAME:W> may
# legitimately contain "__" in NAME (e.g. Miki_Hoshii__The_iDOLM_STER_2011__epoch_8);
# dynamicprompts would read that as a __wildcard__.  Each directive that LORA_RE
# (the one LoRA grammar) accepts is swapped for an opaque placeholder before parsing
# and restored byte-for-byte afterwards; wildcard *values* get the same treatment so
# a LoRA emitted by a wildcard file survives too.  Directives whose NAME carries
# choice syntax ({ } |) are left to dynamicprompts, as before.
LORA_SPAN_OPEN = "\ue002"
LORA_SPAN_CLOSE = "\ue003"
_LORA_SPAN_RE = re.compile(r"<lora:[^<>]*>")
_LORA_PLACEHOLDER_RE = re.compile(LORA_SPAN_OPEN + r"(\d+)" + LORA_SPAN_CLOSE)


class _LoraSpanGuard:
    def __init__(self):
        self.spans: list[str] = []

    def protect(self, text: str) -> str:
        if LORA_SPAN_OPEN in text or LORA_SPAN_CLOSE in text:
            _fail("INVALID_PROMPT_SYNTAX", "Prompt contains reserved dynamic-prompt markers")

        def swap(match):
            token = match.group(0)
            tag = LORA_RE.fullmatch(token)
            if tag is None or any(mark in tag.group(1) for mark in "{}|"):
                return token
            self.spans.append(token)
            return f"{LORA_SPAN_OPEN}{len(self.spans) - 1}{LORA_SPAN_CLOSE}"

        return _LORA_SPAN_RE.sub(swap, text)

    def restore(self, text: str) -> str:
        return _LORA_PLACEHOLDER_RE.sub(lambda match: self.spans[int(match.group(1))], text)

    def guard_manager(self, manager: Any) -> Any:
        """Protect LoRA directives inside wildcard values served by ``manager``."""
        from dataclasses import replace

        original = manager.get_values

        def get_values(name):
            values = original(name)
            items = tuple(
                self.protect(item) if isinstance(item, str) else replace(item, content=self.protect(item.content))
                for item in values
            )
            return type(values).from_items(items)

        manager.get_values = get_values
        return manager


WILDCARD_SYNTAX = ("__wildcard__", "{a|b}", "nested", "weighted", "escaped_braces")


def _wildcard_source_path(collection: Any) -> Path | None:
    """Return a collection's backing path when dynamicprompts exposes one."""
    source = getattr(collection, "_path", None)
    if source is None:
        source = getattr(collection, "source", None)
    if isinstance(source, (tuple, list)):
        source = source[0] if source else None
    return Path(source) if isinstance(source, (Path, str)) else None


def _bounded_source_label(collection: Any, root: Path) -> str | None:
    source = _wildcard_source_path(collection)
    if source is None:
        return None
    try:
        resolved = source.expanduser().resolve()
        relative = resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        _fail("WILDCARD_PATH_ESCAPE", "Wildcard source escapes the Manga wildcard root")
    return relative.as_posix()


def _assert_bounded_collections(manager: Any, root: Path) -> None:
    """Reject symlinked or otherwise resolved collections outside the owned root."""
    for collection in manager.tree.map.values():
        _bounded_source_label(collection, root)


def _catalog_entry(manager: Any, root: Path, name: str, collection: Any) -> dict:
    source = _bounded_source_label(collection, root)
    try:
        values = list(collection.get_values())
    except Exception as exc:
        return {
            "name": name,
            "source": source,
            "entry_count": 0,
            "state": "ERROR",
            "error": str(exc),
        }
    return {
        "name": name,
        "source": source,
        "entry_count": len(values),
        "state": "READY" if values else "EMPTY",
    }


def list_wildcard_catalog(root: Path | str | None = None) -> dict:
    """Discover the current Manga wildcard catalog without creating an index."""
    _dynamic, _Command, _wildcard_type, _generator_type, _parse, manager_type, version = _dynamic_prompt_api()
    resolved_root = _wildcard_root(root)
    manager = manager_type(resolved_root)
    _assert_bounded_collections(manager, resolved_root)
    entries = [
        _catalog_entry(manager, resolved_root, name, manager.tree.map[name])
        for name in sorted(manager.tree.map)
    ]
    catalog = {
        "ok": True,
        "root": str(resolved_root),
        "dynamicprompts_version": version,
        "supported_syntax": list(WILDCARD_SYNTAX),
        "entries": entries,
    }
    catalog["revision"] = _digest(catalog)
    return catalog


CATALOG_RESOURCE_KINDS = {
    "CHECKPOINT": "checkpoints",
    "CHECKPOINTS": "checkpoints",
    "LORA": "loras",
    "LORAS": "loras",
    "SAMPLER": "samplers",
    "SAMPLERS": "samplers",
    "SCHEDULER": "schedulers",
    "SCHEDULERS": "schedulers",
}


def _resource_kind(kind: Any) -> tuple[str, str] | None:
    if not isinstance(kind, str):
        return None
    field = CATALOG_RESOURCE_KINDS.get(kind.upper())
    if field is None:
        return None
    return kind.upper().rstrip("S"), field


def _catalog_resource_entries(catalog: Any, canonical_kind: str, field: str) -> list[dict] | None:
    """Read resource entries from either a live catalog or its plain snapshot."""
    if not isinstance(catalog, dict):
        return None
    if isinstance(catalog.get("resources"), dict):
        raw = catalog["resources"].get(canonical_kind)
    else:
        raw = catalog.get(field)
    if not isinstance(raw, list):
        return None
    entries = []
    for item in raw:
        if field in ("samplers", "schedulers") and isinstance(item, str) and item:
            entries.append({"canonical_id": item, "display_name": item, "available": True})
            continue
        if not isinstance(item, dict) or not isinstance(item.get("id", item.get("canonical_id")), str):
            return None
        identifier = item.get("id", item.get("canonical_id"))
        available = item.get("available", True)
        display_name = item.get("display_name", identifier)
        if type(available) is not bool or not isinstance(display_name, str):
            return None
        if canonical_kind in ("CHECKPOINT", "LORA"):
            try:
                _safe_catalog_id(identifier)
            except GenerationContractError:
                return None
        entries.append({
            "canonical_id": identifier,
            "display_name": display_name,
            "available": available,
        })
    return entries


def get_catalog_snapshot(catalog: dict) -> dict:
    """Return a detached snapshot of currently available Manga resources."""
    if not isinstance(catalog, dict) or catalog.get("ok") is not True or not isinstance(catalog.get("revision"), str):
        _fail("CATALOG_UNAVAILABLE", "Backend catalog is unavailable")
    resources = {}
    for kind, field in (("CHECKPOINT", "checkpoints"), ("LORA", "loras"),
                        ("SAMPLER", "samplers"), ("SCHEDULER", "schedulers")):
        entries = _catalog_resource_entries(catalog, kind, field)
        if entries is None:
            _fail("CATALOG_UNAVAILABLE", f"Catalog resource list '{field}' is unavailable")
        resources[kind] = [
            {
                "canonical_id": entry["canonical_id"],
                "display_name": entry["display_name"],
                "available": True,
            }
            for entry in entries
            if entry["available"]
        ]
    snapshot = {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "source_revision": catalog["revision"],
        "resources": deepcopy(resources),
    }
    snapshot["revision"] = _digest(snapshot)
    return snapshot


def _resolution_result(kind: Any, requested_id: Any, state: str, reason: str,
                      canonical_id: str | None = None, display_name: str | None = None) -> dict:
    return {
        "ok": state == "AVAILABLE",
        "kind": kind,
        "requested_id": requested_id,
        "canonical_id": canonical_id,
        "display_name": display_name,
        "state": state,
        "reason": reason,
    }


def resolve_catalog_resource(kind: Any, requested_id: Any, catalog: dict) -> dict:
    """Resolve one resource by exact canonical ID, without fallback or filesystem access."""
    parsed_kind = _resource_kind(kind)
    if parsed_kind is None:
        return _resolution_result(kind, requested_id, "INVALID_REQUEST", "INVALID_KIND")
    canonical_kind, field = parsed_kind
    if not isinstance(requested_id, str) or not requested_id:
        return _resolution_result(canonical_kind, requested_id, "INVALID_REQUEST", "EMPTY_REQUEST")
    if canonical_kind in ("CHECKPOINT", "LORA"):
        try:
            _safe_catalog_id(requested_id)
        except GenerationContractError:
            return _resolution_result(canonical_kind, requested_id, "INVALID_REQUEST", "INVALID_ID")
    entries = _catalog_resource_entries(catalog, canonical_kind, field)
    if entries is None:
        return _resolution_result(canonical_kind, requested_id, "INVALID_REQUEST", "CATALOG_UNAVAILABLE")
    exact = [entry for entry in entries if entry["canonical_id"] == requested_id]
    available = [entry for entry in exact if entry["available"]]
    if len(exact) > 1 or len(available) > 1:
        return _resolution_result(canonical_kind, requested_id, "AMBIGUOUS", "AMBIGUOUS")
    if len(available) == 1:
        entry = available[0]
        return _resolution_result(canonical_kind, requested_id, "AVAILABLE", "EXACT_MATCH",
                                  entry["canonical_id"], entry["display_name"])
    return _resolution_result(
        canonical_kind,
        requested_id,
        "MISSING",
        "STALE_SELECTION" if exact else "NOT_FOUND",
    )


def resolve_recovered_resources(hints: Any, catalog: dict) -> dict:
    """Resolve metadata-recovery hints without applying them to authoring or generation."""
    if not isinstance(hints, dict):
        return {"ok": False, "checkpoint": None, "loras": [],
                "errors": [{"reason": "INVALID_HINTS"}]}
    checkpoint_hint = hints.get("checkpoint")
    checkpoint = None if checkpoint_hint is None else resolve_catalog_resource(
        "CHECKPOINT", checkpoint_hint, catalog,
    )
    raw_loras = hints.get("lora_references")
    if raw_loras is None:
        raw_loras = hints.get("prompt_lora_references", [])
    if raw_loras is None:
        raw_loras = []
    if not isinstance(raw_loras, list):
        return {"ok": False, "checkpoint": checkpoint, "loras": [],
                "errors": [{"reason": "INVALID_LORA_HINTS"}]}
    loras = []
    for hint in raw_loras:
        requested = hint.get("name") if isinstance(hint, dict) else hint
        resolution = resolve_catalog_resource("LORA", requested, catalog)
        loras.append({"hint": deepcopy(hint), "resolution": resolution})
    resolutions = ([checkpoint] if checkpoint is not None else []) + [item["resolution"] for item in loras]
    errors = [
        {"kind": item["kind"], "requested_id": item["requested_id"],
         "state": item["state"], "reason": item["reason"]}
        for item in resolutions if not item["ok"]
    ]
    return {"ok": not errors, "checkpoint": checkpoint, "loras": loras, "errors": errors}


def _headless_error(exc: Exception) -> dict:
    code = getattr(exc, "code", "INVALID_PROMPT_SYNTAX")
    return {"code": code, "message": str(exc)}


def _validate_wildcard_commands(parsed: Any, wildcard_type: type, manager: Any, root: Path) -> list[dict]:
    references = []
    seen = set()
    for wildcard in _iter_wildcard_commands(parsed, wildcard_type):
        name = wildcard.wildcard
        if not isinstance(name, str):
            continue
        name = _safe_wildcard_name(name)
        if name in seen:
            continue
        seen.add(name)
        if name not in manager.get_collection_names():
            _fail("WILDCARD_NOT_FOUND", f"Wildcard '{name}' was not found in the Manga wildcard root")
        collection = manager.tree.map.get(name)
        values = list(manager.get_values(name))
        if not values:
            _fail("WILDCARD_EMPTY", f"Wildcard '{name}' has no usable entries")
        references.append({
            "name": name,
            "source": _bounded_source_label(collection, root) if collection is not None else None,
            "entry_count": len(values),
        })
    return references


def validate_wildcard_text(
    text: str,
    catalog: dict | None = None,
    root: Path | str | None = None,
) -> dict:
    """Validate dynamic-prompt syntax and references without expanding or writing."""
    result = {
        "ok": False,
        "text": text,
        "wildcards": [],
        "warnings": [],
        "errors": [],
        "trace": [],
    }
    try:
        if not isinstance(text, str):
            _fail("INVALID_PROMPT_SYNTAX", "Wildcard text must be a string")
        _dynamic, _Command, wildcard_type, _generator_type, parse, manager_type, version = _dynamic_prompt_api()
        catalog_root = catalog.get("root") if isinstance(catalog, dict) else None
        resolved_root = _wildcard_root(root if root is not None else catalog_root)
        manager = manager_type(resolved_root)
        _assert_bounded_collections(manager, resolved_root)
        guard = _LoraSpanGuard()
        guard.guard_manager(manager)
        parsed = parse(_protect_escaped_braces(guard.protect(text)))
        result["wildcards"] = _validate_wildcard_commands(parsed, wildcard_type, manager, resolved_root)
        result["dynamicprompts_version"] = version
        result["wildcard_root"] = str(resolved_root)
        result["ok"] = True
    except Exception as exc:
        result["errors"].append(_headless_error(exc))
    return result


def _trace_command_text(command: Any) -> str:
    literal = getattr(command, "literal", None)
    if isinstance(literal, str):
        return literal
    return str(command)


def _trace_expand(
    protected: str,
    manager: Any,
    root: Path,
    dynamic_seed: int,
    trace: list[dict],
    max_depth: int = 32,
) -> str:
    """Run the installed random sampler with a bounded, informational trace."""
    from random import Random

    from dynamicprompts.enums import SamplingMethod
    from dynamicprompts.samplers.combinatorial import CombinatorialSampler
    from dynamicprompts.samplers.cycle import CyclicalSampler
    from dynamicprompts.samplers.random import RandomSampler
    from dynamicprompts.sampling_context import SamplingContext

    class TraceWildcardMixin:
        def _get_wildcard(self, command, context):
            wildcard_path = next(iter(context.sample_prompts(command.wildcard, 1))).text
            wildcard_path = _safe_wildcard_name(wildcard_path)
            context = context.with_variables(command.variables)
            if wildcard_path not in context.wildcard_manager.get_collection_names():
                _fail("WILDCARD_NOT_FOUND", f"Wildcard '{wildcard_path}' was not found in the Manga wildcard root")
            values = context.wildcard_manager.get_values(wildcard_path)
            if not values:
                _fail("WILDCARD_EMPTY", f"Wildcard '{wildcard_path}' has no usable entries")
            if wildcard_path in self._wildcard_stack:
                _fail("WILDCARD_CYCLE", f"Wildcard '{wildcard_path}' references itself recursively")
            if len(self._wildcard_stack) >= self._max_wildcard_depth:
                _fail("WILDCARD_RECURSION_LIMIT", "Wildcard expansion exceeded the bounded depth")
            source = None
            collection = context.wildcard_manager.tree.map.get(wildcard_path)
            if collection is not None:
                source = _bounded_source_label(collection, self._wildcard_root)
            chooser = getattr(self, "_get_wildcard_choice_generator", None)
            generator = chooser(context, values) if chooser else iter(values.iterate_string_values_weighted())
            self._wildcard_stack.append(wildcard_path)
            try:
                while True:
                    selected = next(generator)
                    self._trace.append({
                        "kind": "wildcard",
                        "name": wildcard_path,
                        "selected": selected,
                        "source": source,
                    })
                    yield from context.sample_prompts(selected, 1)
            finally:
                self._wildcard_stack.pop()

    class TraceRandomSampler(TraceWildcardMixin, RandomSampler):
        def _get_variant_choices(self, values, weights, num_choices, rand):
            selected = super()._get_variant_choices(values, weights, num_choices, rand)
            selected_items = []
            for item in selected:
                index = next((i for i, candidate in enumerate(values) if candidate is item), None)
                selected_items.append({"index": index, "value": _trace_command_text(item)})
            self._trace.append({
                "kind": "choice",
                "alternatives_count": len(values),
                "selected": selected_items,
            })
            return selected

    class TraceCombinatorialSampler(TraceWildcardMixin, CombinatorialSampler):
        pass

    class TraceCyclicalSampler(TraceWildcardMixin, CyclicalSampler):
        pass

    samplers = {
        SamplingMethod.RANDOM: TraceRandomSampler(),
        SamplingMethod.COMBINATORIAL: TraceCombinatorialSampler(),
        SamplingMethod.CYCLICAL: TraceCyclicalSampler(),
    }
    wildcard_stack = []
    for sampler in samplers.values():
        sampler._trace = trace
        sampler._wildcard_root = root
        sampler._wildcard_stack = wildcard_stack
        sampler._max_wildcard_depth = max_depth
    context = SamplingContext(
        default_sampling_method=SamplingMethod.RANDOM,
        wildcard_manager=manager,
        rand=Random(dynamic_seed),
        samplers=samplers,
    )
    result = next(iter(context.sample_prompts(protected, 1)), None)
    if result is None:
        return ""
    return result.text


def _resolve_headless_seed(options: dict) -> tuple[int | None, int]:
    requested = options.get("seed")
    random_source = options.get("random_source", options.get("random"))
    if requested is None or requested == -1:
        if random_source is None:
            effective = secrets.randbelow(1 << 32)
        else:
            if not callable(random_source):
                _fail("INVALID_SEED", "random_source must be callable")
            effective = random_source()
        _check_int(effective, "wildcard seed", 0, PRODUCT_BOUNDS["seed"]["max"])
        return requested, effective
    _check_int(requested, "wildcard seed", 0, PRODUCT_BOUNDS["seed"]["max"])
    return requested, requested


def expand_wildcard_text(
    text: str,
    options: dict | None = None,
    *,
    root: Path | str | None = None,
    seed: int | None = None,
    domain: str = "wildcard",
) -> dict:
    """Expand a bounded wildcard expression through the existing TEGAKI owner."""
    supplied = dict(options or {})
    if seed is not None:
        supplied["seed"] = seed
    if root is not None:
        supplied["root"] = root
    if "root" not in supplied and isinstance(supplied.get("catalog"), dict):
        supplied["root"] = supplied["catalog"].get("root")
    supplied.setdefault("domain", domain)
    trace: list[dict] = []
    result = {
        "ok": False,
        "input_text": text,
        "expanded_text": None,
        "expanded": False,
        "used_wildcards": [],
        "choice_selections": [],
        "warnings": [],
        "errors": [],
        "trace": trace,
    }
    try:
        if not isinstance(text, str):
            _fail("INVALID_PROMPT_SYNTAX", "Wildcard text must be a string")
        _dynamic, _Command, wildcard_type, _generator_type, parse, manager_type, version = _dynamic_prompt_api()
        resolved_root = _wildcard_root(supplied.get("root"))
        manager = manager_type(resolved_root)
        _assert_bounded_collections(manager, resolved_root)
        guard = _LoraSpanGuard()
        guard.guard_manager(manager)
        protected = _protect_escaped_braces(guard.protect(text))
        try:
            parsed = parse(protected)
        except Exception as exc:
            _fail("INVALID_PROMPT_SYNTAX", f"Dynamic prompt syntax is invalid: {exc}")
        _validate_wildcard_commands(parsed, wildcard_type, manager, resolved_root)
        requested_seed, effective_seed = _resolve_headless_seed(supplied)
        dynamic_seed = _derive_dynamic_seed(effective_seed, f"headless:{supplied['domain']}")
        expanded_protected = _trace_expand(protected, manager, resolved_root, dynamic_seed, trace)
        try:
            expanded_parsed = parse(expanded_protected)
        except Exception as exc:
            _fail("INVALID_PROMPT_SYNTAX", f"Expanded dynamic prompt is invalid: {exc}")
        _validate_wildcard_commands(expanded_parsed, wildcard_type, manager, resolved_root)
        if WILDCARD_TOKEN_RE.search(expanded_protected):
            _fail("WILDCARD_NOT_FOUND", "Expanded prompt still contains an unresolved wildcard")
        expanded_text = guard.restore(_restore_escaped_braces(expanded_protected))
        result.update({
            "ok": True,
            "expanded_text": expanded_text,
            "expanded": bool(trace),
            "used_wildcards": [entry["name"] for entry in trace if entry["kind"] == "wildcard"],
            "choice_selections": [entry for entry in trace if entry["kind"] == "choice"],
            "requested_seed": requested_seed,
            "effective_seed": effective_seed,
            "dynamic_seed": dynamic_seed,
            "dynamicprompts_version": version,
            "wildcard_root": str(resolved_root),
        })
    except Exception as exc:
        result["errors"].append(_headless_error(exc))
    return result


def _derive_dynamic_seed(seed: int, domain: str) -> int:
    """Derive independent, stable RNG domains from the effective image seed."""
    digest = hashlib.sha256(f"tegaki-manga-play4:{domain}:{seed}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _expand_dynamic_prompt(raw: str, effective_seed: int, domain: str) -> tuple[str, str, str]:
    """Expand one basic/global prompt through installed dynamicprompts only."""
    _dynamic, _Command, wildcard_type, generator_type, parse, manager_type, version = _dynamic_prompt_api()
    root = _wildcard_root()
    manager = manager_type(root)
    guard = _LoraSpanGuard()
    guard.guard_manager(manager)
    protected = _protect_escaped_braces(guard.protect(raw))
    try:
        parsed = parse(protected)
    except Exception as exc:
        _fail("INVALID_PROMPT_SYNTAX", f"Dynamic prompt syntax is invalid: {exc}")

    def validate_commands(command):
        for wildcard in _iter_wildcard_commands(command, wildcard_type):
            name = wildcard.wildcard
            if isinstance(name, str):
                name = _safe_wildcard_name(name)
                if name not in manager.get_collection_names() or not manager.get_values(name):
                    _fail("WILDCARD_NOT_FOUND", f"Wildcard '{name}' was not found in the Manga wildcard root")

    validate_commands(parsed)
    dynamic_seed = _derive_dynamic_seed(effective_seed, domain)
    if protected == "":
        return "", str(root), version
    try:
        expanded_protected = generator_type(wildcard_manager=manager, seed=dynamic_seed).generate(
            protected, num_images=1
        )[0]
    except GenerationContractError:
        raise
    except Exception as exc:
        # Parser failures in wildcard contents are syntax failures; all other
        # missing/invalid wildcard cases are reported without leaking literals.
        message = str(exc)
        code = "INVALID_PROMPT_SYNTAX" if "parse" in message.lower() or "expected" in message.lower() else "WILDCARD_NOT_FOUND"
        _fail(code, f"Dynamic prompt expansion failed: {exc}")

    try:
        expanded_parsed = parse(expanded_protected)
    except Exception as exc:
        _fail("INVALID_PROMPT_SYNTAX", f"Expanded dynamic prompt is invalid: {exc}")
    validate_commands(expanded_parsed)
    if WILDCARD_TOKEN_RE.search(expanded_protected):
        _fail("WILDCARD_NOT_FOUND", "Expanded prompt still contains an unresolved wildcard")
    return guard.restore(_restore_escaped_braces(expanded_protected)), str(root), version


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


def format_lora_strength(strength: Any) -> str:
    """Canonical visible strength text (1 -> '1.0', 0.85 -> '0.85'); mirrors the UI."""
    if type(strength) not in (int, float) or not math.isfinite(strength) or not -4 <= strength <= 4:
        _fail("INVALID_LORA", "LoRA weight must be finite and within -4..4")
    value = float(strength) or 0.0
    text = ("%.4f" % value).rstrip("0")
    return text + "0" if text.endswith(".") else text


def format_lora_directive(canonical_id: str, strength: Any = 1.0) -> str:
    """Visible prompt directive for one canonical LoRA selection.

    This is the reusable selection -> prompt representation (Owner UI today,
    CAST default attachments later).  Parsing/resolution stays in
    ``_compile_prompt``; the result is guaranteed to round-trip through LORA_RE.
    """
    _safe_catalog_id(canonical_id)
    directive = f"<lora:{canonical_id}:{format_lora_strength(strength)}>"
    if LORA_RE.fullmatch(directive) is None:
        _fail("INVALID_LORA", f"LoRA ID cannot be expressed as a prompt directive: {canonical_id!r}")
    return directive


def split_lora_directives(raw: str) -> tuple[str, list[str]]:
    """Separate well-formed LoRA directives from ordinary prompt text.

    Text without directives is returned unchanged.  When directives are
    removed, only the empty comma separators they leave behind are collapsed.
    Malformed ``<...>`` tags stay in place so the canonical compiler rejects them.
    """
    if not isinstance(raw, str):
        _fail("INVALID_DOCUMENT", "Prompt must be a string")
    directives = [match.group(0) for match in LORA_RE.finditer(raw)]
    if not directives:
        return raw, []
    text = LORA_RE.sub("", raw)
    text = re.sub(r"[ \t]*,(?:[ \t]*,)+", ",", text)
    text = re.sub(r"^[\s,]+|[\s,]+$", "", text)
    return text, directives


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
    if seed_text == "-1":
        seed = (random_seed or (lambda: secrets.randbelow(1 << 32)))()
        _check_int(seed, "resolved seed", 0, PRODUCT_BOUNDS["seed"]["max"])
    else:
        seed = int(seed_text)
    if seed > int(bounds["seed"]["max"]) or seed < bounds["seed"]["min"]:
        _fail("INVALID_SEED", "Seed is outside backend bounds")

    # Dynamic Prompt expansion is deliberately before strict LoRA extraction.
    # Each side receives an independent deterministic RNG domain derived from
    # the one effective image seed, so positive choices cannot perturb
    # negative choices.
    positive_expanded, wildcard_root, dynamic_version = _expand_dynamic_prompt(
        request["positive_raw"], seed, "positive"
    )
    negative_expanded, negative_root, _ = _expand_dynamic_prompt(
        request["negative_raw"], seed, "negative"
    )
    if wildcard_root != negative_root:
        _fail("WILDCARD_ROOT_UNAVAILABLE", "Positive and negative prompts resolved different wildcard roots")
    positive, pos_loras = _compile_prompt(positive_expanded, catalog)
    negative, neg_loras = _compile_prompt(negative_expanded, catalog)
    loras = pos_loras + neg_loras
    if len({item["id"] for item in loras}) != len(loras):
        _fail("LORA_DUPLICATE", "The same resolved LoRA appears more than once")

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
        "positive_expanded": positive_expanded, "negative_expanded": negative_expanded,
        "positive_clean": positive, "negative_clean": negative,
        "resolved_loras": loras, "capability_revision": catalog["revision"],
        "wildcard_root": wildcard_root, "dynamicprompts_version": dynamic_version,
        "dynamic_seed_domains": {
            "positive": _derive_dynamic_seed(seed, "positive"),
            "negative": _derive_dynamic_seed(seed, "negative"),
        },
        "graph": graph, "graph_digest": _digest(graph),
    }
