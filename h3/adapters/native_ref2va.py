"""Bounded Native MiniMax H3 Ref2VA graph materialization.

This adapter is intentionally separate from the browser H3 route.  It accepts
only already-staged local input names and the VP2A-R1 608x352 / 5 second /
20-step feasibility contract.  One picture is always connected; one video can
be connected for the matched Picture+Video row.  Audio reference lanes are
never materialized by this adapter.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import PurePosixPath
from pathlib import Path
from typing import Any, Mapping


PORTABLE_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = PORTABLE_ROOT / "workflows" / "h3" / "VP2A_NATIVE_REF2VA_BASE.json"

FPS = 24
BASELINE_WIDTH = 608
BASELINE_HEIGHT = 352
BASELINE_DURATION_SECONDS = 5.0
BASELINE_FRAMES = 124
BASELINE_STEPS = 20
MAX_SEED = (1 << 63) - 1
MAX_PROMPT_LENGTH = 4000
REF2VA_MODEL = "minimax_h3_ref2va_pruned_int8_convrot.safetensors"
PICTURE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".mkv"}

PICTURE_PROMPT_PREFIX = "Use <Picture 1> as the subject identity and appearance reference.\n"
PICTURE_VIDEO_PROMPT_PREFIX = (
    "Use <Picture 1> for the subject identity and appearance.\n"
    "Use <Video 1> for motion, timing, and camera behavior.\n"
)


class RequestValidationError(ValueError):
    """A request is outside the bounded Native Ref2VA feasibility contract."""


class WorkflowIncompatibleError(RuntimeError):
    """The tracked Ref2VA materialization no longer matches its contract."""


@dataclass(frozen=True)
class H3Ref2VARequest:
    prompt: str
    picture_path: str
    video_path: str | None = None
    width: int = BASELINE_WIDTH
    height: int = BASELINE_HEIGHT
    duration_seconds: float = BASELINE_DURATION_SECONDS
    seed: int = 20260910
    steps: int = BASELINE_STEPS
    output_prefix: str = "video/vp2a_r1_ref2va_picture"

    def __post_init__(self) -> None:
        normalized_prompt = _validate_prompt(self.prompt)
        object.__setattr__(self, "prompt", normalized_prompt)
        _validate_picture_path(self.picture_path)
        if self.video_path is not None:
            _validate_video_path(self.video_path)
        _validate_baseline(self.width, self.height, self.duration_seconds, self.steps)
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or not 0 <= self.seed <= MAX_SEED:
            raise RequestValidationError("Seed must be an integer between 0 and 2^63-1.")
        _validate_output_prefix(self.output_prefix)

    @property
    def has_video_reference(self) -> bool:
        return self.video_path is not None

    @property
    def length_frames(self) -> int:
        return BASELINE_FRAMES

    @property
    def stage(self) -> str:
        return "picture-plus-video" if self.has_video_reference else "picture-only"


def _validate_prompt(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RequestValidationError("Prompt is required.")
    prompt = value.strip()
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise RequestValidationError(f"Prompt must be {MAX_PROMPT_LENGTH} characters or fewer.")
    return prompt


def materialize_prompt(user_prompt: Any, *, has_video: bool) -> tuple[str, str]:
    """Return the retained user prompt and its deterministic Native prompt.

    The browser accepts plain-language text.  Ref2VA still receives the
    explicit native reference roles, but there is no LLM rewrite or aesthetic
    prompt expansion in this adapter.
    """

    if not isinstance(user_prompt, str) or not user_prompt.strip():
        raise RequestValidationError("Prompt is required.")
    normalized = user_prompt.strip()
    prefix = PICTURE_VIDEO_PROMPT_PREFIX if has_video else PICTURE_PROMPT_PREFIX
    materialized = f"{prefix}{normalized}"
    if len(materialized) > MAX_PROMPT_LENGTH:
        raise RequestValidationError(
            f"Prompt must be {MAX_PROMPT_LENGTH - len(prefix)} characters or fewer for this reference route."
        )
    return normalized, materialized


def _validate_baseline(width: Any, height: Any, duration_seconds: Any, steps: Any) -> None:
    if (width, height) != (BASELINE_WIDTH, BASELINE_HEIGHT):
        raise RequestValidationError("VP2A-R1 is limited to the 608x352 baseline.")
    if duration_seconds != BASELINE_DURATION_SECONDS:
        raise RequestValidationError("VP2A-R1 is limited to the 5 second baseline.")
    if steps != BASELINE_STEPS:
        raise RequestValidationError("VP2A-R1 is limited to 20 steps.")


def _validate_staged_path(value: Any, suffixes: set[str], field: str) -> str:
    if not isinstance(value, str) or not value:
        raise RequestValidationError(f"{field} must be a staged input path.")
    if "\\" in value or ":" in value:
        raise RequestValidationError(f"{field} must use a relative POSIX input path.")
    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) != 2 or path.parts[0] != "inputs":
        raise RequestValidationError(f"{field} must be exactly inputs/<local-file>.")
    filename = path.parts[1]
    if filename in {"", ".", ".."} or ".." in path.parts:
        raise RequestValidationError(f"{field} contains an unsafe path.")
    if PurePosixPath(filename).suffix.lower() not in suffixes:
        raise RequestValidationError(f"{field} has an unsupported media type.")
    return value


def _validate_picture_path(value: Any) -> str:
    return _validate_staged_path(value, PICTURE_SUFFIXES, "picture_path")


def _validate_video_path(value: Any) -> str:
    return _validate_staged_path(value, VIDEO_SUFFIXES, "video_path")


def _validate_output_prefix(value: Any) -> str:
    if not isinstance(value, str) or not value.startswith("video/"):
        raise RequestValidationError("output_prefix must remain under the H3 video output directory.")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 2 or not path.parts[1]:
        raise RequestValidationError("output_prefix is unsafe.")
    return value


def validate_request(payload: Mapping[str, Any]) -> H3Ref2VARequest:
    if not isinstance(payload, Mapping):
        raise RequestValidationError("Request must be a JSON object.")
    return H3Ref2VARequest(
        prompt=payload.get("prompt", ""),
        picture_path=payload.get("picture_path", ""),
        video_path=payload.get("video_path"),
        width=payload.get("width", BASELINE_WIDTH),
        height=payload.get("height", BASELINE_HEIGHT),
        duration_seconds=payload.get("duration_seconds", BASELINE_DURATION_SECONDS),
        seed=payload.get("seed", 20260910),
        steps=payload.get("steps", BASELINE_STEPS),
        output_prefix=payload.get("output_prefix", "video/vp2a_r1_ref2va_picture"),
    )


def _load_workflow() -> dict[str, Any]:
    try:
        workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowIncompatibleError("Ref2VA workflow could not be loaded.") from exc
    if not isinstance(workflow, dict):
        raise WorkflowIncompatibleError("Ref2VA workflow root must be an object.")
    return workflow


def validate_workflow(workflow: Mapping[str, Any]) -> None:
    if workflow.get("schema") != "tegaki.h3.vp2a.native-ref2va/v1":
        raise WorkflowIncompatibleError("Workflow incompatible: unsupported VP2A Ref2VA schema.")
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
        "audio_decode",
        "video_decode",
        "sampler_select",
        "scheduler",
        "sampler",
        "guider",
        "model",
        "text_encoder",
        "noise",
        "video_create",
        "ref2va_conditioning",
        "picture_loader",
    }
    missing = sorted(required_roles.difference(semantic_nodes))
    if missing:
        raise WorkflowIncompatibleError(
            "Workflow incompatible: missing semantic roles " + ", ".join(missing) + "."
        )
    reference_node = prompt[str(semantic_nodes["ref2va_conditioning"]["id"])]
    reference_inputs = reference_node.get("inputs", {})
    if reference_inputs.get("ref_image_size") != "match":
        raise WorkflowIncompatibleError("Workflow incompatible: ref_image_size must remain match.")
    if "ref_video_audio_1" in reference_inputs or "ref_audio_1" in reference_inputs:
        raise WorkflowIncompatibleError("Workflow incompatible: audio reference lanes must remain disconnected.")


def compile_workflow(request: H3Ref2VARequest | Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Return one validated Native API graph for the requested R1 stage."""

    normalized = request if isinstance(request, H3Ref2VARequest) else validate_request(request)
    workflow = _load_workflow()
    validate_workflow(workflow)
    graph = deepcopy(workflow["prompt"])
    roles = workflow["semantic_nodes"]

    def node_for(role: str) -> dict[str, Any]:
        return graph[str(roles[role]["id"])]

    conditioning = node_for("ref2va_conditioning")
    conditioning["inputs"].update(
        {
            "prompt": normalized.prompt,
            "width": normalized.width,
            "height": normalized.height,
            "length": normalized.length_frames,
            "ref_image_size": "match",
            "ref_images.ref_image_1": [str(roles["picture_loader"]["id"]), 0],
        }
    )
    node_for("picture_loader")["inputs"]["image"] = normalized.picture_path
    node_for("model")["inputs"]["unet_name"] = REF2VA_MODEL
    node_for("noise")["inputs"]["noise_seed"] = normalized.seed
    node_for("scheduler")["inputs"]["steps"] = normalized.steps
    node_for("save_video")["inputs"]["filename_prefix"] = normalized.output_prefix

    motion_loader_id = str(roles["motion_loader"]["id"])
    motion_components_id = str(roles["motion_components"]["id"])
    if normalized.video_path is None:
        conditioning["inputs"].pop("ref_videos.ref_video_1", None)
        graph.pop(motion_loader_id, None)
        graph.pop(motion_components_id, None)
    else:
        node_for("motion_loader")["inputs"]["file"] = normalized.video_path
        node_for("motion_components")["inputs"]["video"] = [motion_loader_id, 0]
        conditioning["inputs"]["ref_videos.ref_video_1"] = [motion_components_id, 0]
    return graph


def workflow_metadata() -> dict[str, Any]:
    workflow = _load_workflow()
    validate_workflow(workflow)
    return {
        "schema": workflow["schema"],
        "source": workflow.get("source", {}),
        "baseline": workflow.get("baseline", {}),
    }
