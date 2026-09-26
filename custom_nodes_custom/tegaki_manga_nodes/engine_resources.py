"""Engine-scoped model resource roots and lazy LoRA browsing.

This is the one thin boundary between logical resources and physical roots:

    engine=illustrious, resource=lora  ->  ComfyUI folder "loras" root

Physical roots are registered with ComfyUI through ``extra_model_paths.yaml``;
this module only *selects* which registered root belongs to an engine/resource
pair and refuses to serve a root ComfyUI cannot load from.  Consumers use the
logical pair and canonical relative IDs, never the Windows path.  Migrating a
collection (for example to ``E:\\DATA``) means changing the root mapping (or its
environment override) plus the ComfyUI registration, not the consumers.

Browsing is intentionally shallow: one ``os.scandir`` of the requested folder.
It never recurses, hashes, opens model files, or writes anything.  Pure Python;
no ComfyUI imports so the contract is testable offline.
"""

from __future__ import annotations

import os
from pathlib import PurePosixPath
from typing import Callable, Iterable, Optional


class ResourceContractError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


# engine -> resource -> ComfyUI folder name, root override env var, default root.
ENGINE_RESOURCE_ROOTS = {
    "illustrious": {
        "lora": {
            "comfy_folder": "loras",
            "env": "TEGAKI_ILLUSTRIOUS_LORA_ROOT",
            "default_root": "D:/Models/Lora",
        },
    },
}

DEFAULT_LORA_EXTENSIONS = (".safetensors",)
# Owner-proven sidecar convention: <lora-stem>.preview.png beside the LoRA file.
PREVIEW_SUFFIX = ".preview.png"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PREVIEW_BYTES = 16 * 1024 * 1024
MAX_ID_LENGTH = 1024
_FORBIDDEN_ID_CHARS = set('<>:"|?*')


def _fail(code: str, message: str) -> None:
    raise ResourceContractError(code, message)


def _norm(path: str) -> str:
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


def resource_spec(engine: str, resource: str) -> dict:
    spec = ENGINE_RESOURCE_ROOTS.get(engine, {}).get(resource)
    if spec is None:
        _fail("RESOURCE_UNSUPPORTED", f"No {resource!r} resource is registered for engine {engine!r}")
    return spec


def resolve_resource_root(
    engine: str,
    resource: str,
    registered_roots: Iterable[str],
    environ: Optional[dict] = None,
) -> str:
    """Return the engine/resource root, verified to be a ComfyUI-registered folder."""
    spec = resource_spec(engine, resource)
    env = os.environ if environ is None else environ
    configured = str(env.get(spec["env"], "") or "").strip() or spec["default_root"]
    if not os.path.isdir(configured):
        _fail("RESOURCE_ROOT_UNAVAILABLE", f"{engine}/{resource} root is unavailable")
    wanted = _norm(configured)
    for registered in registered_roots or ():
        if isinstance(registered, str) and registered and _norm(registered) == wanted:
            return os.path.realpath(os.path.abspath(configured))
    _fail(
        "RESOURCE_ROOT_UNREGISTERED",
        f"{engine}/{resource} root is not registered with ComfyUI folder '{spec['comfy_folder']}'",
    )


def normalize_relative_id(value: str, *, allow_empty: bool = False) -> str:
    """Canonical relative identity: forward slashes, no traversal, no drive/absolute."""
    if not isinstance(value, str):
        _fail("INVALID_RESOURCE_ID", "Resource ID must be a string")
    if len(value) > MAX_ID_LENGTH:
        _fail("INVALID_RESOURCE_ID", "Resource ID is too long")
    text = value.replace("\\", "/")
    if text == "":
        if allow_empty:
            return ""
        _fail("INVALID_RESOURCE_ID", "Resource ID must not be empty")
    if text.startswith("/") or any(ch in _FORBIDDEN_ID_CHARS for ch in text):
        _fail("RESOURCE_PATH_OUTSIDE_ROOT", "Resource ID must be relative to the resource root")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in text):
        _fail("INVALID_RESOURCE_ID", "Resource ID contains control characters")
    parts = text.split("/")
    if any(part in ("", ".", "..") or part != part.strip() for part in parts):
        _fail("RESOURCE_PATH_OUTSIDE_ROOT", "Resource ID contains an invalid or traversal segment")
    return "/".join(parts)


def resolve_within_root(root: str, relative_id: str, *, allow_empty: bool = False) -> str:
    """Map a canonical relative ID to a real path that must stay inside ``root``."""
    canonical = normalize_relative_id(relative_id, allow_empty=allow_empty)
    real_root = os.path.realpath(os.path.abspath(root))
    candidate = os.path.realpath(os.path.join(real_root, *canonical.split("/"))) if canonical else real_root
    try:
        inside = os.path.commonpath([os.path.normcase(real_root), os.path.normcase(candidate)]) == os.path.normcase(real_root)
    except ValueError:
        inside = False
    if not inside:
        _fail("RESOURCE_PATH_OUTSIDE_ROOT", "Resource path escapes the resource root")
    return candidate


def canonical_id_for_path(root: str, path: str) -> str:
    """Canonical ID of an on-disk file: its path relative to the root, '/'-separated."""
    real_root = os.path.realpath(os.path.abspath(root))
    real_path = os.path.realpath(os.path.abspath(path))
    try:
        rel = os.path.relpath(real_path, real_root)
    except ValueError:
        _fail("RESOURCE_PATH_OUTSIDE_ROOT", "Resource path is on a different drive than the root")
    return normalize_relative_id(rel.replace(os.sep, "/"))


def list_lora_directory(
    root: str,
    relative_dir: str = "",
    *,
    extensions: Iterable[str] = DEFAULT_LORA_EXTENSIONS,
    comfy_full_path: Optional[Callable[[str], Optional[str]]] = None,
) -> dict:
    """List ONE folder: immediate child folders and LoRA files. Never recurses.

    ``comfy_full_path`` (ComfyUI ``folder_paths.get_full_path('loras', id)``) lets
    the listing mark an entry unavailable when ComfyUI would load a *different*
    file for the same relative name (shadowed by another registered root).
    """
    folder = normalize_relative_id(relative_dir or "", allow_empty=True)
    directory = resolve_within_root(root, folder, allow_empty=True)
    if not os.path.isdir(directory):
        _fail("RESOURCE_PATH_NOT_FOUND", f"LoRA folder '{folder}' does not exist")
    allowed = {ext.lower() for ext in extensions}
    folders, loras = [], []
    try:
        entries = list(os.scandir(directory))
    except OSError as exc:
        _fail("RESOURCE_PATH_UNREADABLE", f"LoRA folder '{folder}' cannot be read: {exc.strerror or exc}")
    # Previews are detected from this one folder's names only (no extra walk/stat).
    preview_names = {}
    for entry in entries:
        if entry.name.casefold().endswith(PREVIEW_SUFFIX):
            try:
                if entry.is_file():
                    preview_names[entry.name[: -len(PREVIEW_SUFFIX)].casefold()] = True
            except OSError:
                continue
    for entry in entries:
        name = entry.name
        child_id = f"{folder}/{name}" if folder else name
        try:
            child_id = normalize_relative_id(child_id)
        except ResourceContractError:
            continue  # names the prompt grammar cannot carry are not offered
        try:
            if entry.is_dir():
                try:
                    resolve_within_root(root, child_id)
                except ResourceContractError:
                    continue
                folders.append({"id": child_id, "name": name})
                continue
            if not entry.is_file():
                continue
        except OSError:
            continue
        stem, ext = os.path.splitext(name)
        if ext.lower() not in allowed:
            continue
        available = True
        if comfy_full_path is not None:
            try:
                resolved = comfy_full_path(child_id)
            except Exception:
                resolved = None
            available = bool(resolved) and _norm(resolved) == _norm(entry.path)
        loras.append({"id": child_id, "name": stem, "filename": name, "folder": folder, "available": available,
                      "preview": stem.casefold() in preview_names})
    folders.sort(key=lambda item: (item["name"].casefold(), item["name"]))
    loras.sort(key=lambda item: (item["name"].casefold(), item["id"]))
    parent = None if folder == "" else ("/".join(folder.split("/")[:-1]))
    return {"ok": True, "folder": folder, "parent": parent, "folders": folders, "loras": loras}


def resolve_lora_preview(
    root: str,
    lora_id: str,
    *,
    extensions: Iterable[str] = DEFAULT_LORA_EXTENSIONS,
) -> str:
    """Real path of the ``<stem>.preview.png`` sidecar for ONE canonical LoRA ID.

    Only the sidecar derived from a LoRA ID can be addressed; arbitrary files,
    traversal, non-LoRA IDs and non-PNG content fail closed.  Model files are
    never opened.
    """
    canonical = normalize_relative_id(lora_id)
    parts = canonical.split("/")
    stem, ext = os.path.splitext(parts[-1])
    if not stem or ext.lower() not in {e.lower() for e in extensions}:
        _fail("RESOURCE_PREVIEW_UNSUPPORTED", "Previews are only served for LoRA files")
    sidecar_id = "/".join(parts[:-1] + [stem + PREVIEW_SUFFIX])
    path = resolve_within_root(root, sidecar_id)
    if not os.path.isfile(path):
        _fail("RESOURCE_PREVIEW_NOT_FOUND", "No preview sidecar for this LoRA")
    if os.path.getsize(path) > MAX_PREVIEW_BYTES:
        _fail("RESOURCE_PREVIEW_UNSUPPORTED", "Preview sidecar is too large")
    with open(path, "rb") as handle:
        if handle.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
            _fail("RESOURCE_PREVIEW_UNSUPPORTED", "Preview sidecar is not a PNG image")
    return path


def lora_preview_path(
    engine: str,
    lora_id: str,
    registered_roots: Iterable[str],
    *,
    extensions: Iterable[str] = DEFAULT_LORA_EXTENSIONS,
    environ: Optional[dict] = None,
) -> str:
    """HTTP-facing preview resolver; the returned path stays inside the backend."""
    root = resolve_resource_root(engine, "lora", registered_roots, environ=environ)
    return resolve_lora_preview(root, lora_id, extensions=extensions)


def browse_lora_payload(
    engine: str,
    relative_dir: str,
    registered_roots: Iterable[str],
    *,
    extensions: Iterable[str] = DEFAULT_LORA_EXTENSIONS,
    comfy_full_path: Optional[Callable[[str], Optional[str]]] = None,
    environ: Optional[dict] = None,
) -> dict:
    """HTTP-facing payload. The physical root is never returned to the client."""
    root = resolve_resource_root(engine, "lora", registered_roots, environ=environ)
    listing = list_lora_directory(root, relative_dir, extensions=extensions, comfy_full_path=comfy_full_path)
    listing.update({"engine": engine, "resource": "lora"})
    return listing


def is_path_within_root(root: str, candidate_path: str) -> bool:
    """Return True if candidate_path is strictly inside root."""
    try:
        real_root = os.path.realpath(os.path.abspath(root))
        real_candidate = os.path.realpath(os.path.abspath(candidate_path))
        return os.path.commonpath([os.path.normcase(real_root), os.path.normcase(real_candidate)]) == os.path.normcase(real_root)
    except (ValueError, OSError):
        return False


def resolve_engine_lora_root(
    engine: str = "illustrious",
    registered_roots: Optional[Iterable[str]] = None,
    environ: Optional[dict] = None,
) -> str:
    """Return the engine/resource root, verified to exist and optionally registered with ComfyUI."""
    if registered_roots is not None:
        return resolve_resource_root(engine, "lora", registered_roots, environ=environ)
    spec = resource_spec(engine, "lora")
    env = os.environ if environ is None else environ
    configured = str(env.get(spec["env"], "") or "").strip() or spec["default_root"]
    if not os.path.isdir(configured):
        _fail("RESOURCE_ROOT_UNAVAILABLE", f"{engine}/lora root is unavailable")
    return os.path.realpath(os.path.abspath(configured))


def resolve_engine_lora(
    name: str,
    catalog_loras: Iterable[dict],
    *,
    engine: str = "illustrious",
    root: Optional[str] = None,
    registered_roots: Optional[Iterable[str]] = None,
    comfy_full_path: Optional[Callable[[str], Optional[str]]] = None,
    environ: Optional[dict] = None,
) -> str:
    """Resolve a generation-time LoRA token through the trusted engine root boundary.

    Enforces that:
    1. The token is relative, non-traversing, and valid syntax.
    2. The token resolves ONLY against assets belonging to the engine's trusted root.
    3. Any out-of-root ComfyUI entry (even if registered in ComfyUI or a unique basename)
       is strictly rejected (fails closed).
    4. Ambiguous matches within the engine root fail with LORA_AMBIGUOUS.
    5. Returns the exact ComfyUI loadable string for LoraLoader.
    """
    if not isinstance(name, str) or not name or name.strip() != name:
        _fail("INVALID_CATALOG_ID", "Catalog ID must be a non-empty relative name")

    canonical = normalize_relative_id(name)

    if root is None:
        root_dir = resolve_engine_lora_root(engine, registered_roots=registered_roots, environ=environ)
    else:
        root_dir = os.path.realpath(os.path.abspath(root))
        if not os.path.isdir(root_dir):
            _fail("RESOURCE_ROOT_UNAVAILABLE", f"{engine}/lora root is unavailable")

    if comfy_full_path is None:
        try:
            import folder_paths
            live_roots = [os.path.normcase(os.path.realpath(os.path.abspath(r))) for r in folder_paths.get_folder_paths("loras") if r]
            if os.path.normcase(root_dir) in live_roots:
                comfy_full_path = lambda item: folder_paths.get_full_path("loras", item)
        except Exception:
            pass

    in_root_candidates: list[str] = []
    for entry in catalog_loras or ():
        if not isinstance(entry, dict) or not entry.get("available"):
            continue
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id:
            continue

        resolved_path = None
        if comfy_full_path is not None:
            try:
                resolved_path = comfy_full_path(entry_id)
            except Exception:
                resolved_path = None
        else:
            try:
                entry_canonical = normalize_relative_id(entry_id)
                candidate_path = resolve_within_root(root_dir, entry_canonical)
                if os.path.isfile(candidate_path):
                    resolved_path = candidate_path
            except ResourceContractError:
                resolved_path = None

        if resolved_path and os.path.isfile(resolved_path) and is_path_within_root(root_dir, resolved_path):
            in_root_candidates.append(entry_id)

    if name in in_root_candidates:
        return name

    exact_matches = [
        item for item in in_root_candidates
        if item.replace("\\", "/") == canonical
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        _fail("LORA_AMBIGUOUS", f"LoRA '{name}' matches multiple catalog IDs")

    stem = PurePosixPath(canonical).stem
    filename = PurePosixPath(canonical).name
    has_parent = "/" in canonical
    matches = []
    for item in in_root_candidates:
        item_norm = item.replace("\\", "/")
        item_path = PurePosixPath(item_norm)
        if has_parent:
            if item_path.with_suffix("").as_posix() == canonical or item_path.as_posix() == canonical:
                matches.append(item)
        elif item_path.name == filename or (not PurePosixPath(canonical).suffix and item_path.stem == stem):
            matches.append(item)

    if len(matches) == 1:
        return matches[0]
    if matches:
        _fail("LORA_AMBIGUOUS", f"LoRA '{name}' matches multiple catalog IDs")
    _fail("LORA_UNAVAILABLE", f"LoRA '{name}' is unavailable")
