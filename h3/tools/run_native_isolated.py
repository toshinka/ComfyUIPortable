"""Start Native ComfyUI without its machine-wide extra model-path file.

ComfyUI always auto-loads ``ComfyUI/extra_model_paths.yaml`` before applying
the explicit ``--extra-model-paths-config`` arguments. That file belongs to
the shared EasyReforge/Illustrious environment, so H3 uses this small
stdlib-only launcher shim to suppress only that exact auto-load. The Native
runtime, workflow, and explicit H3 config remain unchanged.
"""

from __future__ import annotations

import os
from pathlib import Path
import runpy
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
NATIVE_MAIN = REPO_ROOT / "ComfyUI" / "main.py"
SHARED_EXTRA_CONFIG = os.path.normcase(
    os.path.abspath(os.fspath(REPO_ROOT / "ComfyUI" / "extra_model_paths.yaml"))
)


def _isfile_without_shared_config(path: os.PathLike[str] | str) -> bool:
    candidate = os.path.normcase(os.path.abspath(os.fspath(path)))
    if candidate == SHARED_EXTRA_CONFIG:
        return False
    return _REAL_ISFILE(path)


if not NATIVE_MAIN.is_file():
    raise SystemExit(f"Native ComfyUI entrypoint is missing: {NATIVE_MAIN}")

_REAL_ISFILE = os.path.isfile
os.path.isfile = _isfile_without_shared_config
sys.argv = [os.fspath(NATIVE_MAIN), *sys.argv[1:]]
runpy.run_path(os.fspath(NATIVE_MAIN), run_name="__main__")
