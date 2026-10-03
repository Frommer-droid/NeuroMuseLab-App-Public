"""Reproducible Windows portable build with native and frozen-runtime gates."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import PySide6
import shiboken6

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Build_Tools.post_build import finalize_build
from Build_Tools.runtime_dll_policy import (
    MSVC_RUNTIME_NAMES,
    trusted_binary_roots,
    validate_binary_origins,
)

BUILD_TOOLS = PROJECT_ROOT / "Build_Tools"
SPEC = BUILD_TOOLS / "NeuroMuseLab.spec"
DIST = BUILD_TOOLS / "dist"
WORK = BUILD_TOOLS / "build"
FORBIDDEN_STDERR = re.compile(r"Traceback|ImportError|DLL load failed|PyInstallerImportError|\[PYI-.*?:ERROR\]", re.IGNORECASE)


def require_project_venv() -> None:
    expected = (PROJECT_ROOT / ".venv").resolve()
    if sys.platform != "win32" or Path(sys.prefix).resolve() != expected:
        raise RuntimeError(f"Build requires Windows and the project .venv: {expected}")


def minimal_build_env(*, smoke: bool) -> dict[str, str]:
    system_root = os.environ.get("SystemRoot")
    if not system_root:
        raise RuntimeError("SystemRoot is required for a Windows build")
    path_dirs = (
        Path(sys.prefix) / "Scripts",
        Path(PySide6.__file__).resolve().parent,
        Path(shiboken6.__file__).resolve().parent,
        Path(sys.base_prefix),
        Path(sys.base_prefix) / "DLLs",
        Path(system_root) / "System32",
    )
    if not all(path.is_dir() for path in path_dirs):
        raise RuntimeError("A required Python, Qt or Windows runtime directory is missing")
    env = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH"):
        env.pop(key, None)
    env["PATH"] = os.pathsep.join(str(path) for path in path_dirs)
    env["VIRTUAL_ENV"] = str(Path(sys.prefix).resolve())
    env["NEUROMUSE_BUILD_SMOKE"] = "1" if smoke else "0"
    return env


def run_pyinstaller(*, smoke: bool) -> None:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--distpath",
        str(DIST),
        "--workpath",
        str(WORK / ("smoke" if smoke else "main")),
        str(SPEC),
    ]
    subprocess.run(command, cwd=PROJECT_ROOT, env=minimal_build_env(smoke=smoke), check=True)


def verify_collect_toc(build_name: str) -> int:
    variant = "smoke" if build_name.endswith("-Smoke") else "main"
    toc = WORK / variant / "NeuroMuseLab" / "COLLECT-00.toc"
    if not toc.is_file():
        raise FileNotFoundError(f"Missing PyInstaller collection manifest: {toc}")
    manifest = ast.literal_eval(toc.read_text(encoding="utf-8"))
    entries = manifest[0] if len(manifest) == 1 and isinstance(manifest[0], list) else manifest
    binaries = [
        (destination, source, typecode)
        for destination, source, typecode in entries
        if typecode in {"BINARY", "EXTENSION"}
    ]
    if not binaries:
        raise RuntimeError(f"No binaries recorded in {toc}")
    validate_binary_origins(binaries, trusted_binary_roots(PROJECT_ROOT))
    return len(binaries)


def verify_qt_runtime(build_name: str) -> None:
    internal = DIST / build_name / "_internal"
    qt_dir = Path(PySide6.__file__).resolve().parent
    available = {path.name.casefold(): path for path in internal.iterdir() if path.is_file()}
    for name in MSVC_RUNTIME_NAMES:
        bundled = available.get(name.casefold())
        if bundled is None:
            raise RuntimeError(f"Missing root MSVC runtime: {name}")
        qt_source = qt_dir / name
        digest = lambda path: hashlib.sha256(path.read_bytes()).digest()
        if digest(bundled) != digest(qt_source):
            raise RuntimeError(f"Root MSVC runtime does not match PySide6: {name}")


def verify_frozen_imports() -> None:
    smoke_exe = DIST / "NeuroMuseLab-Smoke" / "NeuroMuseLab-Smoke.exe"
    result = subprocess.run(
        [str(smoke_exe)],
        cwd=smoke_exe.parent,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=45,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode != 0 or "FROZEN_IMPORT_OK" not in result.stdout or FORBIDDEN_STDERR.search(
        result.stdout + result.stderr
    ):
        raise RuntimeError(
            "Frozen runtime smoke failed: "
            f"exit={result.returncode}, stdout={result.stdout[-1000:]!r}, stderr={result.stderr[-1000:]!r}"
        )


def main() -> int:
    require_project_venv()
    portable = PROJECT_ROOT / "NeuroMuseLab"
    if portable.exists():
        raise FileExistsError(f"Review and remove the exact previous portable folder before building: {portable}")
    run_pyinstaller(smoke=False)
    main_binary_count = verify_collect_toc("NeuroMuseLab")
    verify_qt_runtime("NeuroMuseLab")
    run_pyinstaller(smoke=True)
    smoke_binary_count = verify_collect_toc("NeuroMuseLab-Smoke")
    verify_qt_runtime("NeuroMuseLab-Smoke")
    verify_frozen_imports()
    result = finalize_build(PROJECT_ROOT)
    report = {
        "version": (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "main_binaries_checked": main_binary_count,
        "smoke_binaries_checked": smoke_binary_count,
        "foreign_origins": 0,
        "frozen_imports": "passed",
        "portable_folder": str(result),
    }
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "build-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
