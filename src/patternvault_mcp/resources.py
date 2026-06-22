"""MCP resources backed by PatternVault Markdown files."""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastmcp import FastMCP

from patternvault_mcp.settings import Settings


README_PATTERN = "*.md"


def register_resources(mcp: FastMCP, settings: Settings) -> None:
    """Register all PatternVault README resources on the server."""

    readmes_dir = settings.readmes_dir.resolve()

    @mcp.resource(
        "patternvault://readmes/index",
        name="patternvault_readmes_index",
        title="PatternVault README Index",
        description="Index of Markdown pattern resources available in PatternVault.",
        mime_type="application/json",
        tags={"patternvault", "readmes"},
    )
    def readmes_index() -> str:
        resources = [
            {
                "slug": _slug_for_file(path),
                "title": _title_for_file(path),
                "uri": _uri_for_file(path),
                "filename": path.name,
            }
            for path in _iter_readme_files(readmes_dir)
        ]
        return json.dumps({"resources": resources}, indent=2)

    for path in _iter_readme_files(readmes_dir):
        _register_readme_resource(mcp, path)


def _register_readme_resource(mcp: FastMCP, path: Path) -> None:
    slug = _slug_for_file(path)
    uri = _uri_for_file(path)

    def read_readme() -> str:
        return path.read_text(encoding="utf-8")

    read_readme.__name__ = f"readme_{_python_identifier(slug)}"

    mcp.resource(
        uri,
        name=read_readme.__name__,
        title=_title_for_file(path),
        description=f"PatternVault Markdown resource from {path.name}.",
        mime_type="text/markdown",
        tags={"patternvault", "readmes"},
    )(read_readme)


def _iter_readme_files(readmes_dir: Path) -> list[Path]:
    if not readmes_dir.exists():
        return []

    return sorted(
        path
        for path in readmes_dir.glob(README_PATTERN)
        if path.is_file() and not path.name.startswith(".")
    )


def _uri_for_file(path: Path) -> str:
    return f"patternvault://readmes/{_slug_for_file(path)}"


def _slug_for_file(path: Path) -> str:
    return path.stem.lower().replace("_", "-")


def _title_for_file(path: Path) -> str:
    title = re.sub(r"^\d+[-_ ]*", "", path.stem)
    return title.replace("-", " ").replace("_", " ").title()


def _python_identifier(value: str) -> str:
    return re.sub(r"\W+", "_", value).strip("_")
