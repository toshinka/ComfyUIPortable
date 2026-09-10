"""Semantic adapter for the bounded Native ComfyUI MiniMax H3 routes.

The browser-facing app speaks in prompt, size, seconds, seed, and steps. This
module owns the request/reference vocabulary and route resolver. Workflow node
IDs remain in the route-specific adapters. Graphs are validated before a
request can be submitted so a stale or partially edited workflow fails closed.
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
DEFAULT_DURATION_SECONDS = 5.0
DEFAULT_STEPS = 20
MAX_PROMPT_LENGTH = 4000
MIN_DURATION_SECONDS = 0.2
MAX_DURATION_SECONDS = 15.0
VIDEO_RESOLUTION_OPTIONS = (
    {"label": "608 x 352", "width": 608, "height": 352},
    {"label": "736 x 416", "width": 736, "height": 416},
)
VIDEO_DURATION_OPTIONS = (
    {"label": "5 seconds", "value": 5},
    {"label": "15 seconds", "value": 15},
)
ALLOWED_RESOLUTIONS = tuple(
    (option["width"], option["height"]) for option in VIDEO_RESOLUTION_OPTIONS
)
ALLOWED_DURATIONS = tuple(float(option["value"]) for option in VIDEO_DURATION_OPTIONS)
REFERENCE_ROLE_START_FRAME = "start_frame"
REFERENCE_ROLE_END_FRAME = "end_frame"
REFERENCE_ROLES = (REFERENCE_ROLE_START_FRAME, REFERENCE_ROLE_END_FRAME)
ROUTE_T2V = "native_t2v"
ROUTE_I2V = "native_i2v"
REFERENCE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def video_option_metadata() -> dict[str, list[dict[str, Any]]]:
    """Return the verified Video enum options used by /api/config."""

    return {
        "resolution_options": [dict(option) for option in VIDEO_RESOLUTION_OPTIONS],
        "duration_options": [dict(option) for option in VIDEO_DURATION_OPTIONS],
    }


class RequestValidationError(ValueError):
    """A user-facing request value is outside the H1A contract."""


class WorkflowIncompatibleError(RuntimeError):
    """The production workflow no longer matches its semantic contract."""


@dataclass(frozen=True)
class H3Reference:
    """A server-issued reference; the server owns the local asset."""

    id: str
    role: str = REFERENCE_ROLE_START_FRAME

    def public(self) -> dict[str, str]:
        return {"id": self.id, "role": self.role}


@dataclass(frozen=True)
class H3ReferenceSlots:
    """The fixed H1B.1 keyframe slots, not a generic ordered reference list."""

    start_frame: H3Reference | None = None
    end_frame: H3Reference | None = None

    def public(self) -> dict[str, dict[str, str] | None]:
        return {
            REFERENCE_ROLE_START_FRAME: self.start_frame.public()
            if self.start_frame
            else None,
            REFERENCE_ROLE_END_FRAME: self.end_frame.public()
            if self.end_frame
            else None,
        }

    def any(self) -> bool:
        return self.start_frame is not None or self.end_frame is not None


@dataclass(frozen=True)
class H3Request:
    prompt: str
    width: int = 608
    height: int = 352
    duration: float = DEFAULT_DURATION_SECONDS
    seed: int | None = None
    steps: int = DEFAULT_STEPS
    reference: H3Reference | None = None
    references: H3ReferenceSlots | None = None
    legacy_reference: bool = False

    def __post_init__(self) -> None:
        slots = self.references
        if slots is None:
            slots = H3ReferenceSlots(start_frame=self.reference)
        elif self.reference is not None and slots.start_frame is None:
            slots = H3ReferenceSlots(
                start_frame=self.reference,
                end_frame=slots.end_frame,
            )
        object.__setattr__(self, "references", slots)
        object.__setattr__(self, "reference", slots.start_frame)

    def public(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            # Keep the 64-bit seed lossless across the JavaScript boundary.
            "seed": str(self.seed) if self.seed is not None else None,
            "steps": self.steps,
            "reference": self.reference.public() if self.reference else None,
            "references": self.references.public(),
        }


def _reference_from_value(value: Any, expected_role: str | None = None) -> H3Reference | None:
    if value in (None, ""):
        return None
    if isinstance(value, H3Reference):
        reference_id = value.id
        role = value.role
    elif isinstance(value, Mapping):
        reference_id = value.get("id")
        role = value.get("role")
    else:
        raise RequestValidationError("Reference must be an object.")
    if not isinstance(reference_id, str) or not REFERENCE_ID_PATTERN.fullmatch(reference_id):
        raise RequestValidationError("Reference id is invalid.")
    if role not in REFERENCE_ROLES:
        raise RequestValidationError("Reference role is unsupported.")
    if expected_role is not None and role != expected_role:
        raise RequestValidationError(
            f"Reference role must be {expected_role}."
        )
    return H3Reference(reference_id, role)


def validate_reference(value: Any) -> H3Reference | None:
    return _reference_from_value(value)


def validate_reference_slots(value: Any) -> H3ReferenceSlots:
    if value in (None, ""):
        return H3ReferenceSlots()
    if not isinstance(value, Mapping):
        raise RequestValidationError("References must be an object.")
    unknown = set(value).difference(REFERENCE_ROLES)
    if unknown:
        raise RequestValidationError("Reference slots are unsupported.")
    return H3ReferenceSlots(
        start_frame=_reference_from_value(
            value.get(REFERENCE_ROLE_START_FRAME), REFERENCE_ROLE_START_FRAME
        ),
        end_frame=_reference_from_value(
            value.get(REFERENCE_ROLE_END_FRAME), REFERENCE_ROLE_END_FRAME
        ),
    )


def normalize_reference_slots(
    value: Any,
) -> H3ReferenceSlots:
    """Normalize canonical slots or one legacy H1B reference."""

    if isinstance(value, H3Reference):
        if value.role == REFERENCE_ROLE_START_FRAME:
            return H3ReferenceSlots(start_frame=_reference_from_value(value))
        if value.role == REFERENCE_ROLE_END_FRAME:
            return H3ReferenceSlots(end_frame=_reference_from_value(value))
        raise RequestValidationError("Reference role is unsupported.")
    if isinstance(value, H3ReferenceSlots):
        return value
    if isinstance(value, Mapping) and "id" in value:
        return normalize_reference_slots(_reference_from_value(value))
    return validate_reference_slots(value)


def resolve_route(
    references: H3ReferenceSlots | H3Reference | Mapping[str, Any] | None,
) -> str:
    """Resolve fixed-slot presence without a user-facing mode selector."""

    normalized = normalize_reference_slots(references)
    return ROUTE_I2V if normalized.any() else ROUTE_T2V


def reference_route_label(references: H3ReferenceSlots | None) -> str:
    slots = references or H3ReferenceSlots()
    if slots.start_frame and slots.end_frame:
        return "Start + End"
    if slots.start_frame:
        return "Start Frame"
    if slots.end_frame:
        return "End Frame"
    return "Text only"


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
        raise RequestValidationError(
            "H3 currently supports the verified resolutions 608 x 352 and 736 x 416 only."
        )

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
    if duration not in ALLOWED_DURATIONS:
        raise RequestValidationError(
            "H3 currently supports the verified duration options 5 and 15 seconds only."
        )

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

    canonical_references = payload.get("references", None)
    has_canonical_references = "references" in payload
    has_legacy_reference = "reference" in payload
    if has_canonical_references:
        if has_legacy_reference and payload.get("reference") not in (None, ""):
            raise RequestValidationError(
                "Use canonical references slots instead of legacy reference."
            )
        references = validate_reference_slots(canonical_references)
        legacy_reference = False
    elif has_legacy_reference:
        legacy_reference_value = payload.get("reference")
        references = H3ReferenceSlots(
            start_frame=_reference_from_value(
                legacy_reference_value, REFERENCE_ROLE_START_FRAME
            )
        )
        legacy_reference = True
    else:
        references = H3ReferenceSlots()
        legacy_reference = False

    return H3Request(
        prompt=prompt,
        width=width,
        height=height,
        duration=duration,
        seed=seed,
        steps=steps,
        reference=references.start_frame,
        references=references,
        legacy_reference=legacy_reference,
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
