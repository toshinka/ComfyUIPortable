"""Semantic adapter for the bounded Native MiniMax H3 Start Frame route.

This module owns the H1B workflow graph and the single reference binding. The
browser supplies a server-issued reference id; it never supplies a filesystem
path to ComfyUI. The adapter accepts only a safe, server-derived input path and
fails closed if the workflow no longer exposes the expected first-frame edge.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path, PurePosixPath
import json
from typing import Any, Mapping

from h3.adapters.native_t2v import (
    H3Request,
    PORTABLE_ROOT,
    REFERENCE_ROLE_START_FRAME,
    RequestValidationError,
    ROUTE_I2V,
    WorkflowIncompatibleError,
    duration_to_frames,
    resolve_route,
    validate_request,
)


WORKFLOW_PATH = PORTABLE_ROOT / "workflows" / "h3" / "H1B_NATIVE_I2V_BASE.json"
ALLOWED_REFERENCE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _load_workflow() -> dict[str, Any]:
    try:
        with WORKFLOW_PATH.open("r", encoding="utf-8") as handle:
            workflow = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: H1B workflow file cannot be read."
        ) from exc
    if not isinstance(workflow, dict):
        raise WorkflowIncompatibleError("Workflow incompatible: root must be an object.")
    return workflow


def validate_workflow(workflow: Mapping[str, Any]) -> None:
    if workflow.get("schema") != "tegaki.h3.h1b.native-i2v/v1":
        raise WorkflowIncompatibleError("Workflow incompatible: unsupported H1B schema.")

    prompt = workflow.get("prompt")
    semantic_nodes = workflow.get("semantic_nodes")
    if not isinstance(prompt, Mapping) or not isinstance(semantic_nodes, Mapping):
        raise WorkflowIncompatibleError("Workflow incompatible: semantic graph is missing.")

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

    required_roles = {
        "save_video",
        "video_vae",
        "audio_vae",
        "video_decode",
        "audio_decode",
        "sampler",
        "guider",
        "scheduler",
        "sampler_select",
        "noise",
        "model",
        "text_encoder",
        "conditioning_latent",
        "video_create",
        "load_image",
    }
    missing = sorted(required_roles.difference(semantic_nodes))
    if missing:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: missing semantic roles " + ", ".join(missing) + "."
        )

    conditioning_id = str(semantic_nodes["conditioning_latent"]["id"])
    load_image_id = str(semantic_nodes["load_image"]["id"])
    conditioning_inputs = prompt[conditioning_id].get("inputs")
    if not isinstance(conditioning_inputs, Mapping):
        raise WorkflowIncompatibleError("Workflow incompatible: conditioning inputs are missing.")
    if conditioning_inputs.get("first_frame") != [load_image_id, 0]:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: first_frame must be bound to LoadImage."
        )
    if "last_frame" in conditioning_inputs:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: H1B must not bind a last_frame input."
        )


def _safe_reference_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise RequestValidationError("Reference asset path is invalid.")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        raise RequestValidationError("Reference asset path is invalid.")
    if parsed.parts[:1] != ("inputs",) or len(parsed.parts) != 2:
        raise RequestValidationError("Reference asset path is invalid.")
    if Path(parsed.name).suffix.lower() not in ALLOWED_REFERENCE_SUFFIXES:
        raise RequestValidationError("Reference asset path is invalid.")
    return parsed.as_posix()


def compile_workflow(
    request: H3Request | Mapping[str, Any],
    reference_path: str,
) -> dict[str, dict[str, Any]]:
    """Compile one Start Frame into the Native H3 I2V API graph."""

    normalized = request if isinstance(request, H3Request) else validate_request(request)
    if normalized.reference is None or resolve_route(normalized.reference) != ROUTE_I2V:
        raise RequestValidationError("A Start Frame reference is required for this route.")
    relative_path = _safe_reference_path(reference_path)

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
            "length": duration_to_frames(normalized.duration),
            "first_frame": [str(roles["load_image"]["id"]), 0],
        }
    )
    node_for("load_image")["inputs"]["image"] = relative_path
    node_for("noise")["inputs"]["noise_seed"] = normalized.seed
    node_for("scheduler")["inputs"]["steps"] = normalized.steps
    node_for("save_video")["inputs"]["filename_prefix"] = "video/h1b_native_i2v"
    return graph


def workflow_metadata() -> dict[str, Any]:
    workflow = _load_workflow()
    validate_workflow(workflow)
    return {
        "schema": workflow["schema"],
        "source": workflow.get("source", {}),
        "baseline": workflow.get("baseline", {}),
    }
