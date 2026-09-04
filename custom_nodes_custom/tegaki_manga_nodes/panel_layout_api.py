import json
import logging
from aiohttp import web

from .panel_layout_spec import validate_panel_layout_spec
from .panel_layout_split import generic_split_panel

try:
    from server import PromptServer
    routes = PromptServer.instance.routes
except Exception as e:
    logging.warning(f"[TegakiMangaPanelLayout] PromptServer not available (running standalone?): {e}")
    routes = None


async def api_panel_layout_split(request):
    """
    Frontend Split の Single Source of Truth (SSOT) API ルート。
    Python backend の generic_split_panel() を直接実行して Canonical Spec を返却する。
    """
    try:
        body = await request.json()
        raw_spec = body.get("spec")
        panel_id = body.get("panel_id")
        split_mode = body.get("split_mode", "horizontal")
        split_ratio = float(body.get("split_ratio", 0.5))

        if not raw_spec or not panel_id:
            return web.json_response(
                {"ok": False, "error": "Missing required fields: 'spec' and 'panel_id'."},
                status=400
            )

        # 1. 既存 Spec の事前検証
        spec = validate_panel_layout_spec(raw_spec, context_name="API.split.input")

        # 2. 一般分割アルゴリズムの実行 (交点頂点伝播・T-Junction排除)
        new_spec = generic_split_panel(spec, panel_id, split_mode=split_mode, split_ratio=split_ratio)

        # 3. 分割後 Spec の厳格トポロジー検証
        validated_spec = validate_panel_layout_spec(new_spec, context_name="API.split.output")

        return web.json_response({
            "ok": True,
            "spec": validated_spec,
            "topology_summary": validated_spec.get("metadata", {}).get("topology_summary", {})
        })

    except Exception as e:
        logging.warning(f"[API /tegaki/panel-layout/split] Failed: {e}")
        return web.json_response({
            "ok": False,
            "error": str(e)
        }, status=400)


async def api_panel_layout_validate(request):
    """
    Frontend ドラッグ操作の確定 (mouse up) 時、および手動編集時の
    幾何トポロジー検証 API ルート。
    """
    try:
        body = await request.json()
        raw_spec = body.get("spec")

        if not raw_spec:
            return web.json_response(
                {"ok": False, "error": "Missing required field: 'spec'."},
                status=400
            )

        validated_spec = validate_panel_layout_spec(raw_spec, context_name="API.validate")

        return web.json_response({
            "ok": True,
            "spec": validated_spec,
            "topology_summary": validated_spec.get("metadata", {}).get("topology_summary", {})
        })

    except Exception as e:
        logging.warning(f"[API /tegaki/panel-layout/validate] Validation failed: {e}")
        return web.json_response({
            "ok": False,
            "error": str(e)
        }, status=400)


if routes is not None:
    routes.post("/tegaki/panel-layout/split")(api_panel_layout_split)
    routes.post("/tegaki/panel-layout/validate")(api_panel_layout_validate)

