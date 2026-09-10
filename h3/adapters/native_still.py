"""Semantic adapter for the bounded H2A Native H3 still feasibility route.

H3's current native node surface is an audio-video model with a minimum
five-frame temporal packet.  This adapter keeps that fact explicit: it
materializes one short packet, decodes it with the verified video VAE, and
selects one decoded image.  It is deliberately separate from the H1 video
adapter and has no reference or production-UI contract.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import random
from typing import Any, Mapping

from h3.adapters.native_t2v import (
    RequestValidationError,
    WorkflowIncompatibleError,
)


PORTABLE_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = PORTABLE_ROOT / "workflows" / "h3" / "H2A_NATIVE_STILL_BASE.json"

ROUTE_STILL = "native_still"
WIDTH = 608
HEIGHT = 352
FPS = 24
PACKET_FRAMES = 5
SELECTED_FRAME_INDEX = 0
DEFAULT_STEPS = 20
MAX_PROMPT_LENGTH = 4000
MAX_SEED = 2**63 - 1


@dataclass(frozen=True)
class H3StillRequest:
    prompt: str
    width: int = WIDTH
    height: int = HEIGHT
    seed: int = 0
    steps: int = DEFAULT_STEPS

    def public(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "width": self.width,
            "height": self.height,
            "seed": self.seed,
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


def validate_still_request(payload: Mapping[str, Any]) -> H3StillRequest:
    """Validate the text-only feasibility input and fail closed."""

    if not isinstance(payload, Mapping):
        raise RequestValidationError("Still request must be a JSON object.")

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
        raise RequestValidationError("H2A still currently supports 608 x 352 only.")

    steps = _coerce_int(payload.get("steps", DEFAULT_STEPS), "Steps")
    if steps != DEFAULT_STEPS:
        raise RequestValidationError("H2A still uses the verified 20-step baseline.")

    seed_value = payload.get("seed")
    if seed_value in (None, "", "random"):
        seed = random.SystemRandom().randint(0, MAX_SEED)
    else:
        seed = _coerce_int(seed_value, "Seed")
        if not 0 <= seed <= MAX_SEED:
            raise RequestValidationError("Seed must be between 0 and 2^63-1.")

    for reference_key in ("reference", "references"):
        if payload.get(reference_key) not in (None, "", {}):
            raise RequestValidationError("H2A still is text-only; references are unsupported.")

    return H3StillRequest(
        prompt=prompt,
        width=width,
        height=height,
        seed=seed,
        steps=steps,
    )


def workflow_metadata() -> dict[str, Any]:
    return {
        "route": ROUTE_STILL,
        "schema": "tegaki.h3.h2a.native-still/v1",
        "workflow": str(WORKFLOW_PATH.relative_to(PORTABLE_ROOT)).replace("\\", "/"),
        "width": WIDTH,
        "height": HEIGHT,
        "fps": FPS,
        "packet_frames": PACKET_FRAMES,
        "selected_frame_index": SELECTED_FRAME_INDEX,
        "steps": DEFAULT_STEPS,
        "model": "minimax_h3_fl2va_pruned_int8_convrot.safetensors",
        "text_encoder": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
        "video_vae": "minimax_h3_video_vae_fp16.safetensors",
        "audio_vae": "not used by selected still output",
        "custom_nodes": "none",
    }


def _load_workflow() -> dict[str, Any]:
    try:
        with WORKFLOW_PATH.open("r", encoding="utf-8") as handle:
            workflow = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: H2A still workflow file cannot be read."
        ) from exc
    if not isinstance(workflow, dict):
        raise WorkflowIncompatibleError("Workflow incompatible: root must be an object.")
    return workflow


def validate_workflow(workflow: Mapping[str, Any]) -> None:
    if workflow.get("schema") != "tegaki.h3.h2a.native-still/v1":
        raise WorkflowIncompatibleError("Workflow incompatible: unsupported H2A still schema.")

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

    forbidden_classes = {"SaveVideo", "CreateVideo", "VAEDecodeAudio"}
    present_forbidden = sorted(
        str(node.get("class_type"))
        for node in prompt.values()
        if isinstance(node, Mapping) and node.get("class_type") in forbidden_classes
    )
    if present_forbidden:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: still graph contains video/audio output nodes."
        )

    conditioning_id = str(semantic_nodes["conditioning_latent"]["id"])
    conditioning = prompt[conditioning_id]
    if conditioning.get("class_type") != "MiniMaxH3ImageToVideo":
        raise WorkflowIncompatibleError(
            "Workflow incompatible: H2A conditioning node must be MiniMaxH3ImageToVideo."
        )
    if conditioning.get("inputs", {}).get("length") != PACKET_FRAMES:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: H2A packet must contain exactly five frames."
        )

    select_id = str(semantic_nodes["select_frame"]["id"])
    select_frame = prompt[select_id]
    select_inputs = select_frame.get("inputs", {})
    if (
        select_frame.get("class_type") != "ImageFromBatch"
        or select_inputs.get("batch_index") != SELECTED_FRAME_INDEX
        or select_inputs.get("length") != 1
    ):
        raise WorkflowIncompatibleError(
            "Workflow incompatible: H2A must select exactly one decoded frame."
        )


def compile_workflow(request: H3StillRequest | Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Materialize the bounded H2A graph for the Native `/prompt` API."""

    normalized = request if isinstance(request, H3StillRequest) else validate_still_request(request)
    workflow = _load_workflow()
    validate_workflow(workflow)
    graph = deepcopy(workflow["prompt"])
    roles = workflow["semantic_nodes"]

    def node_for(role: str) -> dict[str, Any]:
        return graph[str(roles[role]["id"])]

    node_for("conditioning_latent")["inputs"].update(
        {
            "prompt": normalized.prompt,
            "width": normalized.width,
            "height": normalized.height,
            "length": PACKET_FRAMES,
        }
    )
    node_for("noise")["inputs"]["noise_seed"] = normalized.seed
    node_for("scheduler")["inputs"]["steps"] = normalized.steps
    node_for("save_image")["inputs"]["filename_prefix"] = "still/h2a_native_still"
    return graph
