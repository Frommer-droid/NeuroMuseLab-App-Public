# -*- mode: python ; coding: utf-8 -*-
"""Fail-closed portable build for NeuroMuseLab."""

import atexit
import os
import sys
import tempfile
from pathlib import Path

import PySide6


spec_dir = Path(os.path.abspath(sys.argv[0])).parent
project_root = spec_dir.parent
sys.path.insert(0, str(spec_dir))

from runtime_dll_policy import (  # noqa: E402
    prefer_pyside_msvc_runtime,
    trusted_binary_roots,
    validate_binary_origins,
)


APP_NAME = "NeuroMuseLab"
SMOKE_BUILD = os.environ.get("NEUROMUSE_BUILD_SMOKE") == "1"
BUILD_NAME = f"{APP_NAME}-Smoke" if SMOKE_BUILD else APP_NAME
ENTRYPOINT = "Build_Tools/frozen_import_smoke.py" if SMOKE_BUILD else "main.py"
EXTRA_TRUSTED_BINARY_ROOTS = ()
version = (project_root / "VERSION").read_text(encoding="utf-8").strip()
version_parts = tuple(int(part) for part in version.split("."))
if len(version_parts) != 3 or any(part < 0 or part > 65535 for part in version_parts):
    raise RuntimeError(f"Invalid VERSION for Windows executable: {version!r}")
version_tuple = (*version_parts, 0)

version_info = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple!r}, prodvers={version_tuple!r},
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)
  ),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'Frommer-droid'),
      StringStruct('FileDescription', 'NeuroMuseLab'),
      StringStruct('FileVersion', {version!r}),
      StringStruct('InternalName', 'NeuroMuseLab'),
      StringStruct('OriginalFilename', 'NeuroMuseLab.exe'),
      StringStruct('ProductName', 'NeuroMuseLab'),
      StringStruct('ProductVersion', {version!r})
    ])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)"""
with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix="-version.txt", delete=False) as handle:
    handle.write(version_info)
    version_info_path = handle.name
atexit.register(lambda: Path(version_info_path).unlink(missing_ok=True))

data_files = [(str(project_root / name), ".") for name in ("VERSION", "logo.ico", "LICENSE")]

a = Analysis(
    [str(project_root / ENTRYPOINT)],
    pathex=[str(project_root)],
    binaries=[],
    datas=data_files,
    hiddenimports=["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets", "socksio"],
    hookspath=[str(spec_dir)],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "torch", "tensorflow"],
    noarchive=False,
)

# Check the original Analysis result before replacing an older trusted Python
# runtime with the complete Qt binding runtime. A foreign DLL always fails.
trusted_roots = trusted_binary_roots(project_root, EXTRA_TRUSTED_BINARY_ROOTS)
validate_binary_origins(a.binaries, trusted_roots)
a.binaries = prefer_pyside_msvc_runtime(a.binaries, Path(PySide6.__file__).parent)
validate_binary_origins(a.binaries, trusted_roots)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=BUILD_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=SMOKE_BUILD,
    icon=str(project_root / "logo.ico"),
    version=version_info_path,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=BUILD_NAME,
)
