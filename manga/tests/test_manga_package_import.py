"""Real Manga package import with ACTIVE route registration (MANGA-ISOLATED-BASELINE-CORRECTION1 / B2).

Existing offline tests import individual helper modules through a synthetic
package, and without a ``server`` module ``PromptServer`` is unavailable, so
every ``if routes is not None:`` registration block was skipped.  That is how a
route registered before its handler definition (NameError at live ComfyUI
startup) escaped all offline tests.

This test imports the REAL ``tegaki_manga_nodes`` package through its
``__init__.py`` exactly the way ComfyUI loads a custom node, with minimal stubs
for the ComfyUI-provided modules only (server, folder_paths, nodes,
node_helpers, comfy.utils, comfy.sd).  Real third-party libraries (aiohttp,
torch, numpy, Pillow) are used as installed in python_embeded.

It also proves the test detects the previous regression: a copy of the package
with the page-composite registration moved above its definition must fail to
import with NameError.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import shutil
import sys
import tempfile
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
EMBEDDED_SITE = ROOT / "python_embeded" / "Lib" / "site-packages"
if EMBEDDED_SITE.exists() and str(EMBEDDED_SITE) not in sys.path:
    sys.path.append(str(EMBEDDED_SITE))

PACKAGE_DIR = ROOT / "custom_nodes_custom" / "tegaki_manga_nodes"
STUBBED = ("server", "folder_paths", "nodes", "node_helpers", "comfy", "comfy.utils", "comfy.sd")

EXPECTED_MANGA_ROUTES = {
    ("GET", "/tegaki/manga/generation/capabilities"),
    ("POST", "/tegaki/manga/generation/compile-basic"),
    ("POST", "/tegaki/manga/generation/compile-scene"),
    ("POST", "/tegaki/manga/generation/compile-isolated-scene"),
    ("POST", "/tegaki/manga/page/composite"),
}


class RecordingRoutes:
    """Stand-in for aiohttp RouteTableDef as exposed by PromptServer.instance.routes."""

    def __init__(self):
        self.registered: list[tuple[str, str, object]] = []

    def _decorator(self, method, path):
        def register(handler):
            if not callable(handler):
                raise TypeError(f"{method} {path}: handler is not callable")
            self.registered.append((method, path, handler))
            return handler
        return register

    def get(self, path, **_kw):
        return self._decorator("GET", path)

    def post(self, path, **_kw):
        return self._decorator("POST", path)


def install_comfy_stubs() -> RecordingRoutes:
    routes = RecordingRoutes()

    server = types.ModuleType("server")

    class PromptServer:
        instance = types.SimpleNamespace(routes=routes)

    server.PromptServer = PromptServer

    folder_paths = types.ModuleType("folder_paths")
    folder_paths.get_filename_list = lambda kind: []
    folder_paths.get_full_path = lambda kind, name: None
    folder_paths.get_input_directory = lambda: tempfile.gettempdir()
    folder_paths.get_output_directory = lambda: tempfile.gettempdir()
    folder_paths.get_annotated_filepath = lambda name: name
    folder_paths.models_dir = tempfile.gettempdir()

    nodes = types.ModuleType("nodes")
    nodes.NODE_CLASS_MAPPINGS = {}

    node_helpers = types.ModuleType("node_helpers")
    node_helpers.conditioning_set_values = lambda conditioning, values=None, **_kw: conditioning

    comfy = types.ModuleType("comfy")
    comfy.__path__ = []
    comfy_utils = types.ModuleType("comfy.utils")
    comfy_utils.load_torch_file = lambda *a, **k: {}
    comfy_sd = types.ModuleType("comfy.sd")
    comfy_sd.load_lora_for_models = lambda model, clip, *a, **k: (model, clip)
    comfy.utils = comfy_utils
    comfy.sd = comfy_sd

    for name, module in (
        ("server", server), ("folder_paths", folder_paths), ("nodes", nodes),
        ("node_helpers", node_helpers), ("comfy", comfy),
        ("comfy.utils", comfy_utils), ("comfy.sd", comfy_sd),
    ):
        sys.modules[name] = module
    return routes


def import_package_like_comfyui(package_dir: pathlib.Path, module_name: str):
    """Mirror ComfyUI nodes.load_custom_node: spec from <dir>/__init__.py, exec as a package."""
    spec = importlib.util.spec_from_file_location(
        module_name, str(package_dir / "__init__.py"),
        submodule_search_locations=[str(package_dir)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestRealMangaPackageImport(unittest.TestCase):
    def setUp(self):
        self._saved = {name: sys.modules.get(name) for name in STUBBED}
        self._before = set(sys.modules)
        self.routes = install_comfy_stubs()

    def tearDown(self):
        for name in set(sys.modules) - self._before:
            if name.startswith("tegaki_manga_pkg_under_test"):
                sys.modules.pop(name, None)
        for name, module in self._saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def test_real_package_imports_with_active_route_registration(self):
        # A. Import completes without exception (routes ACTIVE).
        package = import_package_like_comfyui(PACKAGE_DIR, "tegaki_manga_pkg_under_test")

        # B/C. Both Manga package nodes are registered.
        mappings = package.NODE_CLASS_MAPPINGS
        self.assertIn("TegakiMangaSceneCompiler", mappings)
        self.assertIn("TegakiMinimumHandSceneEditor", mappings)

        # Registration really ran against the stub PromptServer (not skipped).
        api = sys.modules["tegaki_manga_pkg_under_test.basic_generation_api"]
        self.assertIs(api.routes, self.routes)

        # D. basic_generation_api's Manga routes are actually registered, bound to real handlers.
        registered = {(m, p): h for m, p, h in self.routes.registered}
        self.assertTrue(EXPECTED_MANGA_ROUTES.issubset(registered.keys()),
                        f"missing: {EXPECTED_MANGA_ROUTES - set(registered)}")

        # E. The page-composite route is among them and bound to its handler.
        self.assertIs(registered[("POST", "/tegaki/manga/page/composite")], api.api_manga_page_composite)
        self.assertIs(registered[("POST", "/tegaki/manga/generation/compile-isolated-scene")],
                      api.api_manga_isolated_scene_compile)

        # No path registered twice.
        paths = [(m, p) for m, p, _ in self.routes.registered]
        self.assertEqual(len(paths), len(set(paths)))

    def test_detects_route_registered_before_definition_regression(self):
        # F. Reproduce the previous live-startup failure in a throwaway copy and
        #    prove this import path fails on it (NameError), i.e. would have caught it.
        with tempfile.TemporaryDirectory() as tmp:
            broken = pathlib.Path(tmp) / "tegaki_manga_nodes"
            shutil.copytree(PACKAGE_DIR, broken, ignore=shutil.ignore_patterns("__pycache__", "web"))
            api_path = broken / "basic_generation_api.py"
            source = api_path.read_text(encoding="utf-8")
            block = re.search(r"^if routes is not None:\n(?:    .*\n?)+", source, re.MULTILINE)
            self.assertIsNotNone(block, "registration block not found")
            without = source[:block.start()] + source[block.end():]
            anchor = "async def api_manga_page_composite("
            self.assertIn(anchor, without)
            regressed = without.replace(anchor, block.group(0).rstrip("\n") + "\n\n\n" + anchor, 1)
            api_path.write_text(regressed, encoding="utf-8")

            with self.assertRaises(NameError) as ctx:
                import_package_like_comfyui(broken, "tegaki_manga_pkg_under_test_regressed")
            self.assertIn("api_manga_page_composite", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
