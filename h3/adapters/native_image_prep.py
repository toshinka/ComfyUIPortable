"""Bounded Native H3 IP1 image-prep/reference-edit materialization.

This is a feasibility adapter, not a Browser route or a generic image-editing
API.  It uses the installed Native ``MiniMaxH3ReferenceToVideo`` node with one
required source Picture and at most one optional donor Picture, then selects
decoded frame 0 from the required five-frame temporal packet.  The existing
VP2B ``native_ref2va`` adapter remains unchanged.
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
)
from h3.adapters.native_t2v import (
    RequestValidationError,
    WorkflowIncompatibleError,
)


PORTABLE_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = PORTABLE_ROOT / "workflows" / "h3" / "IP1_NATIVE_IMAGE_PREP_BASE.json"

SCHEMA = "tegaki.h3.ip1.native-image-prep/v1"
ROUTE_IMAGE_PREP = "native_image_prep"
FPS = 24
MAX_SEED = (1 << 63) - 1
PICTURE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
REF2VA_MODEL = "minimax_h3_ref2va_pruned_int8_convrot.safetensors"
SOURCE_IMAGE_ROLE = "source_image_loader"
DONOR_IMAGE_ROLE = "donor_image_loader"

SOURCE_PROMPT_PREFIX = (
    "Use <Picture 1> as the source subject and composition reference. "
    "Preserve its recognizable identity and general framing.\n"
)
DONOR_PROMPT_PREFIX = (
    "Use <Picture 2> only as the donor for the requested attribute. "
    "Do not replace the whole scene.\n"
)


@dataclass(frozen=True)
class H3ImagePrepRequest:
    prompt: str
    source_path: str
    donor_path: str | None = None
    width: int = WIDTH
    height: int = HEIGHT
    length: int = PACKET_FRAMES
    fps: int = FPS
    seed: int = 0
    steps: int = DEFAULT_STEPS

    def __post_init__(self) -> None:
        normalized_prompt = _validate_prompt(self.prompt)
        object.__setattr__(self, "prompt", normalized_prompt)
        _validate_staged_image_path(self.source_path, "source_path")
        if self.donor_path is not None:
            _validate_staged_image_path(self.donor_path, "donor_path")
        _validate_baseline(self.width, self.height, self.length, self.fps, self.steps)
        if (
            isinstance(self.seed, bool)
            or not isinstance(self.seed, int)
            or not 0 <= self.seed <= MAX_SEED
        ):
            raise RequestValidationError("Seed must be an integer between 0 and 2^63-1.")

    @property
    def has_donor(self) -> bool:
        return self.donor_path is not None

    def public(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "width": self.width,
            "height": self.height,
            "length": self.length,
            "fps": self.fps,
            "seed": str(self.seed),
            "steps": self.steps,
            "reference_roles": {
                "Picture 1": "source",
                "Picture 2": "optional donor attribute" if self.has_donor else None,
            },
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


def _validate_prompt(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RequestValidationError("Prompt is required.")
    prompt = value.strip()
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise RequestValidationError(f"Prompt must be {MAX_PROMPT_LENGTH} characters or fewer.")
    return prompt


def _validate_staged_image_path(value: Any, field: str) -> str:
    """Accept exactly one server-staged image name below ``inputs/``."""

    if not isinstance(value, str) or not value or len(value) > 240:
        raise RequestValidationError(f"{field} must be a staged local image path.")
    lowered = value.lower()
    if (
        "\\" in value
        or ":" in value
        or lowered.startswith(("file://", "http://", "https://"))
        or "[" in value
        or "]" in value
    ):
        raise RequestValidationError(f"{field} must be a relative POSIX input path.")
    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) != 2 or path.parts[0] != "inputs":
        raise RequestValidationError(f"{field} must be exactly inputs/<local-file>.")
    filename = path.parts[1]
    if filename in {"", ".", ".."} or ".." in path.parts:
        raise RequestValidationError(f"{field} contains an unsafe path.")
    if PurePosixPath(filename).suffix.lower() not in PICTURE_SUFFIXES:
        raise RequestValidationError(f"{field} must be PNG, JPEG, or WebP.")
    return path.as_posix()


def _validate_baseline(width: Any, height: Any, length: Any, fps: Any, steps: Any) -> None:
    if (width, height) != (WIDTH, HEIGHT):
        raise RequestValidationError("IP1 is limited to the 608x352 baseline.")
    if length != PACKET_FRAMES:
        raise RequestValidationError("IP1 is limited to one five-frame Native packet.")
    if fps != FPS:
        raise RequestValidationError("IP1 keeps the 24 fps basis for packet metadata.")
    if steps != DEFAULT_STEPS:
        raise RequestValidationError("IP1 is limited to the verified 20-step baseline.")


def materialize_prompt(user_prompt: Any, *, has_donor: bool) -> tuple[str, str]:
    """Add deterministic Native Picture roles without LLM rewriting."""

    normalized = _validate_prompt(user_prompt)
    prefix = SOURCE_PROMPT_PREFIX + (DONOR_PROMPT_PREFIX if has_donor else "")
    if len(prefix) + len(normalized) > MAX_PROMPT_LENGTH:
        raise RequestValidationError(
            f"Prompt must be {MAX_PROMPT_LENGTH - len(prefix)} characters or fewer for IP1."
        )
    return normalized, f"{prefix}{normalized}"


def _reject_extra_reference_lanes(payload: Mapping[str, Any]) -> None:
    lane_keys = {
        "references",
        "ref_images",
        "source_images",
        "donor_images",
        "third_picture",
        "third_picture_path",
        "fourth_picture",
        "fourth_picture_path",
        "video_reference",
        "video_path",
        "audio_reference",
        "audio_path",
        "ref_videos",
        "ref_audios",
        "ref_video_audios",
    }
    for key in lane_keys:
        if key in payload and payload[key] not in (None, "", {}, []):
            raise RequestValidationError(
                "IP1 accepts one source Picture and at most one donor Picture; video/audio and third/fourth references are rejected."
            )


def validate_request(payload: Mapping[str, Any]) -> H3ImagePrepRequest:
    """Validate the narrow source-plus-optional-donor IP1 contract."""

    if not isinstance(payload, Mapping):
        raise RequestValidationError("IP1 request must be a JSON object.")
    _reject_extra_reference_lanes(payload)
    allowed = {
        "prompt",
        "source_path",
        "donor_path",
        "width",
        "height",
        "length",
        "fps",
        "seed",
        "steps",
        "references",
        "ref_images",
        "source_images",
        "donor_images",
        "third_picture",
        "third_picture_path",
        "fourth_picture",
        "fourth_picture_path",
        "video_reference",
        "video_path",
        "audio_reference",
        "audio_path",
        "ref_videos",
        "ref_audios",
        "ref_video_audios",
    }
    unknown = sorted(set(payload).difference(allowed))
    if unknown:
        raise RequestValidationError("IP1 request contains unsupported fields: " + ", ".join(unknown))

    width = _coerce_int(payload.get("width", WIDTH), "Width")
    height = _coerce_int(payload.get("height", HEIGHT), "Height")
    length = _coerce_int(payload.get("length", PACKET_FRAMES), "Length")
    fps = _coerce_int(payload.get("fps", FPS), "FPS")
    steps = _coerce_int(payload.get("steps", DEFAULT_STEPS), "Steps")
    seed_value = payload.get("seed")
    if seed_value in (None, "", "random"):
        seed = random.SystemRandom().randint(0, MAX_SEED)
    else:
        seed = _coerce_int(seed_value, "Seed")
    return H3ImagePrepRequest(
        prompt=payload.get("prompt", ""),
        source_path=payload.get("source_path", ""),
        donor_path=payload.get("donor_path"),
        width=width,
        height=height,
        length=length,
        fps=fps,
        seed=seed,
        steps=steps,
    )


def _load_workflow() -> dict[str, Any]:
    try:
        workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowIncompatibleError("IP1 workflow could not be loaded.") from exc
    if not isinstance(workflow, dict):
        raise WorkflowIncompatibleError("IP1 workflow root must be an object.")
    return workflow


def _node(
    graph: Mapping[str, Mapping[str, Any]],
    roles: Mapping[str, Any],
    role: str,
) -> Mapping[str, Any]:
    return graph[str(roles[role]["id"])]


def validate_workflow(workflow: Mapping[str, Any]) -> None:
    if workflow.get("schema") != SCHEMA:
        raise WorkflowIncompatibleError("Workflow incompatible: unsupported IP1 schema.")
    prompt = workflow.get("prompt")
    roles = workflow.get("semantic_nodes")
    if not isinstance(prompt, Mapping) or not isinstance(roles, Mapping):
        raise WorkflowIncompatibleError("Workflow incompatible: semantic graph is missing.")

    required_roles = {
        "save_image",
        "video_vae",
        "audio_vae",
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
        DONOR_IMAGE_ROLE,
    }
    missing = sorted(required_roles.difference(roles))
    if missing:
        raise WorkflowIncompatibleError("Workflow incompatible: missing semantic roles " + ", ".join(missing) + ".")

    for role, expected in roles.items():
        if not isinstance(expected, Mapping):
            raise WorkflowIncompatibleError(f"Workflow incompatible: {role} contract is invalid.")
        node_id = str(expected.get("id"))
        expected_class = expected.get("class_type")
        node = prompt.get(node_id)
        if not isinstance(node, Mapping) or node.get("class_type") != expected_class:
            raise WorkflowIncompatibleError(
                f"Workflow incompatible: semantic node {role} is not {expected_class}."
            )

    forbidden_classes = {
        "SaveVideo",
        "CreateVideo",
        "VAEDecodeAudio",
        "LoadVideo",
        "GetVideoComponents",
    }
    present_forbidden = sorted(
        str(node.get("class_type"))
        for node in prompt.values()
        if isinstance(node, Mapping) and node.get("class_type") in forbidden_classes
    )
    if present_forbidden:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: IP1 image-prep graph contains video/audio lanes."
        )

    conditioning = _node(prompt, roles, "conditioning_latent")
    inputs = conditioning.get("inputs")
    if conditioning.get("class_type") != "MiniMaxH3ReferenceToVideo" or not isinstance(inputs, Mapping):
        raise WorkflowIncompatibleError(
            "Workflow incompatible: IP1 conditioning must be MiniMaxH3ReferenceToVideo."
        )
    if inputs.get("width") != WIDTH or inputs.get("height") != HEIGHT:
        raise WorkflowIncompatibleError("Workflow incompatible: IP1 canvas must be 608x352.")
    if inputs.get("length") != PACKET_FRAMES:
        raise WorkflowIncompatibleError("Workflow incompatible: IP1 packet must contain exactly five frames.")
    if inputs.get("ref_image_size") != "match":
        raise WorkflowIncompatibleError("Workflow incompatible: IP1 ref_image_size must remain match.")
    source_id = str(roles[SOURCE_IMAGE_ROLE]["id"])
    donor_id = str(roles[DONOR_IMAGE_ROLE]["id"])
    if inputs.get("ref_images.ref_image_1") != [source_id, 0]:
        raise WorkflowIncompatibleError("Workflow incompatible: Picture 1 must bind the source loader.")
    if inputs.get("ref_images.ref_image_2") != [donor_id, 0]:
        raise WorkflowIncompatibleError("Workflow incompatible: Picture 2 must bind the donor loader in the base graph.")
    if any(str(key).startswith(("ref_video", "ref_audio")) for key in inputs):
        raise WorkflowIncompatibleError("Workflow incompatible: IP1 video/audio references must remain disconnected.")

    for role in (SOURCE_IMAGE_ROLE, DONOR_IMAGE_ROLE):
        loader = _node(prompt, roles, role)
        if loader.get("class_type") != "LoadImage":
            raise WorkflowIncompatibleError(f"Workflow incompatible: {role} must be one LoadImage node.")
        _validate_staged_image_path(loader.get("inputs", {}).get("image"), role)

    select = _node(prompt, roles, "select_frame")
    select_inputs = select.get("inputs", {})
    if (
        select.get("class_type") != "ImageFromBatch"
        or select_inputs.get("image") != [str(roles["video_decode"]["id"]), 0]
        or select_inputs.get("batch_index") != SELECTED_FRAME_INDEX
        or select_inputs.get("length") != 1
    ):
        raise WorkflowIncompatibleError("Workflow incompatible: IP1 must select decoded frame 0 only.")


def _validated_workflow() -> dict[str, Any]:
    workflow = _load_workflow()
    validate_workflow(workflow)
    return workflow


def compile_workflow(
    request: H3ImagePrepRequest | Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Materialize one bounded IP1 graph for Native ``/prompt``."""

    normalized = request if isinstance(request, H3ImagePrepRequest) else validate_request(request)
    source_path = _validate_staged_image_path(normalized.source_path, "source_path")
    donor_path = (
        _validate_staged_image_path(normalized.donor_path, "donor_path")
        if normalized.donor_path is not None
        else None
    )
    workflow = _validated_workflow()
    graph = deepcopy(workflow["prompt"])
    roles = workflow["semantic_nodes"]

    def node_for(role: str) -> dict[str, Any]:
        return graph[str(roles[role]["id"])]

    _, materialized = materialize_prompt(normalized.prompt, has_donor=donor_path is not None)
    conditioning = node_for("conditioning_latent")
    conditioning["inputs"].update(
        {
            "prompt": materialized,
            "width": normalized.width,
            "height": normalized.height,
            "length": normalized.length,
            "ref_image_size": "match",
            "ref_images.ref_image_1": [str(roles[SOURCE_IMAGE_ROLE]["id"]), 0],
        }
    )
    node_for(SOURCE_IMAGE_ROLE)["inputs"]["image"] = source_path
    node_for("noise")["inputs"]["noise_seed"] = normalized.seed
    node_for("scheduler")["inputs"]["steps"] = normalized.steps
    node_for("save_image")["inputs"]["filename_prefix"] = "still/ip1_native_image_prep"
    if donor_path is None:
        conditioning["inputs"].pop("ref_images.ref_image_2", None)
        graph.pop(str(roles[DONOR_IMAGE_ROLE]["id"]), None)
    else:
        node_for(DONOR_IMAGE_ROLE)["inputs"]["image"] = donor_path
        conditioning["inputs"]["ref_images.ref_image_2"] = [str(roles[DONOR_IMAGE_ROLE]["id"]), 0]
    return graph


def workflow_metadata() -> dict[str, Any]:
    workflow = _validated_workflow()
    return {
        "route": ROUTE_IMAGE_PREP,
        "schema": workflow["schema"],
        "source": workflow.get("source", {}),
        "baseline": workflow.get("baseline", {}),
        "reference_roles": {
            "Picture 1": "required source",
            "Picture 2": "optional donor attribute",
        },
        "browser_ui": "NOT IMPLEMENTED",
        "custom_nodes": "none",
        "audio_reference": "not connected",
    }
