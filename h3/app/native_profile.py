"""Pure validation for the effective H3 Native ComfyUI profile."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse


CANONICAL_H3 = "CANONICAL_H3"
PROFILE_MISMATCH = "PROFILE_MISMATCH"
PROFILE_UNVERIFIABLE = "PROFILE_UNVERIFIABLE"
UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class H3ProfileExpectation:
    native_main: str
    native_host: str
    native_port: int
    allowed_model_paths: tuple[str, ...]
    output_directory: str
    input_directory: str
    user_directory: str
    temp_directory: str
    database_url: str = "sqlite:///:memory:"


def _normalize_path(value: str | os.PathLike[str]) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(os.fspath(value))))


def build_h3_profile_expectation(base_url: str, portable_root: str | os.PathLike[str]) -> H3ProfileExpectation:
    parsed = urlparse(base_url)
    if not parsed.hostname or parsed.port is None:
        raise ValueError("H3 Native URL must include a hostname and port.")
    root = Path(portable_root).resolve()
    output = root / "output" / "h3"
    return H3ProfileExpectation(
        native_main=_normalize_path(root / "ComfyUI" / "main.py"),
        native_host=parsed.hostname.lower(),
        native_port=parsed.port,
        allowed_model_paths=tuple(
            _normalize_path(root / "h3" / "config" / filename)
            for filename in ("extra_model_paths.yaml", "extra_model_paths.local.yaml")
        ),
        output_directory=_normalize_path(output),
        input_directory=_normalize_path(output),
        user_directory=_normalize_path(output / "h3_native_user"),
        temp_directory=_normalize_path(output / "h3_native_temp"),
    )


def _result(classification: str, detail: str) -> dict[str, str]:
    return {"classification": classification, "detail": detail}


def _option_value(argv: list[str], option: str) -> tuple[str, str | None]:
    indexes = [index for index, value in enumerate(argv) if value == option]
    if len(indexes) != 1:
        return "missing" if not indexes else "unusable", None
    index = indexes[0]
    if index + 1 >= len(argv):
        return "unusable", None
    value = argv[index + 1].strip()
    if not value or value.startswith("--"):
        return "unusable", None
    return "value", value


def validate_h3_native_profile(
    system_stats: Mapping[str, Any],
    expected: H3ProfileExpectation,
) -> dict[str, str]:
    """Classify observable Native evidence without exposing raw argv."""

    system = system_stats.get("system") if isinstance(system_stats, Mapping) else None
    argv = system.get("argv") if isinstance(system, Mapping) else None
    if (
        not isinstance(argv, list)
        or not argv
        or any(not isinstance(value, str) or not value.strip() for value in argv)
    ):
        return _result(PROFILE_UNVERIFIABLE, "H3 Native profile evidence is not observable.")

    if _normalize_path(argv[0]) != expected.native_main:
        return _result(PROFILE_MISMATCH, "Native executable is not the canonical H3 entrypoint.")

    if "--disable-all-custom-nodes" not in argv:
        return _result(PROFILE_MISMATCH, "Canonical H3 custom-node isolation is missing.")

    expected_values = {
        "--listen": (expected.native_host, "H3 Native listen host"),
        "--port": (str(expected.native_port), "H3 Native port"),
        "--output-directory": (expected.output_directory, "H3 output namespace"),
        "--input-directory": (expected.input_directory, "H3 input namespace"),
        "--user-directory": (expected.user_directory, "H3 user namespace"),
        "--temp-directory": (expected.temp_directory, "H3 temp namespace"),
        "--database-url": (expected.database_url, "H3 in-memory database"),
    }
    for option, (expected_value, label) in expected_values.items():
        state, actual_value = _option_value(argv, option)
        if state == "missing":
            return _result(PROFILE_MISMATCH, f"Canonical H3 marker is missing: {option}.")
        if state != "value" or actual_value is None:
            return _result(PROFILE_UNVERIFIABLE, f"Canonical H3 marker is unusable: {option}.")
        if option in {"--output-directory", "--input-directory", "--user-directory", "--temp-directory"}:
            matches = _normalize_path(actual_value) == expected_value
        else:
            matches = actual_value.lower() == expected_value.lower() if option == "--listen" else actual_value == expected_value
        if not matches:
            return _result(PROFILE_MISMATCH, f"{label} does not match the canonical H3 profile.")

    state, model_path = _option_value(argv, "--extra-model-paths-config")
    if state == "missing":
        return _result(PROFILE_MISMATCH, "Canonical H3 model-path config is missing.")
    if state != "value" or model_path is None:
        return _result(PROFILE_UNVERIFIABLE, "Canonical H3 model-path config is unusable.")
    if _normalize_path(model_path) not in expected.allowed_model_paths:
        return _result(PROFILE_MISMATCH, "H3 model-path config is outside the canonical H3 boundary.")

    return _result(CANONICAL_H3, "Canonical H3 Native profile verified.")
