"""Semantic adapter for the bounded H2B source-anchored Native still route.

H2B accepts exactly one local PNG/JPEG staged below the Native input boundary.
The source is bound to the existing ``MiniMaxH3ImageToVideo.first_frame`` edge;
the Native node resizes it to the fixed 608 x 352 canvas, encodes it with the
existing video VAE, and places it at temporal frame zero.  The output remains
the H2A five-frame packet/decode/select-frame still path.

The prompt-only compiler is a matched comparison control.  It uses this same
H2B workflow basis after removing the one source edge and loader, so it does
not create a second Still engine or a generic reference abstraction.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import random
from typing import Any, Mapping

from h3.adapters.native_still import (
    DEFAULT_STEPS,
    HEIGHT,
    MAX_PROMPT_LENGTH,
    PACKET_FRAMES,
    SELECTED_FRAME_INDEX,
    WIDTH,
    H3StillRequest,
    validate_still_request,
)
from h3.adapters.native_t2v import (
    RequestValidationError,
    WorkflowIncompatibleError,
)


PORTABLE_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = PORTABLE_ROOT / "workflows" / "h3" / "H2B_SOURCE_ANCHORED_STILL_BASE.json"
SCHEMA = "tegaki.h3.h2b.source-anchored-still/v1"
ROUTE_SOURCE_ANCHORED_STILL = "native_source_anchored_still"
PROMPT_ONLY_ROUTE = "native_prompt_only_still_control"
SOURCE_IMAGE_ROLE = "source_image_loader"
ALLOWED_SOURCE_SUFFIXES = {".png", ".jpg", ".jpeg"}
MAX_SEED = 2**63 - 1


@dataclass(frozen=True)
class H3SourceAnchorRequest:
    prompt: str
    source_path: str
    width: int = WIDTH
    height: int = HEIGHT
    seed: int = 0
    steps: int = DEFAULT_STEPS

    def public(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "width": self.width,
            "height": self.height,
            # Keep the 64-bit seed lossless across the JavaScript boundary.
            "seed": str(self.seed),
            "steps": self.steps,
        }


def _coerce_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise RequestValidationError(f"{field} must be an integer.")
    try:
        converted = int(value)
    except (TypeError, ValueError) as exc:
        raise RequestValidationError(f"{field} must be an integer.") from exc
    if isinstance(value, float) and value != converted:
        raise RequestValidationError(f"{field} must be an integer.")
    return converted


def _safe_source_path(value: str) -> str:
    """Accept only one server/staging-derived ``inputs/<file>`` path."""

    if not isinstance(value, str) or not value or len(value) > 240:
        raise RequestValidationError("Source image path is invalid.")
    if "\\" in value or ":" in value or "[" in value or "]" in value:
        raise RequestValidationError("Source image path is invalid.")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        raise RequestValidationError("Source image path is invalid.")
    if parsed.parts[:1] != ("inputs",) or len(parsed.parts) != 2:
        raise RequestValidationError("Source image path is invalid.")
    if Path(parsed.name).suffix.lower() not in ALLOWED_SOURCE_SUFFIXES:
        raise RequestValidationError("Source image must be PNG or JPEG.")
    return parsed.as_posix()


def _validate_common(payload: Mapping[str, Any]) -> tuple[str, int, int, int, int]:
    if not isinstance(payload, Mapping):
        raise RequestValidationError("H2B still request must be a JSON object.")

    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise RequestValidationError("Prompt is required.")
    prompt = prompt.strip()
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise RequestValidationError(
            f"Prompt must be {MAX_PROMPT_LENGTH} characters or fewer."
        )

    width = _coerce_int(payload.get("width", WIDTH), "Width")
    height = _coerce_int(payload.get("height", HEIGHT), "Height")
    if (width, height) != (WIDTH, HEIGHT):
        raise RequestValidationError("H2B still currently supports 608 x 352 only.")

    steps = _coerce_int(payload.get("steps", DEFAULT_STEPS), "Steps")
    if steps != DEFAULT_STEPS:
        raise RequestValidationError("H2B still uses the verified 20-step baseline.")

    seed_value = payload.get("seed")
    if seed_value in (None, "", "random"):
        seed = random.SystemRandom().randint(0, MAX_SEED)
    else:
        seed = _coerce_int(seed_value, "Seed")
        if not 0 <= seed <= MAX_SEED:
            raise RequestValidationError("Seed must be between 0 and 2^63-1.")

    for key in ("reference", "references", "source_images", "source_paths"):
        value = payload.get(key)
        if value not in (None, "", {}):
            raise RequestValidationError("H2B accepts exactly one source image.")
    return prompt, width, height, seed, steps


def validate_source_anchor_request(payload: Mapping[str, Any]) -> H3SourceAnchorRequest:
    """Validate one bounded H2B source-anchor request and fail closed."""

    prompt, width, height, seed, steps = _validate_common(payload)
    source_path = _safe_source_path(payload.get("source_path"))
    return H3SourceAnchorRequest(
        prompt=prompt,
        source_path=source_path,
        width=width,
        height=height,
        seed=seed,
        steps=steps,
    )


def _load_workflow() -> dict[str, Any]:
    try:
        with WORKFLOW_PATH.open("r", encoding="utf-8") as handle:
            workflow = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: H2B source-anchor workflow cannot be read."
        ) from exc
    if not isinstance(workflow, dict):
        raise WorkflowIncompatibleError("Workflow incompatible: root must be an object.")
    return workflow


def validate_workflow(workflow: Mapping[str, Any]) -> None:
    if workflow.get("schema") != SCHEMA:
        raise WorkflowIncompatibleError("Workflow incompatible: unsupported H2B schema.")

    semantic_nodes = workflow.get("semantic_nodes")
    prompt = workflow.get("prompt")
    if not isinstance(semantic_nodes, Mapping) or not isinstance(prompt, Mapping):
        raise WorkflowIncompatibleError("Workflow incompatible: semantic graph is missing.")

    required_roles = {
        "save_image",
        "video_vae",
        "video_decode",
        "sampler_select",
        "scheduler",
        "sampler",
        "guider",
        "model",
        "text_encoder",
        "noise",
        "conditioning_latent",
        "select_frame",
        SOURCE_IMAGE_ROLE,
    }
    missing = sorted(required_roles.difference(semantic_nodes))
    if missing:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: missing semantic roles " + ", ".join(missing) + "."
        )

    for role, expected in semantic_nodes.items():
        if not isinstance(expected, Mapping):
            raise WorkflowIncompatibleError(f"Workflow incompatible: {role} contract is invalid.")
        node_id = str(expected.get("id"))
        expected_class = expected.get("class_type")
        node = prompt.get(node_id)
        if not isinstance(node, Mapping) or node.get("class_type") != expected_class:
            raise WorkflowIncompatibleError(
                f"Workflow incompatible: semantic node {role} is not {expected_class}."
            )

    forbidden_classes = {"SaveVideo", "CreateVideo", "VAEDecodeAudio", "MiniMaxH3ReferenceToVideo"}
    present_forbidden = sorted(
        str(node.get("class_type"))
        for node in prompt.values()
        if isinstance(node, Mapping) and node.get("class_type") in forbidden_classes
    )
    if present_forbidden:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: H2B still graph contains unsupported output/reference nodes."
        )

    conditioning_id = str(semantic_nodes["conditioning_latent"]["id"])
    loader_id = str(semantic_nodes[SOURCE_IMAGE_ROLE]["id"])
    conditioning = prompt[conditioning_id]
    conditioning_inputs = conditioning.get("inputs")
    if conditioning.get("class_type") != "MiniMaxH3ImageToVideo" or not isinstance(
        conditioning_inputs, Mapping
    ):
        raise WorkflowIncompatibleError(
            "Workflow incompatible: H2B conditioning node must be MiniMaxH3ImageToVideo."
        )
    if conditioning_inputs.get("length") != PACKET_FRAMES:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: H2B packet must contain exactly five frames."
        )
    if conditioning_inputs.get("first_frame") != [loader_id, 0]:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: source anchor must bind first_frame to LoadImage."
        )

    loader = prompt[loader_id]
    if loader.get("class_type") != "LoadImage":
        raise WorkflowIncompatibleError(
            "Workflow incompatible: source anchor must use one LoadImage node."
        )
    _safe_source_path(loader.get("inputs", {}).get("image"))

    select_id = str(semantic_nodes["select_frame"]["id"])
    select_frame = prompt[select_id]
    select_inputs = select_frame.get("inputs", {})
    if (
        select_frame.get("class_type") != "ImageFromBatch"
        or select_inputs.get("batch_index") != SELECTED_FRAME_INDEX
        or select_inputs.get("length") != 1
    ):
        raise WorkflowIncompatibleError(
            "Workflow incompatible: H2B must select exactly one decoded frame."
        )


def _validated_workflow() -> dict[str, Any]:
    workflow = _load_workflow()
    validate_workflow(workflow)
    return workflow


def _node(graph: dict[str, dict[str, Any]], roles: Mapping[str, Any], role: str) -> dict[str, Any]:
    return graph[str(roles[role]["id"])]


def compile_workflow(
    request: H3SourceAnchorRequest | Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Materialize one source-anchored H2B graph for Native ``/prompt``."""

    normalized = (
        request
        if isinstance(request, H3SourceAnchorRequest)
        else validate_source_anchor_request(request)
    )
    source_path = _safe_source_path(normalized.source_path)
    workflow = _validated_workflow()
    graph = deepcopy(workflow["prompt"])
    roles = workflow["semantic_nodes"]

    _node(graph, roles, "conditioning_latent")["inputs"].update(
        {
            "prompt": normalized.prompt,
            "width": normalized.width,
            "height": normalized.height,
            "length": PACKET_FRAMES,
            "first_frame": [str(roles[SOURCE_IMAGE_ROLE]["id"]), 0],
        }
    )
    _node(graph, roles, SOURCE_IMAGE_ROLE)["inputs"]["image"] = source_path
    _node(graph, roles, "noise")["inputs"]["noise_seed"] = normalized.seed
    _node(graph, roles, "scheduler")["inputs"]["steps"] = normalized.steps
    _node(graph, roles, "save_image")["inputs"]["filename_prefix"] = "still/h2b_source_anchor"
    return graph


def compile_prompt_only_workflow(
    request: H3StillRequest | Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Materialize the matched prompt-only comparison control from H2B."""

    normalized = request if isinstance(request, H3StillRequest) else validate_still_request(request)
    workflow = _validated_workflow()
    graph = deepcopy(workflow["prompt"])
    roles = workflow["semantic_nodes"]
    conditioning = _node(graph, roles, "conditioning_latent")
    conditioning["inputs"].pop("first_frame", None)
    graph.pop(str(roles[SOURCE_IMAGE_ROLE]["id"]), None)
    conditioning["inputs"].update(
        {
            "prompt": normalized.prompt,
            "width": normalized.width,
            "height": normalized.height,
            "length": PACKET_FRAMES,
        }
    )
    _node(graph, roles, "noise")["inputs"]["noise_seed"] = normalized.seed
    _node(graph, roles, "scheduler")["inputs"]["steps"] = normalized.steps
    _node(graph, roles, "save_image")["inputs"]["filename_prefix"] = "still/h2b_prompt_only"
    return graph


def workflow_metadata() -> dict[str, Any]:
    workflow = _validated_workflow()
    return {
        "schema": workflow["schema"],
        "source": workflow.get("source", {}),
        "baseline": workflow.get("baseline", {}),
    }
