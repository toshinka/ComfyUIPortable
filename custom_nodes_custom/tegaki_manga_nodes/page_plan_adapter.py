"""Thin STRING -> PAGE_COMPILE_PLAN transport adapter for Manga Scene jobs.

The authoring document and page-plan compiler remain the backend authorities.
This node only parses the reviewed JSON transport value and delegates schema
validation to the existing PAGE_COMPILE_PLAN contract before conditioning.
"""

from __future__ import annotations

import json
from typing import Any, Tuple

from .scene_spec import validate_page_compile_plan


class TegakiMangaPagePlanFromJSON:
    """Validate a backend-compiled page plan without adding generation logic."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "page_compile_plan_json": ("STRING", {"multiline": True, "default": "{}"}),
            }
        }

    RETURN_TYPES = ("PAGE_COMPILE_PLAN",)
    RETURN_NAMES = ("page_compile_plan",)
    FUNCTION = "parse_page_compile_plan"
    CATEGORY = "tegaki/manga"

    def parse_page_compile_plan(self, page_compile_plan_json: str) -> Tuple[Any]:
        if not isinstance(page_compile_plan_json, str) or not page_compile_plan_json.strip():
            raise ValueError("[TegakiPagePlanAdapter] page_compile_plan_json must be non-empty JSON text")
        try:
            plan = json.loads(page_compile_plan_json)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"[TegakiPagePlanAdapter] Invalid PAGE_COMPILE_PLAN JSON: {exc}") from exc
        try:
            return (validate_page_compile_plan(plan),)
        except ValueError as exc:
            raise ValueError(f"[TegakiPagePlanAdapter] Invalid PAGE_COMPILE_PLAN: {exc}") from exc
