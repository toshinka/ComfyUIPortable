"""Semantic adapter for the verified Native ComfyUI MiniMax H3 T2V route.

The browser-facing app speaks in prompt, size, seconds, seed, and steps. This
module is the only place that knows the ComfyUI node IDs and the H1A workflow
graph. The graph is validated before a request can be submitted so a stale or
partially edited workflow fails closed.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import random
import re
from typing import Any, Mapping


PORTABLE_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = PORTABLE_ROOT / "workflows" / "h3" / "H1A_NATIVE_T2V_BASE.json"

FPS = 24
ALLOWED_RESOLUTIONS = ((608, 352),)
DEFAULT_DURATION_SECONDS = 5.0
DEFAULT_STEPS = 20
MAX_PROMPT_LENGTH = 4000
MIN_DURATION_SECONDS = 0.2
MAX_DURATION_SECONDS = 15.0
REFERENCE_ROLE_START_FRAME = "start_frame"
ROUTE_T2V = "native_t2v"
ROUTE_I2V = "native_i2v"
REFERENCE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


class RequestValidationError(ValueError):
    """A user-facing request value is outside the H1A contract."""


class WorkflowIncompatibleError(RuntimeError):
    """The production workflow no longer matches its semantic contract."""


@dataclass(frozen=True)
class H3Reference:
    """The bounded H1B reference contract; the server owns the local asset."""

    id: str
    role: str = REFERENCE_ROLE_START_FRAME

    def public(self) -> dict[str, str]:
        return {"id": self.id, "role": self.role}


@dataclass(frozen=True)
class H3Request:
    prompt: str
    width: int = 608
    height: int = 352
    duration: float = DEFAULT_DURATION_SECONDS
    seed: int | None = None
    steps: int = DEFAULT_STEPS
    reference: H3Reference | None = None

    def public(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "seed": self.seed,
            "steps": self.steps,
            "reference": self.reference.public() if self.reference else None,
        }


def validate_reference(value: Any) -> H3Reference | None:
    if value in (None, ""):
        return None
    if not isinstance(value, Mapping):
        raise RequestValidationError("Reference must be an object.")
    reference_id = value.get("id")
    if not isinstance(reference_id, str) or not REFERENCE_ID_PATTERN.fullmatch(reference_id):
        raise RequestValidationError("Reference id is invalid.")
    role = value.get("role")
    if role != REFERENCE_ROLE_START_FRAME:
        raise RequestValidationError("Reference role is unsupported.")
    return H3Reference(reference_id, role)


def resolve_route(reference: H3Reference | Mapping[str, Any] | None) -> str:
    """Resolve the only two H1B routes without a user-facing mode selector."""

    normalized = reference if isinstance(reference, H3Reference) else validate_reference(reference)
    return ROUTE_T2V if normalized is None else ROUTE_I2V


def duration_to_frames(duration_seconds: float) -> int:
    """Convert user-facing seconds to the H3 17-frame block grid.

    This is the same conversion used by the official workflow template. At the
    H1A baseline, five seconds becomes 124 frames at 24 FPS.
    """

    if not isinstance(duration_seconds, (int, float)) or isinstance(
        duration_seconds, bool
    ):
        raise RequestValidationError("Duration must be a number of seconds.")
    duration = float(duration_seconds)
    if not MIN_DURATION_SECONDS <= duration <= MAX_DURATION_SECONDS:
        raise RequestValidationError(
            f"Duration must be between {MIN_DURATION_SECONDS:g} and {MAX_DURATION_SECONDS:g} seconds."
        )
    raw_frames = max(5, round(duration * FPS))
    return raw_frames + (5 - (raw_frames % 17)) % 17


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


def validate_request(payload: Mapping[str, Any]) -> H3Request:
    if not isinstance(payload, Mapping):
        raise RequestValidationError("Request must be a JSON object.")

    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise RequestValidationError("Prompt is required.")
    prompt = prompt.strip()
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise RequestValidationError(
            f"Prompt must be {MAX_PROMPT_LENGTH} characters or fewer."
        )

    width = _coerce_int(payload.get("width", 608), "Width")
    height = _coerce_int(payload.get("height", 352), "Height")
    if (width, height) not in ALLOWED_RESOLUTIONS:
        raise RequestValidationError("H3 currently supports 608 x 352 only.")

    duration_value = payload.get("duration", DEFAULT_DURATION_SECONDS)
    if isinstance(duration_value, str):
        try:
            duration_value = float(duration_value)
        except (TypeError, ValueError) as exc:
            raise RequestValidationError("Duration must be a number of seconds.") from exc
    try:
        duration = float(duration_value)
    except (TypeError, ValueError) as exc:
        raise RequestValidationError("Duration must be a number of seconds.") from exc
    duration_to_frames(duration)

    steps = _coerce_int(payload.get("steps", DEFAULT_STEPS), "Steps")
    if steps != DEFAULT_STEPS:
        raise RequestValidationError("H3 uses the verified 20-step baseline.")

    seed_value = payload.get("seed")
    if seed_value in (None, "", "random"):
        seed = random.SystemRandom().randint(0, 2**63 - 1)
    else:
        seed = _coerce_int(seed_value, "Seed")
        if not 0 <= seed <= 2**63 - 1:
            raise RequestValidationError("Seed must be between 0 and 2^63-1.")

    reference = validate_reference(payload.get("reference"))

    return H3Request(
        prompt=prompt,
        width=width,
        height=height,
        duration=duration,
        seed=seed,
        steps=steps,
        reference=reference,
    )


def _load_workflow() -> dict[str, Any]:
    try:
        with WORKFLOW_PATH.open("r", encoding="utf-8") as handle:
            workflow = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: H1A workflow file cannot be read."
        ) from exc
    if not isinstance(workflow, dict):
        raise WorkflowIncompatibleError("Workflow incompatible: root must be an object.")
    return workflow


def validate_workflow(workflow: Mapping[str, Any]) -> None:
    if workflow.get("schema") != "tegaki.h3.h1a.native-t2v/v1":
        raise WorkflowIncompatibleError("Workflow incompatible: unsupported H1A schema.")

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
    }
    missing = sorted(required_roles.difference(semantic_nodes))
    if missing:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: missing semantic roles " + ", ".join(missing) + "."
        )


def compile_workflow(request: H3Request | Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a ComfyUI API prompt graph after fail-closed validation."""

    normalized = request if isinstance(request, H3Request) else validate_request(request)
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
        }
    )
    node_for("noise")["inputs"]["noise_seed"] = normalized.seed
    node_for("scheduler")["inputs"]["steps"] = normalized.steps
    node_for("save_video")["inputs"]["filename_prefix"] = "video/h1a_native_t2v"
    return graph


def workflow_metadata() -> dict[str, Any]:
    workflow = _load_workflow()
    validate_workflow(workflow)
    return {
        "schema": workflow["schema"],
        "source": workflow.get("source", {}),
        "baseline": workflow.get("baseline", {}),
    }
