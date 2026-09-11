"""
product_generation_api.py — Minimum-Hand Manga Generation HTTP Endpoint (M3B-PI2)
================================================================================
Registers HTTP route:
    POST /tegaki/manga/generation/prepare

Accepts:
    {
        "document_json": <dict or JSON string>,
        "page_index": 0,
        "seed": <optional int>,
        "prefix": <optional str>
    }

Returns:
    {
        "ok": True,
        "route": "STANDARD_NO_GUIDE" | "GUIDED_CLEAN_GLOBAL",
        "reason": "...",
        "prompt": { ... },
        "route_meta": { ... }
    }
    or error JSON with HTTP 400.
"""

from __future__ import annotations

import json
import logging
from aiohttp import web

from .product_generation_router import prepare_generation_prompt

try:
    from server import PromptServer

    routes = PromptServer.instance.routes
except Exception as e:
    logging.warning(
        f"[TegakiMangaProductGenerationAPI] PromptServer not available (running standalone?): {e}"
    )
    routes = None


async def api_manga_generation_prepare(request: web.Request) -> web.Response:
    """
    Queue-time authority endpoint: validates authoring document, evaluates route,
    and returns the executable ComfyUI prompt structure.
    """
    try:
        body = await request.json()
    except Exception as e:
        return web.json_response(
            {"ok": False, "error": f"Invalid JSON body: {e}", "error_code": "INVALID_JSON"},
            status=400,
        )

    raw_doc = body.get("document_json")
    if raw_doc is None:
        return web.json_response(
            {
                "ok": False,
                "error": "Missing required field: 'document_json'",
                "error_code": "MISSING_DOCUMENT",
            },
            status=400,
        )

    if isinstance(raw_doc, str):
        try:
            document = json.loads(raw_doc)
        except Exception as e:
            return web.json_response(
                {
                    "ok": False,
                    "error": f"Failed to parse 'document_json': {e}",
                    "error_code": "MALFORMED_DOCUMENT_JSON",
                },
                status=400,
            )
    elif isinstance(raw_doc, dict):
        document = raw_doc
    else:
        return web.json_response(
            {
                "ok": False,
                "error": "'document_json' must be an object or JSON string",
                "error_code": "INVALID_DOCUMENT_TYPE",
            },
            status=400,
        )

    page_index = body.get("page_index", 0)
    try:
        page_index = int(page_index)
    except (ValueError, TypeError):
        return web.json_response(
            {
                "ok": False,
                "error": f"Invalid 'page_index': {page_index}",
                "error_code": "INVALID_PAGE_INDEX",
            },
            status=400,
        )

    seed_override = body.get("seed")
    if seed_override is not None:
        try:
            seed_override = int(seed_override)
        except (ValueError, TypeError):
            seed_override = None

    raw_prefix = body.get("prefix", "MangaDraft_M1")
    # Sanitize prefix: alphanumeric, underscore, hyphen, forward slash only
    prefix = "".join(c for c in str(raw_prefix) if c.isalnum() or c in ("_", "-", "/")).strip()
    if not prefix:
        prefix = "MangaDraft_M1"

    try:
        result = prepare_generation_prompt(
            document=document,
            page_index=page_index,
            seed_override=seed_override,
            prefix=prefix,
        )

        status_code = 200 if result.get("ok") else 400
        return web.json_response(result, status=status_code)

    except Exception as e:
        logging.warning(f"[API /tegaki/manga/generation/prepare] Failed: {e}", exc_info=True)
        return web.json_response(
            {
                "ok": False,
                "error": str(e),
                "error_code": "INTERNAL_PREPARATION_ERROR",
            },
            status=400,
        )


if routes is not None:
    routes.post("/tegaki/manga/generation/prepare")(api_manga_generation_prepare)
    logging.info("[TegakiMangaProductGenerationAPI] Registered POST /tegaki/manga/generation/prepare")
