"""Shared repo-root discovery for skhema modules.

When skhema is run from source (`python -m skhema.render`), __file__ sits
inside the repo and walking up three dirnames gives the repo root. When
installed as a package (the Docker image, or `uv sync --no-editable`),
__file__ sits inside site-packages and the three-dirname trick gives you
something nonsensical. Walking up from __file__ AND from CWD looking for
a `clients/` marker is robust in both layouts.
"""
from pathlib import Path


def find_repo_root() -> str:
    """Locate the skhema repo root by walking up from this file and CWD.

    Searches both the source tree (for dev installs) and the current working
    directory (for package installs invoked from /workspace in Docker) for
    a directory containing `clients/`. Returns the first match; raises if
    neither path contains it.
    """
    seen: set[Path] = set()
    for start in (Path(__file__).resolve(), Path.cwd().resolve()):
        for parent in [start, *start.parents]:
            if parent in seen:
                continue
            seen.add(parent)
            if (parent / "clients").is_dir():
                return str(parent)

    raise RuntimeError(
        "skhema could not find the repo root (no `clients/` directory found "
        "walking up from either the package install path or the current "
        "working directory)."
    )
