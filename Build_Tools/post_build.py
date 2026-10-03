"""Move a verified portable build without copying local runtime state."""

from __future__ import annotations

import shutil
from pathlib import Path

APP_NAME = "NeuroMuseLab"
PUBLIC_RESOURCES = ("logo.ico", "VERSION", "LICENSE")


def finalize_build(project_root: Path) -> Path:
    project_root = project_root.resolve()
    dist_app = (project_root / "Build_Tools" / "dist" / APP_NAME).resolve()
    final_app = (project_root / APP_NAME).resolve()
    if not dist_app.is_relative_to(project_root) or not final_app.is_relative_to(project_root):
        raise RuntimeError("Build paths escape the project root")
    if not (dist_app / f"{APP_NAME}.exe").is_file():
        raise FileNotFoundError(f"Portable executable is missing: {dist_app}")
    if final_app.exists():
        raise FileExistsError(f"Existing portable folder must be reviewed first: {final_app}")

    for name in PUBLIC_RESOURCES:
        source = project_root / name
        if not source.is_file():
            raise FileNotFoundError(f"Required public resource is missing: {source}")
        shutil.copy2(source, dist_app / name)

    shutil.move(str(dist_app), str(final_app))
    return final_app


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    print(f"Portable folder: {finalize_build(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
