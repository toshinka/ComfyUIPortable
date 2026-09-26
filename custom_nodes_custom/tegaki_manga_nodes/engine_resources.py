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
    def __init__(self, code: str, message: str, candidates: Optional[list] = None):
        super().__init__(message)
        self.code = code
        # Canonical relative IDs only (never physical paths), e.g. for LORA_AMBIGUOUS.
        self.candidates = list(candidates or [])


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
PREVIEW_SNIFF_BYTES = 12


def sniff_preview_mime(head: bytes) -> Optional[str]:
    """MIME type from the image's magic bytes (never from the filename).

    Legacy/ReForge sidecars named ``*.preview.png`` may hold JPEG bytes.
    """
    if head.startswith(PNG_SIGNATURE):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return None
MAX_PREVIEW_BYTES = 16 * 1024 * 1024
MAX_ID_LENGTH = 1024
_FORBIDDEN_ID_CHARS = set('<>:"|?*')


def _fail(code: str, message: str, candidates: Optional[list] = None) -> None:
    raise ResourceContractError(code, message, candidates)


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
    token_for: Optional[Callable[[str], Optional[str]]] = None,
) -> dict:
    """List ONE folder: immediate child folders and LoRA files. Never recurses.

    ``token_for`` (TrustedLoraIndex.token_for) supplies the name the UI should
    write into ``<lora:NAME:W>``: the portable basename when unique in the
    trusted root, otherwise the shortest unambiguous canonical form.

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
        entry = {"id": child_id, "name": stem, "filename": name, "folder": folder, "available": available,
                 "preview": stem.casefold() in preview_names}
        if token_for is not None:
            token = token_for(child_id)
            if token:
                entry["token"] = token
        loras.append(entry)
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
    traversal, non-LoRA IDs and non-image content (PNG/JPEG/WebP by magic
    bytes) fail closed.  Model files are never opened.
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
    if preview_mime(path) is None:
        _fail("RESOURCE_PREVIEW_UNSUPPORTED", "Preview sidecar is not a PNG, JPEG or WebP image")
    return path


def preview_mime(path: str) -> Optional[str]:
    """Actual image type of an already root-resolved sidecar (reads 12 bytes)."""
    with open(path, "rb") as handle:
        return sniff_preview_mime(handle.read(PREVIEW_SNIFF_BYTES))


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
    token_for: Optional[Callable[[str], Optional[str]]] = None,
) -> dict:
    """HTTP-facing payload. The physical root is never returned to the client."""
    root = resolve_resource_root(engine, "lora", registered_roots, environ=environ)
    listing = list_lora_directory(root, relative_dir, extensions=extensions, comfy_full_path=comfy_full_path,
                                  token_for=token_for)
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

    index = build_trusted_lora_index(catalog_loras, root_dir, comfy_full_path=comfy_full_path)
    return index.resolve(name).comfy_id


# ---------------------------------------------------------------------------
# Trusted LoRA index: portable aliases + canonical IDs, root-bounded
# ---------------------------------------------------------------------------

PORTABLE_ALIAS_EXTENSION = ".safetensors"


class TrustedLoraEntry:
    __slots__ = ("comfy_id", "id", "id_noext", "basename", "stem", "ext", "folder")

    def __init__(self, comfy_id: str, canonical: str):
        path = PurePosixPath(canonical)
        self.comfy_id = comfy_id              # exact ComfyUI LoraLoader choice
        self.id = canonical                   # canonical relative identity ('/'-separated)
        self.id_noext = path.with_suffix("").as_posix()
        self.basename = path.name
        self.stem = path.stem
        self.ext = path.suffix.lower()
        self.folder = path.parent.as_posix() if path.parent.as_posix() != "." else ""


class TrustedLoraIndex:
    """All LoRAs of ONE trusted engine root, with O(1) lookups per resolution stage.

    Resolution order for a directive name (first stage with any match decides):
      1. exact canonical relative path            characters/A/foo.safetensors
      2. canonical relative path, extension omitted characters/A/foo
      3. exact basename (names without '/')        foo.safetensors
      4. stem with '.safetensors' omitted          foo
    One candidate resolves; several fail LORA_AMBIGUOUS (with candidates);
    none fails LORA_UNAVAILABLE.  Entries outside the root are never candidates.
    """

    def __init__(self, entries: list, outside_ids: list):
        self.entries = entries
        self.outside_ids = outside_ids
        self._stages = ({}, {}, {}, {})
        for entry in entries:
            keys = (entry.id, entry.id_noext, entry.basename,
                    entry.stem if entry.ext == PORTABLE_ALIAS_EXTENSION else None)
            for stage, key in zip(self._stages, keys):
                if key is not None:
                    stage.setdefault(key, []).append(entry)
        self._by_id = {entry.id: entry for entry in entries}

    def candidates(self, name: str) -> list:
        canonical = normalize_relative_id(name)
        has_parent = "/" in canonical
        for number, stage in enumerate(self._stages, start=1):
            if has_parent and number > 2:
                break
            found = stage.get(canonical, [])
            if found:
                return sorted(found, key=lambda entry: entry.id)
        return []

    def resolve(self, name: str) -> TrustedLoraEntry:
        if not isinstance(name, str) or not name or name.strip() != name:
            _fail("INVALID_CATALOG_ID", "Catalog ID must be a non-empty relative name")
        found = self.candidates(name)
        if len(found) == 1:
            return found[0]
        if found:
            ids = [entry.id for entry in found]
            _fail("LORA_AMBIGUOUS", f"LoRA '{name}' matches multiple LoRAs: {', '.join(ids)}", ids)
        _fail("LORA_UNAVAILABLE", f"LoRA '{name}' is unavailable")

    def outside_matches(self, name: str) -> list:
        """Relative IDs in OTHER registered roots matching the same stages (diagnostics only)."""
        try:
            canonical = normalize_relative_id(name)
        except ResourceContractError:
            return []
        other = TrustedLoraIndex([TrustedLoraEntry(i, normalize_relative_id(i)) for i in self.outside_ids], [])
        return [entry.id for entry in other.candidates(canonical)]

    def token_for(self, canonical_id: str) -> Optional[str]:
        """Shortest name that resolves back to exactly this LoRA (portable alias first)."""
        entry = self._by_id.get(canonical_id)
        if entry is None:
            return None
        forms = []
        if entry.ext == PORTABLE_ALIAS_EXTENSION:
            forms.append(entry.stem)
        forms += [entry.basename, entry.id_noext, entry.id]
        for form in forms:
            found = self.candidates(form)
            if len(found) == 1 and found[0] is entry:
                return form
        return entry.id


_INDEX_CACHE: dict = {}


def build_trusted_lora_index(
    catalog_loras: Iterable,
    root: str,
    *,
    comfy_full_path: Optional[Callable[[str], Optional[str]]] = None,
) -> TrustedLoraIndex:
    """Split ComfyUI's merged LoRA catalog into in-root entries and outside IDs.

    Membership uses the same rule as before: the file ComfyUI would load (or,
    without ComfyUI, the file at root/ID) must lie inside the trusted root.
    Cached per (root, catalog names) so batch validation and browsing do not
    re-stat the collection on every request.
    """
    root_dir = os.path.realpath(os.path.abspath(root))
    if comfy_full_path is None:
        try:
            import folder_paths
            live_roots = [os.path.normcase(os.path.realpath(os.path.abspath(r))) for r in folder_paths.get_folder_paths("loras") if r]
            if os.path.normcase(root_dir) in live_roots:
                comfy_full_path = lambda item: folder_paths.get_full_path("loras", item)
        except Exception:
            pass
    names = []
    for entry in catalog_loras or ():
        if isinstance(entry, dict):
            if entry.get("available") and isinstance(entry.get("id"), str) and entry["id"]:
                names.append(entry["id"])
        elif isinstance(entry, str) and entry:
            names.append(entry)
    key = (os.path.normcase(root_dir), comfy_full_path is not None, hash(tuple(names)), len(names))
    cached = _INDEX_CACHE.get("index")
    if cached is not None and cached[0] == key:
        return cached[1]
    inside, outside = [], []
    for entry_id in names:
        try:
            canonical = normalize_relative_id(entry_id)
        except ResourceContractError:
            continue
        resolved_path = None
        if comfy_full_path is not None:
            try:
                resolved_path = comfy_full_path(entry_id)
            except Exception:
                resolved_path = None
        else:
            try:
                candidate_path = resolve_within_root(root_dir, canonical)
                if os.path.isfile(candidate_path):
                    resolved_path = candidate_path
            except ResourceContractError:
                resolved_path = None
        if resolved_path and os.path.isfile(resolved_path) and is_path_within_root(root_dir, resolved_path):
            inside.append(TrustedLoraEntry(entry_id, canonical))
        else:
            outside.append(entry_id)
    index = TrustedLoraIndex(inside, outside)
    _INDEX_CACHE["index"] = (key, index)
    return index


# ---------------------------------------------------------------------------
# Prompt LoRA diagnostics (batch, pre-generation; same resolver as generation)
# ---------------------------------------------------------------------------

DIAGNOSTIC_STATUSES = (
    "RESOLVED", "LORA_UNAVAILABLE", "LORA_AMBIGUOUS", "INVALID_LORA_SYNTAX",
    "INVALID_STRENGTH", "OUTSIDE_RESOURCE_ROOT", "LORA_DUPLICATE", "SCENE_LORA_UNSUPPORTED",
)
_LORA_FRAGMENT_START = "<lora"


def diagnose_lora_sources(sources: list, index: TrustedLoraIndex) -> dict:
    """Report EVERY LoRA directive in prompt order, never stopping at the first problem.

    ``sources`` is ordered as the compiler applies LoRAs, e.g. for an isolated
    Scene: page positive, scene positive, page negative.  A source whose
    ``lora_allowed`` is False (Scene negative) reports SCENE_LORA_UNSUPPORTED.
    ``compiler_code`` is the code the generation compiler raises for the same
    directive, so the UI reason and the compile failure never disagree.
    """
    try:
        from .basic_generation import LORA_RE, TAG_RE
    except (ImportError, ValueError):
        from basic_generation import LORA_RE, TAG_RE
    import math

    entries, chain, seen = [], [], set()
    has_wildcards = False
    for source in sources:
        label = str(source.get("source", ""))
        text = source.get("text", "")
        if not isinstance(text, str):
            continue
        has_wildcards = has_wildcards or ("__" in text)
        allowed = source.get("lora_allowed", True) is not False
        found = []
        covered = []
        for match in TAG_RE.finditer(text):
            covered.append((match.start(), match.end()))
            if match.group(0).lower().startswith(_LORA_FRAGMENT_START):
                found.append((match.start(), match.group(0), True))
        # Unclosed '<lora...' fragments are reported, not silently dropped.
        position = text.lower().find(_LORA_FRAGMENT_START)
        while position != -1:
            if not any(start <= position < end for start, end in covered):
                stop = len(text)
                for delimiter in (",", "\n"):
                    at = text.find(delimiter, position)
                    if at != -1:
                        stop = min(stop, at)
                found.append((position, text[position:stop].strip(), False))
            position = text.lower().find(_LORA_FRAGMENT_START, position + 1)
        for position, raw, closed in sorted(found):
            item = {"source": label, "raw": raw, "position": position}
            tag = LORA_RE.fullmatch(raw) if closed else None
            if tag is None:
                item.update(status="INVALID_LORA_SYNTAX", compiler_code="UNSUPPORTED_PROMPT_TAG",
                            message="Expected <lora:NAME:STRENGTH>")
                entries.append(item)
                continue
            name, strength_text = tag.group(1), tag.group(2)
            item.update(name=name, strength_text=strength_text)
            strength = float(strength_text)
            if name != name.strip():
                item.update(status="INVALID_LORA_SYNTAX", compiler_code="INVALID_LORA",
                            message="LoRA name must not have surrounding whitespace")
            elif not math.isfinite(strength) or not -4 <= strength <= 4:
                item.update(status="INVALID_STRENGTH", compiler_code="INVALID_LORA",
                            message="LoRA strength must be within -4..4")
            elif not allowed:
                item.update(status="SCENE_LORA_UNSUPPORTED", compiler_code="SCENE_LORA_UNSUPPORTED",
                            message="LoRA is not supported in the Scene negative prompt")
            else:
                item["strength"] = strength
                try:
                    resolved = index.resolve(name)
                except ResourceContractError as exc:
                    if exc.code in ("INVALID_CATALOG_ID", "RESOURCE_PATH_OUTSIDE_ROOT", "INVALID_RESOURCE_ID"):
                        item.update(status="OUTSIDE_RESOURCE_ROOT", compiler_code="INVALID_CATALOG_ID",
                                    message="LoRA name must be relative to the trusted LoRA root")
                    elif exc.code == "LORA_UNAVAILABLE" and index.outside_matches(name):
                        item.update(status="OUTSIDE_RESOURCE_ROOT", compiler_code="LORA_UNAVAILABLE",
                                    message="Only found outside the trusted LoRA root",
                                    candidates=index.outside_matches(name))
                    else:
                        item.update(status=exc.code, compiler_code=exc.code, message=str(exc))
                        if exc.candidates:
                            item["candidates"] = exc.candidates
                else:
                    item["resolved_id"] = resolved.id
                    if resolved.id in seen:
                        item.update(status="LORA_DUPLICATE", compiler_code="LORA_DUPLICATE",
                                    message=f"{resolved.id} appears more than once")
                    else:
                        seen.add(resolved.id)
                        item["status"] = "RESOLVED"
                        chain.append({"order": len(chain) + 1, "source": label, "name": name,
                                      "resolved_id": resolved.id, "strength": strength})
            entries.append(item)
    problems = [item for item in entries if item["status"] != "RESOLVED"]
    return {"ok": True, "entries": entries, "chain": chain, "problems": len(problems),
            "has_wildcards": has_wildcards}


MAX_VALIDATE_SOURCES = 8
MAX_VALIDATE_TEXT = 16000


def validate_lora_request(engine: str, body: object, index: TrustedLoraIndex) -> dict:
    """HTTP-facing batch validation: one request for every prompt source."""
    resource_spec(engine, "lora")
    sources = body.get("sources") if isinstance(body, dict) else None
    if not isinstance(sources, list) or not sources or len(sources) > MAX_VALIDATE_SOURCES:
        _fail("INVALID_REQUEST", f"sources must be a list of 1..{MAX_VALIDATE_SOURCES} prompt sources")
    clean = []
    for source in sources:
        if (not isinstance(source, dict) or not isinstance(source.get("source"), str)
                or len(source["source"]) > 32 or not isinstance(source.get("text"), str)
                or len(source["text"]) > MAX_VALIDATE_TEXT
                or not isinstance(source.get("lora_allowed", True), bool)):
            _fail("INVALID_REQUEST", "Each source needs a short 'source' label and a 'text' prompt")
        clean.append({"source": source["source"], "text": source["text"],
                      "lora_allowed": source.get("lora_allowed", True)})
    result = diagnose_lora_sources(clean, index)
    result.update({"engine": engine, "resource": "lora"})
    return result


def lora_index_payload(engine: str, index: TrustedLoraIndex) -> dict:
    """Trusted-root LoRAs for autocomplete: canonical ID, insertable token, folder. No paths."""
    resource_spec(engine, "lora")
    entries = [{"id": entry.id, "token": index.token_for(entry.id), "folder": entry.folder}
               for entry in sorted(index.entries, key=lambda item: item.id)]
    return {"ok": True, "engine": engine, "resource": "lora", "entries": entries}
