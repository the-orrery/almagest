"""Portable source references and host-local source-root resolution."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field

DEFAULT_SOURCE_ROOTS_ENV = "ALMAGEST_SOURCE_ROOTS"


class SourceRef(BaseModel):
    """Identify one portable path without embedding its host-local root."""

    repository: str = Field(min_length=1)
    path: str = Field(min_length=1)


class SourceResolution(BaseModel):
    """Describe a source lookup without raising for an expected missing binding."""

    path: Path | None = None
    status: str = "ok"
    reference: str


def _expand(path: str) -> Path:
    """Expand a user-relative host-local path.

    Args:
        path: Path text from a host-local environment or overlay.

    Returns:
        Expanded filesystem path.
    """
    return Path(path).expanduser()


def source_roots_path() -> Path:
    """Return the legacy host-local source-root overlay path.

    Returns:
        The environment override, or the XDG default.
    """
    override = os.environ.get(DEFAULT_SOURCE_ROOTS_ENV)
    if override:
        return _expand(override)
    config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config_home).expanduser() / "almagest" / "source-roots.json"


def load_source_roots(path: Path | None = None) -> dict[str, Path]:
    """Load repository identity to local-root mappings.

    Args:
        path: Optional explicit overlay path. The legacy default is used when omitted.

    Returns:
        Repository identities mapped to expanded local paths.

    Raises:
        ValueError: The overlay is not a string-to-string JSON object.
    """
    target = path or source_roots_path()
    if not target.exists():
        return {}
    raw = json.loads(target.read_text())
    if not isinstance(raw, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in raw.items()
    ):
        raise ValueError("source-roots.json 必须是 repository -> 本机路径的对象")
    return {repository: _expand(root) for repository, root in raw.items()}


def source_reference(source: str | SourceRef) -> str:
    """Return the safe portable label used by diagnostics.

    Args:
        source: Legacy path text or portable source reference.

    Returns:
        ``legacy-path`` for path sources, otherwise ``repository:path``.
    """
    if isinstance(source, str):
        return "legacy-path"
    return f"{source.repository}:{source.path}"


def resolve_source(
    source: str | SourceRef,
    *,
    source_roots: dict[str, Path] | None = None,
) -> SourceResolution:
    """Resolve a source without allowing a portable path to escape its root.

    Args:
        source: Legacy path text or portable source reference.
        source_roots: Optional explicit host-local roots. The legacy overlay is
            loaded when this argument is omitted.

    Returns:
        A path and stable status code. Expected configuration failures do not raise.
    """
    reference = source_reference(source)
    if isinstance(source, str):
        return SourceResolution(path=_expand(source), reference=reference)

    roots = load_source_roots() if source_roots is None else source_roots
    root = roots.get(source.repository)
    if root is None:
        return SourceResolution(status="missing-source-root", reference=reference)
    candidate = root / source.path
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return SourceResolution(status="source-path-escape", reference=reference)
    except (OSError, RuntimeError):
        return SourceResolution(status="source-resolution-failed", reference=reference)
    return SourceResolution(path=candidate, reference=reference)
